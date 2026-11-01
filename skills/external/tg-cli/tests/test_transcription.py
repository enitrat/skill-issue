#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "click==8.3.3",
#     "telethon==1.44.0",
#     "pytest==9.1.1",
# ]
#
# [tool.uv]
# exclude-newer = "2026-10-27T00:00:00Z"
# ///
"""Optional transcription preserves Telegram messages across provider failures."""

import asyncio
import datetime as dt
import importlib.machinery
import importlib.util
import json
import subprocess
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

import pytest
from click.testing import CliRunner


@pytest.fixture
def app(monkeypatch, tmp_path):
    loader = importlib.machinery.SourceFileLoader(
        "tg_transcription", str(Path(__file__).resolve().parents[1] / "tg_cli.py")
    )
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    monkeypatch.setattr(module, "TRANSCRIPT_CACHE", tmp_path / "transcripts")
    return module


@pytest.fixture
def speech(app, monkeypatch):
    calls = []

    def run(argv, **kwargs):
        calls.append(argv)
        return SimpleNamespace(returncode=0, stdout='{"text":" Bonjour ","language":"fr"}')

    monkeypatch.setattr(app.shutil, "which", lambda _: "transcribe")
    monkeypatch.setattr(app.subprocess, "run", run)
    return calls


def test_transcriber_command(app, speech):
    app._transcribe_audio("voice.ogg", "parakeet")
    assert speech == [["transcribe", "file", "voice.ogg", "--backend", "parakeet", "--json"]]


def test_transcriber_result(app, speech):
    assert app._transcribe_audio("voice.ogg", "auto") == {"text": "Bonjour", "language": "fr"}


@pytest.mark.parametrize("output", ["invalid", "[]", "{}", '{"text":null}', '{"text":12}'])
def test_invalid_output_keeps_message(app, monkeypatch, output):
    monkeypatch.setattr(app.subprocess, "run", lambda *a, **k: SimpleNamespace(returncode=0, stdout=output))
    assert app._transcribe_audio("voice.ogg", "auto") is None


@pytest.mark.parametrize("error", [FileNotFoundError("transcribe"), subprocess.TimeoutExpired("transcribe", 900)])
def test_process_failure_keeps_message(app, monkeypatch, error):
    def run(*args, **kwargs):
        raise error

    monkeypatch.setattr(app.subprocess, "run", run)
    assert app._transcribe_audio("voice.ogg", "auto") is None


def test_nonzero_exit_keeps_message(app, monkeypatch):
    monkeypatch.setattr(app.subprocess, "run", lambda *a, **k: SimpleNamespace(returncode=1, stderr="failed"))
    assert app._transcribe_audio("voice.ogg", "auto") is None


def test_cached_transcript_skips_download(app, speech):
    app._transcript(1, 2, lambda _: "voice.ogg", "auto")
    assert app._transcript(1, 2, lambda _: pytest.fail("cached audio downloaded"), "auto") == "Bonjour"


def test_cache_separates_backends(app, speech):
    app._transcript(1, 2, lambda _: "voice.ogg", "whisper")
    app._transcript(1, 2, lambda _: "voice.ogg", "parakeet")
    assert len(speech) == 2


@pytest.mark.parametrize("contents", ["{", "[]", '{"text":42}'])
def test_damaged_cache_retries(app, speech, contents):
    app.TRANSCRIPT_CACHE.mkdir()
    (app.TRANSCRIPT_CACHE / "1_2_auto.json").write_text(contents)
    assert app._transcript(1, 2, lambda _: "voice.ogg", "auto") == "Bonjour"


@pytest.mark.parametrize("target,mode", [("", 0o700), ("1_2_auto.json", 0o600)])
def test_cache_permissions(app, speech, target, mode):
    app._transcript(1, 2, lambda _: "voice.ogg", "auto")
    assert (app.TRANSCRIPT_CACHE / target).stat().st_mode & 0o777 == mode


def test_download_failure_keeps_message(app):
    def fetch(_):
        raise OSError("download unavailable")

    assert app._transcript(1, 2, fetch, "auto") is None


def test_cache_write_failure_keeps_transcript(app, speech):
    app.TRANSCRIPT_CACHE.write_text("not a directory")
    assert app._transcript(1, 2, lambda _: "voice.ogg", "auto") == "Bonjour"


def test_failed_transcription_is_not_cached(app, monkeypatch):
    monkeypatch.setattr(app, "_transcribe_audio", lambda *a: None)
    app._transcript(1, 2, lambda _: "voice.ogg", "auto")
    assert not app.TRANSCRIPT_CACHE.exists()


