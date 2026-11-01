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
"""Which Telethon call `tg read` makes, with and without --since, against a stub client."""

from __future__ import annotations

import datetime as dt
import importlib.machinery
import importlib.util
import sys
from pathlib import Path

loader = importlib.machinery.SourceFileLoader("tg_cli", str(Path(__file__).parent.parent / "tg_cli.py"))
spec = importlib.util.spec_from_loader("tg_cli", loader)
tg = importlib.util.module_from_spec(spec)
sys.modules["tg_cli"] = tg
loader.exec_module(tg)

CUTOFF = dt.datetime(2026, 9, 28, 22, tzinfo=dt.timezone.utc)


class StubClient:
    """Records the fetch kwargs; get_messages returns newest first like Telethon."""

    def __init__(self):
        self.calls = []

    def get_messages(self, entity, **kw):
        self.calls.append(("get_messages", kw))
        return [3, 2, 1]

    def iter_messages(self, entity, **kw):
        self.calls.append(("iter_messages", kw))
        return iter([1, 2, 3])


def test_no_since_reads_latest_in_chronological_order():
    assert tg._thread_messages(StubClient(), "chat", 3, None) == [1, 2, 3]


def test_since_walks_forward_from_cutoff():
    client = StubClient()
    tg._thread_messages(client, "chat", 60, CUTOFF)
    assert client.calls == [("iter_messages", {"limit": 60, "offset_date": CUTOFF, "reverse": True})]


def test_since_keeps_chronological_order():
    assert tg._thread_messages(StubClient(), "chat", 60, CUTOFF) == [1, 2, 3]


def test_naive_since_is_utc():
    assert tg._parse_since("2026-09-28T22:00:00") == CUTOFF


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-q"]))
