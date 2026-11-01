"""Make Cursor and VS Code open folders in the current window.

Both apps write their own settings.json, so this sets one key and leaves the
rest of the file alone.
"""

import json
import os
import sys

KEY, VALUE = "window.openFoldersInNewWindow", "off"
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
    if data.get(KEY) == VALUE:
        continue
    data[KEY] = VALUE
    with open(path, "w") as f:
        json.dump(data, f, indent=4)
        f.write("\n")
    print(f"[editor-defaults] {name} reuses its current window")
