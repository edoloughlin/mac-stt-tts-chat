from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import AsyncGenerator, Optional

try:
    import vosk  # type: ignore
except ImportError:  # pragma: no cover - optional dependencies may be missing
    vosk = None


@dataclass
class Transcript:
    """Represents a chunk of transcribed text."""

    text: str
    is_final: bool = False


class VoskStream:
    """Streaming STT implementation using the Vosk library.

    Audio frames are pushed from the UI via :meth:`feed_audio` and processed
    asynchronously by :meth:`stream` which yields partial and final transcripts.
    """

    def __init__(self, model_path: str, samplerate: int = 16000) -> None:
        if vosk is None:
            raise RuntimeError("Vosk must be installed to use VoskStream")

        self.model = vosk.Model(model_path)
        self.rec = vosk.KaldiRecognizer(self.model, samplerate)
        self.queue: asyncio.Queue[bytes] = asyncio.Queue()

    def feed_audio(self, data: bytes) -> None:
        """Push raw PCM audio into the recognizer."""

        self.queue.put_nowait(data)

    async def stream(self) -> AsyncGenerator[Transcript, None]:
        """Yield transcripts as they become available."""

        while True:
            data = await self.queue.get()
            if self.rec.AcceptWaveform(data):
                result = json.loads(self.rec.Result())
                text = result.get("text", "")
                if text:
                    yield Transcript(text=text, is_final=True)
            else:
                partial = json.loads(self.rec.PartialResult()).get("partial", "")
                if partial:
                    yield Transcript(text=partial, is_final=False)

