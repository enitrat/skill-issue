#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "click==8.3.3",
#     "qrcode==8.2",
#     "telethon==1.44.0",
# ]
#
# [tool.uv]
# exclude-newer = "2026-10-27T00:00:00Z"
# ///
"""Read and send your own Telegram chats from the terminal via your user account.

This is the Telegram counterpart to the WhatsApp / iMessage / Slack personal
CLIs: list conversations, read a thread, search, send. It logs in as **your
Telegram user account** over MTProto (Telethon), so it sees exactly what your
account sees — not a bot, which could only read chats it was explicitly added to.

Two facts drive the design and the security posture:

* **The session file is a credential.** After `login`, Telethon stores an
  authenticated session at `~/.config/tg-cli/session.session`. Anyone with that
  file (or your `api_id`/`api_hash`) can act as your account, so both are written
  `chmod 600` inside a `chmod 700` config dir, and kept out of the repo. Revoke a
  leaked session anytime from the Telegram app: Settings → Devices → terminate.
* **api_id / api_hash are per-developer, not per-account.** They come from
  my.telegram.org (My Applications) and identify the client app, not you. They
  are read from `~/.config/tg-cli/config.json` or the `TG_API_ID` / `TG_API_HASH`
  environment variables; `login` prompts for them once and stores them.

`link` is the login for callers without a terminal (an MCP client such as
Claude Desktop): it starts a background helper that serves a local page with a
QR code to scan from the Telegram app, plus a field for the 2FA password.

Reading is non-destructive. Only `send --yes` writes anything (an outgoing
message) — an outbound action the calling agent must confirm with the user first.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

import click
from types import SimpleNamespace
from telethon.sync import TelegramClient
from telethon import utils
from telethon.tl import functions, types

logging.basicConfig(
    level=logging.WARNING, format="%(levelname)s: %(message)s", stream=sys.stderr
)
# Telethon logs connection churn at INFO; keep the CLI's stderr clean.
logging.getLogger("telethon").setLevel(logging.ERROR)
log = logging.getLogger("tg")

# Config dir is overridable so tests (and throwaway logins) never touch the real
# session. The session basename is passed to Telethon, which appends `.session`.
CONFIG_DIR = Path(os.environ.get("TG_CONFIG_DIR", Path.home() / ".config" / "tg-cli"))
CONFIG_FILE = CONFIG_DIR / "config.json"
# TG_SESSION names an alternate session file (e.g. "listener"), so a resident `tg listen`
# and the one-shot commands each own a Telethon session: two clients cannot share one.
SESSION_BASE = CONFIG_DIR / os.environ.get("TG_SESSION", "session")
# Transcripts are private message content, so the cache dir is 0700 like the config dir.
TRANSCRIPT_CACHE = Path(os.environ.get("TG_CACHE_DIR", Path.home() / ".cache" / "tg-cli")) / "transcripts"


def _auth_broker(action, payload=None):
    """Keep credential bodies on pipes and suppress provider errors containing secrets."""
    import subprocess
    import json
    try:
        result = subprocess.run(
            ["claudine-secret", "auth", action, "telegram"],
            input=json.dumps(payload) if payload is not None else None,
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode not in (0, 3):
            return None
        value = json.loads(result.stdout)
        if not isinstance(value, dict):
            return None
        if action == "load" and result.returncode:
            return None
        return value
    except (OSError, subprocess.TimeoutExpired, ValueError):
        return None


def _secure_dir() -> None:
    """Ensure the config dir exists and is private (0700)."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_DIR.chmod(stat.S_IRWXU)  # rwx for owner only


def _lock_down(path: Path) -> None:
    """Restrict a credential file to owner read/write (0600)."""
    if path.exists():
        path.chmod(stat.S_IRUSR | stat.S_IWUSR)


def _load_config():
    """API credentials may travel between hosts; authenticated sessions never do."""
    if CONFIG_FILE.with_suffix(".auth-pending").exists():
        return json.loads(CONFIG_FILE.read_text()) if CONFIG_FILE.exists() else {}
    return _auth_broker("load") or (json.loads(CONFIG_FILE.read_text()) if CONFIG_FILE.exists() else {})


def _load_credentials() -> tuple[int, str]:
    """Return (api_id, api_hash) from env or the stored config, else fail cleanly.

    Environment wins over the file so a caller can inject creds without writing
    them to disk. Missing creds are a login-time concern, so the message points
    at `tg login` rather than dumping setup steps on every command.
    """
    env_id, env_hash = os.environ.get("TG_API_ID"), os.environ.get("TG_API_HASH")
    if env_id and env_hash:
        return int(env_id), env_hash
    cfg = _load_config()
    if cfg:
        return int(cfg["api_id"]), cfg["api_hash"]
    raise click.ClickException(
        "No API credentials found. Get an api_id / api_hash from https://my.telegram.org "
        "(API development tools), then enter them in Claude Desktop → Settings → Extensions → "
        "Telegram, or run `tg login` in a terminal."
    )


@contextmanager
def _client():
    """Yield a connected, authorized client; raise if not logged in.

    Kept separate from `login` because every other command must fail fast with a
    clear instruction rather than dropping into an interactive auth prompt.
    """
    api_id, api_hash = _load_credentials()
    # Telethon opens (and may create) the session SQLite file eagerly, so the
    # config dir must exist even before a successful login.
    _secure_dir()
    client = TelegramClient(str(SESSION_BASE), api_id, api_hash)
    client.connect()
    try:
        if not client.is_user_authorized():
            raise click.ClickException("Not logged in. Run `tg link` (QR code, no terminal needed) or `tg login`.")
        yield client
    finally:
        client.disconnect()


