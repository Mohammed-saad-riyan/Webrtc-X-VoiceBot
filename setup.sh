#!/bin/bash

# WebRTC-X-VoiceBot Setup Script
# This script automates the setup process for the voice assistant

set -e  # Exit on any error

echo "🎤 WebRTC-X-VoiceBot Setup Script"
echo "=================================="

# Check if Python 3.12 is available
if ! command -v python3.12 &> /dev/null; then
    echo "❌ Python 3.12 is required but not found."
    echo "Please install Python 3.12 first:"
    echo "  macOS: brew install python@3.12"
    echo "  Ubuntu: sudo apt install python3.12 python3.12-venv"
    exit 1
fi

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required but not found."
    echo "Please install Node.js 18+ first:"
    echo "  Visit: https://nodejs.org/"
    exit 1
fi

echo "✅ Python 3.12 found: $(python3.12 --version)"
echo "✅ Node.js found: $(node --version)"

# Navigate to the project directory
cd gemini-webrtc-web-simple

echo ""
echo "🐍 Setting up Python environment..."
cd server

# Create virtual environment
echo "Creating virtual environment..."
python3.12 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Python environment setup complete!"

# Go back to project root
cd ..

echo ""
echo "📦 Setting up Node.js dependencies..."
npm install

echo "✅ Node.js dependencies installed!"

echo ""
echo "🔧 Setting up environment variables..."

# Check if .env file exists
if [ ! -f "server/.env" ]; then
    if [ -f "server/env.example" ]; then
        cp server/env.example server/.env
        echo "📝 Created .env file from env.example"
        echo ""
        echo "⚠️  IMPORTANT: Please edit server/.env and add your API keys:"
        echo "   - GOOGLE_API_KEY=your_google_api_key"
        echo "   - DAILY_API_KEY=your_daily_api_key"
        echo "   - OPENAI_API_KEY=your_openai_api_key (optional)"
    else
        echo "⚠️  No env.example file found. Please create server/.env manually."
    fi
else
    echo "✅ .env file already exists"
fi

echo ""
echo "🎉 Setup Complete!"
echo "=================="
echo ""
echo "🚀 To start the application:"
echo ""
echo "1. Start the Python server:"
echo "   cd server"
echo "   source venv/bin/activate"
echo "   python server.py"
echo ""
echo "2. In a new terminal, start the frontend:"
echo "   cd gemini-webrtc-web-simple"
echo "   npm run dev"
echo ""
echo "3. Visit http://localhost:7860 to choose your interface"
echo ""
echo "📚 For more information, see README.md"
echo ""
echo "⚠️  Don't forget to configure your API keys in server/.env!" 