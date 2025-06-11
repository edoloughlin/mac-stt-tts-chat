from __future__ import annotations

import asyncio
import contextlib
import json
from typing import Any

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

    async def _send_transcripts(self, websocket: Any) -> None:
        async for t in self.stt.stream():
            payload = json.dumps({"text": t.text, "final": t.is_final})
            await websocket.send(payload)

    async def _handler(self, websocket: Any) -> None:
        send_task = asyncio.create_task(self._send_transcripts(websocket))
        try:
            async for message in websocket:
                if isinstance(message, (bytes, bytearray)):
                    self.stt.feed_audio(bytes(message))
        finally:
            send_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await send_task

    async def run(self) -> None:
        async with websockets.serve(self._handler, self.host, self.port):
            await asyncio.Future()  # run forever
