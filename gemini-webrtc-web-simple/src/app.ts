import { RTVIClient, RTVIEvent, RTVIMessage, Participant, BotLLMTextData, Transport } from "@pipecat-ai/client-js";

// Type definition for transcript data
interface TranscriptData {
  text: string;
  final: boolean;
}
import { DailyTransport } from "@pipecat-ai/daily-transport";

//
// Global variables
//

let joinDiv: HTMLElement;
let toggleBotBtn: HTMLButtonElement;
let disconnectBtn: HTMLButtonElement;
let sessionStatusEl: HTMLElement;
let botStatusEl: HTMLElement;
let rtviClient: RTVIClient | null = null;
let isBotActive = false;
let currentRoomUrl: string | null = null;

document.addEventListener('DOMContentLoaded', () => {
  joinDiv = document.getElementById('join-div');
  toggleBotBtn = document.getElementById('toggle-bot') as HTMLButtonElement;
  disconnectBtn = document.getElementById('disconnect-session') as HTMLButtonElement;
  sessionStatusEl = document.getElementById('session-status');
  botStatusEl = document.getElementById('bot-status');
  
  // Event listeners
  document.getElementById('start-webrtc-transport-session').addEventListener('click', () => {
    startSession();
  });
  
  toggleBotBtn.addEventListener('click', () => {
    toggleBot();
  });
  
  disconnectBtn.addEventListener('click', () => {
    disconnectSession();
  });
});

//
// Session management
//

async function startSession() {
  updateSessionStatus('Connecting...', 'connecting');
  
  try {
    console.log('-- starting voice session --');
    const transport = new DailyTransport();

    rtviClient = new RTVIClient({
      transport,
      params: {
        baseUrl: "http://localhost:7860/",
      },
      enableMic: true,
      enableCam: false,
      timeout: 30 * 1000,
    });

    setupEventHandlers(rtviClient);
    
    await rtviClient.initDevices();
    const response = await rtviClient.connect();
    
    // Extract room URL from the connect response
    console.log('Connect response:', response);
    
    // Try multiple ways to get the room URL
    if (response && (response as any).room_url) {
      currentRoomUrl = (response as any).room_url;
      console.log('Got room URL from response:', currentRoomUrl);
    } else if (rtviClient.transport && (rtviClient.transport as any)._roomUrl) {
      currentRoomUrl = (rtviClient.transport as any)._roomUrl;
      console.log('Got room URL from transport._roomUrl:', currentRoomUrl);
    } else if (rtviClient.transport && (rtviClient.transport as any).roomUrl) {
      currentRoomUrl = (rtviClient.transport as any).roomUrl;
      console.log('Got room URL from transport.roomUrl:', currentRoomUrl);
    }
    
  } catch (e) {
    console.log('Error connecting', e);
    updateSessionStatus('Connection Failed', 'error');
  }
}

async function toggleBot() {
  if (!rtviClient || !currentRoomUrl) {
    console.log('No active session or room URL');
    updateBotStatus('Error - No active session', false);
    return;
  }
  
  try {
    if (isBotActive) {
      // Deactivate bot
      console.log('-- deactivating bot --');
      updateBotStatus('Deactivating...', false);
      
      const response = await fetch(`http://localhost:7860/bot/deactivate?room_url=${encodeURIComponent(currentRoomUrl)}`, {
        method: 'GET'
      });
      const result = await response.json();
      console.log('Bot deactivation result:', result);
      
      isBotActive = false;
      updateBotStatus('Inactive', false);
      toggleBotBtn.textContent = '🤖 Activate Bot';
      
    } else {
      // Activate bot
      console.log('-- activating bot --');
      updateBotStatus('Activating...', false);
      
      // Trigger bot to join using the current room URL
      const response = await fetch(`http://localhost:7860/bot/activate?room_url=${encodeURIComponent(currentRoomUrl)}`, {
        method: 'GET'
      });
      const result = await response.json();
      console.log('Bot activation result:', result);
      
      if (result.status === 'bot_activated') {
        isBotActive = true;
        updateBotStatus('Active', true);
        toggleBotBtn.textContent = '🤖 Deactivate Bot';
      } else {
        updateBotStatus('Error activating', false);
      }
    }
  } catch (e) {
    console.log('Error toggling bot', e);
    updateBotStatus('Error', false);
  }
}