def _kind(dialog) -> str:
    if dialog.is_user:
        return "dm"
    if dialog.is_channel and not dialog.is_group:
        return "channel"
    return "group"


SELF_ALIASES = {"me", "saved", "saved messages", "moi", "messages enregistrés"}


def _resolve_dialog(client, query: str, match: int):
    """Return the single dialog best matching QUERY, or exit with a picker.

    Matching is a case-insensitive substring test over the dialog name — the same
    fuzzy behaviour as the iMessage/WhatsApp CLIs. Ambiguity is surfaced (numbered
    list on stderr) rather than guessed, so an agent never silently targets the
    wrong chat; `--match N` disambiguates.
    """
    needle = query.lower()
    if needle in SELF_ALIASES:
        # "Saved Messages" is not a dialog until it holds messages, and Telethon
        # names it after the user; the aliases make it addressable either way.
        me = client.get_me()
        return SimpleNamespace(entity=me, name="Saved Messages", is_user=True, is_group=False, is_channel=False)
    candidates = [d for d in client.get_dialogs() if needle in (d.name or "").lower()]
    if not candidates:
        raise click.ClickException(f"No conversation matches {query!r}.")
    if len(candidates) > 1 and not match:
        click.echo(f"Multiple matches for {query!r} — pick with --match N:", err=True)
        for i, d in enumerate(candidates[:20], 1):
            click.echo(f"  {i}. {d.name}  [{_kind(d)}]", err=True)
        raise SystemExit(1)
    return candidates[match - 1 if match else 0]


def _message_dict(m) -> dict:
    """One message as the CLI's JSON row; ids and reply links let a script follow a thread."""
    media = None
    if m.voice or m.audio:
        media = {"kind": "audio", "mimetype": getattr(getattr(m, "document", None), "mime_type", None), "voice": bool(m.voice)}
    elif m.photo:
        media = {"kind": "image"}
    elif m.document:
        media = {"kind": "document", "mimetype": getattr(m.document, "mime_type", None), "file_name": getattr(m.file, "name", None) if m.file else None}
    return {
        "id": m.id,
        "ts": _local(m.date),
        "epoch": int(m.date.timestamp()) if m.date else None,
        "sender": "me" if m.out else utils.get_display_name(m.sender) or str(m.sender_id),
        "from_me": bool(m.out),
        "text": _msg_text(m),
        # The message this one replies to (Telegram's reply bubble), None otherwise.
        "reply_to": m.reply_to_msg_id,
        "media": media,
    }


def _local(dt) -> str:
    """Format a Telegram (UTC-aware) datetime in local time."""
    return dt.astimezone().strftime("%Y-%m-%d %H:%M") if dt else ""


def _parse_since(value: str | None) -> datetime | None:
    """Parse an ISO date/datetime cutoff; naive values are read as UTC."""
    if not value:
        return None
    dt = datetime.fromisoformat(value)
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt


def _dialog_filters(client):
    """Return the account's chat folders (DialogFilter objects)."""
    res = client(functions.messages.GetDialogFiltersRequest())
    # Newer Telethon wraps the list in a DialogFilters container; older returns it raw.
    return res.filters if hasattr(res, "filters") else res


def _folder_title(f) -> str:
    # The title is a TextWithEntities in recent layers, a plain str before that.
    return f.title.text if hasattr(f.title, "text") else f.title


def _folder_peers(f) -> list:
    """Peers explicitly placed in a folder (pinned + included), de-duplicated."""
    return list(getattr(f, "pinned_peers", []) or []) + list(
        getattr(f, "include_peers", []) or []
    )


def _peer_id(peer) -> int | None:
    """Canonical numeric id for a peer/entity, comparable across InputPeer forms."""
    try:
        return utils.get_peer_id(peer)
    except Exception:
        return None


def _resolve_folder(client, name: str):
    """Return the single **editable** folder matching NAME, else exit.

    Only plain `DialogFilter` folders are editable here: `DialogFilterDefault`
    (All chats) has no membership, and `DialogFilterChatlist` (a shared/invite
    folder) is not owned by this account so its peer list can't be rewritten.
    """
    needle = name.lower()
    chosen = next(
        (
            f
            for f in _dialog_filters(client)
            if isinstance(f, types.DialogFilter)
            and needle in (_folder_title(f) or "").lower()
        ),
        None,
    )
    if chosen is None:
        raise click.ClickException(f"No editable folder matches {name!r}.")
    return chosen


def _msg_text(msg) -> str:
    if msg.message:
        return msg.message
    if msg.media:
        return f"[{type(msg.media).__name__}]"
    if msg.action:
        return f"[{type(msg.action).__name__}]"
    return ""


def _transcribe_audio(path: str, backend: str) -> dict | None:
    """Run transcribe-cli on one audio file; None (with a warning) when it fails.

    A failed transcription must not abort a read, so errors degrade to the
    untranscribed message instead of raising.
    """
    exe = shutil.which("transcribe") or str(Path.home() / ".local" / "bin" / "transcribe")
    try:
        result = subprocess.run([exe, "file", path, "--backend", backend, "--json"], capture_output=True, text=True, timeout=900)
    except (OSError, subprocess.TimeoutExpired) as exc:
        log.warning("transcribe failed for %s: %s", path, exc)
        return None
    if result.returncode != 0:
        log.warning("transcribe failed for %s: %s", path, result.stderr.strip()[-300:])
        return None
    try:
        out = json.loads(result.stdout)
        if not isinstance(out, dict) or not isinstance(out.get("text"), str):
            raise ValueError("expected a JSON object with string text")
    except ValueError as exc:
        log.warning("Invalid transcribe output: %s", exc)
        return None
    return {"text": out["text"].strip(), "language": out.get("language")}


