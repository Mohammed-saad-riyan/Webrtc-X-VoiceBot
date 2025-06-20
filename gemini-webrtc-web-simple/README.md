# Gemini Multimodal Live WebRTC Example

This example shows how to build a very simple voice AI application using the Gemini Multimodal Live API and WebRTC.

The client is a web app in a single [app.ts](./src/app.ts) file and has just four dependencies:
  1. the Open Source [Pipecat JavaScript SDK](https://github.com/pipecat-ai/pipecat-client-web)
  2. a [Daily WebRTC transport](https://github.com/pipecat-ai/pipecat-client-web-transports) plugin
  3. [ts-node-dev](https://www.npmjs.com/package/ts-node-dev)
  4. [vite](https://vite.dev/)

The WebRTC connection is just this code, plus event handlers for setting up audio playback and handling any events that you want to wire up to your user interface.

```typescript
  const rtviClient = new RTVIClient({
    transport,
    params: {
      baseUrl: "http://localhost:7860/", 
    },
    enableMic: true,
    enableCam: false,
    timeout: 30 * 1000,
  });
```

The server is a [Pipecat](https://github.com/pipecat-ai/pipecat) pipeline that uses the Gemini Multimodal Live WebSocket API [implementation](https://github.com/pipecat-ai/pipecat/tree/main/src/pipecat/services/gemini_multimodal_live) in Pipecat core.

## Installation and first run

Use two terminals, one for the web app (client) and one for the server.

### Server

```
cd server
cp env.example .env
```

You'll need a Gemini API key and a Daily API Key
  * Create a free Gemini API key at [https://aistudio.google.com/](https://aistudio.google.com/)
  * Create a free Daily account at [https://dashboard.daily.co/u/signup](https://dashboard.daily.co/u/signup)

Add both API keys to `.env`

Create a Python virtual environment and run `python server.py`.

```
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python server.py
```

### Web app

```
npm i
npm run dev
```

Open a web browser to the **Local** url that `npm run dev` printed to the console. This defaults to [http://localhost:5173](http://localhost:5173/)

### Architecture

The web app connects to a server running a [Pipecat](https://github.com/pipecat-ai/pipecat) process. Pipecat is an orchestration framework for realtime, multimodal AI. In this use case, Pipecat is translating between the WebRTC media streams (and Pipecat client/server events), and the Multimodal Live API.

You can think of this architecture as as smart proxy.

1. The client is sending/receiving audio and events using the WebRTC protocol.
2. The Pipecat pipeline is relaying the audio and events to the Multimodal Live API.

This two-hop approach has several advantages over connecting directly from the client to the Multimodal API WebSocket infrastructure. 

  - WebRTC delivers lower latency and better robustness for the median real-world user. Even though we are using a proxy/relay approach, for a large percentage of users, voice-to-voice response times will be measurably faster than using direct WebSocket connection. See the next section — "Why WebRTC?" — for more details on this. 
  - You can add functionality using Pipecat's built-in services, or write custom server-side realtime logic in Python. As an example, this Pipecat pipeline implements audio transcription by sending both the user and the model audio to Gemini's standard (non-Live) API.
  - The SDK implements the [RTVI open standard](https://docs.pipecat.ai/client/introduction#about-rtvi) for AI client-server events. This rich set of events make it easy to implement core features of voice-to-voice and multimodal AI applications. Pipecat's React components, for example, leverage this event system.
  - Compatible Web, React, React Native, iOS, Android, Python, and C++ SDKs, all maintained and developed by a large and active Open Source community.

There are also two disadvantages to using WebRTC this way.

  - WebRTC is more complicated than WebSockets. You'll need to use an SDK rather than write code that calls low-level WebRTC APIs. (This is generally true for Web applications, though arguing about *how* true it is for programmers with different levels of networking experience is outside the scope of this readme. It's *definitely* true for native mobile applications.) This is the pain point that the Pipecat open source client SDKs aim to alleviate.
  - In production, you probably will not want to run your own WebRTC server clusters. WebRTC is closer to telephony, in complexity, than to Web servers. You probably don't run your own SIP/PSTN/SMS infrastructure. So you'll likely pay a WebRTC infrastructure provider per-minute or per-gigabyte for each bot session. The Pipecat SDKs support both WebSockets and WebRTC. You can use WebSockets in development and then transition over to WebRTC when you're ready to deploy to real-world users.


```

                                 ┌─────────────────────────────────────────┐     
                                 │                                         │     
                                 │ Server                                  │     
                                 │                                         │     
                                 │                                         │     
                                 │                 ┌────────────────────┐  │     
                                 │                 │                    │  │     
                                 │                 │  Pipecat           │  │     
                                 │                 │  Pipeline          │  │     
                                 │                 │                    │  │     
                                 │                 │                    │  │     
┌──────────────────────────┐     │                 │  Audio Processing  │  │     
│                          │     │                 │         ▼          │  │     
│      Pipecat Client      │     │   ┌─────────────│   Gemini Flash    ─┼──┼────►
│    ┌───────────────┐     │     │   │             │   Transcription   ◄┼──┼─────
│    │ WebRTC (Daily)│ ────┼────────►│WebRTC (Daily)         ▼          │  │     
│    │   Transport   │ ◄───┼─────────│  Transport  │  Gemini Multimodal─┼──┼────►
│    └───────────────┘     │     │   │             │     Live API      ◄┼──┼─────
│                          │     │   └─────────────│         ▼          │  │     
└──────────────────────────┘     │                 │   Gemini Flash    ─┼──┼────►
                                 │                 │   Transcription   ◄┼──┼─────
                                 │                 │         ▼          │  │     
                                 │                 │   Conversation     │  │     
                                 │                 │     Context        │  │     
                                 │                 │    Management      │  │     
                                 │                 │         ▼          │  │     
                                 │                 │   RTVI Events      │  │     
                                 │                 │                    │  │     
                                 │                 └────────────────────┘  │     
                                 │                                         │     
                                 └─────────────────────────────────────────┘  
```     


One other note about infrastructure: the instructions in this readme show you how to run the Pipecat process on your local machine. For a production application, you would would run the bot on a machine in the cloud.

If you expect your maximum traffic to be ~100 or so concurrent connections, you can just deploy the `/server` directory from this project. It will scale fine on a single, mid-range, cloud VM. For higher traffic volumes, or if you'd rather somebody else handle the infrastructure devops for you, you might consider using a hosted Pipecat platform such as [Daily Bots](https://bots.daily.co/). 

## Why WebRTC?

If you're just starting out with voice AI, you might gravitate towards using a WebSocket library for networking. WebSockets are familiar, simple, and widely supported. And they are great for server-to-server use cases, for use cases where latency is not a primary concern, and are fine for prototyping and general hacking.

But WebSockets shouldn't be used in production for client-server, real-time media connections.

For production apps, you need to use WebRTC. WebRTC was designed from the ground up as *the* protocol for real-time media on the Internet.

The major problems with WebSockets for real-time media delivery to and from end-user devices are:

- WebSockets are built on TCP, so audio streams will be subject to head-of-line blocking and will automatically attempt packet resends even if packets are delayed so much that they can not be used for playout.

- The Opus audio codec used for WebRTC is tightly coupled to WebRTC's bandwidth estimation and packet pacing (congestion control) logic, making a WebRTC audio stream resilient to a wide range of real-world network behaviors that would cause a WebSocket connection to accumulate latency.

- The Opus audio codec has very good forward error correction, making the audio stream resilient to relatively high amounts of packet loss. (This only helps you if your network transport can drop late-arriving packets and doesn't do head of line blocking, though.)

- Audio sent and received over WebRTC is automatically time-stamped so both playout and interruption logic are trivial. These are harder to get right for all corner cases, when using WebSockets.

- WebRTC includes hooks for detailed performance and media quality statistics. A good WebRTC platform will give you detailed dashboards and analytics for both aggregate and individual session statistics that are specific to audio and video. This level of observability is somewhere between very hard and impossible to build for WebSockets.

- WebSocket reconnection logic is very hard to implement robustly. You will have to build a ping/ack framework (or fully test and understand the framework that your WebSocket library provides). TCP timeouts and connection events behave differently on different platforms.

- Finally, good WebRTC implementations today come with very good echo cancellation, noise reduction, and automatic gain control. You will likely need to figure out how to stitch this audio processing into an app that uses WebSockets.

In addition, long-haul public Internet routes are problematic for latency and real-time media reliability, no matter what the underlying network protocol is. So if your end-users are a significant distance from OpenAI's servers, it's important to try to connect the user to a media router as close to them as possible. Beyond that first "edge" connection, you can then use a more efficient backbone route. A good WebRTC platform will do this for you automatically.

In this sample application, for example, the latency for a typical user will actually be faster, routing through Daily's WebRTC network — which has many, many servers close to the edge of the network all over the world — than via a "direct" WebSocket server via a public Internet route. (There are no direct connections on the Internet. Every packet is relayed through multiple routers. Better routing means better response times.)

## More resources

The Gemini Multimodal Live docs overview

https://ai.google.dev/api/multimodal-live

The repo for the Pipecat SDK for Gemini and WebRTC on the web (and React) is here:  

https://github.com/pipecat-ai/pipecat-client-web

Contributions are welcome! If you want to write a new pluggable network transport for the SDK, check out this repo and README:

https://github.com/pipecat-ai/pipecat-client-web-transports

Here's a full-featured multimodal chat applicaton that demonstrates how to use the Gemini Multimodal Modal Live WebSocket API, HTTP single-turn APIs, and WebRTC all in one app. (They all have their place for different use cases.)

https://github.com/pipecat-ai/gemini-multimodal-live-demo

[Pipecat's SDKs] for Web, React, React Native, Android, iOS, Python, and C++ are all architecture-compatible and Open Source.

The Pipecat Android SDK repo is here:

https://github.com/pipecat-ai/pipecat-client-android

The Pipecat iOS SDK repo is here:

https://github.com/pipecat-ai/pipecat-client-ios

If you're interested in network protocols designed for sending media, here's a technical overview of RTMP, HLS, and WebRTC:

https://www.daily.co/blog/video-live-streaming/

For a deep dive into WebRTC edge and mesh routing, here's a long post about Daily's global WebRTC infrastructure:

https://www.daily.co/blog/global-mesh-network/

