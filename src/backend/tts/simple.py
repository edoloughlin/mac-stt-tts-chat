from __future__ import annotations

from .base import TTS


class ConsoleTTS(TTS):
    """TTS implementation that just prints to stdout."""

    async def speak(self, text: str) -> None:
        print(text)
