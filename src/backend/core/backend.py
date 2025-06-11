from __future__ import annotations

from ..stt import Transcript
from ..agent.base import Agent
from ..tts.base import TTS


class ChatBackend:
    """Wire STT, Agent and TTS together."""

    def __init__(self, stt, agent: Agent, tts: TTS) -> None:
        self.stt = stt
        self.agent = agent
        self.tts = tts

    async def run(self, turns: int = -1) -> None:
        """Run the main loop.

        Parameters
        ----------
        turns: int
            Stop after this many final transcripts if > 0.
        """
        final_count = 0
        async for transcript in self.stt.stream():
            if transcript.is_final:
                reply = await self.agent.process(transcript.text)
                await self.tts.speak(reply)
                final_count += 1
                if turns > 0 and final_count >= turns:
                    break