def _cached_transcript(chat_id, msg_id: int, backend: str) -> str | None:
    """Read a backend-specific cache entry; damaged entries are retried."""
    cache = TRANSCRIPT_CACHE / f"{chat_id}_{msg_id}_{backend}.json"
    try:
        result = json.loads(cache.read_text())
        if isinstance(result, dict) and isinstance(result.get("text"), str):
            return result["text"]
    except FileNotFoundError:
        pass
    except (OSError, ValueError) as exc:
        log.warning("Cannot read transcript cache: %s", exc)
    return None


def _transcript(chat_id, msg_id: int, fetch, backend: str) -> str | None:
    """Cache one audio transcript per chat, message, and requested backend.

    `fetch(dir)` downloads the audio into `dir` and returns its path; it is only
    called on a cache miss.
    """
    cached = _cached_transcript(chat_id, msg_id, backend)
    if cached is not None:
        return cached
    try:
        with tempfile.TemporaryDirectory() as tmp:
            path = fetch(tmp)
            result = _transcribe_audio(str(path), backend) if path else None
    except Exception as exc:
        log.warning("Audio transcription failed for message %s: %s", msg_id, exc)
        return None
    if result is None:
        return None
    try:
        TRANSCRIPT_CACHE.mkdir(parents=True, exist_ok=True)
        TRANSCRIPT_CACHE.chmod(stat.S_IRWXU)
        cache = TRANSCRIPT_CACHE / f"{chat_id}_{msg_id}_{backend}.json"
        # Atomic replacement keeps concurrent readers away from partial JSON.
        with tempfile.NamedTemporaryFile(mode="w", dir=TRANSCRIPT_CACHE, delete=False) as handle:
            pending = Path(handle.name)
            try:
                handle.write(json.dumps(result, ensure_ascii=False))
                handle.close()
                pending.replace(cache)
            finally:
                pending.unlink(missing_ok=True)
    except OSError as exc:
        log.warning("Cannot save transcript cache: %s", exc)
    return result["text"]


async def _live_transcript(message, backend: str) -> str | None:
    """Download on Telegram's event loop; run speech inference off the loop."""
    import asyncio

    cached = _cached_transcript(message.chat_id, message.id, backend)
    if cached is not None:
        return cached
    try:
        with tempfile.TemporaryDirectory() as tmp:
            path = await message.download_media(file=tmp)
            return await asyncio.to_thread(
                _transcript, message.chat_id, message.id, lambda _d: path, backend
            )
    except Exception as exc:
        log.warning("Audio transcription failed for message %s: %s", message.id, exc)
        return None


def _add_transcripts(client, messages, rows: list[dict], backend: str) -> None:
    """Set `transcript` on each row whose message is a voice note or audio file."""
    for m, row in zip(messages, rows):
        if m.voice or m.audio:
            row["transcript"] = _transcript(m.chat_id, m.id, lambda d, m=m: client.download_media(m, file=d), backend)


def _line_text(m: dict) -> str:
    """Human rendering of a row's text, with an audio transcript in place of the media stub."""
    return f"{m['text']} [transcript] {m['transcript']}" if m.get("transcript") else m["text"]


# Off by default: Whisper costs seconds per note. TG_TRANSCRIBE=1 turns it on everywhere.
transcribe_option = click.option(
    "--transcribe/--no-transcribe", default=False, envvar="TG_TRANSCRIBE", show_envvar=True,
    help="Transcribe voice notes and audio files locally via `transcribe` (transcribe-cli); adds a `transcript` field.",
)
transcribe_backend_option = click.option(
    "--transcribe-backend", type=click.Choice(["auto", "whisper", "parakeet"]), default="auto",
    envvar="TG_TRANSCRIBE_BACKEND", show_envvar=True, show_default=True,
    help="Speech model for --transcribe (see `transcribe file --help`).",
)


@click.group(context_settings={"help_option_names": ["-h", "--help"]}, epilog="\b\nExamples:\n  tg chats --limit 20\n  tg read alice --limit 50\n  tg send alice \"running late\"")
def cli() -> None:
    """Read and send your own Telegram chats (user account, via Telethon)."""


@cli.command(epilog="\b\nExamples:\n  tg login\n  tg login --api-id 12345 --api-hash 0123456789abcdef0123456789abcdef")
@click.option("--api-id", "api_id", default=None, help="Telegram api_id (else prompted/stored).")
@click.option("--api-hash", "api_hash", default=None, help="Telegram api_hash (else prompted/stored).")
def login(api_id: str | None, api_hash: str | None) -> None:
    """Authenticate this device as your Telegram user account (one-time).

    Prompts for the api_id / api_hash (from https://my.telegram.org) if not
    already stored, then runs Telethon's interactive login: it asks for your
    phone number, the login code Telegram sends you, and your 2FA password if one
    is set. The resulting session is stored `chmod 600` in the config dir.
    """
    _secure_dir()
    if not (api_id and api_hash):
        stored = _load_config()
        api_id = api_id or (str(stored["api_id"]) if "api_id" in stored else None)
        api_hash = api_hash or stored.get("api_hash")
    # hide_input keeps every secret off the screen (and thus out of terminal
    # scrollback): the api_hash, phone, and login code are as sensitive as the
    # 2FA password, so none of them are ever echoed.
    if not api_id:
        api_id = click.prompt("api_id (from my.telegram.org)", hide_input=True)
    if not api_hash:
        api_hash = click.prompt("api_hash (from my.telegram.org)", hide_input=True)

    _store_credentials(api_id, api_hash)

    client = TelegramClient(str(SESSION_BASE), int(api_id), api_hash)
    # Drive Telethon's interactive login through masked prompts rather than its
    # default plaintext input() for phone and code.
    client.start(
        phone=lambda: click.prompt("phone number (e.g. +33…)", hide_input=True),
        code_callback=lambda: click.prompt("login code Telegram sent you", hide_input=True),
        password=lambda: click.prompt("2FA password", hide_input=True),
    )
    _lock_down(Path(str(SESSION_BASE) + ".session"))
    me = client.get_me()
    client.disconnect()
    click.echo(f"Logged in as {utils.get_display_name(me)} (@{me.username or me.id}).")


