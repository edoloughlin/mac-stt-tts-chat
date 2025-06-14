# mac-stt-tts-chat

**Local AI Voice Agent for macOS (Apple Silicon)**

This project aims to provide a foundation for building a fully on-device AI voice agent for macOS, leveraging open-source Speech-to-Text (STT) and Text-to-Speech (TTS) engines. All models and components run locally.

---

## Features

- **Speech-to-Text (STT):** High-accuracy, low-latency transcription using local models
- **Text-to-Speech (TTS):** Speech is generated with **Orpheus 3B / StyleTTS 2**
  (falling back to the macOS `say` command if unavailable) and streamed to the UI
  for playback
- **Voice Chat Loop:** Real-time, conversational back-and-forth between user and agent
- **Optimized for Apple Silicon:** Utilizes Metal, Core ML, and Neural Engine
- **Built-in streaming STT:** Real-time microphone transcription powered by Vosk
  with partial and final results.
- **React UI:** Includes a microphone toggle button to start or stop capturing audio
- **Live stats:** While listening, the UI shows how many audio bytes have been sent
  to the backend and received back.
- **WebSocket server:** Streams audio from the UI directly to the STT backend
- **Raw PCM streaming:** The UI uses an AudioWorklet to send 16 kHz mono PCM
  bytes to the backend for compatibility with Vosk and other STT engines
- **Silence detection:** Audio frames are skipped when no speech is detected
- **Adjustable threshold:** The silence threshold can be tweaked via a slider in
  the UI and a live spectrogram visualizes microphone input

---

## 1. Recommended STT Engines

| Engine                                  | Install/Build                                      | Key Notes                                                        |
| ---------------------------------------- | -------------------------------------------------- | ---------------------------------------------------------------  |
| **whisper.cpp**                         | `brew install cmake`<br>`git clone https://github.com/ggml-org/whisper.cpp && make` | State-of-the-art, Metal support, quantized models (2–6GB RAM)     |
| **mlx-whisper**                         | `pip install mlx-whisper`                          | Fast on Neural Engine, native for Apple silicon                   |
| **faster-whisper / whisperX**           | `pip install faster-whisper whisperx`              | Word-level timestamps, speaker diarization, 2–4× real-time        |
| **Vosk**                                | `pip install vosk` (plus 50MB model)               | Lightweight, streaming, <300MB RAM, 20+ languages                 |
| **WeNet**                               | Build from source                                  | Production-grade streaming, sub-second latency                    |
| **Apple Speech Framework**               | Native API (Swift/Obj-C)                           | No install, great quality, 1-min per request cap                  |

