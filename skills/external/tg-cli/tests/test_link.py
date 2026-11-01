#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "click==8.3.3",
#     "qrcode==8.2",
#     "telethon==1.44.0",
#     "pytest==9.1.1",
# ]
#
# [tool.uv]
# exclude-newer = "2026-10-27T00:00:00Z"
# ///
"""`tg link` without Telegram: the QR rendering, credential checks and auth-status under env credentials."""
import importlib.machinery
import importlib.util
import json
from pathlib import Path

import pytest
from click.testing import CliRunner


@pytest.fixture
def app(monkeypatch, tmp_path):
    path = Path(__file__).resolve().parents[1] / "tg_cli.py"
    loader = importlib.machinery.SourceFileLoader("link_telegram", str(path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    monkeypatch.setattr(module, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(module, "CONFIG_FILE", tmp_path / "config.json")
    monkeypatch.setattr(module, "SESSION_BASE", tmp_path / "session")
    monkeypatch.setattr(module, "LINK_STATE", tmp_path / "link.json")
    monkeypatch.setattr(module, "_auth_broker", lambda *args: None)
    monkeypatch.delenv("TG_API_ID", raising=False)
    monkeypatch.delenv("TG_API_HASH", raising=False)
    return module


def test_qr_svg_is_an_svg(app):
    assert app._qr_svg("tg://login?token=abc").lstrip().startswith("<svg")


def test_link_without_credentials_names_the_fix(app):
    result = CliRunner().invoke(app.cli, ["link"])
    assert "my.telegram.org" in result.output


def test_link_options_store_credentials(app, monkeypatch):
    # The helper announces its page through LINK_STATE; the stub does it at once.
    monkeypatch.setattr(app.subprocess, "Popen", lambda *a, **k: app.LINK_STATE.write_text('{"url": "u"}'))
    CliRunner().invoke(app.cli, ["link", "--api-id", "12345", "--api-hash", "abc"])
    assert json.loads(app.CONFIG_FILE.read_text()) == {"api_id": 12345, "api_hash": "abc"}


def test_auth_status_counts_env_credentials(app, monkeypatch):
    monkeypatch.setenv("TG_API_ID", "1")
    monkeypatch.setenv("TG_API_HASH", "h")
    result = CliRunner().invoke(app.cli, ["auth-status"])
    assert json.loads(result.output)["source"] == "env"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