LINK_STATE = CONFIG_DIR / "link.json"
LINK_TIMEOUT = 300
LINK_PAGE = """<!doctype html><meta charset=utf-8><title>Link Telegram</title>
<style>body{font:16px system-ui;max-width:28rem;margin:3rem auto;text-align:center}svg{width:16rem;height:16rem}</style>
<h1>Link Telegram</h1><div id=s>Starting…</div>
<form id=f hidden><p>Your account has a 2FA password:</p><input type=password id=p autofocus> <button>Send</button></form>
<script>
const f=document.getElementById('f'),s=document.getElementById('s');
f.onsubmit=e=>{e.preventDefault();fetch('password',{method:'POST',body:document.getElementById('p').value});f.hidden=true};
async function tick(){const r=await (await fetch('state')).json();
 if(r.step==='qr')s.innerHTML='<p>On your phone: Telegram → Settings → Devices → <b>Link Desktop Device</b>, then scan:</p>'+r.svg;
 else if(r.step==='password'){s.textContent=r.error||'';f.hidden=false}
 else if(r.step==='done'){s.textContent='Linked as '+r.name+'. You can close this page.';return}
 else if(r.step==='failed'){s.textContent='Failed: '+r.error;return}
 setTimeout(tick,1000)}
tick();
</script>"""


def _qr_svg(url: str) -> str:
    import qrcode
    import qrcode.image.svg

    return qrcode.make(url, image_factory=qrcode.image.svg.SvgPathImage).to_string(encoding="unicode")


def _store_credentials(api_id: str, api_hash: str) -> None:
    """Write api_id/api_hash chmod 600 and hand them to the vault when there is one."""
    CONFIG_FILE.touch(mode=0o600, exist_ok=True)
    _lock_down(CONFIG_FILE)
    CONFIG_FILE.write_text(json.dumps({"api_id": int(api_id), "api_hash": api_hash}))
    _lock_down(CONFIG_FILE)
    pending = CONFIG_FILE.with_suffix(".auth-pending")
    if _auth_broker("save", {"api_id": int(api_id), "api_hash": api_hash}) is None:
        pending.touch(mode=0o600)
    else:
        pending.unlink(missing_ok=True)


def _link_helper() -> None:
    """Serve the QR page on 127.0.0.1 and drive Telethon's QR login until done or timed out."""
    import asyncio
    import secrets
    import threading
    import webbrowser
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    from telethon.errors import PasswordHashInvalidError, SessionPasswordNeededError

    api_id, api_hash = _load_credentials()
    state: dict = {"step": "starting"}
    passwords: list[str] = []
    # A random path keeps other local pages and processes from reading the QR.
    token = secrets.token_urlsafe(16)

    class Page(BaseHTTPRequestHandler):
        def _send(self, body: str, kind: str) -> None:
            data = body.encode()
            self.send_response(200)
            self.send_header("Content-Type", kind)
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            if self.path == f"/{token}/":
                self._send(LINK_PAGE, "text/html; charset=utf-8")
            elif self.path == f"/{token}/state":
                self._send(json.dumps(state), "application/json")
            else:
                self.send_error(404)

        def do_POST(self):
            if self.path != f"/{token}/password":
                self.send_error(404)
                return
            passwords.append(self.rfile.read(int(self.headers.get("Content-Length", 0))).decode())
            self._send("{}", "application/json")

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Page)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{server.server_port}/{token}/"
    LINK_STATE.write_text(json.dumps({"url": url, "pid": os.getpid()}))
    _lock_down(LINK_STATE)
    webbrowser.open(url)

    async def password() -> str:
        while not passwords:
            await asyncio.sleep(0.5)
        return passwords.pop()

    async def drive() -> None:
        client = TelegramClient(str(SESSION_BASE), api_id, api_hash)
        await client.connect()
        try:
            if not await client.is_user_authorized():
                qr = await client.qr_login()
                while True:
                    state.update(step="qr", svg=_qr_svg(qr.url))
                    try:
                        await qr.wait()
                        break
                    except asyncio.TimeoutError:
                        await qr.recreate()
                    except SessionPasswordNeededError:
                        state.update(step="password", svg=None, error=None)
                        while True:
                            try:
                                await client.sign_in(password=await password())
                                break
                            except PasswordHashInvalidError:
                                state.update(step="password", error="Wrong password, try again.")
                        break
            me = await client.get_me()
            _lock_down(Path(str(SESSION_BASE) + ".session"))
            state.update(step="done", svg=None, name=utils.get_display_name(me))
        finally:
            await client.disconnect()

    try:
        asyncio.run(asyncio.wait_for(drive(), LINK_TIMEOUT))
    except Exception as exc:  # noqa: BLE001 — shown on the page; the helper has no other reader
        state.update(step="failed", svg=None, error=str(exc) or type(exc).__name__)
    # Let the page poll the final state before the server goes away.
    import time

    time.sleep(5)
    server.shutdown()
    LINK_STATE.unlink(missing_ok=True)