@pytest.fixture
def telegram(app, monkeypatch):
    message = SimpleNamespace(
        id=2, chat_id=1, date=dt.datetime(2026, 10, 15, tzinfo=dt.timezone.utc),
        out=True, sender=None, sender_id=1, voice=True, audio=None, photo=None,
        document=SimpleNamespace(mime_type="audio/ogg"), file=None,
        reply_to_msg_id=None, message="", media=SimpleNamespace(), action=None,
    )
    downloads = []

    def download(message, file):
        downloads.append(file)
        return str(Path(file) / "voice.ogg")

    client = SimpleNamespace(get_messages=lambda *a, **k: [message], download_media=download)

    @contextmanager
    def connected():
        yield client

    monkeypatch.setattr(app, "_client", connected)
    monkeypatch.setattr(app, "_resolve_dialog", lambda *a: SimpleNamespace(entity=1, name="Alice"))
    monkeypatch.setattr(app, "_dialog_filters", lambda *a: [SimpleNamespace(title="Work", include_peers=[1])])
    client.get_entity = lambda _: SimpleNamespace(first_name="Alice", last_name="")
    return message, client, downloads


@pytest.mark.parametrize("command", [["read", "Alice"], ["folder", "Work"]])
def test_json_command_adds_transcript(app, telegram, speech, command):
    result = CliRunner().invoke(app.cli, command + ["--transcribe", "--json"])
    if result.exception:
        raise result.exception
    rows = json.loads(result.output)
    row = rows[0]["messages"][0] if command[0] == "folder" else rows[0]
    assert row["transcript"] == "Bonjour"


@pytest.mark.parametrize("options", [[], ["--no-transcribe"]])
def test_read_without_transcription_skips_download(app, telegram, options, monkeypatch):
    monkeypatch.setenv("TG_TRANSCRIBE", "1" if options else "0")
    CliRunner().invoke(app.cli, ["read", "Alice", "--json"] + options)
    assert telegram[2] == []


def test_environment_enables_transcription(app, telegram, speech, monkeypatch):
    monkeypatch.setenv("TG_TRANSCRIBE", "1")
    result = CliRunner().invoke(app.cli, ["read", "Alice", "--json"])
    assert json.loads(result.output)[0]["transcript"] == "Bonjour"


def test_human_output_includes_transcript(app, telegram, speech):
    result = CliRunner().invoke(app.cli, ["read", "Alice", "--transcribe"])
    assert "[transcript] Bonjour" in result.output


def test_live_cache_skips_download(app, telegram, speech):
    app._transcript(1, 2, lambda _: "voice.ogg", "auto")
    assert asyncio.run(app._live_transcript(telegram[0], "auto")) == "Bonjour"


def test_live_transcription(app, telegram, speech):
    async def download(file):
        return str(Path(file) / "voice.ogg")

    telegram[0].download_media = download
    assert asyncio.run(app._live_transcript(telegram[0], "auto")) == "Bonjour"


def test_live_download_failure_keeps_message(app, telegram):
    async def download(file):
        raise OSError("download unavailable")

    telegram[0].download_media = download
    assert asyncio.run(app._live_transcript(telegram[0], "auto")) is None


def test_listen_emits_transcript(app, telegram, speech):
    message, client, _ = telegram

    async def download(file):
        return str(Path(file) / "voice.ogg")

    message.download_media = download

    def on(event_filter):
        def register(handler):
            client.handler = handler
            return handler

        return register

    client.on = on
    client.run_until_disconnected = lambda: asyncio.run(
        client.handler(SimpleNamespace(message=message, chat_id=1))
    )
    result = CliRunner().invoke(app.cli, ["listen", "Alice", "--transcribe"])
    if result.exception:
        raise result.exception
    assert json.loads(result.stdout)["transcript"] == "Bonjour"


def test_text_messages_skip_transcription(app, telegram, speech):
    telegram[0].voice = None
    telegram[0].message = "hello"
    result = CliRunner().invoke(app.cli, ["read", "Alice", "--transcribe", "--json"])
    assert "transcript" not in json.loads(result.output)[0]


def test_json_read_survives_download_failure(app, telegram):
    def download(*args, **kwargs):
        raise OSError("download unavailable")

    telegram[1].download_media = download
    result = CliRunner().invoke(app.cli, ["read", "Alice", "--transcribe", "--json"])
    assert json.loads(result.stdout)[0]["transcript"] is None


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
