"""Make Cursor and VS Code open each folder as a native macOS tab of the current window.

A new window joins the existing window group as a tab because AppleWindowTabbingMode
is "always" (nix/darwin/default.nix). Both apps write their own settings.json, so this
sets two keys and leaves the rest of the file alone.
"""

import json
import os
import sys

SETTINGS = {
    "window.openFoldersInNewWindow": "on",
    "window.nativeTabs": True,
}
EDITORS = {
    "Cursor": "~/Library/Application Support/Cursor/User/settings.json",
    "VS Code": "~/Library/Application Support/Code/User/settings.json",
}

for name, path in EDITORS.items():
    path = os.path.expanduser(path)
    if not os.path.isdir(os.path.dirname(path)):
        continue
    data = {}
    if os.path.exists(path):
        try:
            with open(path) as f:
                data = json.load(f)
        except json.JSONDecodeError as error:
            print(f"[editor-defaults] invalid JSON in {path}: {error}", file=sys.stderr)
            sys.exit(1)
    if all(data.get(key) == value for key, value in SETTINGS.items()):
        continue
    data.update(SETTINGS)
    with open(path, "w") as f:
        json.dump(data, f, indent=4)
        f.write("\n")
    print(f"[editor-defaults] {name} opens folders as tabs")
