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

## Other macOS Tweaks

(Add more macOS system customizations here as needed)
