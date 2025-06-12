from __future__ import annotations

import abc


class TTS(abc.ABC):
    """Abstract text-to-speech interface."""

    @abc.abstractmethod
    async def speak(self, text: str) -> bytes:
        """Generate speech audio for the given text.

        Returns the audio as a WAV byte string so callers can play it or
        stream it elsewhere.
        """
        raise NotImplementedError