async function disconnectSession() {
  if (rtviClient) {
    await rtviClient.disconnect();
    rtviClient = null;
  }
  
  isBotActive = false;
  updateSessionStatus('Disconnected', 'error');
  updateBotStatus('Inactive', false);
  
  // Reset button states
  document.getElementById('start-webrtc-transport-session').textContent = '🎤 Join Voice Session';
  toggleBotBtn.textContent = '🤖 Activate Bot';
  toggleBotBtn.disabled = true;
  disconnectBtn.disabled = true;
}

//
// UI helpers
//

function updateSessionStatus(text: string, type: 'connected' | 'error' | 'connecting') {
  sessionStatusEl.textContent = text;
  sessionStatusEl.className = `status-indicator status-${type}`;
}

function updateBotStatus(text: string, active: boolean) {
  botStatusEl.textContent = text;
  botStatusEl.className = active ? 'bot-active' : 'bot-inactive';
}

//
// Event handlers (modified from original)
//

let audioDiv: HTMLDivElement;
let chatTextDiv: HTMLDivElement;

let currentUserSpeechDiv: HTMLDivElement;
let currentBotSpeechDiv: HTMLDivElement;
let currentSpeaker = ''; // 'user' or 'bot'

export async function setupEventHandlers(rtviClient: RTVIClient) {
  audioDiv = document.getElementById('audio') as HTMLDivElement;
  chatTextDiv = document.getElementById('chat-text') as HTMLDivElement;

  rtviClient.on(RTVIEvent.TransportStateChanged, (state: string) => {
    console.log(`-- transport state change: ${state} --`);
    
    if (state === 'connected') {
      updateSessionStatus('Connected', 'connected');
      toggleBotBtn.disabled = false;
      disconnectBtn.disabled = false;
      document.getElementById('start-webrtc-transport-session').textContent = '✅ Session Active';
    } else if (state === 'error') {
      updateSessionStatus('Connection Error', 'error');
    } else {
      updateSessionStatus(`Status: ${state}`, 'connecting');
    }
  });

  rtviClient.on(RTVIEvent.Connected, () => {
    console.log("-- user connected --");
    updateSessionStatus('Connected - Ready to activate bot', 'connected');
    
    // Additional attempt to get room URL after connection
    if (!currentRoomUrl) {
      const transport = rtviClient?.transport as any;
      if (transport) {
        console.log('Transport object:', transport);
        
        // Try different property names
        currentRoomUrl = transport.roomUrl || transport._roomUrl || transport.room_url || transport._room_url;
        
        if (currentRoomUrl) {
          console.log('Found room URL after connection:', currentRoomUrl);
        } else {
          console.log('Still no room URL found. Transport properties:', Object.keys(transport));
        }
      }
    }
  });

  rtviClient.on(RTVIEvent.Disconnected, () => {
    console.log("-- user disconnected --");
    updateSessionStatus('Disconnected', 'error');
    toggleBotBtn.disabled = true;
    disconnectBtn.disabled = true;
  });    

  rtviClient.on(RTVIEvent.BotConnected, () => {
    console.log("-- bot connected --");
    updateBotStatus('Active', true);
    isBotActive = true;
    toggleBotBtn.textContent = '🤖 Deactivate Bot';
  });

  rtviClient.on(RTVIEvent.BotDisconnected, () => {
    console.log("-- bot disconnected --");
    updateBotStatus('Inactive', false);
    isBotActive = false;
    toggleBotBtn.textContent = '🤖 Activate Bot';
  });

  rtviClient.on(RTVIEvent.BotReady, () => {
    console.log("-- bot ready to chat! --");
    updateBotStatus('Ready to Chat!', true);
  });

  rtviClient.on(RTVIEvent.TrackStarted, (track: MediaStreamTrack, participant: Participant) => {
    console.log(" --> track started", participant, track);
    if (participant.local) {
      return;
    }
    let audio = document.createElement("audio");
    audio.srcObject = new MediaStream([track]);
    audio.autoplay = true;
    audioDiv.appendChild(audio);
  });

  rtviClient.on(RTVIEvent.UserStartedSpeaking, startUserSpeechBubble);

  rtviClient.on(RTVIEvent.UserStoppedSpeaking, finishUserSpeechBubble);

  rtviClient.on(RTVIEvent.BotStartedSpeaking, startBotSpeechBubble);

  rtviClient.on(RTVIEvent.BotStoppedSpeaking, finishBotSpeechBubble);

  rtviClient.on(RTVIEvent.UserTranscript, (transcript: TranscriptData) => {
    if (transcript.final) {
      handleUserFinalTranscription(transcript.text);
    } else {
      handleUserInterimTranscription(transcript.text);
    }
  });

  rtviClient.on(RTVIEvent.BotTranscript, handleBotLLMText);

  rtviClient.on(RTVIEvent.Error, (message: RTVIMessage) => {
    console.log("[EVENT] RTVI Error!", message);
    updateSessionStatus('Error occurred', 'error');
  });

  rtviClient.on(RTVIEvent.MessageError, (message: RTVIMessage) => {
    console.log("[EVENT] RTVI ErrorMessage error!", message);
  });

  rtviClient.on(RTVIEvent.Metrics, (data) => {
    // let's only print out ttfb for now
    if (! data.ttfb) {
      return;
    }
    data.ttfb.map((metric) => {
      console.log(`[METRICS] ${metric.processor} ttfb: ${metric.value}`);
    });
  });
}


