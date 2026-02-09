# macOS System Settings

Configuration tweaks for macOS system behavior and appearance.

## Menu Bar Icon Spacing

Adjust the spacing and padding of icons in the macOS menu bar (top-bar).

### Apply Custom Spacing

```bash
# Set icon spacing (default: ~20, recommended: 12)
defaults -currentHost write -globalDomain NSStatusItemSpacing -int 12

# Set selection padding (default: ~12, recommended: 8)
defaults -currentHost write -globalDomain NSStatusItemSelectionPadding -int 8

# Restart SystemUIServer to apply changes
killall SystemUIServer
```

### Recommended Values

- **Spacing**: `12` - Good balance between visibility and space efficiency
- **Padding**: `8` - Comfortable selection target without wasting space

Adjust these numbers based on your preferences:
- **Smaller values** = tighter spacing (more icons visible)
- **Larger values** = more breathing room (easier to click)

### Revert to Defaults

```bash
defaults -currentHost delete -globalDomain NSStatusItemSpacing
defaults -currentHost delete -globalDomain NSStatusItemSelectionPadding
killall SystemUIServer
```

### Quick Test Different Values

```bash
# Try different spacing values
for spacing in 6 8 10 12 15 20; do
  defaults -currentHost write -globalDomain NSStatusItemSpacing -int $spacing
  defaults -currentHost write -globalDomain NSStatusItemSelectionPadding -int $(($spacing - 4))
  killall SystemUIServer
  echo "Applied spacing: $spacing, padding: $(($spacing - 4))"
  read -p "Press Enter to try next value..."
done
```

## Keep Mac Awake with Lid Closed

Use Amphetamine to keep your Mac running even when the lid is closed (e.g., in a backpack with network/terminal sessions active).

### Why Amphetamine?

The built-in `caffeinate` command doesn't reliably prevent sleep when the MacBook lid is closed. Amphetamine is a free Mac App Store app with "closed-lid mode" that actually works.

### Installation

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

## Other macOS Tweaks

(Add more macOS system customizations here as needed)
