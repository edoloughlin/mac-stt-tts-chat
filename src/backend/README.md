# Backend

This directory contains the Python backend for the chat application. The backend wires together the speech-to-text (STT), agent and text-to-speech (TTS) components. A small runner script is provided for testing the flow on the command line.

## Setup

It is recommended to run the backend in an isolated Python virtual environment.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

The only runtime dependency at the moment is [Vosk](https://alphacephei.com/vosk/), which provides streaming STT. Development dependencies (such as `pytest` for the test suite) can be installed via `requirements-dev.txt`.

```bash
pip install -r requirements-dev.txt
```

Download a small Vosk model for testing (approx. 50MB):

```bash
curl -L -o model.zip https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip model.zip && mv vosk-model-small-en-us-0.15 vosk-model
```

## Running

To run the demo backend with the default echo agent and console TTS implementation, execute the runner module and provide the path to the unzipped Vosk model directory:

```bash
python -m src.backend.core.runner vosk-model --turns 1
```

Each final transcript will be echoed back to you as text output. The `--turns` argument limits the number of transcripts processed (use `-1` for no limit).

## Testing

Activate your virtual environment and install the development requirements, then run:

```bash
pytest
```

This executes the unit tests under the `tests` directory.
