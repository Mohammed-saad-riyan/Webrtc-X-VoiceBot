#
# Copyright (c) 2024, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

"""RTVI Bot Server Implementation.

This FastAPI server manages RTVI bot instances and provides endpoints for both
direct browser access and RTVI client connections. It handles:
- Creating Daily rooms
- Managing bot processes
- Providing connection credentials
- Monitoring bot status

Requirements:
- Daily API key (set in .env file)
- Python 3.10+
- FastAPI
- Running bot implementation
"""

import argparse
import os
import subprocess
from contextlib import asynccontextmanager
from typing import Any, Dict

import aiohttp
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse

from pipecat.transports.services.helpers.daily_rest import DailyRESTHelper, DailyRoomParams

# Load environment variables from .env file
load_dotenv(override=True)

# Maximum number of bot instances allowed per room
MAX_BOTS_PER_ROOM = 1

# Dictionary to track bot processes: {pid: (process, room_url)}
bot_procs = {}

# Store Daily API helpers
daily_helpers = {}


def cleanup():
    """Cleanup function to terminate all bot processes.

    Called during server shutdown.
    """
    for entry in bot_procs.values():
        proc = entry[0]
        proc.terminate()
        proc.wait()


def get_bot_file():
    return "bot-gemini"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan manager that handles startup and shutdown tasks.

    - Creates aiohttp session
    - Initializes Daily API helper
    - Cleans up resources on shutdown
    """
    aiohttp_session = aiohttp.ClientSession()
    daily_helpers["rest"] = DailyRESTHelper(
        daily_api_key=os.getenv("DAILY_API_KEY", ""),
        daily_api_url=os.getenv("DAILY_API_URL", "https://api.daily.co/v1"),
        aiohttp_session=aiohttp_session,
    )
    yield
    await aiohttp_session.close()
    cleanup()


# Initialize FastAPI app with lifespan manager
app = FastAPI(lifespan=lifespan)

# Configure CORS to allow requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def create_room_and_token() -> tuple[str, str]:
    """Helper function to create a Daily room and generate an access token.

    Returns:
        tuple[str, str]: A tuple containing (room_url, token)

    Raises:
        HTTPException: If room creation or token generation fails
    """
    room = await daily_helpers["rest"].create_room(DailyRoomParams())
    if not room.url:
        raise HTTPException(status_code=500, detail="Failed to create room")

    token = await daily_helpers["rest"].get_token(room.url)
    if not token:
        raise HTTPException(status_code=500, detail=f"Failed to get token for room: {room.url}")

    return room.url, token


@app.get("/")
async def start_agent(request: Request):
    """Endpoint for direct browser access.
    
    NOW SERVES THE CHOICE INTERFACE BY DEFAULT - NO AUTO-BOT!
    Only starts auto-bot if explicitly requested with ?autobot=true
    """
    # Check if user explicitly wants auto-bot
    autobot = request.query_params.get('autobot', '').lower()
    control = request.query_params.get('control', '').lower()
    
    if autobot == 'true' or autobot == '1':
        # Original auto-bot behavior - only when explicitly requested
        print("Creating room with auto-bot (explicitly requested)")
        room_url, token = await create_room_and_token()
        print(f"Room URL: {room_url}")

        # Check if there is already an existing process running in this room
        num_bots_in_room = sum(
            1 for proc in bot_procs.values() if proc[1] == room_url and proc[0].poll() is None
        )
        if num_bots_in_room >= MAX_BOTS_PER_ROOM:
            raise HTTPException(status_code=500, detail=f"Max bot limit reached for room: {room_url}")

        # Spawn a new bot process
        try:
            bot_file = get_bot_file()
            proc = subprocess.Popen(
                [f"python3 -m {bot_file} -u {room_url} -t {token}"],
                shell=True,
                bufsize=1,
                cwd=os.path.dirname(os.path.abspath(__file__)),
            )
            bot_procs[proc.pid] = (proc, room_url)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to start subprocess: {e}")

        return RedirectResponse(room_url)
    
    elif control == 'true' or control == '1':
        # Serve the direct control interface
        try:
            with open('../direct-with-control.html', 'r') as f:
                html_content = f.read()
            return HTMLResponse(content=html_content)
        except FileNotFoundError:
            return HTMLResponse(content="""
                <h1>Control Interface Not Found</h1>
                <p>The direct-with-control.html file was not found.</p>
                <p><a href="/">Try the choice interface</a></p>
            """)
    
    else:
        # Default: serve the choice interface (NO AUTO-BOT!)
        return await choose_interface()


@app.post("/connect")
async def rtvi_connect(request: Request) -> Dict[Any, Any]:
    """RTVI connect endpoint that creates a room and returns connection credentials.

    This endpoint is called by RTVI clients to establish a connection.
    Modified to NOT automatically start the bot - user can control when bot joins.

    Returns:
        Dict[Any, Any]: Authentication bundle containing room_url and token

    Raises:
        HTTPException: If room creation or token generation fails
    """
    print("Creating room for Pipecat connection (no auto-bot)")
    room_url, token = await create_room_and_token()
    print(f"Room URL: {room_url}")

    # DO NOT automatically start the bot - let the user control it with the button
    # The bot will be started when /bot/activate is called

    # Return the authentication bundle in format expected by DailyTransport
    return {"room_url": room_url, "token": token}


@app.get("/status/{pid}")
def get_status(pid: int):
    """Get the status of a specific bot process.

    Args:
        pid (int): Process ID of the bot

    Returns:
        JSONResponse: Status information for the bot

    Raises:
        HTTPException: If the specified bot process is not found
    """
    # Look up the subprocess
    proc = bot_procs.get(pid)

    # If the subprocess doesn't exist, return an error
    if not proc:
        raise HTTPException(status_code=404, detail=f"Bot with process id: {pid} not found")

    # Check the status of the subprocess
    status = "running" if proc[0].poll() is None else "finished"
    return JSONResponse({"bot_id": pid, "status": status})


# Add a new endpoint for bot control
@app.get("/bot/activate")
async def activate_bot(room_url: str = None):
    """Manually activate the bot in the current session."""
    try:
        if not room_url:
            # Create a new room if none provided
            room_url, token = await create_room_and_token()
        
        # Check if there is already an existing process running in this room
        num_bots_in_room = sum(
            1 for proc in bot_procs.values() if proc[1] == room_url and proc[0].poll() is None
        )
        if num_bots_in_room >= MAX_BOTS_PER_ROOM:
            return {"status": "error", "message": f"Max bot limit reached for room: {room_url}"}

        # Start the bot process
        bot_file = get_bot_file()
        proc = subprocess.Popen(
            [f"python3 -m {bot_file} -u {room_url} -t {await daily_helpers['rest'].get_token(room_url)}"],
            shell=True,
            bufsize=1,
            cwd=os.path.dirname(os.path.abspath(__file__)),
        )
        bot_procs[proc.pid] = (proc, room_url)
        
        return {
            "status": "bot_activated",
            "room_url": room_url,
            "bot_pid": proc.pid,
            "message": "Bot has been activated in the session"
        }
    except Exception as e:
        logger.error(f"Error activating bot: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/bot/deactivate")
async def deactivate_bot(room_url: str = None):
    """Deactivate the bot."""
    try:
        if room_url:
            # Find and stop bots in the specific room
            stopped_bots = []
            for pid, (proc, proc_room_url) in bot_procs.items():
                if proc_room_url == room_url and proc.poll() is None:
                    proc.terminate()
                    stopped_bots.append(pid)
            
            return {
                "status": "bot_deactivated", 
                "stopped_bots": stopped_bots,
                "message": f"Bot(s) deactivated in room: {room_url}"
            }
        else:
            return {
                "status": "bot_deactivated", 
                "message": "No specific room provided - use room_url parameter"
            }
    except Exception as e:
        logger.error(f"Error deactivating bot: {e}")
        return {"status": "error", "message": str(e)}

# Add a new endpoint for the choice interface
@app.get("/choose")
async def choose_interface():
    """Landing page that lets users choose which interface to use."""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🎤 Voice Assistant - Choose Interface</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                max-width: 900px;
                margin: 0 auto;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                min-height: 100vh;
            }
            .container {
                background: rgba(255,255,255,0.1);
                backdrop-filter: blur(10px);
                border-radius: 20px;
                padding: 30px;
                margin: 20px 0;
            }
            .option-card {
                background: white;
                color: #333;
                border-radius: 15px;
                padding: 25px;
                margin: 20px 0;
                box-shadow: 0 8px 25px rgba(0,0,0,0.2);
                transition: transform 0.3s ease;
            }
            .option-card:hover {
                transform: translateY(-5px);
            }
            .option-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
            }
            .btn {
                display: inline-block;
                padding: 15px 30px;
                background: #007bff;
                color: white;
                text-decoration: none;
                border-radius: 8px;
                font-weight: bold;
                margin: 10px 5px;
                transition: all 0.3s ease;
            }
            .btn:hover {
                background: #0056b3;
                transform: translateY(-2px);
            }
            .btn-success { background: #28a745; }
            .btn-success:hover { background: #1e7e34; }
            .btn-warning { background: #ffc107; color: #333; }
            .btn-warning:hover { background: #e0a800; }
            h1 { text-align: center; font-size: 2.5em; margin-bottom: 30px; }
            h3 { color: #007bff; margin-top: 0; }
            .emoji { font-size: 1.5em; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎤 Voice Assistant Interfaces</h1>
            <p style="text-align: center; font-size: 1.2em;">Choose how you want to interact with your AI voice assistant:</p>
            
            <div class="option-grid">
                <div class="option-card">
                    <h3><span class="emoji">🎮</span> Manual Control Interface</h3>
                    <p><strong>Best for:</strong> Testing, demonstrations, controlled conversations</p>
                    <ul>
                        <li>Full control over bot activation</li>
                        <li>Join session → Activate bot when ready</li>
                        <li>Perfect for development and testing</li>
                    </ul>
                    <a href="http://localhost:5174" class="btn btn-success">🚀 Launch Control Interface</a>
                    <p><small>Note: Make sure to run <code>npm run dev</code> in another terminal</small></p>
                </div>
                
                <div class="option-card">
                    <h3><span class="emoji">⚡</span> Direct Auto-Bot</h3>
                    <p><strong>Best for:</strong> Quick voice chats, immediate AI interaction</p>
                    <ul>
                        <li>Bot joins automatically</li>
                        <li>Instant voice conversation</li>
                        <li>Simple and fast</li>
                    </ul>
                    <a href="/?autobot=true" class="btn btn-warning">🤖 Launch Auto-Bot</a>
                </div>
                
                <div class="option-card">
                    <h3><span class="emoji">🎯</span> Enhanced Direct Control</h3>
                    <p><strong>Best for:</strong> Direct room access with bot control</p>
                    <ul>
                        <li>Use any Daily room URL</li>
                        <li>Manual bot activation in direct rooms</li>
                        <li>Best of both worlds</li>
                    </ul>
                    <a href="/?control=true" class="btn">🎯 Launch Enhanced Control</a>
                </div>
            </div>
            
            <div style="text-align: center; margin-top: 30px; padding: 20px; background: rgba(255,255,255,0.1); border-radius: 10px;">
                <h3>🔧 Development Info</h3>
                <p><strong>Server:</strong> Running on port 7860</p>
                <p><strong>Frontend:</strong> Available on port 5174</p>
                <p><strong>Voice Engine:</strong> Pipecat + Gemini + Daily.co</p>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


if __name__ == "__main__":
    import uvicorn

    # Parse command line arguments for server configuration
    default_host = os.getenv("HOST", "0.0.0.0")
    default_port = int(os.getenv("FAST_API_PORT", "7860"))

    parser = argparse.ArgumentParser(description="Daily Storyteller FastAPI server")
    parser.add_argument("--host", type=str, default=default_host, help="Host address")
    parser.add_argument("--port", type=int, default=default_port, help="Port number")
    parser.add_argument("--reload", action="store_true", help="Reload code on change")

    config = parser.parse_args()

    # Start the FastAPI server
    uvicorn.run(
        "server:app",
        host=config.host,
        port=config.port,
        reload=config.reload,
    )
