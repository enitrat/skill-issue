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
"""The JSON row `tg read --json` emits, built from a stub Telethon message."""

from __future__ import annotations

import datetime as dt
import importlib.machinery
import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

loader = importlib.machinery.SourceFileLoader("tg_cli", str(Path(__file__).parent.parent / "tg_cli.py"))
spec = importlib.util.spec_from_loader("tg_cli", loader)
tg = importlib.util.module_from_spec(spec)
sys.modules["tg_cli"] = tg
loader.exec_module(tg)


def message(**over):
    base = dict(id=42, date=dt.datetime(2026, 9, 3, 16, 22, tzinfo=dt.timezone.utc), out=True, sender=None, sender_id=1,
                voice=None, audio=None, photo=None, document=None, file=None, reply_to_msg_id=None, message="hello", text="hello")
    base.update(over)
    return SimpleNamespace(**base)


def test_text_message_row():
    row = tg._message_dict(message())
    assert (row["id"], row["from_me"], row["reply_to"], row["media"]) == (42, True, None, None)


def test_reply_link_is_kept():
    assert tg._message_dict(message(reply_to_msg_id=41))["reply_to"] == 41


def test_voice_note_is_audio_media():
    doc = SimpleNamespace(mime_type="audio/ogg")
    row = tg._message_dict(message(voice=True, document=doc))
    assert row["media"] == {"kind": "audio", "mimetype": "audio/ogg", "voice": True}


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-q"]))
