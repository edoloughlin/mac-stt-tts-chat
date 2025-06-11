# TODO

A list of initial tasks to move the project forward.

1. Select the UI framework (Electron, Tauri or SwiftUI) and create a basic window layout.
2. Implement microphone capture and streaming to the STT engine.
3. Integrate a streaming STT backend (e.g. whisper.cpp or mlx-whisper).
4. Build a simple LLM chat agent that conforms to the agent interface.
5. Implement a TTS backend capable of streaming audio playback.
6. Create the asynchronous event loop connecting STT, Agent and TTS modules.
7. Add interruption detection so user speech can cut off TTS playback.
8. Define a plugin mechanism to swap out the agent with more advanced versions.
9. Document configuration options and provide example scripts.
10. Write tests for individual components where possible.
