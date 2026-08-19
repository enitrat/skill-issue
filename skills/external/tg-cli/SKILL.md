---
name: tg-cli
description:
  "Read and send your own Telegram chats from the terminal via the bundled
  `tg` command. Logs in as your Telegram **user account** over MTProto
  (Telethon) — not a bot — so it sees every chat your account sees. `tg login`
  authenticates once (phone + code + 2FA), `tg chats` lists conversations, `tg
  folders` / `tg folder <name>` list and batch-read chat folders, `tg folder-add
  <folder> <chat>` folds a chat into a folder (dry-run unless `--yes`) and `tg
  chats --not-in-folder <folder>` finds chats sitting outside one, `tg read
  <name>` shows a thread, `tg search <text>` searches, `tg send <name> <text>`
  sends a message or a `--file` document (dry-run unless `--yes`), and `tg
  download <name>` saves attachments. Session and API credentials are stored
  chmod 600 in ~/.config/tg-cli. Use when the user wants to read, search, send,
  or download their personal Telegram messages and attachments."
---

# Telegram reader / sender CLI

Terminal access to your **own** Telegram account. It authenticates as your user
account over MTProto via [Telethon](https://docs.telethon.dev), so it can read
and send anything your account can — unlike a bot, which only sees chats it was
explicitly added to.

## How to invoke

Invoke it as **`tg`** — on `$PATH` via a symlink in `~/.local/bin` onto this
repo's `bin/tg`, so it always runs the current checkout: a `git pull`, or even
an uncommitted edit, takes effect immediately with nothing to reinstall.

```bash
tg chats
```

Examples in this doc are written that way. If `tg` is not on `$PATH`, run the
bundled launcher `bin/tg` resolved against this skill's own directory (PEP 723
— `uv` resolves deps inline on first run: `click` + `telethon`), or link it once:

```bash
ln -sfn <skill-dir>/bin/tg ~/.local/bin/tg
```

## Prerequisite: log in (one-time)

1. Get an **api_id** and **api_hash** from <https://my.telegram.org> → *API
   development tools*. These identify the client app, not your account, and are
   reused across logins.
2. Run `tg login`. It prompts for the api_id / api_hash (stored after the
   first time), then for your **phone number**, the **login code** Telegram
   sends you, and your **2FA password** if you have one set.

Credentials and the authenticated session are written `chmod 600` inside a
`chmod 700` `~/.config/tg-cli/` (override with `TG_CONFIG_DIR`, or inject creds
via `TG_API_ID` / `TG_API_HASH`).

## Security

The session file (`~/.config/tg-cli/session.session`) **is a credential** — it
grants full access to the account without the password. Keep it off synced
folders and out of git (the repo `.gitignore` blocks `*.session` and
`config.json`). If it ever leaks, revoke it instantly from the Telegram app:
**Settings → Devices → terminate session**. Enabling a 2FA password on the
account is strongly recommended.

## When to use

Trigger when the user wants to **read, search, or send their personal Telegram
messages** — "show my Telegram chat with X", "what did Y send me on Telegram",
"search my Telegram for Z", "message X on Telegram that …".

Do **not** use it on someone else's account. Sending is an outbound action:
confirm the exact recipient and text with the user before running `send --yes`.

## Commands

### `tg login [--api-id ID] [--api-hash HASH]`

Interactive one-time authentication (see above).

### `tg whoami [--json]`

Show the logged-in account (name, username, id).

### `tg chats [--limit N] [--not-in-folder NAME] [--json]`

List conversations, most recent first, each tagged `[dm]` / `[group]` /
`[channel]` with an unread count. `--not-in-folder NAME` restricts the listing to
chats **not** already in the named folder — the way a folder-scoped digest job
spots a newly-joined partner group sitting outside its curated folder (which a
folder-only sweep would otherwise miss).

```bash
tg chats --not-in-folder Zama --limit 60 --json   # recent chats outside the Zama folder
```

### `tg folders [--json]`

List chat folders (Telegram "chat folders" / dialog filters) and how many chats
each explicitly contains.

### `tg folder <name> [--since ISO] [--limit N] [--json]`

Read recent messages from **every chat in the folder** matching `<name>`,
windowed by `--since` (ISO date/datetime, UTC if no tz). This is the batch
building block for digest jobs: it enumerates the folder's chats, fetches each
chat's recent messages, and keeps those at/after the cutoff. In `--json` each
message carries an `epoch` (Unix seconds) so a caller can filter precisely
against its own cutoff.

```bash
tg folders                              # list folders + chat counts
tg folder Zama --since 2026-07-05 --json
```

### `tg folder-add <folder> <query> [--match N] [--yes] [--json]`

Add the chat matching `<query>` into the folder matching `<folder>`. This edits
your account's **folder layout only** — never any chat's messages — and
**defaults to a dry-run**; pass `--yes` to apply. Idempotent: a chat already in
the folder is left untouched (`already_in_folder: true`). Use it to fold a
newly-joined partner group into a curated folder so folder-scoped digests stop
missing it. Only plain folders are editable (not "All chats", not shared/invite
folders). Gate auto-adds to real partner **groups** (e.g. `X <> Zama`,
`Zama x Y`) — don't sweep in public channels or unrelated personal groups.

```bash
tg folder-add Zama "Zama x Ember"          # dry-run: shows the proposed add
tg folder-add Zama "Zama x Ember" --yes    # actually add it to the folder
```

### `tg read <query> [--limit N] [--match N] [--json]`

Show messages from the chat whose name best matches `<query>` (case-insensitive
substring). Ambiguous matches print a numbered list — pick one with `--match N`.

```bash
tg read alice              # most likely "Alice" chat
tg read "Dev Team" --limit 200
tg read alice --match 2    # 2nd match when ambiguous
```

### `tg search <text> [--chat QUERY] [--match N] [--limit N] [--json]`

Search messages containing `<text>`. With `--chat` it searches that one
conversation (single exact request); without it, a best-effort global search
across all chats.

### `tg send <query> [text] [--file PATH] [--match N] [--peer P] [--yes]`

Send to the chat matching `<query>`. With `--file` it sends that document and any
`text` becomes the caption. **Defaults to a dry-run** printing the resolved
recipient and payload; pass `--yes` to actually send. Target an exact recipient
with `--peer @username` / phone / id, or disambiguate with `--match`.

```bash
tg send alice "running late"                 # dry-run: shows recipient + text
tg send alice "running late" --yes           # actually sends
tg send alice "the deck" --file deck.pdf --yes   # send a document with caption
```

### `tg download <query> [--limit N] [--since ISO] [--docs-only] [--match N] [--out DIR] [--json]`

Scan the last `--limit` messages of the matched chat and save every media
attachment into `--out` (default `.`), using Telegram's own filename where
available. Narrow with `--since` (only messages at/after the cutoff) and
`--docs-only` (files like PDFs/decks, skipping photos and stickers).

```bash
tg download alice --limit 50 --out ./tg-media
tg download "Zama x Steakhouse" --since 2026-07-05 --docs-only --out ./tg-docs
```

## Notes

- **Reading is non-destructive** — only `send --yes` writes anything.
- **Timestamps** are converted from Telegram's UTC to local time.
- Non-text messages render as a `[MediaType]` / `[ActionType]` placeholder.
- Every read command supports `--json` for structured output.
