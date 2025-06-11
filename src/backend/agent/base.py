from __future__ import annotations

import abc


class Agent(abc.ABC):
    """Abstract chat agent."""

    @abc.abstractmethod
    async def process(self, text: str) -> str:
        """Return a response for the given input text."""
        raise NotImplementedError
