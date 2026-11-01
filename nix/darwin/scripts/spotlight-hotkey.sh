#!/bin/bash
# Disable symbolic hotkey 64 (Spotlight, Cmd+Space). The WindowServer reads
# symbolic hotkeys at login, so this takes effect at the next login.
set -euo pipefail

plist="$HOME/Library/Preferences/com.apple.symbolichotkeys.plist"
buddy=/usr/libexec/PlistBuddy

if "$buddy" -c "Print :AppleSymbolicHotKeys:64" "$plist" >/dev/null 2>&1; then
    [ "$("$buddy" -c "Print :AppleSymbolicHotKeys:64:enabled" "$plist")" = false ] && exit 0
    "$buddy" -c "Set :AppleSymbolicHotKeys:64:enabled false" "$plist"
else
    "$buddy" \
        -c "Add :AppleSymbolicHotKeys:64 dict" \
        -c "Add :AppleSymbolicHotKeys:64:enabled bool false" \
        -c "Add :AppleSymbolicHotKeys:64:value dict" \
        -c "Add :AppleSymbolicHotKeys:64:value:type string standard" \
        -c "Add :AppleSymbolicHotKeys:64:value:parameters array" \
        -c "Add :AppleSymbolicHotKeys:64:value:parameters: integer 65535" \
        -c "Add :AppleSymbolicHotKeys:64:value:parameters: integer 49" \
        -c "Add :AppleSymbolicHotKeys:64:value:parameters: integer 1048576" \
        "$plist"
fi
killall cfprefsd 2>/dev/null || true
echo "[spotlight-hotkey] Cmd+Space released; set it in Raycast > Settings > General after the next login"
