from __future__ import annotations

import asyncio
import contextlib
import json
import datetime
from typing import Any, Iterable, Optional, TextIO

try:
    import websockets  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    websockets = None

from ..stt import VoskStream, Transcript
from ..agent.base import Agent
from ..agent.simple import EchoAgent
from ..tts.base import TTS
from ..tts.simple import ConsoleTTS
from ..tts.macsay import MacSayTTS
from ..tts.orpheus import OrpheusStyleTTS
from ..config import (
    BackendConfig,
    create_agent,
    create_stt,
    create_tts,
    load_config,
)


class AudioWebSocketServer:
    """Serve a WebSocket endpoint that streams audio to STT."""

    def __init__(
        self,
        model_path: str,
        host: str = "localhost",
        port: int = 8000,
        transcript_log: Optional[str] = "transcript.log",
        agent: Optional[Agent] = None,
        tts: Optional[TTS] = None,
    ) -> None:
        if websockets is None:
            raise RuntimeError("websockets must be installed to run the server")
        self.host = host
        self.port = port
        self.stt = VoskStream(model_path)
        self.bytes_received = 0
        self.bytes_sent = 0
        self._last_bytes_received = 0
        self._last_bytes_sent = 0
        self._log_file: Optional[TextIO] = (
            open(transcript_log, "a", encoding="utf-8") if transcript_log else None
        )
        self.agent = agent or EchoAgent()
        self.tts = tts or self._default_tts()

    def _default_tts(self) -> TTS:
        """Return a TTS instance, preferring Orpheus if available."""
        import os

        model_path = os.environ.get("ORPHEUS_MODEL", "orpheus-3b")
        try:
            return OrpheusStyleTTS(model_path)
        except Exception:
            try:
                return MacSayTTS()
            except Exception:
                return ConsoleTTS()

    def _timestamp(self) -> str:
        """Return the current timestamp with millisecond precision."""
        now = datetime.datetime.now()
        return now.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

    async def _log_bytes(self) -> None:
        """Periodically print the number of audio bytes sent/received."""
        while True:
            await asyncio.sleep(10)
            if (
                self.bytes_received != self._last_bytes_received
                or self.bytes_sent != self._last_bytes_sent
            ):
                print(
                    f"Audio bytes received: {self.bytes_received}, sent: {self.bytes_sent}"
                )
                self._last_bytes_received = self.bytes_received
                self._last_bytes_sent = self.bytes_sent

    async def _send_transcripts(self, websocket: Any) -> None:
        async for t in self.stt.stream():
            payload = json.dumps({"text": t.text, "final": t.is_final})
            await websocket.send(payload)
            if self._log_file and t.is_final and t.text:
                self._log_file.write(f"{self._timestamp()} < {t.text}\n")
                self._log_file.flush()
            if t.is_final and t.text:
                reply = await self.agent.process(t.text)
                audio = await self.tts.speak(reply)
                if audio:
                    await websocket.send(audio)
                if self._log_file:
                    self._log_file.write(f"{self._timestamp()} > {reply}\n")
                    self._log_file.flush()
                reply_payload = json.dumps({"text": reply, "final": True, "agent": True})
                await websocket.send(reply_payload)

    async def _handler(self, websocket: Any) -> None:
        send_task = asyncio.create_task(self._send_transcripts(websocket))
        try:
            async for message in websocket:
                if isinstance(message, (bytes, bytearray)):
                    data = bytes(message)
                    self.bytes_received += len(data)
                    self.stt.feed_audio(data)
        finally:
            send_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await send_task

    async def run(self) -> None:
        log_task = asyncio.create_task(self._log_bytes())
        try:
            async with websockets.serve(self._handler, self.host, self.port):
                await asyncio.Future()  # run forever
        finally:
            log_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await log_task
            if self._log_file:
                self._log_file.close()


def main(argv: Optional[Iterable[str]] = None) -> None:
    """CLI entry point to start the WebSocket server."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Run the audio WebSocket server")
    parser.add_argument("model", nargs="?", help="Path to Vosk model")
    parser.add_argument("--host", help="Host to bind")
    parser.add_argument("--port", type=int, help="Port to bind")
    parser.add_argument(
        "--transcript-log",
        help="File to write final transcripts",
    )
    parser.add_argument("--config", help="Path to JSON config file")
    args = parser.parse_args(list(argv) if argv is not None else None)

    cfg = load_config(args.config)
    if args.model:
        cfg.stt.model_path = args.model
    if args.host:
        cfg.server.host = args.host
    if args.port:
        cfg.server.port = args.port
    if args.transcript_log:
        cfg.server.transcript_log = args.transcript_log

    try:
        server = AudioWebSocketServer(
            cfg.stt.model_path,
            host=cfg.server.host,
            port=cfg.server.port,
            transcript_log=cfg.server.transcript_log,
            agent=create_agent(cfg.agent),
            tts=create_tts(cfg.tts),
        )
    except RuntimeError as exc:  # Missing optional dependency
        print(f"Error: {exc}", file=sys.stderr)
        return

    print(f"Listening on ws://{cfg.server.host}:{cfg.server.port}")
    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        print("Server stopped by user")


if __name__ == "__main__":  # pragma: no cover - entry point
    main()
