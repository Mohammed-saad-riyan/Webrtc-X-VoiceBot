#!/usr/bin/env python3
"""
Simple Voice Assistant
A working voice-only assistant using OpenAI APIs
"""

import asyncio
import os
import sys
from datetime import date

from dotenv import load_dotenv
from loguru import logger

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.frames.frames import EndFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.services.openai.tts import OpenAITTSService
from pipecat.services.whisper.stt import WhisperSTTService
from pipecat.transports.services.daily import DailyParams, DailyTransport
from pipecat.transports.services.helpers.daily_rest import DailyRESTHelper, DailyRoomParams

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

load_dotenv(override=True)

logger.remove(0)
logger.add(sys.stderr, level="DEBUG")

# Customize your AI assistant personality here!
SYSTEM_PROMPT = f"""You are a helpful voice assistant. Keep your responses:
- Brief and conversational (1-2 sentences max)
- Natural and friendly
- Avoid special characters since this will be spoken aloud

Today is {date.today().strftime("%A, %B %d, %Y")}.

You can help with questions, have conversations, or just chat!
"""

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Daily REST helper for creating rooms
daily_rest_helper = DailyRESTHelper(
    daily_api_key=os.getenv("DAILY_API_KEY"),
    daily_api_url=os.getenv("DAILY_API_URL", "https://api.daily.co/v1"),
)

async def create_room_and_token():
    """Create a Daily room and token for the voice session."""
    # Create a new room
    room = await daily_rest_helper.create_room(DailyRoomParams())
    room_url = room.url
    
    # Create a token for the room
    token = await daily_rest_helper.create_token(room_url)
    
    return room_url, token

async def start_voice_bot(room_url: str, token: str):
    """Start the voice bot in the given room."""
    
    # Set up VOICE-ONLY transport
    transport = DailyTransport(
        room_url,
        token,
        "Voice Assistant",
        DailyParams(
            audio_in_sample_rate=16000,
            audio_out_sample_rate=24000,
            audio_out_enabled=True,
            camera_out_enabled=False,  # No video
            camera_in_enabled=False,   # No video
            vad_enabled=True,
            vad_audio_passthrough=True,
            vad_analyzer=SileroVADAnalyzer(params=VADParams(stop_secs=1.0)),
        ),
    )

    # Set up the AI services
    stt = WhisperSTTService(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="whisper-1"
    )

    llm = OpenAILLMService(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o-mini",
    )

    tts = OpenAITTSService(
        api_key=os.getenv("OPENAI_API_KEY"),
        voice="alloy",
    )

    # Set up conversation context
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "assistant", "content": "Hi! I'm your voice assistant. What can I help you with?"}
    ]
    
    context = OpenAILLMContext(messages)
    context_aggregator = llm.create_context_aggregator(context)

    # Create the pipeline
    pipeline = Pipeline([
        transport.input(),
        stt,
        context_aggregator.user(),
        llm,
        tts,
        transport.output(),
        context_aggregator.assistant(),
    ])

    task = PipelineTask(
        pipeline,
        PipelineParams(
            allow_interruptions=True,
            enable_metrics=True,
            enable_usage_metrics=True,
        ),
    )

    @transport.event_handler("on_first_participant_joined")
    async def on_first_participant_joined(transport, participant):
        print(f"👋 User joined: {participant['info']['userName'] or 'Guest'}")
        await task.queue_frames([context_aggregator.user().get_context_frame()])

    @transport.event_handler("on_participant_left")
    async def on_participant_left(transport, participant, reason):
        print(f"👋 User left: {participant}")
        await task.queue_frame(EndFrame())

    # Run the voice assistant
    runner = PipelineRunner()
    print("🚀 Voice Assistant is ready!")
    await runner.run(task)

@app.get("/")
async def start_session():
    """Start a new voice session."""
    
    # Check for required API keys
    if not os.getenv("OPENAI_API_KEY"):
        return {"error": "OPENAI_API_KEY not found"}
    if not os.getenv("DAILY_API_KEY"):
        return {"error": "DAILY_API_KEY not found"}
    
    print("Creating room and starting voice bot...")
    room_url, token = await create_room_and_token()
    
    print(f"🎤 Room created: {room_url}")
    
    # Start the bot in the background
    asyncio.create_task(start_voice_bot(room_url, token))
    
    return {
        "room_url": room_url,
        "token": token,
        "room_name": "voice-assistant"
    }

if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Please add OPENAI_API_KEY to your .env file")
        sys.exit(1)
    if not os.getenv("DAILY_API_KEY"):
        print("❌ Please add DAILY_API_KEY to your .env file")
        sys.exit(1)
        
    print("🎤 Starting Simple Voice Assistant Server...")
    uvicorn.run(app, host="0.0.0.0", port=7860) 