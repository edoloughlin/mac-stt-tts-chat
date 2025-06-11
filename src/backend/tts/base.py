from __future__ import annotations

import abc


class TTS(abc.ABC):
    """Abstract text-to-speech interface."""

    @abc.abstractmethod
    async def speak(self, text: str) -> None:
        """Speak the given text."""
        raise NotImplementedError
