from __future__ import annotations

import asyncio
import contextlib
import json
from typing import Any, Iterable, Optional

try:
    import websockets  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    websockets = None

from ..stt import VoskStream, Transcript


class AudioWebSocketServer:
    """Serve a WebSocket endpoint that streams audio to STT."""

    def __init__(self, model_path: str, host: str = "localhost", port: int = 8000) -> None:
        if websockets is None:
            raise RuntimeError("websockets must be installed to run the server")
        self.host = host
        self.port = port
        self.stt = VoskStream(model_path)
        self.bytes_received = 0
        self.bytes_sent = 0

    async def _log_bytes(self) -> None:
        """Periodically print the number of audio bytes sent/received."""
        while True:
            await asyncio.sleep(10)
            print(
                f"Audio bytes received: {self.bytes_received}, sent: {self.bytes_sent}"
            )

    async def _send_transcripts(self, websocket: Any) -> None:
        async for t in self.stt.stream():
            payload = json.dumps({"text": t.text, "final": t.is_final})
            await websocket.send(payload)

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


def main(argv: Optional[Iterable[str]] = None) -> None:
    """CLI entry point to start the WebSocket server."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Run the audio WebSocket server")
    parser.add_argument("model", help="Path to Vosk model")
    parser.add_argument("--host", default="localhost", help="Host to bind")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind")
    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        server = AudioWebSocketServer(args.model, host=args.host, port=args.port)
    except RuntimeError as exc:  # Missing optional dependency
        print(f"Error: {exc}", file=sys.stderr)
        return

    print(f"Listening on ws://{args.host}:{args.port}")
    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        print("Server stopped by user")


if __name__ == "__main__":  # pragma: no cover - entry point
    main()
