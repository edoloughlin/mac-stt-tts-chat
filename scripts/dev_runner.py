#!/usr/bin/env python3
"""Development runner for mac-stt-tts-chat.

This script ensures a Python virtual environment exists,
installs dependencies and launches the backend WebSocket
server along with the React frontend. A Rich based
console layout displays logs and allows basic commands
like restart and git pull.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

VENV_DIR = Path("venv")
VENV_PY = VENV_DIR / "bin" / "python"

if sys.prefix == sys.base_prefix:
    if not VENV_PY.exists():
        print("Creating virtual environment...")
        subprocess.check_call(["python3.12", "-m", "venv", str(VENV_DIR)])
    print("Installing dependencies...")
    subprocess.check_call([str(VENV_PY), "-m", "pip", "install", "-r", "requirements.txt"])
    dev_req = Path("requirements-dev.txt")
    if dev_req.exists():
        subprocess.check_call([str(VENV_PY), "-m", "pip", "install", "-r", str(dev_req)])
    os.execv(str(VENV_PY), [str(VENV_PY)] + sys.argv)

import asyncio
import json
from datetime import datetime
from typing import List

import contextlib
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

TRANSCRIPT_LOG = Path("transcript.log")
BACKEND_LOG = Path("backend.log")
FRONTEND_LOG = Path("frontend.log")
CONFIG_PATH = Path("config.example.json")

console = Console()

def ensure_venv() -> Path:
    """Create the virtual environment if needed."""
    if not VENV_PY.exists():
        console.print("[bold]Creating virtual environment...[/]")
        subprocess.check_call(["python3.12", "-m", "venv", str(VENV_DIR)])
    return VENV_PY


def install_deps(python: Path) -> None:
    """Install Python dependencies using pip."""
    console.print("[bold]Installing dependencies...[/]")
    subprocess.check_call([str(python), "-m", "pip", "install", "-r", "requirements.txt"])
    dev_req = Path("requirements-dev.txt")
    if dev_req.exists():
        subprocess.check_call([str(python), "-m", "pip", "install", "-r", str(dev_req)])


def _download_vosk() -> None:
    url = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
    console.print(f"[bold]Downloading Vosk model from {url}...[/]")
    subprocess.check_call(["curl", "-L", "-o", "model.zip", url])
    subprocess.check_call(["unzip", "-q", "model.zip"])
    os.rename("vosk-model-small-en-us-0.15", "vosk-model")
    Path("model.zip").unlink()


def _download_orpheus(dest: Path) -> None:
    url = os.environ.get(
        "ORPHEUS_REPO",
        "https://huggingface.co/orpheus-speech/orpheus-3b-styletts2/resolve/main/orpheus.tar.gz",
    )
    console.print(f"[bold]Downloading Orpheus model from {url}...[/]")
    subprocess.check_call(["curl", "-L", "-o", "orpheus.tar.gz", url])
    dest.mkdir(exist_ok=True)
    subprocess.check_call(["tar", "-xzf", "orpheus.tar.gz", "-C", str(dest)])
    Path("orpheus.tar.gz").unlink()


def check_models() -> None:
    """Ensure STT/TTS model files exist, downloading them with permission."""
    if not Path("vosk-model").exists():
        ans = input("Vosk model not found. Download now (~50MB)? [y/N] ")
        if ans.lower().startswith("y"):
            _download_vosk()
        else:
            sys.exit(1)

    orpheus = Path(os.environ.get("ORPHEUS_MODEL", "orpheus-3b-styletts2"))
    if not orpheus.exists():
        ans = input("Orpheus model not found. Download now (~1GB)? [y/N] ")
        if ans.lower().startswith("y"):
            _download_orpheus(orpheus)
        else:
            sys.exit(1)

def format_config() -> Text:
    data = {}
    if CONFIG_PATH.exists():
        data = json.loads(CONFIG_PATH.read_text())
    txt = Text()
    for k, v in data.items():
        txt.append(f"{k}: ", style="cyan")
        txt.append(str(v), style="magenta")
        txt.append("\n")
    return txt


async def read_stream(stream: asyncio.StreamReader, buf: List[str]) -> None:
    while True:
        line = await stream.readline()
        if not line:
            break
        buf.append(line.decode(errors="ignore").rstrip())
        if len(buf) > 100:
            del buf[0]


async def start_backend(python: Path) -> asyncio.subprocess.Process:
    proc = await asyncio.create_subprocess_exec(
        str(python),
        "-m",
        "src.backend.core.websocket_server",
        "vosk-model",
        "--transcript-log",
        str(TRANSCRIPT_LOG),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    return proc


async def start_frontend() -> asyncio.subprocess.Process:
    proc = await asyncio.create_subprocess_exec(
        "npm",
        "run",
        "dev",
        cwd="src/ui",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    return proc


async def main() -> None:
    python = ensure_venv()
    install_deps(python)
    check_models()
    TRANSCRIPT_LOG.touch(exist_ok=True)
    BACKEND_LOG.write_text("")
    FRONTEND_LOG.write_text("")

    backend_lines: List[str] = []
    frontend_lines: List[str] = []

    backend = await start_backend(python)
    asyncio.create_task(read_stream(backend.stdout, backend_lines))
    frontend = await start_frontend()
    asyncio.create_task(read_stream(frontend.stdout, frontend_lines))

    layout = Layout()
    layout.split_row(
        Layout(name="left", ratio=2),
        Layout(name="right", ratio=1),
    )
    layout["left"].split_column(
        Layout(name="transcript"), Layout(name="backend")
    )
    layout["right"].split_column(Layout(name="config"), Layout(name="frontend"))

    def refresh_layout() -> None:
        transcript_text = (
            Text("\n".join(TRANSCRIPT_LOG.read_text().splitlines()[-100:]))
            if TRANSCRIPT_LOG.exists()
            else Text()
        )
        layout["transcript"].update(Panel(transcript_text, title="transcript.log"))
        layout["backend"].update(
            Panel(Text("\n".join(backend_lines[-100:])), title="backend")
        )
        layout["frontend"].update(
            Panel(Text("\n".join(frontend_lines[-100:])), title="frontend")
        )
        layout["config"].update(Panel(format_config(), title="config"))
        footer = Text("Q quit | R restart | P pull")
        commit = (
            subprocess.check_output(["git", "rev-parse", "--short", "HEAD"]).decode().strip()
        )
        footer.append(f"    {commit} {datetime.now():%Y-%m-%d %H:%M:%S}", style="dim")
        layout.footer = Panel(footer)

    async def input_loop() -> None:
        nonlocal backend, frontend
        loop = asyncio.get_running_loop()
        while True:
            ch = await loop.run_in_executor(None, sys.stdin.read, 1)
            if not ch:
                continue
            ch = ch.upper()
            if ch == "Q":
                backend.terminate()
                frontend.terminate()
                return
            if ch == "R":
                backend.terminate()
                frontend.terminate()
                await backend.wait()
                await frontend.wait()
                backend = await start_backend(python)
                asyncio.create_task(read_stream(backend.stdout, backend_lines))
                frontend = await start_frontend()
                asyncio.create_task(read_stream(frontend.stdout, frontend_lines))
            if ch == "P":
                subprocess.call(["git", "pull"])
                backend.terminate()
                frontend.terminate()
                await backend.wait()
                await frontend.wait()
                backend = await start_backend(python)
                asyncio.create_task(read_stream(backend.stdout, backend_lines))
                frontend = await start_frontend()
                asyncio.create_task(read_stream(frontend.stdout, frontend_lines))

    input_task = asyncio.create_task(input_loop())

    try:
        with Live(layout, console=console, screen=True, refresh_per_second=2):
            while not input_task.done():
                refresh_layout()
                await asyncio.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        input_task.cancel()
        backend.terminate()
        frontend.terminate()
        with contextlib.suppress(asyncio.CancelledError):
            await input_task
        await backend.wait()
        await frontend.wait()


if __name__ == "__main__":
    asyncio.run(main())
