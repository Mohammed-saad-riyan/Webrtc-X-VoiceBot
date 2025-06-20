#!/bin/bash

echo "🎤 Voice Assistant Setup"
echo "======================="
echo

# Check if .env file exists
if [ ! -f "server/.env" ]; then
    echo "❌ No .env file found. Copying from env.example..."
    cp server/env.example server/.env
fi

echo "📝 Please add your API keys to server/.env:"
echo "   - GOOGLE_API_KEY (for Gemini voice assistant)"
echo "   - DAILY_API_KEY (for WebRTC infrastructure)"
echo "   - OPENAI_API_KEY (for OpenAI voice assistant)"
echo
echo "Get API keys from:"
echo "   - Google: https://aistudio.google.com/"
echo "   - Daily: https://dashboard.daily.co/u/signup"
echo "   - OpenAI: https://platform.openai.com/api-keys"
echo

read -p "Press Enter after you've added your API keys..."

echo
echo "🚀 Starting servers..."
echo

# Start the servers in the background
echo "Starting Python server..."
cd server
source venv/bin/activate
python voice_assistant.py &
SERVER_PID=$!

cd ..
echo "Starting web server..."
npm run dev &
WEB_PID=$!

echo
echo "✅ Servers started!"
echo "📱 Open: http://localhost:5173/voice-only.html"
echo "🎤 Click 'Start' and begin talking!"
echo
echo "Press Ctrl+C to stop both servers"

# Wait for Ctrl+C and cleanup
trap "echo 'Stopping servers...'; kill $SERVER_PID $WEB_PID; exit" INT
wait 