#!/usr/bin/env python3
"""
Real-time Voice Assistant
Voice Input → Transcription → LLM → Text-to-Speech → Voice Output

This creates a simple voice-only assistant that:
1. Listens to your voice
2. Transcribes it using Whisper
3. Sends transcription to an LLM (OpenAI/Claude/etc)
4. Converts LLM response to speech
5. Plays the speech back to you
"""

import asyncio
import os
import sys
from datetime import date

import aiohttp
from dotenv import load_dotenv
from loguru import logger

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.frames.frames import Frame, EndFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.services.openai.tts import OpenAITTSService
from pipecat.services.whisper.stt import WhisperSTTService
from pipecat.transports.services.daily import DailyParams, DailyTransport

# We'll use the server's create_room_and_token function instead

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

async def main():
    """Main voice assistant function."""
    
    # You'll need to add OPENAI_API_KEY to your .env file
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Please add OPENAI_API_KEY to your .env file")
        print("Get one at: https://platform.openai.com/api-keys")
        return
    
    # Use the server approach to create Daily room
    from server import create_room_and_token
    
    room_url, token = await create_room_and_token()

    print(f"🎤 Starting Voice Assistant...")
    print(f"🔗 Join at: {room_url}")

    # Set up VOICE-ONLY transport (no video!)
    transport = DailyTransport(
        room_url,
        token,
        "Voice Assistant",
        DailyParams(
            audio_in_sample_rate=16000,   # Good for speech recognition
            audio_out_sample_rate=24000,  # Good for speech synthesis
            audio_out_enabled=True,
            camera_out_enabled=False,     # No video output
            camera_in_enabled=False,      # No video input
            vad_enabled=True,             # Voice Activity Detection
            vad_audio_passthrough=True,
            vad_analyzer=SileroVADAnalyzer(params=VADParams(stop_secs=1.0)),
        ),
    )

    # 1. Speech-to-Text: Your voice → text
    stt = WhisperSTTService(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="whisper-1"
    )

    # 2. LLM: Text → intelligent response
    llm = OpenAILLMService(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o-mini",  # Fast and cheap for conversation
    )

    # 3. Text-to-Speech: Response text → voice
    tts = OpenAITTSService(
        api_key=os.getenv("OPENAI_API_KEY"),
        voice="alloy",  # Options: alloy, echo, fable, onyx, nova, shimmer
    )

    # Set up conversation context
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "assistant", "content": "Hi! I'm your voice assistant. What can I help you with?"}
    ]
    
    context = OpenAILLMContext(messages)
    context_aggregator = llm.create_context_aggregator(context)

    # Create the pipeline: Input → STT → LLM → TTS → Output
    pipeline = Pipeline([
        transport.input(),      # Capture audio from microphone
        stt,                   # Speech to text
        context_aggregator.user(),  # Add to conversation context
        llm,                   # Get LLM response
        tts,                   # Convert response to speech
        transport.output(),    # Play speech back
        context_aggregator.assistant(),  # Save assistant response
    ])

    task = PipelineTask(
        pipeline,
        PipelineParams(
            allow_interruptions=True,  # Let user interrupt the AI
            enable_metrics=True,
            enable_usage_metrics=True,
        ),
    )

    @transport.event_handler("on_first_participant_joined")
    async def on_first_participant_joined(transport, participant):
        print(f"👋 User joined: {participant['info']['userName'] or 'Guest'}")
        # Start the conversation
        await task.queue_frames([context_aggregator.user().get_context_frame()])

    @transport.event_handler("on_participant_left")
    async def on_participant_left(transport, participant, reason):
        print(f"👋 User left: {participant}")
        await task.queue_frame(EndFrame())

    # Run the voice assistant
    runner = PipelineRunner()
    print("🚀 Voice Assistant is ready! Join the room and start talking...")
    await runner.run(task)

if __name__ == "__main__":
    asyncio.run(main()) 