@cli.command(epilog="\b\nExamples:\n  tg link\n  tg link --api-id 12345 --api-hash 0123456789abcdef0123456789abcdef")
@click.option("--api-id", "api_id", default=None, hidden=True, help="Telegram api_id, stored for later runs.")
@click.option("--api-hash", "api_hash", default=None, hidden=True, help="Telegram api_hash, stored for later runs.")
@click.option("--helper", is_flag=True, hidden=True, help="Run the page and login in this process.")
def link(api_id: str | None, api_hash: str | None, helper: bool) -> None:
    """Link this device to your Telegram account by scanning a QR code; no terminal needed.

    Opens a local page in the browser showing a QR code; scan it from the Telegram
    app (Settings → Devices → Link Desktop Device) and enter the 2FA password there
    if asked. Returns at once: check the result with `whoami`. The page stays up
    for 5 minutes. Needs api_id / api_hash: from TG_API_ID / TG_API_HASH (the
    Claude Desktop extension's settings), the stored config, or the options.
    """
    _secure_dir()
    if api_id and api_hash:
        _store_credentials(api_id, api_hash)
    if helper:
        _link_helper()
        return
    _load_credentials()
    LINK_STATE.unlink(missing_ok=True)
    # Detached so the page outlives this command, which an MCP client waits on.
    subprocess.Popen(
        [sys.executable, str(Path(__file__).resolve()), "link", "--helper"],
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True,
    )
    import time

    for _ in range(100):
        if LINK_STATE.exists():
            url = json.loads(LINK_STATE.read_text())["url"]
            click.echo(
                f"A page opened in the browser ({url}). On your phone: Telegram → Settings → Devices → "
                "Link Desktop Device, scan the QR code, and type your 2FA password on the page if asked. "
                "Then check with `tg whoami`."
            )
            return
        time.sleep(0.1)
    raise click.ClickException("the link page did not start; run `tg link --helper` to see why")


@cli.command(epilog="\b\nExamples:\n  tg logout")
def logout() -> None:
    """Revoke this session server-side and delete the local session file."""
    with _client() as client:
        client.log_out()
    session = Path(str(SESSION_BASE) + ".session")
    session.unlink(missing_ok=True)
    click.echo("Logged out; session revoked and local session file removed.")


@cli.command(epilog="\b\nExamples:\n  tg whoami\n  tg whoami --json")
@click.option("--json", "as_json", is_flag=True, help="Emit JSON.")
def whoami(as_json: bool) -> None:
    """Show the logged-in account."""
    with _client() as client:
        me = client.get_me()
    info = {
        "id": me.id,
        "name": utils.get_display_name(me),
        "username": me.username,
        "phone": me.phone,
    }
    click.echo(json.dumps(info, ensure_ascii=False) if as_json else
               f"{info['name']} (@{info['username'] or info['id']})")


@cli.command(epilog="\b\nExamples:\n  tg chats --limit 30\n  tg chats --not-in-folder Work --limit 60 --json")
@click.option("--limit", default=30, help="Number of conversations to list.")
@click.option("--not-in-folder", "not_in_folder", default=None, help="Only list chats NOT already in the folder matching this name — spot newly-joined partner groups sitting outside a curated folder.")
@click.option("--json", "as_json", is_flag=True, help="Emit JSON.")
def chats(limit: int, not_in_folder: str | None, as_json: bool) -> None:
    """List conversations, most recent first.

    With --not-in-folder, restrict the listing to chats that are NOT members of
    the named folder. A folder-scoped digest job uses this to catch partner
    groups you were just added to that never landed in the curated folder (and
    would otherwise be missed by a folder-only sweep).
    """
    with _client() as client:
        dialogs = client.get_dialogs(limit=limit)
        exclude: set = set()
        if not_in_folder:
            exclude = {_peer_id(p) for p in _folder_peers(_resolve_folder(client, not_in_folder))}
        out = [
            {
                "last": _local(d.date),
                "name": d.name,
                "kind": _kind(d),
                "unread": d.unread_count,
            }
            for d in dialogs
            if not not_in_folder or _peer_id(d.entity) not in exclude
        ]
    if as_json:
        click.echo(json.dumps(out, ensure_ascii=False))
        return
    for c in out:
        badge = f" ({c['unread']} unread)" if c["unread"] else ""
        click.echo(f"{c['last']}  [{c['kind']}] {c['name']}{badge}")


@cli.command(epilog="\b\nExamples:\n  tg folders\n  tg folders --json")
@click.option("--json", "as_json", is_flag=True, help="Emit JSON.")
def folders(as_json: bool) -> None:
    """List chat folders and how many chats each explicitly contains."""
    with _client() as client:
        out = [
            {"title": _folder_title(f), "chats": len(_folder_peers(f))}
            for f in _dialog_filters(client)
            if not isinstance(f, types.DialogFilterDefault)
        ]
    if as_json:
        click.echo(json.dumps(out, ensure_ascii=False))
        return
    for f in out:
        click.echo(f"{f['chats']:>3}  {f['title']}")