*Tip: Wrappers like [MacWhisper](https://github.com/ggerganov/whisper.cpp) and [UtterType](https://github.com/utype-org/uttertype) offer hotkey/menubar UX on top of whisper.cpp/MLX.*

---

## 2. Recommended TTS Engines

| Engine           | Install/Build                                      | Key Notes                                  |
| ---------------- | -------------------------------------------------- | ------------------------------------------ |
| **Piper (MIT)**  | `brew install portaudio`<br>`git clone https://github.com/rhasspy/piper && make` | Fast, many voices, 24kHz, <1GB             |
| **Kokoro-82 M**  | `pip install kokoro`                               | Very fast, 82M params, natural sound       |
| **Orpheus 3B / StyleTTS 2** | `pip install orpheus-speech`<br>`git lfs clone https://huggingface.co/orpheus-speech/orpheus-3b-styletts2` | Diffusion-based, near-human quality |
| **Mimic 3**      | `pip install mimic3-tts`                           | <1GB RAM, privacy-first, multi-language    |
| **AVSpeechSynthesizer** | Native API                                  | Built-in voices, offline once downloaded   |

---

## 3. Example CLI Prototype

```bash
# Transcribe user audio to text
./whisper.cpp/main -m models/ggml-large-v3-q5_0.bin -f input.wav -otxt -of input.txt

# Generate speech from agent reply
echo "$(cat reply.txt)" | ./piper --model en_GB-alba-medium.onnx --output_file reply.wav

afplay reply.wav   # Play the reply
```

**REST Endpoint:**  
For a unified local API, use [mlx-omni-server](https://github.com/ml-explore/mlx-omni-server):

```bash
pip install mlx-omni-server
mlx-omni-server run
# Provides /v1/audio/transcriptions & /v1/audio/speech endpoints
```

---

## 4. Real-Time Voice Chat Architecture

For a natural conversational loop (<700ms round-trip):

- **Streaming/incremental STT**: Partial hypotheses while user speaks (`whisper.cpp --stream`, [RealtimeSTT](https://github.com/m-bain/realtimestt))
- **Streaming/low-buffer TTS**: Begin playback as soon as audio is buffered (Piper daemon, [RealtimeTTS](https://github.com/m-bain/realtimetts))
- **Async event loop**: Wire STT → LLM → TTS with queues for parallelism and low latency

Example event loop:

```
┌──────────┐   audio frames   ┌────────────┐  partial text ┌────────────┐  final text ┌───────────┐
│ PortAudio│ ───────────────▶ │  STT task  │──────────────▶│  LLM task  │────────────▶│  TTS task │
└──────────┘   back-pressure  └────────────┘               └────────────┘             └───────────┘
      ▲                                                                                       │
      └───────────────────────────── playback PCM  ◀───────────────────────────────────────────┘
```

- **STT task:** Streams audio, sends partials and final transcripts
- **LLM task:** Waits for final transcript, generates response, splits into sentences
- **TTS task:** Streams audio, playback starts as soon as 50–100ms is ready

---

## 5. Recommendations by Use-Case

| Criterion                             | Good Picks                       |
| -------------------------------------- | --------------------------------- |
| **Lowest latency conversation loop**   | `faster-whisper` + Piper         |
| **Highest transcription accuracy**     | `mlx-whisper large-v3-turbo`     |
| **High-emotion TTS**                  | Orpheus 3B / StyleTTS 2          |
| **<1GB RAM envelope (Edge)**           | Vosk + Kokoro-82 M               |
| **Swift/Obj-C app, no Python**         | Apple Speech + AVSpeechSynthesizer|

---

## 6. Practical Tips

- **Keep models loaded in RAM** and share across requests for speed.
- **Quantization:** Q4_1 or Q5_0 Whisper models use 2–3GB RAM.
- **VAD:** Use voice activity detection to avoid sending silence/breathing to LLM.
- **TTS chunking:** Split on `[.!?] + space`, stream each sentence.
- **Profiling:** Log time-to-first-token (STT) and time-to-first-sample (TTS).

---

## 7. License

All recommended models are open-weight (MIT, Apache-2.0, AGPL). Double-check license terms if embedding in closed-source apps.

---

## Running the Web UI

The React based frontend lives in `src/ui` and uses Vite for development.

```bash
cd src/ui
npm install
npm run dev
```

Open your browser to `http://localhost:5173` to view the app.

Click the microphone button to toggle audio capture on or off.
While the microphone is active, the UI displays how many audio bytes have been
sent to and received from the backend.

---

## Using the STT Streamer

The backend now includes a small helper class, `VoskStream`, which accepts raw
PCM audio streamed from the web UI and yields transcription results as they are
produced. Install `vosk` and download a model, then run:

```python
from src.backend.stt import VoskStream

stream = VoskStream("/path/to/vosk-model")  # path to the unzipped model folder
# Download models from https://alphacephei.com/vosk/models

# when new 16 kHz mono PCM bytes arrive from the UI
stream.feed_audio(audio_bytes)

async for t in stream.stream():
    print(t.text, t.is_final)
```

This will print partial and final transcripts from the streamed audio.

---
## Running the Backend

The backend requires **Python 3.12**. Create a virtual environment and install the dependencies first:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Next download a Vosk model (50MB) and extract it somewhere on disk:

```bash
curl -L -o model.zip https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip model.zip && mv vosk-model-small-en-us-0.15 vosk-model
```

### Installing Orpheus 3B / StyleTTS 2

Install the TTS package and download the model weights:

```bash
pip install orpheus-speech
git lfs install
git lfs clone https://huggingface.co/orpheus-speech/orpheus-3b-styletts2
```

Set the `ORPHEUS_MODEL` environment variable to the path of the cloned
repository so the backend can find it.

A small runner script wires the pieces together using an echo agent and a console
TTS implementation:

```bash
python -m src.backend.core.runner vosk-model --turns 1
```

The script processes microphone audio via `VoskStream` and prints the agent reply
to stdout.

### Running the WebSocket server

To stream audio from the React UI, start the WebSocket server. It prints the
address it is listening on and runs until interrupted. Use `--host` and
`--port` to change the bind address. Conversation transcripts are written to
`transcript.log` by default. Use `--transcript-log` to change the file path.
Each line in the log is timestamped with millisecond precision and prefixed with
`<` or `>` to indicate STT input or TTS output:

```bash
python -m src.backend.core.websocket_server vosk-model
```

The server now also feeds final transcripts to the built-in echo agent. Speech
is produced using **Orpheus 3B / StyleTTS 2** (falling back to `say` on macOS or
a short beep if unavailable), streamed back over the WebSocket and recorded in
`transcript.log`.

---
## Final Thoughts

Apple Silicon (especially the Neural Engine) enables fast, private voice agents without a discrete GPU. Start with **mlx-whisper + Piper** for simplicity, then upgrade as needed!

---

*This README summarizes technical guidance from a ChatGPT session on building local AI voice agents for macOS*

## Planning Documents

For an overview of the proposed architecture and development tasks, see the [docs](docs/) directory:

- [docs/architecture.md](docs/architecture.md) &ndash; component breakdown and real-time audio pipeline
- [docs/todo.md](docs/todo.md) &ndash; list of upcoming work items

