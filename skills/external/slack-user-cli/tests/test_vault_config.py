#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11,<3.12"  # leveldb 0.201 (via slacktokens) uses PyUnicode_AS_UNICODE, removed in 3.12
# dependencies = [
#     "pytest==9.1.1",
#     "slack-sdk==3.41.0",
#     "slacktokens==0.2.6",
#     "click==8.3.2",
#     "rich==14.3.3",
#     "requests==2.33.1",
# ]
#
# [tool.uv]
# exclude-newer = "2026-10-27T00:00:00Z"
# ///
"""Credential precedence and safe synchronization through the shared vault broker."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import slack_user_cli as cli  # noqa: E402


def completed(stdout: str, code: int = 0) -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(args=[], returncode=code, stdout=stdout, stderr="")


def test_vault_config_parses_helper_output(monkeypatch):
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: completed(json.dumps({"cookie": "d", "workspaces": {}})))
    assert cli.vault_config()["cookie"] == "d"


def test_vault_config_uses_connector_broker(monkeypatch):
    seen = {}
    monkeypatch.setattr(subprocess, "run", lambda cmd, **k: seen.setdefault("cmd", cmd) and completed("{}"))
    cli.vault_config()
    assert seen["cmd"][1:] == ["auth", "load", "slack"]


def test_vault_config_empty_when_helper_fails(monkeypatch):
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: completed("", 3))
    assert cli.vault_config() == {}


def test_vault_config_empty_when_helper_missing(monkeypatch):
    def boom(*a, **k):
        raise FileNotFoundError("claudine-secret")
    monkeypatch.setattr(subprocess, "run", boom)
    assert cli.vault_config() == {}


def test_load_config_uses_vault_without_local_file(monkeypatch, tmp_path):
    monkeypatch.setattr(cli, "CONFIG_FILE", tmp_path / "missing.json")
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: completed(json.dumps({"default": "acme", "workspaces": {}})))
    assert cli.load_config()["default"] == "acme"


def test_vault_precedes_existing_local_config(monkeypatch, tmp_path):
    path = tmp_path / "config.json"
    path.write_text('{"value": "local"}')
    monkeypatch.setattr(cli, "CONFIG_FILE", path)
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: completed('{"value": "vault"}'))
    assert cli.load_config()["value"] == "vault"


def test_pending_local_login_precedes_vault(monkeypatch, tmp_path):
    path = tmp_path / "config.json"
    path.write_text('{"value": "fresh"}')
    path.with_suffix(".pending").touch()
    monkeypatch.setattr(cli, "CONFIG_FILE", path)
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: completed('{"value": "stale"}'))
    assert cli.load_config()["value"] == "fresh"


def test_malformed_broker_output_is_unavailable(monkeypatch):
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: completed('invalid'))
    assert cli.auth_broker("load") == {}


def test_auth_status_cli_is_noninteractive(monkeypatch, tmp_path):
    from click.testing import CliRunner
    monkeypatch.setattr(cli, "CONFIG_FILE", tmp_path / "missing.json")
    monkeypatch.setattr(cli, "auth_broker", lambda *a: {"source": "vault", "pending": False})
    result = CliRunner().invoke(cli.cli, ["auth-status", "--json"])
    assert json.loads(result.output)["source"] == "vault"


def test_auth_sync_cli_reports_pending(monkeypatch, tmp_path):
    from click.testing import CliRunner
    monkeypatch.setattr(cli, "CONFIG_FILE", tmp_path / "missing.json")
    monkeypatch.setattr(cli, "auth_broker", lambda operation, *a: {"key": "value"} if operation == "load" else {"pending": True})
    assert CliRunner().invoke(cli.cli, ["auth-sync"]).exit_code == 3


def test_save_sends_credentials_only_via_stdin(monkeypatch, tmp_path):
    seen = {}
    monkeypatch.setattr(cli, "CONFIG_FILE", tmp_path / "config.json")
    def run(command, **kwargs):
        seen.update(command=command, stdin=kwargs["input"])
        return completed('{"source": "vault", "pending": false}')
    monkeypatch.setattr(subprocess, "run", run)
    cli.save_config({"secret": "credential"})
    assert (seen["command"][1:], json.loads(seen["stdin"])) == (["auth", "save", "slack"], {"secret": "credential"})


def test_save_restricts_existing_file_permissions(monkeypatch, tmp_path):
    path = tmp_path / "config.json"
    path.touch(mode=0o644)
    monkeypatch.setattr(cli, "CONFIG_FILE", path)
    monkeypatch.setattr(cli, "auth_broker", lambda *a: {})
    cli.save_config({"secret": "credential"})
    assert path.stat().st_mode & 0o777 == 0o600


def test_save_retains_pending_marker_when_broker_missing(monkeypatch, tmp_path):
    path = tmp_path / "config.json"
    monkeypatch.setattr(cli, "CONFIG_FILE", path)
    monkeypatch.setattr(cli, "auth_broker", lambda *a: {})
    cli.save_config({"secret": "credential"})
    assert path.with_suffix(".pending").exists()


def test_save_clears_pending_after_vault_success(monkeypatch, tmp_path):
    path = tmp_path / "config.json"
    monkeypatch.setattr(cli, "CONFIG_FILE", path)
    monkeypatch.setattr(cli, "auth_broker", lambda *a: {"source": "vault", "pending": False})
    cli.save_config({"secret": "credential"})
    assert not path.with_suffix(".pending").exists()


def test_auth_status_process_works_without_login(tmp_path):
    import os
    import sys
    from pathlib import Path

    broker = tmp_path / "claudine-secret"
    broker.write_text(
        "#!" + sys.executable + "\n"
        '# /// script\n# requires-python = ">=3.11"\n# dependencies = []\n# ///\n'
        '"""Return credential metadata for the process-level test."""\n'
        'import sys\n'
        'sys.stdout.write(\'{"source":"vault","pending":false,"configured":true}\')\n'
    )
    broker.chmod(0o700)
    env = {**os.environ, "HOME": str(tmp_path), "PATH": str(tmp_path) + os.pathsep + os.environ["PATH"]}
    result = subprocess.run(
        [sys.executable, "-O", str(Path(cli.__file__)), "auth-status", "--json"],
        capture_output=True, text=True, timeout=15, env=env,
    )
    assert (result.returncode, json.loads(result.stdout)["source"]) == (0, "vault")


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, *sys.argv[1:]]))
