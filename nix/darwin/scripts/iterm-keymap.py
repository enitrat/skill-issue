"""Give every iTerm profile the "Natural Text Editing" key mappings.

iTerm rewrites its preferences when it quits, so editing them while it runs
loses the change. This reconciles on every switch, but only while iTerm is
stopped.
"""

import os
import plistlib
import subprocess
import sys

PRESET = "/Applications/iTerm.app/Contents/Resources/PresetKeyMappings.plist"
PREFS = os.path.expanduser("~/Library/Preferences/com.googlecode.iterm2.plist")


def log(message: str) -> None:
    print(f"[iterm-keymap] {message}")


if not os.path.isdir("/Applications/iTerm.app"):
    log("iTerm not installed, nothing to configure")
    sys.exit(0)
if not os.path.isfile(PRESET):
    log(f"no preset file at {PRESET}; did iTerm's layout change?")
    sys.exit(1)
if not os.path.isfile(PREFS):
    log("iTerm has no preferences yet; launch it once, then switch again")
    sys.exit(0)

# Not pgrep: reading another process's argv needs an entitlement the shell
# lacks, so pgrep silently finds nothing. `ps -Ac` reports the accounting name.
# Absolute path: home-manager activation runs with a minimal PATH.
running = subprocess.run(["/bin/ps", "-Ac", "-o", "comm="], capture_output=True, text=True).stdout.split("\n")
if "iTerm2" in running:
    log("iTerm is running and would overwrite this on quit; skipping.")
    log("Quit iTerm and switch again, or set it by hand: Settings > Profiles > Keys > Presets > Natural Text Editing")
    sys.exit(0)

with open(PRESET, "rb") as f:
    preset = plistlib.load(f).get("Natural Text Editing")
if not preset:
    log("preset 'Natural Text Editing' not found")
    sys.exit(1)

with open(PREFS, "rb") as f:
    prefs = plistlib.load(f)

changed = 0
for profile in prefs.get("New Bookmarks") or []:
    keymap = profile.get("Keyboard Map") or {}
    missing = {k: v for k, v in preset.items() if keymap.get(k) != v}
    if missing:
        keymap.update(missing)
        profile["Keyboard Map"] = keymap
        changed += 1

if changed:
    with open(PREFS, "wb") as f:
        plistlib.dump(prefs, f, fmt=plistlib.FMT_BINARY)
    log(f"Natural Text Editing applied to {changed} profile(s)")
