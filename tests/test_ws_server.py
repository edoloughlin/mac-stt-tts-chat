import asyncio
import json
import pathlib
import sys
from unittest import mock

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from src.backend.core import websocket_server
from src.backend.core.websocket_server import AudioWebSocketServer
from src.backend.config import BackendConfig, ServerConfig
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


class DummyAgent:
    async def process(self, text: str) -> str:
        return text.upper()


class DummyTTS:
    def __init__(self) -> None:
        self.spoken = []

    async def speak(self, text: str) -> bytes:
        self.spoken.append(text)
        return b"audio"


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

        server = AudioWebSocketServer("model", transcript_log=None, tts=DummyTTS())
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
        server.agent = DummyAgent()
        server.tts = DummyTTS()
        asyncio.run(server._send_transcripts(dummy_ws))

        assert dummy_ws.sent == [
            json.dumps({"text": "hi", "final": False}),
            json.dumps({"text": "bye", "final": True}),
            b"audio",
            json.dumps({"text": "BYE", "final": True, "agent": True}),
        ]
        assert server.tts.spoken == ["BYE"]


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
        server.agent = DummyAgent()
        server.tts = DummyTTS()
        with mock.patch.object(server, "_timestamp", return_value="2021-01-01 00:00:00.000"):
            asyncio.run(server._send_transcripts(dummy_ws))

        assert log_file.read_text() == (
            "2021-01-01 00:00:00.000 < hello\n"
            "2021-01-01 00:00:00.000 > HELLO\n"
        )
        assert dummy_ws.sent[1] == b"audio"
        assert server.tts.spoken == ["HELLO"]


def test_main_starts_server():
    with mock.patch(
        "src.backend.core.websocket_server.AudioWebSocketServer"
    ) as cls, mock.patch("asyncio.run") as run, mock.patch(
        "src.backend.core.websocket_server.load_config"
    ) as load, mock.patch(
        "src.backend.core.websocket_server.create_tts", return_value=DummyTTS()
    ):
        inst = cls.return_value
        load.return_value = BackendConfig()
        websocket_server.main(["model", "--host", "0.0.0.0", "--port", "1234"])

        cls.assert_called_with(
            "model",
            host="0.0.0.0",
            port=1234,
            transcript_log="transcript.log",
            agent=mock.ANY,
            tts=mock.ANY,
        )
        run.assert_called_once_with(inst.run())


def test_main_uses_config_file(tmp_path):
    cfg = tmp_path / "c.json"
    cfg.write_text("{}")
    with mock.patch(
        "src.backend.core.websocket_server.AudioWebSocketServer"
    ) as cls, mock.patch("asyncio.run") as run, mock.patch(
        "src.backend.core.websocket_server.load_config"
    ) as load, mock.patch(
        "src.backend.core.websocket_server.create_tts", return_value=DummyTTS()
    ):
        load.return_value = BackendConfig(
            server=ServerConfig(host="h", port=9)
        )
        websocket_server.main(["--config", str(cfg)])

        cls.assert_called_with(
            "vosk-model",
            host="h",
            port=9,
            transcript_log="transcript.log",
            agent=mock.ANY,
            tts=mock.ANY,
        )
        run.assert_called_once_with(cls.return_value.run())


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
