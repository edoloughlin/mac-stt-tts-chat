# TODO

A list of initial tasks to move the project forward.

## Pending

1. Create a basic UI layout.
1. Implement microphone capture and streaming to the STT engine.
1. Integrate a streaming STT backend (e.g. whisper.cpp or mlx-whisper).
1. Build a simple LLM chat agent that conforms to the agent interface.
1. Implement a TTS backend capable of streaming audio playback.
1. Create the asynchronous event loop connecting STT, Agent and TTS modules.
1. Add interruption detection so user speech can cut off TTS playback.
1. Define a plugin mechanism to swap out the agent with more advanced versions.
1. Document configuration options and provide example scripts.
1. Write tests for individual components where possible.

# Done

1. Select the UI framework: The UI will be web based and will use ReactJS.