@cli.command(name="folder-add", epilog="\b\nExamples:\n  tg folder-add Work \"Dev Team\"\n  tg folder-add Work \"Dev Team\" --yes")
@click.argument("folder")
@click.argument("query")
@click.option("--match", default=0, help="Pick the Nth matching chat when QUERY is ambiguous (1-based).")
@click.option("--yes", is_flag=True, help="Actually apply. Without it, prints a dry-run only.")
@click.option("--json", "as_json", is_flag=True, help="Emit JSON.")
def folder_add(folder: str, query: str, match: int, yes: bool, as_json: bool) -> None:
    """Add the chat matching QUERY into the chat folder matching FOLDER.

    A write to your account's folder layout (never to any chat's messages), so it
    defaults to a dry-run; pass --yes to apply. Idempotent — a chat already in the
    folder is left untouched. Use it to fold a newly-joined partner group into a
    curated folder so a folder-scoped digest stops missing it.
    """
    with _client() as client:
        chosen = _resolve_folder(client, folder)
        dialog = _resolve_dialog(client, query, match)
        target_id = _peer_id(dialog.entity)
        existing = {_peer_id(p) for p in _folder_peers(chosen)}
        result = {
            "folder": _folder_title(chosen),
            "chat": dialog.name,
            "already_in_folder": target_id in existing,
            "added": False,
        }
        if result["already_in_folder"]:
            click.echo(json.dumps(result, ensure_ascii=False) if as_json else
                       f"{dialog.name!r} is already in folder {result['folder']!r}.")
            return
        if not yes:
            result["dry_run"] = True
            if as_json:
                click.echo(json.dumps(result, ensure_ascii=False))
            else:
                click.echo("DRY-RUN (folder unchanged). Re-run with --yes to apply.")
                click.echo(f"  add: {dialog.name!r}  →  folder {result['folder']!r}")
            return
        # Append the new peer to include_peers and push the whole filter back.
        chosen.include_peers = list(getattr(chosen, "include_peers", []) or []) + [
            client.get_input_entity(dialog.entity)
        ]
        client(functions.messages.UpdateDialogFilterRequest(id=chosen.id, filter=chosen))
        result["added"] = True
        click.echo(json.dumps(result, ensure_ascii=False) if as_json else
                   f"Added {dialog.name!r} to folder {result['folder']!r}.")


@cli.command(epilog="\b\nExamples:\n  tg folder Work --since 2026-07-05\n  tg folder Work --since 2026-07-05 --limit 200 --json")
@click.argument("name")
@click.option("--since", default=None, help="ISO date/datetime; keep only messages at/after it (UTC if no tz).")
@click.option("--limit", default=100, help="Max messages fetched per chat before the --since filter.")
@transcribe_option
@transcribe_backend_option
@click.option("--json", "as_json", is_flag=True, help="Emit JSON.")
def folder(name: str, since: str | None, limit: int, transcribe: bool, transcribe_backend: str, as_json: bool) -> None:
    """Read recent messages from every chat in the folder matching NAME.

    Windowed batch read across a whole folder — the building block a digest job
    uses: enumerate the folder's chats, fetch each chat's recent messages, and
    keep those at/after --since. Each message carries an `epoch` field so a
    caller can filter precisely against its own cutoff.

    Example: tg folder Zama --transcribe --json
    """
    cutoff = _parse_since(since)
    needle = name.lower()
    with _client() as client:
        chosen = next(
            (
                f
                for f in _dialog_filters(client)
                if not isinstance(f, types.DialogFilterDefault)
                and needle in (_folder_title(f) or "").lower()
            ),
            None,
        )
        if chosen is None:
            raise click.ClickException(f"No folder matches {name!r}.")
        out = []
        for peer in _folder_peers(chosen):
            entity = client.get_entity(peer)
            messages = [m for m in reversed(client.get_messages(entity, limit=limit)) if cutoff is None or m.date >= cutoff]
            rows = [
                {
                    "ts": _local(m.date),
                    "epoch": int(m.date.timestamp()),
                    "sender": "me" if m.out else utils.get_display_name(m.sender)
                    or str(m.sender_id),
                    "text": _msg_text(m),
                }
                for m in messages
            ]
            if transcribe:
                _add_transcripts(client, messages, rows, transcribe_backend)
            out.append({"chat": utils.get_display_name(entity), "messages": rows})
    if as_json:
        click.echo(json.dumps(out, ensure_ascii=False))
        return
    for chat in out:
        if not chat["messages"]:
            continue
        click.echo(f"\n# {chat['chat']} — {len(chat['messages'])} messages")
        for m in chat["messages"]:
            click.echo(f"{m['ts']}  {m['sender']}: {_line_text(m)}")


@cli.command(epilog="\b\nExamples:\n  tg listen me --transcribe\n  tg listen me --exec 'cat >> inbox.jsonl'")
@click.argument("query")
@click.option("--exec", "exec_cmd", default=None, help="Shell command run for each message, its JSON on stdin (e.g. an inbox trigger).")
@click.option("--match", default=0, help="Pick the Nth match when ambiguous (1-based).")
@click.option("--all", "all_chats", is_flag=True, help="Every chat, not just the one matching QUERY.")
@transcribe_option
@transcribe_backend_option
def listen(query: str, exec_cmd: str | None, match: int, all_chats: bool, transcribe: bool, transcribe_backend: str) -> None:
    """Stay connected and print each new message of the chat matching QUERY as one JSON line.

    Push instead of polling: Telegram delivers updates over the open MTProto
    connection. Outgoing messages (yours, from any device) are included, which
    is what makes Saved Messages a live inbox. Runs until interrupted. Use a
    dedicated session (`TG_SESSION=listener tg login`, then `TG_SESSION=listener
    tg listen me`) so one-shot commands keep working alongside.

    Example: tg listen me --transcribe
    """
    import subprocess as _sp

    from telethon import events

    with _client() as client:
        entity = None if all_chats else _resolve_dialog(client, query, match).entity

        @client.on(events.NewMessage(chats=None if entity is None else entity, incoming=True, outgoing=True))
        async def _on_message(event):
            m = event.message
            row = _message_dict(m)
            row["chat_id"] = event.chat_id
            if transcribe and (m.voice or m.audio):
                row["transcript"] = await _live_transcript(m, transcribe_backend)
            line = json.dumps(row, ensure_ascii=False)
            click.echo(line)
            sys.stdout.flush()
            if exec_cmd:
                _sp.Popen(exec_cmd, shell=True, stdin=_sp.PIPE, text=True).communicate(line + "\n")

        click.echo(f"# listening on {'all chats' if all_chats else query}", err=True)
        client.run_until_disconnected()


