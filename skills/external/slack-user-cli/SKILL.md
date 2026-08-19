---
name: slack-user-cli
description:
  "Read and write Slack channels, DMs, threads, and search from the terminal
  using slack_user_cli. Use when the user asks to interact with Slack
  workspaces, read messages, send messages, or search Slack. Every command
  supports `--json`; every read defaults to raw IDs (users, channels) and
  accepts `--names` to resolve to display names. For programmatic consumers
  (scripts, smithers workflows, pipelines) prefer `--json` to get structured
  output rather than parsing rendered text."
allowed-tools:
  - Bash
  - Read
---

# Slack User CLI

Terminal access to Slack using browser session credentials (`xoxc-` token + `d`
cookie). Located at `~/.claude/skills/slack-user-cli/slack_user_cli.py`.

## How to invoke

Invoke it as **`slack-user`** — on `$PATH` via a symlink in `~/.local/bin` onto this
repo's `bin/slack-user`, so it always runs the current checkout: a `git pull`, or even
an uncommitted edit, takes effect immediately with nothing to reinstall.

```bash
slack-user channels
```

Examples in this doc are written that way. If `slack-user` is not on `$PATH`, run the
bundled launcher `bin/slack-user` resolved against this skill's own directory (PEP 723
— `uv` resolves deps inline on first run), or link it once:

```bash
ln -sfn <skill-dir>/bin/slack-user ~/.local/bin/slack-user
```

## Authentication

Must be logged in before using any command. Credentials are stored in
`~/.config/slack-user-cli/config.json`.

```bash
# Auto-extract from Slack desktop app (close Slack first)
slack_user_cli login --auto

# Import all workspaces from browser — copies to clipboard, reads via pbpaste
slack_user_cli login --browser

# Add a single workspace manually
slack_user_cli login --manual
```

## Global Options

| Option                            | Description                                 |
| --------------------------------- | ------------------------------------------- |
| `-w <name>`, `--workspace <name>` | Use a specific workspace instead of default |
| `--debug`                         | Enable debug logging                        |

## Output Conventions

- **IDs by default.** Every read command emits raw Slack IDs (`U…` users,
  `C…`/`D…`/`G…` channels) so output is stable for scripts. Do **not** add
  `--names` unless the user explicitly asks for human-readable names — raw IDs
  are the right answer for chaining further commands.
- **`--names` is opt-in.** Only when the user specifically wants display names
  (e.g. "show me who said what", "summarize this thread"), pass `--names` to
  resolve user/channel IDs and rewrite `<@UXXX>` mentions.
- **CRITICAL — never guess a name; resolve it with a command.** This applies to
  **both** user names and **channel** names. Every ID→name mapping must come from
  an actual resolver command, **never** from inference (message content, username
  stem, DM/MPIM/channel title, channel topic, or surrounding context) — that is
  silent misattribution and a correctness failure. The proper commands:
  - **Any ID (fastest):** `slack_user_cli resolve <id> [<id> …]` resolves both
    user (`U…`) and channel (`C…`/`G…`) IDs in one call, backed by the permanent
    id→name store (one API hit per new ID, none thereafter). This is the default
    way to name an ID.
  - **User ID → name:** also via `--names` on `read`/`thread`/`url`/`dm`
    (resolves authors and rewrites `<@UXXX>` mentions), or `users --json`.
  - **Channel ID → name:** `resolve` uses a single `conversations_info` call.
    (`channels --all --json` also works but lists every channel and is
    rate-limit-prone; `read <id> --json` does **not** return a name — it only
    echoes the ID you passed.)
  - If a name will not resolve (not in the workspace, rate-limited, etc.), keep
    the raw `U…`/`C…` ID and **say so** — do not approximate or invent one, and do
    not infer it from the topic or the conversation. `conversations.list` /
    `users.list` are rate-limited; on `ratelimited`, wait and retry rather than
    falling back to a guess.
