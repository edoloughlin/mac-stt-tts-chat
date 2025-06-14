# Architecture Overview

This document outlines the planned architecture for the real-time voice chat application.

## Goals

- Modern UI for voice conversations on macOS
- Low-latency interaction with streaming STT and TTS
- Graceful handling of user interruptions
- Pluggable AI agent interface for conversation logic and UI updates

## Tech Stack

- Python 3.12

## Components

1. **UI Layer**
   - A ReactJS application using web audio and multimedia APIs.
   - Displays conversation history and agent state
   - Captures microphone audio and streams it to the backend STT engine over a WebSocket connection
   - Skips sending audio when input is silent to reduce bandwidth
   - Microphone capture is toggled on/off via a button (no push-to-talk)
   - A slider controls the silence detection threshold and a live spectrogram
     shows microphone levels
   - Shows live counts of audio bytes sent and received when listening
   - Receives updates from the agent to modify the UI in real time

2. **Audio Pipeline**
  - Audio from the UI is fed to the STT engine which emits partial and final transcripts
  - Final transcripts and agent replies are appended to `transcript.log`
    with millisecond timestamps and `<`/`>` prefixes
  - A final transcript triggers the agent
  - Agent response is converted to speech by the TTS engine and streamed back to the user
  - The backend streams TTS audio to the UI which plays it via the Web Audio API
  - Current implementation uses the Vosk backend for real-time STT streaming
  - The WebSocket server echoes final transcripts via an `EchoAgent` and
    `OrpheusStyleTTS` (falls back to `MacSayTTS` or `ConsoleTTS` if unavailable)

3. **Agent Interface**
   - Abstract interface that receives text and returns text plus optional actions
   - Initial implementation will be a simple LLM chat agent
   - Designed so that more advanced agents can be plugged in without major changes

4. **Interruption Detection**
   - Voice activity detection (VAD) monitors the incoming audio stream
   - When the user speaks while the agent is talking, TTS playback stops and the transcript resumes

5. **Real-Time Loop**
   - Asynchronous event loop connecting STT, Agent and TTS via queues
   - Allows overlapping operations for minimal latency
   - Implemented by `ChatBackend` in `src/backend/core/backend.py`

## Proposed Directory Structure

```
docs/              - documentation
src/
  ui/              - UI components
  backend/         - Backend
    stt/           - speech-to-text utilities
    tts/           - text-to-speech utilities
    agent/         - pluggable agent implementations
    core/          - event loop and common utilities
```

A simple CLI runner located at `src/backend/core/runner.py` wires the default
components together for testing. For development convenience there is also a
 Rich based dashboard runner at `scripts/dev_runner.py` which installs
 dependencies and launches both the backend server and React UI. If started
 outside the virtual environment it creates it, installs the packages and
 restarts itself. Missing Vosk and Orpheus models are downloaded automatically
 using only macOS built-in tools after prompting the user.

## Configuration

Each backend component (STT, TTS, agent and server) can be configured via a JSON
file. The WebSocket server loads this configuration at startup and uses the
settings to instantiate the appropriate classes. Command line arguments override
values from the file.
