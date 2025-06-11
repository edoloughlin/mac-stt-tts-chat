from __future__ import annotations

from .base import Agent


class EchoAgent(Agent):
    """A trivial agent that echoes the input text."""

    async def process(self, text: str) -> str:
        return text