def _thread_messages(client, entity, limit: int, cutoff: datetime | None) -> list:
    """A chat's messages in chronological order: the last `limit`, or the first `limit` at/after `cutoff`."""
    if cutoff is None:
        return list(reversed(client.get_messages(entity, limit=limit)))
    # reverse=True walks forward from offset_date, so a busy window is read from
    # its start instead of being cut to the most recent `limit` messages.
    return list(client.iter_messages(entity, limit=limit, offset_date=cutoff, reverse=True))


@cli.command(epilog="\b\nExamples:\n  tg read alice\n  tg read \"Dev Team\" --since 2026-09-28T22:00:00 --limit 200\n  tg read alice --match 2 --json")
@click.argument("query")
@click.option("--limit", default=50, help="Number of messages to show.")
@click.option("--since", default=None, help="ISO date/datetime; read from this point forward (UTC if no tz).")
@click.option("--match", default=0, help="Pick the Nth match when ambiguous (1-based).")
@transcribe_option
@transcribe_backend_option
@click.option("--json", "as_json", is_flag=True, help="Emit JSON.")
def read(query: str, limit: int, since: str | None, match: int, transcribe: bool, transcribe_backend: str, as_json: bool) -> None:
    """Read messages from the chat best matching QUERY (name substring).

    Without --since, shows the last --limit messages. With --since, shows the
    first --limit messages at/after it, oldest first.

    Example: tg read alice --transcribe --json
    """
    cutoff = _parse_since(since)
    with _client() as client:
        dialog = _resolve_dialog(client, query, match)
        messages = _thread_messages(client, dialog.entity, limit, cutoff)
        out = [_message_dict(m) for m in messages]
        if transcribe:
            _add_transcripts(client, messages, out, transcribe_backend)
        title = dialog.name
    if as_json:
        click.echo(json.dumps(out, ensure_ascii=False))
        return
    click.echo(f"# {title} — {len(out)} messages\n")
    for m in out:
        click.echo(f"{m['ts']}  {m['sender']}: {_line_text(m)}")


@cli.command(epilog="\b\nExamples:\n  tg search invoice\n  tg search invoice --chat alice --limit 20 --json")
@click.argument("text")
@click.option("--chat", "chat_query", default=None, help="Restrict to the chat matching this name (reliable, single request).")
@click.option("--match", default=0, help="Pick the Nth chat match when --chat is ambiguous.")
@click.option("--limit", default=50, help="Number of matches to show.")
@click.option("--json", "as_json", is_flag=True, help="Emit JSON.")
def search(text: str, chat_query: str | None, match: int, limit: int, as_json: bool) -> None:
    """Search messages containing TEXT.

    With --chat, searches that one conversation (one API call, exact). Without it,
    runs a best-effort global search across all your chats via Telegram's global
    search endpoint.
    """
    with _client() as client:
        if chat_query:
            dialog = _resolve_dialog(client, chat_query, match)
            messages = client.get_messages(dialog.entity, search=text, limit=limit)
            out = [
                {"ts": _local(m.date), "chat": dialog.name, "text": _msg_text(m)}
                for m in messages
            ]
        else:
            result = client(
                functions.messages.SearchGlobalRequest(
                    q=text,
                    filter=types.InputMessagesFilterEmpty(),
                    min_date=None,
                    max_date=None,
                    offset_rate=0,
                    offset_peer=types.InputPeerEmpty(),
                    offset_id=0,
                    limit=limit,
                )
            )
            # The response bundles the peers referenced by the hits; map raw ids
            # to names so each result shows which chat it came from.
            names = {u.id: utils.get_display_name(u) for u in result.users}
            names.update({c.id: utils.get_display_name(c) for c in result.chats})

            def _peer_name(peer) -> str:
                for attr in ("user_id", "chat_id", "channel_id"):
                    pid = getattr(peer, attr, None)
                    if pid is not None:
                        return names.get(pid, str(pid))
                return "?"

            out = [
                {"ts": _local(m.date), "chat": _peer_name(m.peer_id), "text": _msg_text(m)}
                for m in result.messages
            ]
    if as_json:
        click.echo(json.dumps(out, ensure_ascii=False))
        return
    for m in out:
        click.echo(f"{m['ts']}  {m['chat']}: {m['text']}")


