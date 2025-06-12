import asyncio
import json
import pathlib
import sys
from unittest import mock

import pytest

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

    with mock.patch(
        "src.backend.core.websocket_server.websockets", mock.Mock()
    ), mock.patch(
        "src.backend.core.websocket_server.VoskStream"
    ) as m_vosk, mock.patch.object(
        AudioWebSocketServer, "_send_transcripts", dummy_send
    ):
        stt_instance = mock.Mock()
        m_vosk.return_value = stt_instance

        server = AudioWebSocketServer("model", transcript_log=None)
        asyncio.run(server._handler(dummy_ws))

        assert stt_instance.feed_audio.call_count == 2
        assert server.bytes_received == 2


def test_send_transcripts_sends_messages():
    async def gen():
        yield Transcript(text="hi", is_final=False)
        yield Transcript(text="bye", is_final=True)

    dummy_ws = DummyWebSocket()

    with mock.patch(
        "src.backend.core.websocket_server.websockets", mock.Mock()
    ), mock.patch("src.backend.core.websocket_server.VoskStream") as m_vosk:
        stt_instance = mock.Mock()
        stt_instance.stream.return_value = gen()
        m_vosk.return_value = stt_instance

        server = AudioWebSocketServer("model", transcript_log=None)
        asyncio.run(server._send_transcripts(dummy_ws))

        assert dummy_ws.sent == [
            json.dumps({"text": "hi", "final": False}),
            json.dumps({"text": "bye", "final": True}),
        ]


def test_send_transcripts_logs_transcripts(tmp_path):
    async def gen():
        yield Transcript(text="hello", is_final=True)

    dummy_ws = DummyWebSocket()

    with mock.patch(
        "src.backend.core.websocket_server.websockets", mock.Mock()
    ), mock.patch("src.backend.core.websocket_server.VoskStream") as m_vosk:
        stt_instance = mock.Mock()
        stt_instance.stream.return_value = gen()
        m_vosk.return_value = stt_instance

        log_file = tmp_path / "t.log"
        server = AudioWebSocketServer("model", transcript_log=str(log_file))
        asyncio.run(server._send_transcripts(dummy_ws))

        assert log_file.read_text() == "hello\n"


def test_main_starts_server():
    with mock.patch(
        "src.backend.core.websocket_server.AudioWebSocketServer"
    ) as cls, mock.patch("asyncio.run") as run:
        inst = cls.return_value
        websocket_server.main(["model", "--host", "0.0.0.0", "--port", "1234"])

        cls.assert_called_with(
            "model", host="0.0.0.0", port=1234, transcript_log="transcript.log"
        )
        run.assert_called_once_with(inst.run())


def test_log_bytes_only_when_changed():
    with mock.patch(
        "src.backend.core.websocket_server.websockets", mock.Mock()
    ), mock.patch("src.backend.core.websocket_server.VoskStream"):
        server = AudioWebSocketServer("model", transcript_log=None)

        async def fake_sleep(_: float):
            raise asyncio.CancelledError

        with mock.patch("asyncio.sleep", fake_sleep), mock.patch(
            "builtins.print"
        ) as m_print:
            with pytest.raises(asyncio.CancelledError):
                asyncio.run(server._log_bytes())
            m_print.assert_not_called()

        server.bytes_received = 1

        async def fake_sleep2(_: float):
            pass

        with mock.patch("asyncio.sleep", fake_sleep2), mock.patch(
            "builtins.print", side_effect=asyncio.CancelledError
        ) as m_print:
            with pytest.raises(asyncio.CancelledError):
                asyncio.run(server._log_bytes())
            m_print.assert_called_once()
