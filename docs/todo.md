# TODO

A list of initial tasks to move the project forward.

## Pending

1. ~~Implement microphone capture and streaming to the STT engine.~~
1. ~~Integrate a streaming STT backend (e.g. whisper.cpp or mlx-whisper).~~
1. Build a simple LLM chat agent that conforms to the agent interface.
1. Create the asynchronous event loop connecting STT, Agent and TTS modules.
1. Add interruption detection so user speech can cut off TTS playback.
1. Define a plugin mechanism to swap out the agent with more advanced versions.
1. Document configuration options and provide example scripts.
1. Write tests for individual components where possible.

# Done

1. Select the UI framework: The UI will be web based and will use ReactJS.
1. Create a basic UI layout.
1. Implement streaming STT using Vosk that accepts audio from the UI.
1. Integrate the Vosk backend for real-time transcription.
1. Add README files for the source modules.
1. Implemented a microphone toggle in the React UI to start/stop audio capture.
1. Added console logging for microphone events in the React UI.
1. Created backend scaffolding with an event loop and CLI runner script.
1. Added dependency management with `requirements.txt` and backend setup instructions.
1. Documented how to download and use a Vosk model for the backend.
1. Added WebSocket server for streaming audio from the UI.
1. Fixed WebSocket server CLI entrypoint to start the server and display a
   startup message.
1. Added audio byte counters in the UI and periodic byte logging on the backend.
1. Fixed zero-byte streaming bug by starting MediaRecorder with a timeslice.
1. Added transcript logging and improved byte logging to avoid duplicates.
1. Fixed incorrect audio encoding by streaming raw 16 kHz PCM via an AudioWorklet.
1. Hooked up the WebSocket server to the echo agent and console TTS.
1. Added browser speech synthesis and fixed duplicate transcripts in the UI.
1. Switched to backend TTS streaming audio to the UI for playback.
1. Added timestamped transcript logging for STT and TTS without console output.
1. Implemented a macOS `say` TTS backend for streaming speech audio.
1. Added Orpheus 3B / StyleTTS 2 backend for high-quality speech synthesis.
1. Added silence detection in the UI to avoid sending empty audio frames.
1. Included `orpheus-speech` in the dependency manifests.
