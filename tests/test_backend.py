import asyncio
import pathlib
import sys
from unittest import mock

# Allow importing the src package
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from src.backend.core.backend import ChatBackend
from src.backend.stt import Transcript
from src.backend.agent.base import Agent
from src.backend.tts.base import TTS


class DummyAgent(Agent):
    async def process(self, text: str) -> str:
        return text.upper()


class DummyTTS(TTS):
    def __init__(self) -> None:
        self.spoken = []

    async def speak(self, text: str) -> bytes:
        self.spoken.append(text)
        return b"audio"


def test_backend_processes_final_transcripts():
    async def gen():
        yield Transcript(text="hello", is_final=True)
        yield Transcript(text="world", is_final=True)

    stt = mock.Mock()
    stt.stream.return_value = gen()

    backend = ChatBackend(stt, DummyAgent(), DummyTTS())
    tts = backend.tts
    asyncio.run(backend.run(turns=2))

    assert tts.spoken == ["HELLO", "WORLD"]
