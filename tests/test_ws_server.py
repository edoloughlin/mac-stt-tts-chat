import asyncio
import json
import pathlib
import sys
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from src.backend.core import websocket_server
from src.backend.core.websocket_server import AudioWebSocketServer
from src.backend.stt import Transcript


class DummyWebSocket:
    def __init__(self, messages=None):
        self.messages = list(messages or [])
        self.sent = []

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.messages:
            return self.messages.pop(0)
        raise StopAsyncIteration

    async def send(self, data):
        self.sent.append(data)


def test_handler_feeds_audio():
    dummy_ws = DummyWebSocket([b"a", b"b"])

    async def dummy_send(self, ws):
        return None

    with mock.patch("src.backend.core.websocket_server.websockets", mock.Mock()), \
         mock.patch("src.backend.core.websocket_server.VoskStream") as m_vosk, \
         mock.patch.object(AudioWebSocketServer, "_send_transcripts", dummy_send):
        stt_instance = mock.Mock()
        m_vosk.return_value = stt_instance

        server = AudioWebSocketServer("model")
        asyncio.run(server._handler(dummy_ws))

        assert stt_instance.feed_audio.call_count == 2
        assert server.bytes_received == 2


def test_send_transcripts_sends_messages():
    async def gen():
        yield Transcript(text="hi", is_final=False)
        yield Transcript(text="bye", is_final=True)

    dummy_ws = DummyWebSocket()

    with mock.patch("src.backend.core.websocket_server.websockets", mock.Mock()), \
         mock.patch("src.backend.core.websocket_server.VoskStream") as m_vosk:
        stt_instance = mock.Mock()
        stt_instance.stream.return_value = gen()
        m_vosk.return_value = stt_instance

        server = AudioWebSocketServer("model")
        asyncio.run(server._send_transcripts(dummy_ws))

        assert dummy_ws.sent == [
            json.dumps({"text": "hi", "final": False}),
            json.dumps({"text": "bye", "final": True}),
        ]


def test_main_starts_server():
    with mock.patch("src.backend.core.websocket_server.AudioWebSocketServer") as cls, \
         mock.patch("asyncio.run") as run:
        inst = cls.return_value
        websocket_server.main(["model", "--host", "0.0.0.0", "--port", "1234"])

        cls.assert_called_with("model", host="0.0.0.0", port=1234)
        run.assert_called_once_with(inst.run())
