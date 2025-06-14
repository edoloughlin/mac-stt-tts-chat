import json
import pathlib
import sys
from unittest import mock
import types

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from src.backend import config


def test_load_config_overrides_defaults(tmp_path):
    cfg_file = tmp_path / "cfg.json"
    cfg_file.write_text(json.dumps({"server": {"port": 9000}, "tts": {"voice": "alice"}}))
    cfg = config.load_config(str(cfg_file))
    assert cfg.server.port == 9000
    assert cfg.server.host == "localhost"
    assert cfg.tts.voice == "alice"


def test_create_tts_passes_voice():
    fake = types.SimpleNamespace(Synthesizer=mock.Mock())
    with mock.patch.dict(sys.modules, {"orpheus_speech": fake}):
        cfg = config.TTSConfig(type="orpheus", model_path="m", voice="bob")
        tts = config.create_tts(cfg)
        fake.Synthesizer.assert_called_with("m", device="cpu", voice="bob")
        assert tts is not None
