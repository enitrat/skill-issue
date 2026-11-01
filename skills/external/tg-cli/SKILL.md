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

Invoke it as **`tg`** — on `$PATH` via `claudine/scripts/link_clis.py`, which
links this repo's `bin/tg` into `~/.local/bin`, so it always runs the current
checkout: a `git pull`, or even an uncommitted edit, takes effect immediately
with nothing to reinstall.

```bash
tg chats
```

If `tg` is not on `$PATH`, run `<skill-dir>/bin/tg` (a symlink to `tg_cli.py`,
a PEP 723 script — `uv` resolves deps inline on first run: `click` +
`telethon`).

## Authentication

### Log in (one-time)

1. Get an **api_id** and **api_hash** from <https://my.telegram.org> → *API
   development tools*. These identify the client app, not your account, and are
   reused across logins.
2. Run `tg login`. It prompts for the api_id / api_hash (stored after the
   first time), then for your **phone number**, the **login code** Telegram
   sends you, and your **2FA password** if you have one set.

Without a terminal (Claude Desktop, Cowork), use `tg link` instead of step 2:
it returns at once and opens a local page with a QR code. On the phone,
Telegram → Settings → Devices → **Link Desktop Device**, scan it, and type the
2FA password on the page if asked; then `tg whoami` confirms. The page stays up
5 minutes. The api_id / api_hash come from `TG_API_ID` / `TG_API_HASH` (the
extension's settings) or the stored config.

Credentials and the authenticated session are written `chmod 600` inside a
`chmod 700` `~/.config/tg-cli/` (override with `TG_CONFIG_DIR`, or inject creds
via `TG_API_ID` / `TG_API_HASH`).

`tg whoami` proves the binding; `tg auth-status [--json]` reports where the
credentials come from (vault broker or local file) without secrets, and
`tg auth-sync` retries a pending vault sync (exit 3 while still pending).
`tg logout` drops the session.

### Security

The session file (`~/.config/tg-cli/session.session`) **is a credential** — it
grants full access to the account without the password. Keep it off synced
folders and out of git (the repo `.gitignore` blocks `*.session` and
`config.json`). If it ever leaks, revoke it instantly from the Telegram app:
**Settings → Devices → terminate session**. Enabling a 2FA password on the
account is strongly recommended.

## Output conventions

- Default: compact text, one line per message (`ts  sender: text`) or per chat.
- `--json` on every read command: structured rows; messages carry `id`, `ts`,
  `epoch` (Unix seconds), `sender`, `text` (and `transcript` with
  `--transcribe`). `tg folder --json` is a bare list of
  `{chat, messages: [...]}`.
- `tg listen` prints one JSON line per new message; its status line goes to
  stderr.
- stdout carries data only; warnings (e.g. a failed transcription) go to stderr.
- **Timestamps** are converted from Telegram's UTC to local time; filter on
  `epoch` against your own UTC cutoff.
- Non-text messages render as a `[MediaType]` / `[ActionType]` placeholder.
- **Senders.** `sender` is `me` for own messages, else the display name; a sender
  with no resolvable name is emitted as its numeric id. Write that literal id,
  never a name guessed from content or context.

## Commands

```bash
# Read
tg whoami [--json]                                    # logged-in account (name, username, id)
tg chats [--limit N] [--not-in-folder NAME] [--json]  # conversations, most recent first
tg folders [--json]                                   # chat folders + chat counts
tg folder <name> [--since ISO] [--limit N] [--json]   # batch-read every chat in a folder
tg read <query> [--limit N] [--since ISO] [--match N] [--transcribe] [--json]
tg search <text> [--chat QUERY] [--match N] [--limit N] [--json]
tg download <query> [--limit N] [--since ISO] [--docs-only] [--match N] [--out DIR] [--json]
tg listen <query> [--all] [--exec CMD] [--transcribe]  # stream new messages as JSON lines
# Write (dry-run unless --yes)
tg send <query> [text] [--file PATH] [--peer P] [--match N] [--reply-to ID] [--yes]
tg folder-add <folder> <query> [--match N] [--yes] [--json]
# Auth
tg login [--api-id ID] [--api-hash HASH]   # interactive, one-time
tg link                                    # QR code page, no terminal needed
tg logout
tg auth-status [--json]
tg auth-sync
```

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

A chat already in the folder can still appear in this listing (a stale or
unresolved peer entry, not a fold-in candidate): confirm against the actual
`tg folder <name>` output before adding it.

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

`--json` is a bare list of `{chat, messages: [{ts, epoch, sender, text}]}` (no
dict wrapper); filter on `epoch` against your own UTC cutoff. `--limit` caps
messages fetched per chat before the `--since` filter, so if a folder's newest
messages all cluster at the window start the fetch was truncated: re-pull with a
larger `--limit`. A folder chat count lower than a previous run's is a fetch
failure, not a smaller folder.

The call can hang on an otherwise healthy session. Wrap it in a timeout and
retry once before treating it as a failure. macOS ships no GNU `timeout`
binary, so use a subprocess timeout or background the call and poll:

```bash
tg folder Zama --since 2026-07-05 --json > out.json 2> err.log & pid=$!
sleep 45; kill -0 $pid 2>/dev/null && kill $pid   # finished on its own if out.json has content
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

### `tg read <query> [--limit N] [--since ISO] [--match N] [--json]`

Show messages from the chat whose name best matches `<query>` (case-insensitive
substring). Ambiguous matches print a numbered list — pick one with `--match N`.
Without `--since` it shows the last `--limit` messages (default 50); with
`--since` (ISO date/datetime, UTC if no tz) it shows the first `--limit`
messages at/after the cutoff, oldest first, so a busy window is read from its
start. Raise `--limit` if the output stops short of now.

```bash
tg read alice              # most likely "Alice" chat
tg read "Dev Team" --limit 200
tg read alice --match 2    # 2nd match when ambiguous
tg read "Founding Apes" --since 2026-09-28T22:00:00 --limit 200   # a day's window
tg read alice --limit 20 --transcribe --json   # latest messages with local audio transcripts
```

For `--transcribe`, install `transcribe-cli` so `transcribe` is on PATH on the
machine running `tg`. Each machine needs its own `tg login`; authenticated
sessions must not be copied between machines. Transcripts can misrecognize
names and technical terms. See the transcription options and cache behavior
under Notes.

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

`download` can hang indefinitely on a link-only chat (one with no attachments in
the window). Wrap each call in a ~30s timeout (see the `folder` note for the
macOS pattern) and treat a hang or an empty result as "no docs", not an error.
Read a downloaded deck in full, not just the intro: a partner's load-bearing
constraints usually sit in a later product-spec page.

## Recipes

```bash
# What happened in a folder since yesterday (digest)
tg folder Work --since 2026-07-05 --json > out.json

# A newly-joined group missing from a curated folder: find it, then fold it in
tg chats --not-in-folder Work --limit 60 --json
tg folder-add Work "Dev Team"          # dry-run
tg folder-add Work "Dev Team" --yes

# What did alice send me this week, with voice notes transcribed
tg read alice --since 2026-10-20 --transcribe --json

# Every PDF/deck shared in a chat
tg download "Dev Team" --since 2026-07-05 --docs-only --out ./tg-docs

# Reply to a specific message
tg read alice --limit 5 --json        # take the message id
tg send alice "agreed" --reply-to 12345 --yes
```

## Gotchas

- `tg folder` can hang on an otherwise healthy session: wrap it in a timeout and
  retry once (macOS has no GNU `timeout`; background the call and kill it).
- `tg download` can hang indefinitely on a link-only chat: wrap each call in a
  ~30s timeout and treat a hang or empty result as "no docs".
- `--limit` caps messages fetched per chat before `--since` filters: if the
  newest messages cluster at the window start, re-pull with a larger `--limit`.
  A folder chat count lower than a previous run's is a fetch failure, not a
  smaller folder.
- `chats --not-in-folder` can list a chat already in the folder (stale peer
  entry): confirm against `tg folder <name>` before `folder-add`.
- Global `search` (without `--chat`) is best-effort; `--chat` is one exact
  request.
- **No per-message permalinks exist.** Cite a message by chat name + timestamp
  (+ filename for an attachment).
- Sending is outbound: confirm the exact recipient and text with the user before
  `send --yes`. Each machine needs its own `tg login`; never copy a session.

## When to use

Trigger when the user wants to **read, search, or send their personal Telegram
messages** — "show my Telegram chat with X", "what did Y send me on Telegram",
"search my Telegram for Z", "message X on Telegram that …".

Do **not** use it on someone else's account. Sending is an outbound action:
confirm the exact recipient and text with the user before running `send --yes`.

## Notes

- **Optional transcription.** `read`, `folder`, and `listen` accept
  `--transcribe/--no-transcribe` and `--transcribe-backend auto|whisper|parakeet`.
  They download voice notes and audio files and call `transcribe file` locally;
  `transcribe` must be installed on PATH. Off by default; `TG_TRANSCRIBE=1`
  enables it, `TG_TRANSCRIBE_BACKEND` selects the backend. JSON preserves `text`
  and adds `transcript` to audio rows (null on failure); human output includes
  the transcript. Errors warn on stderr without dropping the message.
  Audio downloads are temporary; transcripts persist in
  `~/.cache/tg-cli/transcripts` (`TG_CACHE_DIR` overrides the cache root), keyed
  by chat, message, and requested backend, with directory/file modes 0700/0600.
  Delete entries to retranscribe. Example: `tg read alice --transcribe --json`.

- **Reading is non-destructive** — only `send --yes` and `folder-add --yes` write anything.

## Tests

```bash
for t in tests/test_*.py; do uv run --script "$t"; done
```

## Project layout

```
tg-cli/
  SKILL.md        # this file
  README.md
  tg_cli.py       # the CLI (PEP 723 script, Telethon client)
  bin/tg          # symlink -> ../tg_cli.py — invoke this
  tests/          # offline tests (PEP 723 scripts)
```
