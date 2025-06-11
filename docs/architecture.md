# Architecture Overview

This document outlines the planned architecture for the real-time voice chat application.

## Goals

- Modern UI for voice conversations on macOS
- Low-latency interaction with streaming STT and TTS
- Graceful handling of user interruptions
- Pluggable AI agent interface for conversation logic and UI updates

## Components

1. **UI Layer**
   - Built with a cross-platform toolkit (Electron, Tauri or SwiftUI)
   - Displays conversation history and agent state
   - Streams microphone audio to the STT engine
   - Receives updates from the agent to modify the UI in real time

2. **Audio Pipeline**
   - Microphone input is fed to the STT engine which emits partial and final transcripts
   - Final transcript triggers the agent
   - Agent response is converted to speech by the TTS engine and streamed back to the user

3. **Agent Interface**
   - Abstract interface that receives text and returns text plus optional actions
   - Initial implementation will be a simple LLM chat agent
   - Designed so that more advanced agents can be plugged in without major changes

4. **Interruption Detection**
   - Voice activity detection (VAD) monitors microphone input
   - When the user speaks while the agent is talking, TTS playback stops and the transcript resumes

5. **Real-Time Loop**
   - Asynchronous event loop connecting STT, Agent and TTS via queues
   - Allows overlapping operations for minimal latency

## Proposed Directory Structure

```
docs/              - documentation
src/
  ui/              - UI components
  stt/             - speech-to-text utilities
  tts/             - text-to-speech utilities
  agent/           - pluggable agent implementations
  core/            - event loop and common utilities
```
