from __future__ import annotations

import json
from dataclasses import dataclass, field, is_dataclass
from pathlib import Path
from typing import Optional


@dataclass
class STTConfig:
    type: str = "vosk"
    model_path: str = "vosk-model"
    samplerate: int = 16000


@dataclass
class TTSConfig:
    type: str = "orpheus"
    model_path: str = "orpheus-3b"
    device: str = "cpu"
    voice: str = "default"


@dataclass
class AgentConfig:
    type: str = "echo"


@dataclass
class ServerConfig:
    host: str = "localhost"
    port: int = 8000
    transcript_log: Optional[str] = "transcript.log"


@dataclass
class BackendConfig:
    stt: STTConfig = field(default_factory=STTConfig)
    tts: TTSConfig = field(default_factory=TTSConfig)
    agent: AgentConfig = field(default_factory=AgentConfig)
    server: ServerConfig = field(default_factory=ServerConfig)


def _update(obj, data):
    for key, value in data.items():
        if hasattr(obj, key):
            attr = getattr(obj, key)
            if is_dataclass(attr) and isinstance(value, dict):
                _update(attr, value)
            else:
                setattr(obj, key, value)


def load_config(path: str | None) -> BackendConfig:
    cfg = BackendConfig()
    if path:
        data = json.loads(Path(path).read_text())
        _update(cfg, data)
    return cfg


def create_stt(cfg: STTConfig):
    if cfg.type == "vosk":
        from .stt import VoskStream
        return VoskStream(cfg.model_path, samplerate=cfg.samplerate)
    raise ValueError(f"Unknown STT type: {cfg.type}")


def create_agent(cfg: AgentConfig):
    if cfg.type == "echo":
        from .agent.simple import EchoAgent
        return EchoAgent()
    raise ValueError(f"Unknown agent type: {cfg.type}")


def create_tts(cfg: TTSConfig):
    if cfg.type == "orpheus":
        from .tts.orpheus import OrpheusStyleTTS
        return OrpheusStyleTTS(cfg.model_path, device=cfg.device, voice=cfg.voice)
    if cfg.type == "macsay":
        from .tts.macsay import MacSayTTS
        return MacSayTTS()
    if cfg.type == "console":
        from .tts.simple import ConsoleTTS
        return ConsoleTTS()
    raise ValueError(f"Unknown TTS type: {cfg.type}")
