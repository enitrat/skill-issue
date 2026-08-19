# tg-cli

Read and send your **own** Telegram chats from the terminal. It logs in as your
Telegram user account over MTProto (via [Telethon](https://docs.telethon.dev)),
so it sees everything your account sees — the Telegram counterpart to the
WhatsApp / iMessage / Slack personal CLIs.

Not a bot: a bot can only read chats it is explicitly added to and never your
personal DMs, so a user-account client is the only way to read your own history.

## Install / run

`tg` is a single self-contained script run via
[uv](https://docs.astral.sh/uv/) with inline PEP 723 dependencies — no virtualenv
setup. The only dependencies are `click` and `telethon`, both version-pinned, so
the entire codebase you run is this one readable file plus those two libraries.

```bash
# one-time login (prompts for api_id/api_hash, then phone + code + 2FA)
tg login

tg chats                       # list conversations
tg folders                     # list chat folders
tg folder Zama --since 2026-07-05 --json   # batch-read a whole folder, windowed
tg read alice                  # read a thread
tg search "invoice"            # global search
tg send alice "on my way"      # dry-run
tg send alice "on my way" --yes
tg send alice "the deck" --file deck.pdf --yes   # send a document
tg download alice --out ./tg-media               # save attachments
```

## Credentials

1. Create an app at <https://my.telegram.org> → *API development tools* to get an
   `api_id` and `api_hash` (these identify the client, not the account).
2. `tg login` stores them and the authenticated session `chmod 600` under
   `~/.config/tg-cli/` (a `chmod 700` dir). Override the location with
   `TG_CONFIG_DIR`, or inject creds via `TG_API_ID` / `TG_API_HASH`.

## Security

The session file is a full credential for the account. It never leaves
`~/.config/tg-cli/`, and the repo `.gitignore` blocks `*.session` and
`config.json` from ever being committed. Revoke a compromised session from the
Telegram app: **Settings → Devices → terminate**. Enable a 2FA password on the
account.

See [SKILL.md](SKILL.md) for the agent-facing command reference.
