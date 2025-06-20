# 🎤 WebRTC-X-VoiceBot

**Real-time Voice Assistant powered by WebRTC, Gemini AI, and Pipecat**

A sophisticated voice assistant that enables natural, real-time conversations with AI through WebRTC technology. Built with multiple interface options for different use cases - from quick voice chats to controlled development environments.

![Voice Assistant Demo](https://img.shields.io/badge/Status-Active-brightgreen) ![WebRTC](https://img.shields.io/badge/WebRTC-Enabled-blue) ![AI](https://img.shields.io/badge/AI-Gemini-orange)

## 🌟 Features

- **🎯 Multiple Interface Options**: Choose from 4 different ways to interact with your AI
- **🗣️ Real-time Voice Conversations**: Seamless voice-to-voice communication with AI
- **🤖 Manual Bot Control**: Full control over when the AI joins your conversation
- **⚡ Instant Voice Chat**: Quick access for immediate AI interaction
- **🔧 Developer-Friendly**: Built for testing, demos, and development
- **🌐 WebRTC Technology**: Low-latency, high-quality audio streaming
- **🧠 Advanced AI**: Powered by Google's Gemini Multimodal Live API

## 🏗️ Architecture

### Core Technologies

**WebRTC (Web Real-Time Communication)**
- Enables peer-to-peer audio/video communication
- Provides low-latency, high-quality audio streaming
- Handles real-time media transport between browser and AI service

**Pipecat Framework**
- Orchestrates the voice processing pipeline
- Manages audio input/output streams
- Handles Voice Activity Detection (VAD)
- Coordinates between different AI services

**Daily.co Platform**
- WebRTC infrastructure provider
- Handles room creation and management
- Provides reliable audio/video transport
- Manages participant connections

**Google Gemini Multimodal Live API**
- Advanced conversational AI with real-time capabilities
- Speech-to-text and text-to-speech processing
- Context-aware responses
- Multimodal understanding

### Data Flow Architecture

```
User Voice Input → WebRTC → Daily.co → Pipecat Pipeline → Gemini AI → TTS → WebRTC → User Audio Output
```

**Detailed Pipeline:**
1. **Voice Capture**: Browser captures microphone input via WebRTC
2. **Transport**: Daily.co handles real-time audio transport
3. **Processing**: Pipecat processes audio streams and manages VAD
4. **AI Processing**: Gemini converts speech to text, generates response, converts to speech
5. **Output**: Processed audio returns through the same pipeline to user

## 🚀 Quick Start

### Prerequisites

- **Python 3.12+** (Required for Pipecat compatibility)
- **Node.js 18+** (For frontend development)
- **API Keys**:
  - Google AI API key (for Gemini)
  - Daily.co API key (for WebRTC rooms)
  - OpenAI API key (optional, for additional features)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Mohammed-saad-riyan/Webrtc-X-VoiceBot.git
   cd Webrtc-X-VoiceBot/gemini-webrtc-web-simple
   ```

2. **Set up Python environment**
   ```bash
   cd server
   python3.12 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your API keys:
   # GOOGLE_API_KEY=your_google_api_key
   # DAILY_API_KEY=your_daily_api_key
   # OPENAI_API_KEY=your_openai_api_key (optional)
   ```

4. **Install frontend dependencies**
   ```bash
   cd ..  # Back to gemini-webrtc-web-simple
   npm install
   ```

### Running the Application

1. **Start the Python server**
   ```bash
   cd server
   source venv/bin/activate
   python server.py
   ```
   Server will run on `http://localhost:7860`

2. **Start the frontend (for manual control interface)**
   ```bash
   # In a new terminal
   cd gemini-webrtc-web-simple
   npm run dev
   ```
   Frontend will run on `http://localhost:5174`

3. **Access the application**
   - Visit `http://localhost:7860` to see all interface options
   - Choose your preferred interaction method

## 🎮 Interface Options

### 1. 🏠 **Choice Landing Page**
**URL**: `http://localhost:7860`
- Beautiful interface to choose your preferred method
- Clear explanations of each option
- One-click access to all interfaces

### 2. 🎮 **Manual Control Interface**
**URL**: `http://localhost:5174`
- **Best for**: Testing, demonstrations, controlled conversations
- Full control over bot activation
- Step-by-step process: Join Session → Activate Bot → Talk
- Perfect for development and debugging

### 3. ⚡ **Direct Auto-Bot**
**URL**: `http://localhost:7860/?autobot=true`
- **Best for**: Quick voice chats, immediate AI interaction
- Bot joins automatically when you enter the room
- Instant voice conversation
- Simple and fast

### 4. 🎯 **Enhanced Direct Control**
**URL**: `http://localhost:7860/?control=true`
- **Best for**: Direct room access with manual bot control
- Use any Daily room URL
- Create new rooms or join existing ones
- Manual bot activation in direct rooms
- Best of both worlds!

## 🔧 Technical Implementation

### WebRTC Integration

The application leverages WebRTC for real-time audio communication:

```javascript
// RTVI Client setup for WebRTC connection
const rtviClient = new RTVIClient({
  transport: new DailyTransport(),
  params: { baseUrl: "http://localhost:7860/" },
  enableMic: true,
  enableCam: false,
  timeout: 30 * 1000,
});
```

### Pipecat Pipeline

The voice processing pipeline is built with Pipecat:

```python
# Core pipeline components
pipeline = Pipeline([
    transport.input(),           # WebRTC audio input
    user_context_aggregator,     # User context management
    gemini_live_service,         # AI processing
    transport.output(),          # WebRTC audio output
    assistant_context_aggregator # Assistant context management
])
```

### AI Integration

Gemini Multimodal Live API integration:

```python
# Gemini service configuration
gemini_service = GeminiMultimodalLiveLLMService(
    api_key=os.getenv("GOOGLE_API_KEY"),
    voice_id="Puck",  # AI voice selection
    transcribe_user_audio=True,
    transcribe_model="whisper",
    # Additional configuration...
)
```

## 🛠️ Development

### Project Structure

```
gemini-webrtc-web-simple/
├── server/                 # Python backend
│   ├── server.py          # FastAPI server
│   ├── bot-gemini.py      # Pipecat bot implementation
│   ├── requirements.txt   # Python dependencies
│   └── .env              # Environment variables
├── src/                   # Frontend source
│   ├── app.ts            # Main TypeScript application
│   └── styles.css        # Styling
├── index.html            # Manual control interface
├── direct-with-control.html # Enhanced control interface
├── package.json          # Node.js dependencies
└── README.md            # This file
```

### Key Components

**Backend (Python/FastAPI)**
- `server.py`: Main server with multiple endpoints
- `bot-gemini.py`: Pipecat pipeline implementation
- WebRTC room management via Daily.co API
- Bot process management and control

**Frontend (TypeScript/HTML)**
- RTVI client for WebRTC connections
- Multiple UI interfaces for different use cases
- Real-time status updates and controls
- Responsive design for various devices

### API Endpoints

- `GET /` - Landing page with interface choices
- `POST /connect` - RTVI connection endpoint (no auto-bot)
- `GET /?autobot=true` - Auto-bot activation
- `GET /?control=true` - Enhanced control interface
- `GET /bot/activate` - Manual bot activation
- `GET /bot/deactivate` - Manual bot deactivation

## 🎯 Use Cases

### 1. **Development & Testing**
Use the Manual Control Interface for:
- Testing voice recognition accuracy
- Debugging conversation flows
- Demonstrating AI capabilities
- Controlled development environment

### 2. **Quick Interactions**
Use the Direct Auto-Bot for:
- Immediate voice assistance
- Quick questions and answers
- Casual AI conversations
- Rapid prototyping

### 3. **Production Deployments**
Use the Enhanced Direct Control for:
- Customer-facing applications
- Controlled user experiences
- Integration with existing systems
- Scalable voice applications

## 🔐 Security & Privacy

- **API Key Management**: Environment variables for secure key storage
- **WebRTC Security**: Encrypted peer-to-peer connections
- **Room Isolation**: Each conversation in separate Daily.co rooms
- **Process Management**: Isolated bot processes for each session

## 🚀 Deployment

### Local Development
Follow the Quick Start guide above for local development setup.

### Production Deployment
1. Set up a server with Python 3.12+ and Node.js
2. Configure environment variables securely
3. Use a process manager (PM2, systemd) for the Python server
4. Set up a reverse proxy (nginx) for production serving
5. Configure SSL/TLS for secure connections

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Pipecat Team** for the excellent voice AI framework
- **Daily.co** for robust WebRTC infrastructure
- **Google** for the powerful Gemini AI API
- **WebRTC Community** for real-time communication standards

## 📞 Support

For support, questions, or feature requests:
- Open an issue on GitHub
- Check the documentation
- Review the troubleshooting guide below

## 🐛 Troubleshooting

### Common Issues

**Connection Failed Error**
- Ensure Python server is running on port 7860
- Check that all API keys are properly configured
- Verify network connectivity

**Bot Not Responding**
- Check Google API key validity
- Ensure microphone permissions are granted
- Verify audio input/output devices

**Room Access Issues**
- Confirm Daily.co API key is correct
- Check room URL format
- Ensure proper WebRTC support in browser

---

**Built with ❤️ by Mohammed Saad Riyan**

*Empowering conversations between humans and AI through cutting-edge voice technology.* 