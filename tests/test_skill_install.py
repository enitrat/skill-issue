#!/usr/bin/env python3
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class SkillInstallTests(unittest.TestCase):
    def test_emil_failed_publish_restores_skills_and_metadata(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            emil = root / "plugins/emil"
            (emil / "skills").mkdir(parents=True)
            shutil.copy(ROOT / "plugins/emil/sync", emil / "sync")
            for name in ("skills/old", "UPSTREAM"):
                (emil / name).write_text(f"old {name}")
            (emil / "LICENSE").symlink_to("missing-license")
            bin_dir = root / "bin"
            bin_dir.mkdir()
            git = bin_dir / "git"
            git.write_text('''#!/bin/sh
if [ "$1" = clone ]; then
  for arg do dest=$arg; done
  mkdir -p "$dest/skills"
  printf new > "$dest/skills/new"
  printf new > "$dest/LICENSE"
else
  printf 'new-revision\\n'
fi
''')
            git.chmod(0o755)
            mv = bin_dir / "mv"
            mv.write_text('''#!/bin/sh
case "$1" in */.sync.*/UPSTREAM) exit 1 ;; esac
exec /bin/mv "$@"
''')
            mv.chmod(0o755)
            env = {**os.environ, "PATH": f"{bin_dir}:{os.environ['PATH']}"}
            result = subprocess.run([str(emil / "sync")], env=env, capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            for name in ("skills/old", "UPSTREAM"):
                self.assertEqual((emil / name).read_text(), f"old {name}")
            self.assertTrue((emil / "LICENSE").is_symlink())
            self.assertEqual(os.readlink(emil / "LICENSE"), "missing-license")

    def test_emil_failed_fetch_keeps_old_skills(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "plugins/emil/skills").mkdir(parents=True)
            shutil.copy(ROOT / "plugins/emil/sync", root / "plugins/emil/sync")
            (root / "plugins/emil/skills/old").write_text("old")
            bin_dir = root / "bin"
            bin_dir.mkdir()
            fake = bin_dir / "git"
            fake.write_text('#!/bin/sh\nfor arg do dest=$arg; done\nmkdir -p "$dest"\n')
            fake.chmod(0o755)
            env = {**os.environ, "PATH": f"{bin_dir}:{os.environ['PATH']}"}
            result = subprocess.run([str(root / "plugins/emil/sync")], env=env, capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual((root / "plugins/emil/skills/old").read_text(), "old")

    def test_update_stages_every_skill_before_replacing_catalog(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "scripts").mkdir()
            shutil.copy(ROOT / "scripts/install-skills", root / "scripts/install-skills")
            catalog = root / "skills/external"
            for name in ("first", "second"):
                (catalog / name).mkdir(parents=True)
                (catalog / name / "SKILL.md").write_text(f"old {name}")
            (root / "skills-external.json").write_text(json.dumps({"skills": [
                {"name": "first", "source": "first-source"},
                {"name": "second", "source": "second-source"},
            ]}))
            bin_dir = root / "bin"
            bin_dir.mkdir()
            fake = bin_dir / "npx"
            fake.write_text('''#!/bin/sh
if [ "$2" = add ] && [ "$3" = . ]; then
  printf 'install\\n' >> "$TEST_LOG"
  exit 0
fi
name=$5
printf 'fetch %s\\n' "$name" >> "$TEST_LOG"
[ "$name" != "${FAIL_SKILL:-}" ] || exit 1
mkdir -p ".agents/skills/$name"
printf 'new %s' "$name" > ".agents/skills/$name/SKILL.md"
''')
            fake.chmod(0o755)
            env = {**os.environ, "HOME": temp, "PATH": f"{bin_dir}:{os.environ['PATH']}", "TEST_LOG": str(root / "log")}
            command = [str(root / "scripts/install-skills")]
            for name in ("first", "unrelated"):
                installed = root / ".agents/skills" / name
                (installed / "bin").mkdir(parents=True)
                (installed / "launcher").write_text("launcher")
                (installed / "bin/launcher").write_text("launcher")
            subprocess.run(command + ["--yes"], env=env, check=True, capture_output=True)
            self.assertEqual((root / "log").read_text(), "install\n")
            self.assertTrue((root / ".agents/skills/first/bin/launcher").is_symlink())
            self.assertFalse((root / ".agents/skills/unrelated/bin/launcher").is_symlink())
            result = subprocess.run(command + ["--update"], env={**env, "TMPDIR": str(root / "missing")}, capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(list(catalog.glob(".update-*")), [])
            result = subprocess.run(command + ["--update"], env={**env, "FAIL_SKILL": "second"}, capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            for name in ("first", "second"):
                self.assertEqual((catalog / name / "SKILL.md").read_text(), f"old {name}")
            shutil.rmtree(catalog / "first")
            (catalog / "first").symlink_to("missing-target")
            preload = root / "fail-rename.cjs"
            preload.write_text('''const fs = require("fs");
const rename = fs.renameSync;
fs.renameSync = (from, to) => {
  if (from.includes("/.update-") && !from.includes("/.backups/") && from.endsWith("/second") && to.endsWith("/external/second")) {
    throw new Error("injected publish failure");
  }
  return rename(from, to);
};
require("module").syncBuiltinESMExports();
''')
            result = subprocess.run(command + ["--update"], env={**env, "NODE_OPTIONS": f"--require={preload}"}, capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertTrue((catalog / "first").is_symlink())
            self.assertEqual(os.readlink(catalog / "first"), "missing-target")
            self.assertEqual((catalog / "second/SKILL.md").read_text(), "old second")
            (catalog / "first").unlink()
            (catalog / "first").mkdir()
            (catalog / "first/SKILL.md").write_text("old first")
            subprocess.run(command + ["--update"], env=env, check=True, capture_output=True)
            for name in ("first", "second"):
                self.assertEqual((catalog / name / "SKILL.md").read_text(), f"new {name}")


if __name__ == "__main__":
    unittest.main()