@cli.command(epilog="\b\nExamples:\n  tg send alice \"running late\"\n  tg send alice \"the deck\" --file deck.pdf --yes\n  tg send x --peer @alice \"hi\"")
@click.argument("query")
@click.argument("text", required=False, default="")
@click.option("--file", "file_path", default=None, help="Attach and send this file/document; TEXT (if any) becomes its caption.")
@click.option("--peer", "peer_override", default=None, help="Send to this exact @username / phone / id, skipping query resolution.")
@click.option("--match", default=0, help="Pick the Nth matching chat when ambiguous (1-based).")
@click.option("--reply-to", "reply_to", type=int, default=None, help="Reply to this message id (from `tg read --json`), shown as a reply bubble.")
@click.option("--yes", is_flag=True, help="Actually send. Without it, prints a dry-run only.")
def send(query: str, text: str, file_path: str | None, peer_override: str | None, match: int, reply_to: int | None, yes: bool) -> None:
    """Send a message (and/or a file) to the chat matching QUERY.

    With --file, sends that document; any TEXT becomes its caption. Defaults to a
    dry-run that prints the resolved recipient and payload without sending. Pass
    --yes to actually send — an outbound action the calling agent must confirm
    with the user first.
    """
    if not text and not file_path:
        raise click.ClickException("Nothing to send: provide TEXT, --file, or both.")
    attachment = Path(file_path).expanduser() if file_path else None
    if attachment and not attachment.is_file():
        raise click.ClickException(f"File not found: {attachment}")

    with _client() as client:
        if peer_override:
            entity = client.get_entity(peer_override)
            label = utils.get_display_name(entity) or peer_override
        else:
            dialog = _resolve_dialog(client, query, match)
            entity, label = dialog.entity, dialog.name

        if not yes:
            click.echo("DRY-RUN (nothing sent). Re-run with --yes to send.")
            click.echo(f"  to:      {label}")
            if attachment:
                click.echo(f"  file:    {attachment}")
            if text:
                click.echo(f"  message: {text}")
            return

        if attachment:
            sent = client.send_file(entity, str(attachment), caption=text or None, reply_to=reply_to)
        else:
            sent = client.send_message(entity, text, reply_to=reply_to)
    what = f"file {attachment.name}" if attachment else "message"
    # The id lets a script record what it sent and route a later reply to it.
    click.echo(f"Sent {what} to {label} (id {sent.id}).")
    click.echo(f"sent: {sent.id}")


@cli.command(epilog="\b\nExamples:\n  tg download alice --limit 50 --out ./tg-media\n  tg download \"Dev Team\" --since 2026-07-05 --docs-only --out ./tg-docs")
@click.argument("query")
@click.option("--limit", default=20, help="How many recent messages to scan for media.")
@click.option("--since", default=None, help="ISO date/datetime; only download attachments from messages at/after it (UTC if no tz).")
@click.option("--docs-only", is_flag=True, help="Skip photos/stickers; download only file documents (PDF, decks, …).")
@click.option("--match", default=0, help="Pick the Nth matching chat when ambiguous (1-based).")
@click.option("--out", default=".", help="Directory to save attachments into (created if missing).")
@click.option("--json", "as_json", is_flag=True, help="Emit JSON.")
def download(query: str, limit: int, since: str | None, docs_only: bool, match: int, out: str, as_json: bool) -> None:
    """Download attachments from the recent messages of the chat matching QUERY.

    Scans the last --limit messages of the matched chat and saves every media
    attachment into --out, using Telegram's own filename where available. Narrow
    the set with --since (only in-window messages) and --docs-only (files, not
    photos/stickers).
    """
    cutoff = _parse_since(since)
    outdir = Path(out).expanduser()
    outdir.mkdir(parents=True, exist_ok=True)
    with _client() as client:
        dialog = _resolve_dialog(client, query, match)
        saved = []
        for m in client.get_messages(dialog.entity, limit=limit):
            if not m.media:
                continue
            if cutoff is not None and m.date < cutoff:
                continue
            # A "document" is any non-photo file (PDF, deck, video, …); photos and
            # stickers are not `m.document`, so this cleanly drops image chatter.
            if docs_only and not m.document:
                continue
            path = client.download_media(m, file=str(outdir))
            if path:
                saved.append({"ts": _local(m.date), "id": m.id, "reply_to": m.reply_to_msg_id, "file": path, "caption": _msg_text(m)})
    if as_json:
        click.echo(json.dumps(saved, ensure_ascii=False))
        return
    if not saved:
        click.echo(f"No attachments found in the last {limit} messages of {dialog.name!r}.")
        return
    click.echo(f"Saved {len(saved)} attachment(s) from {dialog.name!r} into {outdir}:")
    for s in saved:
        click.echo(f"  {s['ts']}  {s['file']}")



@cli.command("auth-status", epilog="\b\nExamples:\n  tg auth-status\n  tg auth-status --json")
@click.option("--json", "as_json", is_flag=True, help="Emit secret-free metadata.")
def auth_status(as_json):
    """Report credential storage without contacting the provider. Example: auth-status --json."""
    import json
    metadata = _auth_broker("status") or {
        "connector": "telegram", "account": "default", "source": "unavailable",
        "configured": False, "pending": False, "last_sync": None,
    }
    if not metadata.get("configured") and CONFIG_FILE.exists():
        metadata.update(source="legacy", configured=True)
    if not metadata.get("configured") and os.environ.get("TG_API_ID") and os.environ.get("TG_API_HASH"):
        metadata.update(source="env", configured=True)
    metadata.update(session_scope="host", session_present=Path(str(SESSION_BASE) + ".session").exists(), pairing_required=not Path(str(SESSION_BASE) + ".session").exists())
    if CONFIG_FILE.with_suffix(".auth-pending").exists():
        metadata.update(source="pending-local", configured=True, pending=True)
    click.echo(json.dumps(metadata))


@cli.command("auth-sync", epilog="\b\nExamples:\n  tg auth-sync")
def auth_sync():
    """Move stored credentials into 1Password. Example: auth-sync."""
    import json
    local_pending = CONFIG_FILE.with_suffix(".auth-pending")
    metadata = _auth_broker("save", _load_config()) if local_pending.exists() else _auth_broker("sync")
    if metadata and local_pending.exists():
        local_pending.unlink()
    if not metadata or not metadata.get("configured"):
        config = _load_config()
        metadata = _auth_broker("save", config) if config else metadata
    click.echo(json.dumps(metadata or {"connector": "telegram", "source": "unavailable", "pending": False}))
    if not metadata or not metadata.get("configured") or metadata.get("pending"):
        raise click.exceptions.Exit(3)


if __name__ == "__main__":
    cli()
