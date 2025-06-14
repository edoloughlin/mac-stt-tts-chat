from __future__ import annotations

import asyncio
from pathlib import Path

from .base import TTS


class OrpheusStyleTTS(TTS):
    """TTS using the Orpheus 3B / StyleTTS 2 model."""

    def __init__(self, model_path: str, device: str = "cpu", voice: str = "default") -> None:
        try:
            from orpheus_speech import Synthesizer  # type: ignore
        except Exception as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("orpheus-speech is required for OrpheusStyleTTS") from exc

        self._synth = Synthesizer(str(Path(model_path)), device=device, voice=voice)

    async def speak(self, text: str) -> bytes:
        def _run() -> bytes:
            wav = self._synth.tts(text)
            if isinstance(wav, bytes):
                return wav
            return getattr(wav, "tobytes", lambda: bytes())()

        return await asyncio.to_thread(_run)
