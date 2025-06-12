from __future__ import annotations

import io
import math
import struct
import wave

from .base import TTS


class ConsoleTTS(TTS):
    """TTS implementation that returns a short beep for any text."""

    async def speak(self, text: str) -> bytes:

        sr = 16000
        duration = 0.3
        freq = 440.0
        frames = []
        for i in range(int(sr * duration)):
            sample = int(math.sin(2 * math.pi * freq * i / sr) * 32767)
            frames.append(struct.pack("<h", sample))

        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sr)
            wf.writeframes(b"".join(frames))

        return buffer.getvalue()
