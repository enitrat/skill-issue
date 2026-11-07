#!/usr/bin/env python3
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ToolSafetyTests(unittest.TestCase):
    def test_boat_resolve_passes_token_on_stdin(self):
        with tempfile.TemporaryDirectory() as home:
            home = Path(home)
            bin_dir = home / "bin"
            bin_dir.mkdir()
            (home / ".ssh").mkdir()
            (home / ".ssh/ascii_box_ed25519.pub").write_text("public-key\n")
            security = bin_dir / "security"
            security.write_text("#!/bin/sh\nprintf '%s\\n' secret-token\n")
            security.chmod(0o755)
            curl = bin_dir / "curl"
            curl.write_text(
                "#!/bin/sh\nprintf '%s\\n' \"$@\" > \"$HOME/curl-args\"\n"
                "cat > \"$HOME/curl-input\"\n"
                "printf '%s\\n' '{\"hostKey\":\"ssh-ed25519 public-key\"}'\n"
            )
            curl.chmod(0o755)
            env = {**os.environ, "HOME": str(home), "XDG_CACHE_HOME": str(home / ".cache"), "PATH": f"{bin_dir}:{os.environ['PATH']}"}
            subprocess.run([str(ROOT / "tools/boat-resolve"), "hostkey", "bx_test"], env=env, check=True, capture_output=True)
            self.assertNotIn("secret-token", (home / "curl-args").read_text())
            self.assertEqual((home / "curl-input").read_text(), "Authorization: Bearer secret-token\n")

    def test_prune_only_removes_oldest_enumerated_directory(self):
        with tempfile.TemporaryDirectory() as home:
            home = Path(home)
            cache = home / ".cursor-server/bin"
            cache.mkdir(parents=True)
            for i, name in enumerate(["old\nname", "second", "third", "newest"]):
                path = cache / name
                path.mkdir()
                os.utime(path, (1000000000 + i, 1000000000 + i))
            env = {**os.environ, "HOME": str(home)}
            command = [str(ROOT / "tools/prune-cursor-server"), "--keep", "3"]
            subprocess.run(command + ["--dry-run"], env=env, check=True, capture_output=True)
            self.assertEqual(len(list(cache.iterdir())), 4)
            subprocess.run(command, env=env, check=True, capture_output=True)
            self.assertEqual({p.name for p in cache.iterdir()}, {"second", "third", "newest"})


if __name__ == "__main__":
    unittest.main()
