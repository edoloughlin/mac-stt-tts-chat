# TODO

A list of initial tasks to move the project forward.

## Pending

1. ~~Implement microphone capture and streaming to the STT engine.~~
1. ~~Integrate a streaming STT backend (e.g. whisper.cpp or mlx-whisper).~~
1. Build a simple LLM chat agent that conforms to the agent interface.
1. Implement a TTS backend capable of streaming audio playback.
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
