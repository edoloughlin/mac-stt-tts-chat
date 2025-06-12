from __future__ import annotations

import asyncio
import subprocess
import shutil
import tempfile
from pathlib import Path

from .base import TTS


class MacSayTTS(TTS):
    """TTS using the macOS ``say`` command."""

    def __init__(self, voice: str = "Samantha") -> None:
        if shutil.which("say") is None:
            raise RuntimeError("'say' command not found")
        self.voice = voice

    async def speak(self, text: str) -> bytes:
        def _run() -> bytes:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                path = Path(tmp.name)
            cmd = [
                "say",
                "-v",
                self.voice,
                text,
                "-o",
                str(path),
                "--data-format=LEI16@16000",
            ]
            subprocess.run(cmd, check=True)
            data = path.read_bytes()
            path.unlink(missing_ok=True)
            return data

        return await asyncio.to_thread(_run)
