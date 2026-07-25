# Editor Setup Guide

This guide covers editor configuration for a fresh macOS install.

## Cursor / VS Code Extensions

| Extension | Description |
|-----------|-------------|
| [SemanticDiff](https://semanticdiff.com/) | Semantics-aware diff viewer that understands code structure for cleaner PR reviews |

### Install SemanticDiff

Open the command palette (`Cmd+Shift+P`) and run:
```
ext install semanticdiff.semanticdiff
```

Or via CLI:
```bash
cursor --install-extension semanticdiff.semanticdiff
# or for VS Code:
code --install-extension semanticdiff.semanticdiff
```

## Cursor Remote-SSH

Cursor's Settings Sync does not work — the Cursor team has confirmed it is
VS Code only. Extensions also don't sync to remote servers; install the ones
you need once via the Extensions panel over the Remote-SSH connection and they
persist in `~/.cursor-server/extensions`.

Cursor keeps every server version it has ever connected with under
`~/.cursor-server/bin/<commit>` and re-scans all of them on connect, so a
long-lived remote box gets slower to log into over time. Prune it with:

```bash
prune-cursor-server --dry-run   # see what would go
prune-cursor-server             # keep the 3 newest
```

This is periodic maintenance, not provisioning — run it by hand or from cron.
