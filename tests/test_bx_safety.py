#!/usr/bin/env python3
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

BX = Path(__file__).resolve().parents[1] / "tools" / "bx"

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    home = root / "home"
    home.mkdir()
    bin_dir = root / "bin"
    bin_dir.mkdir()
    shutil.copy(BX, bin_dir / "bx")
    log = root / "calls"
    env = os.environ | {"HOME": str(home), "PATH": f"{bin_dir}:{os.environ['PATH']}", "CALLS": str(log)}

    def command(name, body):
        path = bin_dir / name
        path.write_text("#!/bin/bash\n" + body + "\n")
        path.chmod(0o755)

    command("boat", '''echo "boat $*" >> "$CALLS"
case "$1" in
  list) [ "${FAIL_INVENTORY:-}" = 1 ] && exit 1; if [ "${INVALID_INVENTORY:-}" = 1 ]; then echo '{"sandboxes":[{"id":"bx_live"}]}'; else echo '{"sandboxes":[{"id":"bx_live","name":"live-box","state":"running"}]}'; fi ;;
  snapshots) echo '{"named":[{"name":"dev"}]}' ;;
  new) echo '{"event":"ready","id":"bx_build"}' ;;
  info) echo '{"sandbox":{"hydrated":true}}' ;;
  snapshot) echo '{"event":"saved"}' ;;
esac''')
    command("herdr", 'echo "[]"')
    command("tailnet", 'echo "tailnet $*" >> "$CALLS"; [ "$1" != boxes ] || echo live-box')
    command("git", "printf '0123456789abcdef0123456789abcdef01234567\\trefs/heads/main\\n'")
    command("rm", '[ "${FAIL_RM:-}" != 1 ] || exit 1; exec /bin/rm "$@"')
    command("sudo", 'exit 0')
    command("systemctl", 'exit 1')
    command("ssh", '''echo "ssh $*" >> "$CALLS"
case "$*" in *"rm -f"*) bash -c "${@: -1}";; esac''')

    result = subprocess.run([str(bin_dir / "bx"), "gc", "--yes"], env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    calls = log.read_text()
    assert calls.count("boat list") == 1, calls
    assert "tailnet forget" not in calls, calls

    log.write_text("")
    result = subprocess.run([str(bin_dir / "bx"), "gc", "--yes"], env=env | {"FAIL_INVENTORY": "1"}, capture_output=True, text=True)
    assert result.returncode != 0, result.stderr
    assert "tailnet" not in log.read_text(), log.read_text()

    log.write_text("")
    result = subprocess.run([str(bin_dir / "bx"), "gc", "--yes"], env=env | {"INVALID_INVENTORY": "1"}, capture_output=True, text=True)
    assert result.returncode != 0, result.stderr
    assert "tailnet" not in log.read_text(), log.read_text()

    log.write_text("")
    result = subprocess.run([str(bin_dir / "bx"), "update", "dev"], env=env | {"FAIL_RM": "1"}, capture_output=True, text=True, timeout=10)
    assert result.returncode != 0, result.stderr
    assert "could not delete the logins" in result.stderr, result.stderr
    assert "boat snapshot " not in log.read_text(), log.read_text()

    log.write_text("")
    result = subprocess.run([str(bin_dir / "bx"), "update", "dev"], env=env, capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    assert "boat snapshot bx_build dev" in log.read_text(), log.read_text()

    log.write_text("")
    result = subprocess.run([str(bin_dir / "bx"), "new", "--snapshot", "dev", "--name", "fresh"], env=env, capture_output=True, text=True, timeout=10)
    assert result.returncode != 0, result.stderr
    assert "no box signing key" in result.stderr, result.stderr
    assert "boat new" not in log.read_text(), log.read_text()

print("bx safety checks passed")
