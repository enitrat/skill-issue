# macOS System Settings

Configuration tweaks for macOS system behavior and appearance.

## Menu Bar Icon Spacing

Applied automatically by `run_once_after_40-system-defaults-macos`, which sets
spacing and padding to 6 so icons stop sliding behind the notch.

The keys must go under `com.apple.controlcenter`. The `NSGlobalDomain`
equivalents you'll find in most blog posts only move third-party
`NSStatusItem` apps and do nothing for Apple's own menu bar icons.

Changes take effect on next login — `killall SystemUIServer` does not reload
these.

### Try other values

```bash
defaults write com.apple.controlcenter NSStatusItemSpacing -int 8
defaults write com.apple.controlcenter NSStatusItem2ExtensionMinPadding -int 8
```

Smaller is tighter. Log out and back in to see the result. To make a new value
stick across machines, change it in the provisioning script rather than here.

### Revert to defaults

```bash
defaults delete com.apple.controlcenter NSStatusItemSpacing
defaults delete com.apple.controlcenter NSStatusItem2ExtensionMinPadding
```

## Keep Mac Awake with Lid Closed

Use Amphetamine to keep your Mac running even when the lid is closed (e.g., in a backpack with network/terminal sessions active).

### Why Amphetamine?

The built-in `caffeinate` command doesn't reliably prevent sleep when the MacBook lid is closed. Amphetamine is a free Mac App Store app with "closed-lid mode" that actually works.

### Installation

Amphetamine is declared in `dotfiles/.chezmoidata/packages.toml` and installed
with the rest of the Brewfile. To install it standalone:

```bash
# Install via Homebrew
brew install --cask amphetamine

# Or download from Mac App Store
open "macappstore://apps.apple.com/app/amphetamine/id937984704"
```

### Configuration

1. Launch Amphetamine
2. Settings → General → Enable "Allow closed-display sleep prevention"
3. Start a session with "Closed-Display Mode" enabled

### Alternative: caffeinate (requires external display or won't close lid)

```bash
# Basic usage (won't survive lid close alone)
caffeinate -s -i

# Run with a specific command
caffeinate -s -i claude
```

Flags:
- `-s` prevents system sleep
- `-i` prevents idle sleep
- `-d` prevents display sleep

**Note**: For reliable closed-lid operation, use Amphetamine instead.

## Raycast Replacing Spotlight (Cmd+Space)

Raycast is declared in `dotfiles/.chezmoidata/packages.toml`.
`run_once_after_40-system-defaults-macos` then disables Spotlight's Cmd+Space
binding (`AppleSymbolicHotKeys` key `64`) so Raycast can claim it.

### Manual step required

Raycast has no scriptable preference for its own global hotkey (it isn't
stored under `defaults read com.raycast.macos`). After the script runs:

1. Open Raycast > Settings (`Cmd+,`) > General
2. Set "Raycast Hotkey" to `Cmd+Space`

### Revert to Spotlight

```bash
/usr/libexec/PlistBuddy -c "Set :AppleSymbolicHotKeys:64:enabled true" \
  ~/Library/Preferences/com.apple.symbolichotkeys.plist
killall SystemUIServer
```

## Other macOS Tweaks

(Add more macOS system customizations here as needed)