async function startUserSpeechBubble() {
  console.log('-- user started speaking -- ');
  if (currentSpeaker === 'user') {
    if (currentUserSpeechDiv) {
      return;
    }
    // Should never get here, but, you know.
  }
  currentSpeaker = 'user';
  currentUserSpeechDiv = document.createElement('div');
  currentUserSpeechDiv.className = 'user-message';
  let span = document.createElement('span');
  currentUserSpeechDiv.appendChild(span);
  chatTextDiv.appendChild(currentUserSpeechDiv);
}

async function finishUserSpeechBubble() {
  console.log('-- user stopped speaking -- ');
  // noop for now. Could do UI update here.
}

async function startBotSpeechBubble() {
  currentSpeaker = 'bot';
  currentBotSpeechDiv = document.createElement('div');
  currentBotSpeechDiv.className = 'assistant-message';
  chatTextDiv.appendChild(currentBotSpeechDiv);
}

async function finishBotSpeechBubble() {
  console.log('-- bot stopped speaking -- ');
}

async function handleUserInterimTranscription(text: string) {
  // No interim transcriptions (yet) from Gemini Multimodal Live. Leave this
  // code here for a future update.
  console.log('interim transcription:', text);
  if (currentSpeaker !== 'user') {
    return;
  }
  let span = currentUserSpeechDiv.querySelector('span:last-of-type');
  span.classList.add('interim');
  span.textContent = text + " ";
  scroll();
}

async function handleUserFinalTranscription(text: string) {
  console.log('final transcription:', text);
  let span = currentUserSpeechDiv.querySelector('span:last-of-type');
  span.classList.remove('interim');
  span.textContent = text + " ";
  let newSpan = document.createElement('span');
  currentUserSpeechDiv.appendChild(newSpan);
  scroll();
}

async function handleBotLLMText(data: BotLLMTextData) {
  console.log('bot llm text:', data.text);
  if (!currentBotSpeechDiv) {
    return;
  }
  currentBotSpeechDiv.textContent += data.text;
  scroll();
}

function scroll() {
  window.scrollTo({
    top: document.body.scrollHeight,
    behavior: 'smooth'
  });
}

async function activateBot() {
  try {
    updateBotStatus('Activating bot...', false);
    
    // Debug: log the current room URL
    console.log('Current room URL for bot activation:', currentRoomUrl);
    
    let roomUrlToUse = currentRoomUrl;
    
    // If we don't have a room URL, try to get it from a manual input
    if (!roomUrlToUse) {
      console.log('No room URL found, prompting user...');
      roomUrlToUse = prompt('Please enter the Daily room URL (e.g., from the browser address bar if you opened the Direct Daily room):');
      if (!roomUrlToUse) {
        updateBotStatus('Error - No room URL provided', false);
        return;
      }
      console.log('Manual room URL provided:', roomUrlToUse);
    }

    const response = await fetch(`http://localhost:7860/bot/activate?room_url=${encodeURIComponent(roomUrlToUse)}`);
    const result = await response.json();
    
    console.log('Bot activation response:', result);
    
    if (result.status === 'bot_activated') {
      updateBotStatus(`Bot Active (PID: ${result.bot_pid})`, true);
    } else {
      updateBotStatus(`Error - ${result.message}`, false);
    }
  } catch (error) {
    console.error('Failed to activate bot:', error);
    updateBotStatus('Error - Failed to activate bot', false);
  }
}