- **`--json` everywhere.** Every command supports `--json` for structured
  output. Use it whenever a programmatic consumer would otherwise parse rendered
  text. `--json` and `--names` are independent.

## Commands Reference

### Workspace Management

The user's first successful `login` automatically becomes the default.
If that login imports several workspaces at once (`--browser`/`--auto`) and
it's running on a real terminal, the user is prompted to pick which one;
non-interactively (e.g. invoked by an agent without a TTY), the first one
wins silently. Logging in to additional workspaces later never changes an
existing default. Every command uses the default unless `-w <name>` is
passed (see [Cross-workspace Usage](#cross-workspace-usage)) or it's changed
permanently with `default`.

```bash
# Show who the active workspace's credentials belong to (own user ID, team ID)
slack_user_cli whoami
slack_user_cli whoami --json   # {"workspace": "…", "user": "…", "user_id": "U…", "team": "…", "team_id": "T…", "url": "https://….slack.com/"}

# List all saved workspaces (marks which one is default)
slack_user_cli workspaces

# Permanently change the default workspace
slack_user_cli default "Workspace Name"

# Force-refresh the channel and user cache
slack_user_cli refresh
```

### Reading

```bash
# List joined channels (output: channel IDs)
slack_user_cli channels
slack_user_cli channels --all
slack_user_cli channels --type "public_channel,private_channel,mpim,im"
slack_user_cli channels --json   # {channels: [{id, name, type, num_members, topic, is_member}, ...]}

# Read recent messages from a channel (by name or ID; output: user IDs)
slack_user_cli read <channel_name_or_id> --limit 20

# Emit structured JSON instead of human-readable text (for programmatic
# consumers — smithers workflows, scripts, pipelines). Shape:
#   {"channel": "...", "messages": [{"ts", "raw_ts", "user", "text", "thread_ts"?, "threadCount"?, "files"?, "replies"?}, ...]}
# Every message carries `raw_ts` (full microsecond ts) — `ts` is minute-precision
# for humans, but `raw_ts` is what you pass to the `permalink`/`click`/`thread`
# commands. Use --json whenever you'd otherwise parse the pretty output back into
# fields — the parse step is the #1 source of bugs and timeouts.
# Messages with attachments carry a `files` array: each entry has
# {id, name, filetype, mimetype, size, url_private, url_private_download,
# permalink}. In text output, attachments show as a 📎 line under the message.
# To actually read a file's contents, fetch it with the `download` command
# (the message text alone never includes attachment contents).
# A message that QUOTES/SHARES another message carries the original under a
# `shared` array: [{url, author, channel, ts, text, files:[...]}]. Its `files`
# are the quoted message's attachments — so a forwarded message never hides its
# attachments (text output shows them under a "↪ quoted <author>" line). Plain
# pasted message permalinks appear in a `links` array ([{url, channel, ts}]).
slack_user_cli read <channel_name_or_id> --limit 20 --json

# Add --expand-thread to inline every thread's replies under `replies: [...]`
# on the parent. Only meaningful with --json. Most decisions live in replies
# rather than parent posts, so expansion is almost always what you want for
# analysis; skip it only when you need cheap channel-level metadata.
slack_user_cli read <channel_name_or_id> --limit 20 --json --expand-thread

# Time-bounded fetch: only messages at/after an ISO date or datetime (UTC if
# no tz). Sets the history `oldest` bound; pair with a larger --limit to pull a
# whole window. To catch threads whose parent predates the window but that got
# fresh replies inside it, set --since a couple of days earlier, --expand-thread,
# and filter on each message's raw_ts >= your real cutoff.
slack_user_cli read <channel_name_or_id> --since 2026-05-29 --limit 200 --json --expand-thread
slack_user_cli read <channel_name_or_id> --since 2026-05-29T10:07:00 --limit 200 --json

# Read thread replies (use --dm when CHANNEL is a user name, not a channel)
slack_user_cli thread <channel_name_or_id> <message_ts>
slack_user_cli thread <channel_name_or_id> <message_ts> --json
slack_user_cli thread --dm <user_name_or_id> <message_ts>

# Read a thread directly from a Slack permalink URL
slack_user_cli url "https://workspace.slack.com/archives/C.../p..."
slack_user_cli url "https://workspace.slack.com/archives/C.../p..." --json

# Canonical permalink(s) via chat.getPermalink — pass the channel + one or more
# raw_ts. Unlike a hand-built /p<ts> URL, these are thread-aware (carry
# thread_ts/cid) so they navigate correctly to threaded replies, not just roots.
# ALWAYS use this to cite a message rather than constructing /p<ts> by hand.
slack_user_cli permalink <channel_name_or_id> <raw_ts> [<raw_ts> ...]
slack_user_cli permalink <channel_name_or_id> <raw_ts> --json   # {channel, permalinks: {ts: url}}

# List workspace members (output: user IDs)
slack_user_cli users
slack_user_cli users --json   # {users: [{id, name, display_name, real_name, status_emoji, status_text}, ...]}

# List channels a user is a member of (by username or user ID; output: channel IDs)
slack_user_cli user-channels <user_name_or_id>
slack_user_cli user-channels <user_name_or_id> --json
slack_user_cli user-channels <user_name_or_id> --type "public_channel,private_channel,mpim"

# Resolve one or more IDs to names — the RIGHT way to name a U…/C…/G… ID instead
# of guessing it. Backed by the permanent id→name store: one API call per ID the
# first time, none thereafter. Mixes users and channels freely.
slack_user_cli resolve C01234ABCDE U05678FGHIJ
slack_user_cli resolve C01234ABCDE U05678FGHIJ --json   # {"resolved": {"C01234ABCDE": "engineering", "U05678FGHIJ": "alex"}}
```

### Writing

**CRITICAL: When drafting messages for the user, read and follow the tone guide
in `~/.claude/skills/slack-user-cli/TONE.md`.** Match the user's natural voice:
casual, humble, concrete, no marketing-speak. If file does not exist, create it.

**CRITICAL: Before sending any message to a main channel (i.e. a `send`
command), you MUST use `AskUserQuestion` to get explicit approval.** Posting to
a main channel is visible to everyone and cannot be undone. Always confirm with
the user first.

**Permalink timestamp parsing:** When replying to a thread from a Slack
permalink URL (e.g. `https://...slack.com/archives/C.../p1012345678907689`),
extract the thread_ts by inserting a dot before the last 6 digits of the `p`
value: `p1012345678907689` → `1012345678.907689`. Double-check this conversion
before sending.

```bash
# Send a message to a channel (use --thread to reply in a thread)
slack_user_cli send <channel_name_or_id> "message text"
slack_user_cli send <channel_name_or_id> "reply text" --thread <message_ts>

# DM a user (by display name or user ID; use --thread for thread replies)
slack_user_cli dm <user_name_or_id> "message text"
slack_user_cli dm <user_name_or_id> "reply text" --thread <message_ts>
slack_user_cli dm <user_name_or_id> "message" --json

# Read DM history (omit message; output: user IDs). Same --json shape as `read`.
slack_user_cli dm <user_name_or_id>
slack_user_cli dm <user_name_or_id> --json
```

### Clicking Block-Kit Buttons

`read --json` surfaces interactive elements alongside the text. When a bot
message has a block-kit `actions` block, the JSON entry gains an `actions`
field. The `raw_ts` field (the unformatted ts you pass to `click`) is present
on **every** message, not just block-kit ones:

```json
{
  "ts": "2026-05-04 09:30",
  "raw_ts": "1777887012.881539",
  "user": "bot",
  "text": "Which one is legit?",
  "bot_id": "B095...",
  "app_id": "A01G...",
  "actions": [
    {"type": "button", "block_id": "...", "action_id": "...", "text": "The first one!", "value": "..."},
    {"type": "button", "block_id": "...", "action_id": "...", "text": "The second one!", "value": "..."}
  ]
}
```

`click` dispatches a button or radio choice via Slack's internal
`blocks.actions` endpoint (the same call the web client makes when you click
a button). It's how you complete training bots like Riot/Albert from the CLI.

**Same approval rules as Writing above** — clicking a button on a message in a
shared channel produces side effects visible to everyone. DMs to bots are
fine without confirmation.

```bash
# Click by visible button label (most ergonomic)
slack_user_cli click <channel> <raw_ts> --option "The first one!"

# Pick a radio option by its label
slack_user_cli click <channel> <raw_ts> --option "A few seconds"

# Pick by 1-based index across all action elements on the message
slack_user_cli click <channel> <raw_ts> --index 2

# Pick by exact action_id (precise; needed if multiple buttons share text)
slack_user_cli click <channel> <raw_ts> --action-id "WyIw..."

# Pick by exact value (for buttons or radio options)
slack_user_cli click <channel> <raw_ts> --value "WyJiY..."

# JSON output with the raw blocks.actions response
slack_user_cli click <channel> <raw_ts> --option "OK" --json
```

Supported element types: `button`, `radio_buttons`, `static_select`. Other
types (datepickers, multi-selects, modals) raise an error explaining how to
extend `_build_action_payload`.

### File Uploads

**Same approval rules as Writing above** — uploading to a main channel (without
`--thread`) requires `AskUserQuestion` confirmation first.

```bash
# Upload a file to a channel
slack_user_cli upload <channel_name_or_id> /path/to/file.png

# Upload with a message and title
slack_user_cli upload <channel_name_or_id> /path/to/file.png --message "Here's the report" --title "Q1 Report"

# Upload in a thread
slack_user_cli upload <channel_name_or_id> /path/to/file.png --thread <message_ts>

# Upload a file via DM
slack_user_cli dm-upload <user_name_or_id> /path/to/file.png

# DM upload with message and in a thread
slack_user_cli dm-upload <user_name_or_id> /path/to/file.png --message "See attached" --thread <message_ts>
```

### Downloading File Attachments

Messages often carry uploaded files (PDFs, images, docs). The message **text**
never contains the file contents, so to read an attachment you must download it.
`read`/`url`/`thread --json` expose a `files` array (and text output shows a 📎
line) so you can spot attachments; `download` fetches the bytes locally.

```bash
# Download every attachment on a message — pass a permalink…
slack_user_cli download "https://workspace.slack.com/archives/C.../p..." -o ./out

# …or a channel + message raw_ts
slack_user_cli download <channel_name_or_id> <raw_ts> -o ./out

# …or a single file by its ID (starts with F)
slack_user_cli download F0B883G50V6 -o ./out

# Just list the attachments (name, type, size, id) without downloading
slack_user_cli download <channel_name_or_id> <raw_ts> --list
slack_user_cli download <channel_name_or_id> <raw_ts> --list --json

# JSON: {"files": [...], "downloaded": ["./out/quote.pdf", ...]}
slack_user_cli download <channel_name_or_id> <raw_ts> -o ./out --json
```

Default output directory is `./slack-downloads`. Downloaded files can then be
read with normal file tools (e.g. a PDF reader). Reading another workspace's
files is gated by your own access — `download` uses the same session auth.

`download` also fetches attachments from a **quoted/shared** message: if you
point it at a message that forwards another one (the original shows up under
`shared` in JSON / a "↪ quoted" line in text), it pulls the original's files
too — so you don't have to chase the source message manually.

### Important: DM User Name Resolution

When using `dm`, the USER argument must match the Slack **username** (e.g.
`first.last`), not the display name with spaces (e.g. `First Last`). Use
`search "from:<username>"` to discover the correct username format.

### Search

```bash
# Search messages (output: raw user/channel IDs in user/channel fields)
slack_user_cli search "query" --count 20 --page 1
slack_user_cli search "query" --json
```

**Pull thread context via global search.** When asked to read or explain a
specific thread, don't stop at that thread — a message is often a terse callback
to a fuller discussion elsewhere. Pull 2–3 distinctive keywords/phrases from the
thread and run a **global** (workspace-wide, not channel-scoped) `search` on
them, then follow any Notion/GitHub/doc links found before answering. This
routinely surfaces the prior design, decision, or doc that gives the current
message its real meaning.

```bash
# After fetching the target thread, search the whole workspace for its key terms
slack_user_cli search "<keyword from thread>" --count 15 --json
```

### Canvases

```bash
# Read a canvas by URL (outputs plain text by default)
slack_user_cli canvas "https://workspace.slack.com/docs/TEAM_ID/FILE_ID"

# Read a canvas by file ID
slack_user_cli canvas DEADBEEFUUV

# Get raw HTML output
slack_user_cli canvas "https://workspace.slack.com/docs/TEAM_ID/FILE_ID" --html

# JSON: {file_id, title, text} (or html with --html)
slack_user_cli canvas DEADBEEFUUV --json

# Append markdown to a canvas (default: insert_at_end)
slack_user_cli canvas-edit DEADBEEFUUV "## New Section\nSome text"

# Replace entire canvas content
slack_user_cli canvas-edit DEADBEEFUUV "## Fresh Start" --operation replace

# Prepend content
slack_user_cli canvas-edit DEADBEEFUUV "## Header" --operation insert_at_start

# Pipe content from a file or heredoc
cat summary.md | slack_user_cli canvas-edit DEADBEEFUUV --operation replace
```

### Cross-workspace Usage

```bash
# Read from a specific workspace
slack_user_cli -w "Other Workspace" channels
slack_user_cli -w "Other Workspace" read general --limit 5
```

## Cache

Channel and user data is cached to disk for fast resolution:

- **Location**: `~/.config/slack-user-cli/cache/<workspace>/`
- **Files**:
  - `channels.json` (name→id map) and `users.json` (id→display, name→id,
    display→id maps) — the **name↔id lookup** caches, **TTL 1 hour**
    (auto-expire and rebuild, since names/membership can change).
  - `id_names.json` (`{users: {id: name}, channels: {id: name}}`) — the
    **permanent id→name store**, **NO TTL**. Slack IDs are immutable, so once an
    ID has been resolved to a name — by any prior invocation — it is reused
    forever with no API call. Full builds (`refresh`) seed it; individual
    `resolve`/`--names` lookups append to it.
- **Refresh**: run `slack_user_cli refresh` to force-rebuild the TTL caches and
  re-seed the permanent store (overwrites entries — the escape hatch if a
  channel or display name actually changed).
- **Behavior**: `resolve_user()` checks in-memory → permanent store → disk TTL
  cache → a single `users_info` call, persisting anything it learns to
  `id_names.json`. `resolve_channel_name()` (channel **id→name**) checks the
  permanent store then a single `conversations_info` call — it never lists all
  channels. `resolve_channel()` (name→id) auto-builds the TTL cache on first use.

Run `refresh` after joining new channels or when a name lookup returns an ID and
you suspect the underlying name changed.

## Key Details

- **Auth model**: `xoxc-` token (per-workspace) + `d` cookie (shared across
  workspaces), extracted from browser or Slack desktop app
- **Config location**: `~/.config/slack-user-cli/config.json`
- **Cache location**: `~/.config/slack-user-cli/cache/<workspace>/`
- **Multi-workspace**: stores all workspaces; use `-w` to switch or `default` to
  set the default
- **Channel resolution**: accepts channel names (without `#`) or IDs (starting
  with C/D/G); uses disk cache for fast lookup
- **User resolution**: accepts display names, usernames, or user IDs (starting
  with U); uses disk cache + single API fallback
- **Pagination**: handled automatically for channels, users, messages, and
  threads
- **Search**: uses page-based pagination (`--page`, `--count`)
- **Output**: formatted with Rich tables and colored text
- **Timestamps**: message timestamps (`ts`) are displayed as `YYYY-MM-DD HH:MM`
  UTC

## Channel Summary Workflow

When the user asks to summarize a Slack channel (e.g., "summarize #general since
Feb 27"), follow this procedure:

### 1. Resolve channel ID and start date

- If the user gives a channel name, resolve the ID:
  ```bash
  slack_user_cli channels --all 2>&1 | grep -i "<channel_name>"
  ```
- If the channel name isn't found (e.g., cross-workspace channel), ask the user
  for a sample message link from that channel to extract the channel ID (`C...`
  from the URL).
- If no start date is provided, **ask the user** for one before proceeding.

### 2. Read channel messages from the start date

```bash
# --since bounds the fetch server-side; --expand-thread inlines replies, and
# --json gives you each message's raw_ts for citation.
slack_user_cli read <channel_id> --since <start_date> --limit 200 --json --expand-thread
```

- Each message carries `raw_ts`; keep it for permalinks and for filtering on the
  exact cutoff.
- Threads arrive inline under `replies` (with `--expand-thread`) — no need to
  re-fetch each one. To catch threads whose parent predates the window but got
  fresh replies inside it, set `--since` a day or two earlier and filter replies
  on `raw_ts >= cutoff`.

### 3. Cite each message with a real permalink

Use the `permalink` command with the message's `raw_ts` — **do not hand-build
`/p<ts>` URLs**. Hand-built URLs only resolve for root messages; threaded
replies need the `thread_ts`/`cid` query params that `chat.getPermalink`
(behind `permalink`) returns:

```bash
slack_user_cli permalink <channel_id> <raw_ts> [<raw_ts> ...] --json
```

If you only have a permalink (not a raw_ts) and want the thread, the `url`
command reads it directly:

```bash
slack_user_cli url "https://<workspace>.slack.com/archives/<channel_id>/p<ts>"
```

**If `url` fails** with `thread_not_found`, fall back to `search` with targeted
keywords to retrieve thread replies:

```bash
slack_user_cli search "<topic keywords> in:<channel_name>" --count 15
```

### 4. Summarize each thread

For each thread, produce a structured summary:

- **Topic**: One-line description
- **Decisions taken**: What was agreed upon
- **Pending / Open questions**: Unresolved items
- **Next steps / Action items**: Who does what
- **Codebase relevance**: How it relates to the current project (backend,
  frontend, SDK, infrastructure, etc.) — only include if applicable

### 5. Cross-cutting summary

After all threads, add a cross-cutting table of **technical issues** that span
multiple threads, with columns: Issue | Impact | Status.

### Tips

- The `read` command returns messages newest-first by default. Increase
  `--limit` if the start date is far back.
- Search is more reliable than `read` for finding specific messages and their
  thread replies. Use `in:<channel_name>` to scope searches.
- Watch for Slack API rate limits. If you hit `ratelimited`, wait a few seconds
  and retry.
- For large channels, process threads in batches of 3-5 to avoid rate limits.

## Troubleshooting

- **"Not logged in"**: run `slack_user_cli login --browser` or `--manual`
- **"Workspace not found"**: check available names with
  `slack_user_cli workspaces`
- **Token expired**: tokens expire on Slack logout; re-run `login`.
  `slack_user_cli whoami` tells you whether the stored credentials still work —
  it hits the API, so it fails exactly when they've expired
- **Too many channels**: `channels` shows only joined by default; this is
  correct
- **macOS Keychain prompt**: expected when using `--auto` (cookie decryption)
- **User shows as ID instead of name**: run `slack_user_cli refresh` to rebuild
  the user cache
- **Channel not found after joining**: run `slack_user_cli refresh` to rebuild
  the channel cache
