#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11,<3.12"  # leveldb 0.201 (via slacktokens) uses PyUnicode_AS_UNICODE, removed in 3.12
# dependencies = [
#     "slack-sdk>=3.33",
#     "slacktokens>=0.2.6",
#     "click>=8.0",
#     "rich>=13.0",
#     "requests>=2.31",
# ]
# ///
"""Slack User CLI — terminal access to Slack using browser session credentials.

Provides read/write access to Slack channels, DMs, threads, and search
using xoxc- tokens and d cookies extracted from the Slack desktop app
or browser DevTools. No Slack app registration needed.
"""

import json
import logging
import re
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import click
from rich.console import Console
from rich.table import Table
from rich.text import Text
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

logger = logging.getLogger(__name__)

# -- Config management --------------------------------------------------------

CONFIG_DIR = Path.home() / ".config" / "slack-user-cli"
CONFIG_FILE = CONFIG_DIR / "config.json"

console = Console()


def load_config() -> dict:
    """Load config from disk, returning empty dict if missing.

    Migrates legacy single-workspace format to multi-workspace on read.
    """
    if not CONFIG_FILE.exists():
        return {}
    config = json.loads(CONFIG_FILE.read_text())
    # Migrate legacy format: {token, cookie, team, user} → multi-workspace
    if "token" in config and "workspaces" not in config:
        team = config.get("team", "default")
        config = {
            "cookie": config.get("cookie", ""),
            "default": team,
            "workspaces": {
                team: {
                    "token": config["token"],
                    "team": team,
                    "user": config.get("user", ""),
                }
            },
        }
        save_config(config)
    return config


def save_config(config: dict) -> None:
    """Persist config to disk, creating parent dirs as needed."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(config, indent=2))


def get_workspace_config(config: dict, workspace: str | None) -> dict:
    """Extract token + cookie for a specific workspace.

    Returns a dict with 'token' and 'cookie' keys ready for WebClient.
    """
    workspaces = config.get("workspaces", {})
    cookie = config.get("cookie", "")

    if not workspaces:
        raise click.ClickException(
            "Not logged in. Run 'login' first to set credentials."
        )

    if workspace is None:
        workspace = config.get("default", "")
        if not workspace:
            available = ", ".join(workspaces.keys())
            raise click.ClickException(
                "No default workspace set. Use -w <name> or run "
                f"'default <name>' to set one. Available: {available}"
            )

    if workspace not in workspaces:
        available = ", ".join(workspaces.keys())
        raise click.ClickException(
            f"Workspace '{workspace}' not found. Available: {available}"
        )

    ws = workspaces[workspace]
    return {"token": ws["token"], "cookie": cookie}


def get_client(config: dict | None = None, workspace: str | None = None) -> WebClient:
    """Build an authenticated WebClient from stored credentials.

    The xoxc- token goes in the standard token param while the d cookie
    must be injected via a custom Cookie header — this mirrors how the
    Slack web client authenticates.
    """
    if config is None:
        config = load_config()
    ws = get_workspace_config(config, workspace)
    token = ws.get("token")
    cookie = ws.get("cookie")
    if not token or not cookie:
        raise click.ClickException(
            "Not logged in. Run 'login' first to set credentials."
        )
    return WebClient(token=token, headers={"cookie": f"d={cookie}"})


# -- Disk-backed cache --------------------------------------------------------

# Cache TTL: 1 hour — channels and users rarely change
CACHE_TTL_SECONDS = 3600

# In-memory user display name cache (populated from disk + API)
_user_cache: dict[str, str] = {}


def _cache_path(workspace: str, kind: str) -> Path:
    """Return the cache file path for a workspace and cache kind.

    Derived from CONFIG_DIR at call time so monkeypatching works in tests.
    """
    return CONFIG_DIR / "cache" / workspace / f"{kind}.json"


def _load_cache(workspace: str, kind: str) -> dict | None:
    """Load a cache file if it exists and hasn't expired."""
    path = _cache_path(workspace, kind)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None
    # Check TTL
    if time.time() - data.get("ts", 0) > CACHE_TTL_SECONDS:
        logger.debug("Cache expired for %s/%s", workspace, kind)
        return None
    return data.get("data")


def _save_cache(workspace: str, kind: str, data: dict) -> None:
    """Save data to a cache file with a timestamp."""
    path = _cache_path(workspace, kind)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"ts": time.time(), "data": data}))


# -- Permanent ID→name store --------------------------------------------------
#
# Slack IDs are immutable and their names change rarely, so id→name resolutions
# are cached forever with NO TTL. This avoids re-hitting the (rate-limited)
# users_info / conversations_info / *_list endpoints for an ID already seen in
# any prior invocation. `refresh` overwrites entries; individual resolutions and
# full builds append to it. Kinds: "users" and "channels".


def _permanent_path(workspace: str) -> Path:
    """Return the never-expiring id→name store path for a workspace."""
    return CONFIG_DIR / "cache" / workspace / "id_names.json"


def _load_permanent(workspace: str) -> dict:
    """Load the never-expiring id→name store (no TTL). Always has both kinds."""
    store = {"users": {}, "channels": {}}
    path = _permanent_path(workspace)
    if not path.exists():
        return store
    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return store
    store["users"].update(data.get("users", {}))
    store["channels"].update(data.get("channels", {}))
    return store


def _permanent_get(workspace: str, kind: str, _id: str) -> str | None:
    """Look up a single id→name mapping in the never-expiring store."""
    if not workspace:
        return None
    return _load_permanent(workspace).get(kind, {}).get(_id)


def _permanent_put(workspace: str, kind: str, mapping: dict[str, str]) -> None:
    """Merge id→name entries into the never-expiring store (immutable IDs)."""
    if not workspace or not mapping:
        return
    store = _load_permanent(workspace)
    store.setdefault(kind, {}).update(mapping)
    path = _permanent_path(workspace)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(store, ensure_ascii=False))


def _get_active_workspace(config: dict | None = None, workspace: str | None = None) -> str:
    """Resolve the active workspace name for cache keying."""
    if config is None:
        config = load_config()
    if workspace is None:
        workspace = config.get("default", "")
    return workspace


def build_channel_cache(client: WebClient, workspace: str) -> dict[str, str]:
    """Fetch all channels and build a name→id mapping, saving to disk."""
    name_to_id: dict[str, str] = {}
    cursor = None
    while True:
        kwargs: dict = {
            "types": "public_channel,private_channel,mpim,im",
            "limit": 200,
        }
        if cursor:
            kwargs["cursor"] = cursor
        resp = client.conversations_list(**kwargs)
        for ch in resp["channels"]:
            name = ch.get("name", "")
            if name:
                name_to_id[name] = ch["id"]
        cursor = resp.get("response_metadata", {}).get("next_cursor")
        if not cursor:
            break
    _save_cache(workspace, "channels", name_to_id)
    # Seed the never-expiring id→name store with the inverse mapping.
    _permanent_put(workspace, "channels", {cid: name for name, cid in name_to_id.items()})
    logger.debug("Cached %d channels for %s", len(name_to_id), workspace)
    return name_to_id


def build_user_cache(client: WebClient, workspace: str) -> dict:
    """Fetch all users and build lookup maps, saving to disk.

    Returns dict with:
      - id_to_display: {user_id: display_name}
      - name_to_id: {username: user_id}
      - display_to_id: {display_name: user_id}
    """
    id_to_display: dict[str, str] = {}
    name_to_id: dict[str, str] = {}
    display_to_id: dict[str, str] = {}
    cursor = None
    while True:
        kwargs: dict = {"limit": 200}
        if cursor:
            kwargs["cursor"] = cursor
        resp = client.users_list(**kwargs)
        for member in resp["members"]:
            uid = member["id"]
            username = member.get("name", "")
            profile = member.get("profile", {})
            display = profile.get("display_name") or member.get("real_name") or username
            id_to_display[uid] = display
            if username:
                name_to_id[username] = uid
            if profile.get("display_name"):
                display_to_id[profile["display_name"]] = uid
        cursor = resp.get("response_metadata", {}).get("next_cursor")
        if not cursor:
            break
    data = {
        "id_to_display": id_to_display,
        "name_to_id": name_to_id,
        "display_to_id": display_to_id,
    }
    _save_cache(workspace, "users", data)
    # Seed the never-expiring id→name store (immutable IDs, one resolution forever).
    _permanent_put(workspace, "users", id_to_display)
    logger.debug("Cached %d users for %s", len(id_to_display), workspace)
    return data


def _get_channel_cache(client: WebClient, workspace: str) -> dict[str, str]:
    """Get channel name→id map from cache or API."""
    cached = _load_cache(workspace, "channels")
    if cached is not None:
        return cached
    return build_channel_cache(client, workspace)


def _get_user_cache(client: WebClient, workspace: str) -> dict:
    """Get user lookup maps from cache or API."""
    cached = _load_cache(workspace, "users")
    if cached is not None:
        return cached
    return build_user_cache(client, workspace)


def resolve_user(client: WebClient, user_id: str, workspace: str = "") -> str:
    """Resolve a Slack user ID to a display name, using disk cache.

    Only reads the disk cache passively — never triggers a full users_list
    build. This keeps individual user lookups fast and avoids pagination
    storms when the cache hasn't been built yet.
    """
    if user_id in _user_cache:
        return _user_cache[user_id]

    # Never-expiring id→name store: IDs are immutable, so a prior resolution
    # (from any earlier invocation) is reused forever with no API call.
    name = _permanent_get(workspace, "users", user_id)
    if name:
        _user_cache[user_id] = name
        return name

    # Passively check disk cache (no API call if missing)
    if workspace:
        cached = _load_cache(workspace, "users")
        if cached is not None:
            name = cached.get("id_to_display", {}).get(user_id)
            if name:
                _user_cache[user_id] = name
                _permanent_put(workspace, "users", {user_id: name})
                return name

    # Fall back to single API call for unknown users
    try:
        resp = client.users_info(user=user_id)
        user = resp["user"]
        name = (
            user.get("profile", {}).get("display_name")
            or user.get("real_name")
            or user_id
        )
        _user_cache[user_id] = name
        # Persist the resolution forever (skip the id→id non-resolution).
        if name != user_id:
            _permanent_put(workspace, "users", {user_id: name})
        return name
    except SlackApiError:
        logger.debug("Failed to resolve user %s", user_id)
        _user_cache[user_id] = user_id
        return user_id


def resolve_channel(client: WebClient, name_or_id: str, workspace: str = "") -> str:
    """Resolve a channel name (without #) to its ID, or pass through an ID."""
    # Already an ID — starts with C, D, or G
    if name_or_id[0] in ("C", "D", "G") and name_or_id[1:].isalnum():
        return name_or_id

    # Check disk cache first
    if workspace:
        channel_map = _get_channel_cache(client, workspace)
        if name_or_id in channel_map:
            return channel_map[name_or_id]

    # Cache miss — walk the API (and rebuild cache while we're at it)
    channel_map = build_channel_cache(client, workspace) if workspace else {}
    if name_or_id in channel_map:
        return channel_map[name_or_id]

    # Final fallback: paginate without caching (no workspace context)
    if not workspace:
        cursor = None
        while True:
            kwargs: dict = {
                "types": "public_channel,private_channel,mpim,im",
                "limit": 200,
            }
            if cursor:
                kwargs["cursor"] = cursor
            resp = client.conversations_list(**kwargs)
            for ch in resp["channels"]:
                if ch.get("name") == name_or_id:
                    return ch["id"]
            cursor = resp.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break

    raise click.ClickException(f"Channel '{name_or_id}' not found.")


def resolve_channel_name(client: WebClient, channel_id: str, workspace: str = "") -> str:
    """Resolve a channel ID (C…/G…) to its #name, cached forever.

    Uses the never-expiring id→name store first, then a single
    conversations_info call (cheap — avoids listing every channel), and
    persists the result. Returns the raw ID if it cannot be resolved so callers
    never silently invent a name.
    """
    name = _permanent_get(workspace, "channels", channel_id)
    if name:
        return name
    try:
        resp = client.conversations_info(channel=channel_id)
        name = resp["channel"].get("name") or channel_id
        if name != channel_id:
            _permanent_put(workspace, "channels", {channel_id: name})
        return name
    except SlackApiError:
        logger.debug("Failed to resolve channel %s", channel_id)
        return channel_id


# -- URL parsing --------------------------------------------------------------

# Slack permalink pattern: https://<workspace>.slack.com/archives/<channel>/p<ts>
_SLACK_URL_PATH_RE = re.compile(r"^/archives/([CDG][A-Z0-9]+)/p(\d{16})$")


def parse_slack_url(url: str) -> tuple[str, str, str]:
    """Parse a Slack permalink into (workspace_domain, channel_id, message_ts).

    Slack permalinks follow: https://<workspace>.slack.com/archives/<channel>/p<ts>
    The timestamp is encoded without the dot; we re-insert it before the last 6 digits.

    Raises click.ClickException on invalid URL.
    """
    parsed = urlparse(url)
    hostname = parsed.hostname or ""

    # Validate <workspace>.slack.com
    if not hostname.endswith(".slack.com"):
        raise click.ClickException(
            f"Not a Slack URL (expected *.slack.com): {url}"
        )
    workspace = hostname.removesuffix(".slack.com")

    match = _SLACK_URL_PATH_RE.match(parsed.path)
    if not match:
        raise click.ClickException(
            f"Malformed Slack permalink path: {parsed.path}"
        )

    channel_id = match.group(1)
    raw_ts = match.group(2)
    # Insert dot before last 6 digits: 1700000000000123 → 1700000000.000123
    message_ts = f"{raw_ts[:-6]}.{raw_ts[-6:]}"

    return workspace, channel_id, message_ts


# Canvas URL pattern: https://<workspace>.slack.com/docs/<team_id>/<file_id>
_CANVAS_URL_PATH_RE = re.compile(r"^/docs/([A-Z0-9]+)/([A-Z0-9]+)$")


def parse_canvas_url(url: str) -> str:
    """Extract the file ID from a Slack canvas URL.

    Canvas URLs follow: https://<workspace>.slack.com/docs/<team_id>/<file_id>
    Returns the file_id needed for the files.info API call.
    """
    parsed = urlparse(url)
    hostname = parsed.hostname or ""

    if not hostname.endswith(".slack.com"):
        raise click.ClickException(
            f"Not a Slack URL (expected *.slack.com): {url}"
        )

    match = _CANVAS_URL_PATH_RE.match(parsed.path)
    if not match:
        raise click.ClickException(
            f"Malformed Slack canvas URL path: {parsed.path}"
        )

    return match.group(2)


def _fetch_canvas_content(client: WebClient, file_id: str) -> tuple[str, str]:
    """Fetch canvas HTML content via files.info private URL.

    Returns (title, html_content). The canvas is stored as a Quip document
    accessible through the file's url_private endpoint.
    """
    import requests  # noqa: PLC0415

    try:
        resp = client.api_call("files.info", params={"file": file_id})
    except SlackApiError as exc:
        raise click.ClickException(str(exc)) from exc

    file_info = resp.get("file", {})
    title = file_info.get("title", "Untitled")
    url_private = file_info.get("url_private")

    if not url_private:
        raise click.ClickException(
            f"No private URL found for file {file_id}. "
            "The canvas may not be accessible."
        )

    # Download content using the same auth headers as the WebClient
    headers = dict(client.headers or {})
    headers["Authorization"] = f"Bearer {client.token}"
    dl_resp = requests.get(url_private, headers=headers, timeout=30)
    dl_resp.raise_for_status()

    return title, dl_resp.text


def _html_to_text(html: str) -> str:
    """Convert simple canvas HTML to readable plain text.

    Handles headings, lists, links, and paragraphs without requiring
    a full HTML parser — canvases use a small, predictable HTML subset.
    """
    text = html
    # Convert headings to markdown-style
    text = re.sub(r"<h1[^>]*>(.*?)</h1>", r"# \1\n", text)
    text = re.sub(r"<h2[^>]*>(.*?)</h2>", r"## \1\n", text)
    text = re.sub(r"<h3[^>]*>(.*?)</h3>", r"### \1\n", text)
    # Convert links to markdown
    text = re.sub(r'<a\s+href="([^"]*)"[^>]*>(.*?)</a>', r"[\2](\1)", text)
    # Convert list items
    text = re.sub(r"<li[^>]*>(.*?)</li>", r"- \1", text)
    # Line breaks
    text = re.sub(r"<br\s*/?>", "\n", text)
    # Strip remaining tags
    text = re.sub(r"<[^>]+>", "", text)
    # Clean up whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Decode HTML entities
    text = text.replace("&amp;", "&")
    text = text.replace("&lt;", "<")
    text = text.replace("&gt;", ">")
    text = text.replace("&quot;", '"')
    text = text.replace("&#39;", "'")
    text = text.replace("\u200b", "")  # zero-width space
    return text.strip()


# -- CLI group ----------------------------------------------------------------


@click.group()
@click.option(
    "--debug", is_flag=True, default=False, help="Enable debug logging."
)
@click.option(
    "-w",
    "--workspace",
    default=None,
    help="Workspace name to use (defaults to the default workspace).",
)
@click.pass_context
def cli(ctx: click.Context, debug: bool, workspace: str | None) -> None:
    """Slack User CLI — read and write Slack from your terminal."""
    level = logging.DEBUG if debug else logging.WARNING
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")
    # Resolve and store the active workspace name for cache keying
    ctx.ensure_object(dict)
    ctx.obj["workspace"] = workspace
    config = load_config()
    ctx.obj["workspace_name"] = _get_active_workspace(config, workspace)


# -- login --------------------------------------------------------------------


@cli.command()
@click.option(
    "--auto",
    "mode",
    flag_value="auto",
    help="Extract credentials from Slack desktop app.",
)
@click.option(
    "--manual",
    "mode",
    flag_value="manual",
    help="Paste credentials from browser DevTools (one workspace).",
)
@click.option(
    "--browser",
    "mode",
    flag_value="browser",
    help="Paste localStorage JSON from browser to import all workspaces.",
)
@click.option(
    "--workspace-name",
    default=None,
    help="Name for this workspace (manual mode only).",
)
def login(mode: str | None, workspace_name: str | None) -> None:
    """Authenticate with Slack using session credentials.

    Three modes:
      --auto     Extract from Slack desktop app (all workspaces).
      --browser  Paste browser localStorage JSON (all workspaces).
      --manual   Paste a single xoxc- token + d cookie.
    """
    if mode is None:
        mode = "auto"

    config = load_config()
    config.setdefault("workspaces", {})

    if mode == "auto":
        _login_auto(config)
    elif mode == "browser":
        _login_browser(config)
    else:
        _login_manual(config, workspace_name)

    save_config(config)

    # Show summary of all workspaces
    ws_count = len(config.get("workspaces", {}))
    default = config.get("default", "")
    if ws_count > 1:
        console.print(
            f"\n[bold]{ws_count} workspaces saved.[/] "
            f"Default: [cyan]{default}[/]"
        )
        console.print(
            "[dim]Use -w <name> to switch, or 'workspaces' to list all.[/]"
        )


def _patch_pycookiecheat_macos_slack_bugs() -> None:
    """Work around two macOS bugs in pycookiecheat (<=0.8.0) when reading Slack's
    cookie store, both upstream in pycookiecheat rather than in slacktokens.

    1. It always looks up the Keychain entry under the account name
       "Slack App Store Key", but direct-download installs of Slack (not from
       the Mac App Store) use the account name "Slack Key" instead.
    2. Its App-Store-vs-direct-download cookie file detection never expands
       "~" before calling `.exists()`, so the check is always False and it
       always falls back to the App Store container path — even when the
       default-location Cookies file is right there.

    Only engages if the unpatched lookup actually fails, so this is a no-op
    once/if pycookiecheat fixes it upstream.
    """
    try:
        import keyring
        from pycookiecheat import chrome as _chrome
        from pycookiecheat.common import BrowserType
    except ImportError:
        return

    original_get_macos_config = _chrome.get_macos_config

    def patched_get_macos_config(browser):
        if browser is not BrowserType.SLACK:
            return original_get_macos_config(browser)
        try:
            return original_get_macos_config(browser)
        except ValueError:
            key_material = keyring.get_password("Slack Safe Storage", "Slack Key")
            if key_material is None:
                raise
            app_support = Path("Library/Application Support")
            cookie_file = Path("~") / app_support / "Slack/Cookies"
            if not cookie_file.expanduser().exists():
                cookie_file = (
                    Path("~/Library/Containers/com.tinyspeck.slackmacgap/Data")
                    / app_support
                    / "Slack/Cookies"
                )
            return {
                "key_material": key_material,
                "iterations": 1003,
                "cookie_file": cookie_file,
            }

    _chrome.get_macos_config = patched_get_macos_config


def _login_auto(config: dict) -> None:
    """Extract credentials from Slack desktop app via slacktokens."""
    try:
        from slacktokens import get_tokens_and_cookie  # noqa: PLC0415
    except ImportError as exc:
        raise click.ClickException(
            "slacktokens not available. Use --manual or --browser instead."
        ) from exc

    _patch_pycookiecheat_macos_slack_bugs()

    console.print(
        "[yellow]Extracting credentials from Slack desktop app…[/]"
    )
    console.print(
        "[dim]Note: close Slack desktop first (LevelDB lock) "
        "and allow Keychain access when prompted.[/]"
    )
    result = get_tokens_and_cookie()

    # slacktokens returns cookie as {'name': 'd', 'value': str}
    raw_cookie = result.get("cookie") or {}
    cookie = (
        raw_cookie.get("value", "")
        if isinstance(raw_cookie, dict)
        else str(raw_cookie)
    )
    config["cookie"] = cookie

    # slacktokens returns tokens as
    # {workspace_url: {'token': str, 'name': str}, ...}
    raw_tokens = result.get("tokens") or {}
    tokens = {
        v.get("name", k): v.get("token", "")
        for k, v in raw_tokens.items()
        if isinstance(v, dict) and v.get("token")
    }
    if not tokens:
        raise click.ClickException(
            "No tokens found. Is Slack desktop installed and logged in?"
        )

    _validate_and_save_tokens(config, tokens, cookie)


def _get_cookie_auto_or_prompt(config: dict) -> str:
    """Try to extract the d cookie from the Slack desktop app, fall back to prompt.

    The d cookie expires frequently and is httpOnly (can't be read via JS).
    The Slack desktop app stores it locally, so we try that first.
    """
    try:
        from slacktokens import get_cookie  # noqa: PLC0415

        _patch_pycookiecheat_macos_slack_bugs()

        console.print(
            "[yellow]Extracting d cookie from Slack desktop app…[/]"
        )
        result = get_cookie()
        # get_cookie returns either a dict with 'value' key or a string
        cookie = (
            result.get("value", result)
            if isinstance(result, dict)
            else str(result)
        )
        if cookie:
            console.print("[green]Got d cookie from desktop app[/]")
            return cookie
    except Exception as exc:
        logger.debug("Could not extract cookie from desktop app: %s", exc)

    # Fall back to manual prompt
    existing_cookie = config.get("cookie", "")
    if existing_cookie:
        console.print(
            "[yellow]Could not auto-extract d cookie. "
            "Press Enter to reuse stored cookie, or paste a new one.[/]"
        )
        console.print(
            "[dim]Get it from: browser DevTools → Application "
            "→ Cookies → app.slack.com → 'd'[/]"
        )
        return click.prompt(
            "Paste d cookie value (xoxd-…)",
            default=existing_cookie,
            show_default=False,
        )

    console.print(
        "[yellow]Get your d cookie from: browser DevTools → Application "
        "→ Cookies → app.slack.com → 'd'[/]"
    )
    return click.prompt("Paste d cookie value (xoxd-…)")


def _login_browser(config: dict) -> None:
    """Import all workspaces from browser localStorage JSON.

    The user pastes the output of:
        JSON.stringify(JSON.parse(localStorage.localConfig_v2))
    from browser DevTools. We extract every team's token from it.
    """
    # JS snippet that copies the result to clipboard automatically
    js_snippet = (
        "copy(JSON.stringify(JSON.parse(localStorage.localConfig_v2)))"
    )
    console.print(
        "[yellow]Run this in your browser DevTools console:[/]"
    )
    console.print(f"[bold]{js_snippet}[/]")
    click.prompt("Press Enter when copied", default="", show_default=False)

    # Read directly from macOS clipboard to avoid terminal paste truncation
    try:
        result = subprocess.run(
            ["pbpaste"], capture_output=True, text=True, check=True
        )
        raw = result.stdout
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        raise click.ClickException(
            "Failed to read clipboard. Paste the JSON manually with "
            "'pbpaste | slack_user_cli login --browser-stdin'"
        ) from exc

    if not raw.strip():
        raise click.ClickException("Clipboard is empty.")

    try:
        local_config = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise click.ClickException(f"Invalid JSON: {exc}") from exc

    teams = local_config.get("teams", {})
    if not teams:
        raise click.ClickException("No teams found in the pasted JSON.")

    # Extract tokens keyed by team name
    tokens: dict[str, str] = {}
    for _team_id, team_data in teams.items():
        name = team_data.get("name", team_data.get("team_name", _team_id))
        token = team_data.get("token", "")
        if token:
            tokens[name] = token

    if not tokens:
        raise click.ClickException("No tokens found in the pasted JSON.")

    # Try to auto-extract d cookie from the Slack desktop app first
    cookie = _get_cookie_auto_or_prompt(config)
    config["cookie"] = cookie

    _validate_and_save_tokens(config, tokens, cookie)


def _login_manual(config: dict, workspace_name: str | None) -> None:
    """Login with a single manually-pasted token + cookie."""
    token = click.prompt("Paste xoxc- token")
    cookie = click.prompt("Paste d cookie value (xoxd-…)")
    config["cookie"] = cookie

    client = WebClient(token=token, headers={"cookie": f"d={cookie}"})
    try:
        resp = client.auth_test()
    except SlackApiError as exc:
        raise click.ClickException(
            f"Auth validation failed: {exc.response['error']}"
        ) from exc

    team = workspace_name or resp.get("team", "default")
    user = resp.get("user", "")
    config["workspaces"][team] = {
        "token": token,
        "team": team,
        "user": user,
    }
    if len(config["workspaces"]) == 1:
        config["default"] = team

    console.print(
        f"[green]Logged in as [bold]{user}[/bold] "
        f"in [bold]{team}[/bold][/]"
    )


def _validate_and_save_tokens(
    config: dict, tokens: dict[str, str], cookie: str
) -> None:
    """Validate each token with auth.test and save to config.

    If all tokens fail with invalid_auth, the d cookie is likely expired.
    Prompts for a fresh cookie and retries once before giving up.
    """
    validated, cookie = _try_validate_tokens(config, tokens, cookie)

    # All failed — likely an expired d cookie, retry with a fresh one
    if not validated:
        console.print(
            "\n[yellow]All workspaces failed authentication. "
            "The d cookie is likely expired.[/]"
        )
        console.print(
            "[yellow]Get a fresh one: browser DevTools → Application "
            "→ Cookies → app.slack.com → 'd'[/]"
        )
        cookie = click.prompt("Paste new d cookie value (xoxd-…)")
        config["cookie"] = cookie
        validated, cookie = _try_validate_tokens(config, tokens, cookie)

    if not validated:
        raise click.ClickException(
            "No workspaces could be validated. Check your tokens and cookie."
        )


def _try_validate_tokens(
    config: dict, tokens: dict[str, str], cookie: str
) -> tuple[bool, str]:
    """Attempt to validate all tokens against the Slack API.

    Returns (any_succeeded, cookie) so the caller can retry if needed.
    """
    validated_teams: list[str] = []
    for ws_name, token in tokens.items():
        client = WebClient(
            token=token, headers={"cookie": f"d={cookie}"}
        )
        try:
            resp = client.auth_test()
        except SlackApiError as exc:
            error = exc.response.get("error", str(exc))
            console.print(
                f"[red]Skipping {ws_name}: {error}[/]"
            )
            continue

        team = resp.get("team", ws_name)
        user = resp.get("user", "")
        config["workspaces"][team] = {
            "token": token,
            "team": team,
            "user": user,
        }
        validated_teams.append(team)
        console.print(
            f"[green]Logged in as [bold]{user}[/bold] "
            f"in [bold]{team}[/bold][/]"
        )

    if validated_teams and "default" not in config:
        config["default"] = _choose_default(validated_teams)

    return (bool(validated_teams), cookie)


def _choose_default(teams: list[str]) -> str:
    """Pick the default workspace out of teams just logged in.

    With one workspace there's nothing to choose. With several, ask —
    but only when attached to a real terminal; a non-interactive/scripted
    invocation has no one to ask, so it keeps the old first-wins behavior.
    """
    if len(teams) == 1 or not sys.stdin.isatty():
        return teams[0]

    console.print("\n[bold]Which workspace should be the default?[/]")
    for i, team in enumerate(teams, 1):
        console.print(f"  {i}. {team}")
    choice = click.prompt("Enter a number", default="1", show_default=True)
    try:
        return teams[int(choice) - 1]
    except (ValueError, IndexError):
        return teams[0]


# -- whoami -------------------------------------------------------------------


@cli.command()
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    default=False,
    help="Emit structured JSON.",
)
@click.pass_context
def whoami(ctx: click.Context, as_json: bool) -> None:
    """Show the identity behind the active workspace's credentials.

    Hits auth.test rather than reading the stored 'user' field, so the output
    doubles as a liveness check: it fails exactly when the token or d cookie
    has expired.
    """
    client = get_client(workspace=ctx.obj["workspace"])
    try:
        resp = client.auth_test()
    except SlackApiError as exc:
        error = exc.response.get("error", str(exc))
        raise click.ClickException(
            f"Credentials rejected ({error}). Run 'login' to refresh them."
        ) from exc

    info = {
        "workspace": ctx.obj["workspace_name"],
        "user": resp.get("user", ""),
        "user_id": resp.get("user_id", ""),
        "team": resp.get("team", ""),
        "team_id": resp.get("team_id", ""),
        "url": resp.get("url", ""),
    }

    if as_json:
        click.echo(json.dumps(info, ensure_ascii=False))
        return

    table = Table(title="Identity")
    table.add_column("Field", style="cyan")
    table.add_column("Value")
    for field, value in info.items():
        table.add_row(field, value)

    console.print(table)


# -- workspaces ---------------------------------------------------------------


@cli.command()
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    default=False,
    help="Emit structured JSON.",
)
def workspaces(as_json: bool) -> None:
    """List all saved workspaces."""
    config = load_config()
    ws_map = config.get("workspaces", {})
    default = config.get("default", "")

    if not ws_map:
        raise click.ClickException("No workspaces saved. Run 'login' first.")

    if as_json:
        out = [
            {
                "name": name,
                "user": ws.get("user", ""),
                "is_default": name == default,
            }
            for name, ws in ws_map.items()
        ]
        click.echo(
            json.dumps(
                {"default": default, "workspaces": out}, ensure_ascii=False
            )
        )
        return

    table = Table(title="Workspaces")
    table.add_column("Name", style="cyan")
    table.add_column("User")
    table.add_column("Default")

    for name, ws in ws_map.items():
        is_default = "yes" if name == default else ""
        table.add_row(name, ws.get("user", ""), is_default)

    console.print(table)
    console.print("[dim]Use -w <name> to switch workspace for a command.[/]")


@cli.command()
@click.argument("name")
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    default=False,
    help="Emit structured JSON.",
)
def default(name: str, as_json: bool) -> None:
    """Set the default workspace."""
    config = load_config()
    ws_map = config.get("workspaces", {})
    if name not in ws_map:
        available = ", ".join(ws_map.keys())
        raise click.ClickException(
            f"Workspace '{name}' not found. Available: {available}"
        )
    config["default"] = name
    save_config(config)
    if as_json:
        click.echo(json.dumps({"ok": True, "default": name}, ensure_ascii=False))
    else:
        console.print(f"[green]Default workspace set to [bold]{name}[/bold][/]")


@cli.command()
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    default=False,
    help="Emit structured JSON.",
)
@click.pass_context
def refresh(ctx: click.Context, as_json: bool) -> None:
    """Force-refresh the channel and user cache for the active workspace."""
    client = get_client(workspace=ctx.obj["workspace"])
    ws = ctx.obj["workspace_name"]

    if not as_json:
        console.print(f"[yellow]Refreshing cache for {ws}…[/]")
    ch_map = build_channel_cache(client, ws)
    user_data = build_user_cache(client, ws)
    user_count = len(user_data.get("id_to_display", {}))
    if as_json:
        click.echo(
            json.dumps(
                {
                    "ok": True,
                    "workspace": ws,
                    "channels": len(ch_map),
                    "users": user_count,
                },
                ensure_ascii=False,
            )
        )
    else:
        console.print(f"  Cached [bold]{len(ch_map)}[/] channels")
        console.print(f"  Cached [bold]{user_count}[/] users")
        console.print("[green]Cache refreshed.[/]")


@cli.command()
@click.argument("ids", nargs=-1, required=True)
@click.option("--json", "as_json", is_flag=True, default=False, help="Emit structured JSON.")
@click.pass_context
def resolve(ctx: click.Context, ids: tuple[str, ...], as_json: bool) -> None:
    """Resolve user (U…) and channel (C…/G…) IDs to names.

    Backed by the never-expiring id→name store, so each ID costs one API call
    the first time and none thereafter. Use this to name an ID instead of
    guessing it from context.
    """
    client = get_client(workspace=ctx.obj["workspace"])
    ws = ctx.obj["workspace_name"]

    out: dict[str, str] = {}
    for _id in ids:
        if _id[:1] == "U":
            out[_id] = resolve_user(client, _id, ws)
        elif _id[:1] in ("C", "G"):
            out[_id] = resolve_channel_name(client, _id, ws)
        else:
            out[_id] = _id  # DMs (D…) and unknown prefixes have no channel name

    if as_json:
        click.echo(json.dumps({"resolved": out}, ensure_ascii=False))
    else:
        for _id, name in out.items():
            mark = "" if name != _id else "  [dim](unresolved)[/]"
            console.print(f"{_id} → [bold]{name}[/]{mark}")


# -- channels -----------------------------------------------------------------


@cli.command()
@click.option(
    "--type",
    "channel_types",
    default="public_channel,private_channel",
    help="Comma-separated channel types to list.",
)
@click.option(
    "--all",
    "show_all",
    is_flag=True,
    default=False,
    help="Show all visible channels, not just joined ones.",
)
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    default=False,
    help="Emit structured JSON.",
)
@click.option(
    "--names",
    "with_names",
    is_flag=True,
    default=False,
    help="Show channel names in the primary column. Default shows raw IDs.",
)
@click.pass_context
def channels(
    ctx: click.Context,
    channel_types: str,
    show_all: bool,
    as_json: bool,
    with_names: bool,
) -> None:
    """List joined channels (use --all to include unjoined)."""
    client = get_client(workspace=ctx.obj["workspace"])

    collected: list[dict] = []
    cursor = None
    while True:
        kwargs: dict = {"types": channel_types, "limit": 200}
        if cursor:
            kwargs["cursor"] = cursor
        try:
            resp = client.conversations_list(**kwargs)
        except SlackApiError as exc:
            raise click.ClickException(str(exc)) from exc

        for ch in resp["channels"]:
            # Skip channels the user hasn't joined unless --all
            if not show_all and not ch.get("is_member"):
                continue
            collected.append(ch)

        cursor = resp.get("response_metadata", {}).get("next_cursor")
        if not cursor:
            break

    if as_json:
        out = [
            {
                "id": ch["id"],
                "name": ch.get("name", ""),
                "type": _channel_type_label(ch),
                "num_members": ch.get("num_members", 0),
                "topic": ch.get("topic", {}).get("value", ""),
                "is_member": bool(ch.get("is_member")),
            }
            for ch in collected
        ]
        click.echo(json.dumps({"channels": out}, ensure_ascii=False))
        return

    table = Table(title="Channels")
    table.add_column("ID" if not with_names else "Name", style="cyan")
    table.add_column("Type", style="magenta")
    table.add_column("Members", justify="right")
    table.add_column("Topic")

    for ch in collected:
        ch_type = _channel_type_label(ch)
        topic = ch.get("topic", {}).get("value", "")
        if len(topic) > 60:
            topic = topic[:57] + "…"
        primary = ch.get("name", ch["id"]) if with_names else ch["id"]
        table.add_row(
            primary,
            ch_type,
            str(ch.get("num_members", "")),
            topic,
        )

    console.print(table)


def _channel_type_label(ch: dict) -> str:
    """Derive a human-readable type label from channel metadata."""
    if ch.get("is_im"):
        return "DM"
    if ch.get("is_mpim"):
        return "Group DM"
    if ch.get("is_private"):
        return "Private"
    return "Public"


# -- read ---------------------------------------------------------------------


@cli.command()
@click.argument("channel")
@click.option("--limit", default=20, help="Number of messages to show.")
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    default=False,
    help="Emit structured JSON instead of human-readable output. "
    "Intended for programmatic consumers (e.g. smithers workflows) that "
    "would otherwise have to parse the rendered text back into fields.",
)
@click.option(
    "--names",
    "with_names",
    is_flag=True,
    default=False,
    help="Resolve user IDs to display names (and rewrite <@UXXX> mentions). "
    "Default emits raw IDs so output is stable for scripts.",
)
@click.option(
    "--expand-thread",
    is_flag=True,
    default=False,
    help="For every returned message that started a thread, also fetch its "
    "replies and attach them inline under `replies`. Only meaningful with "
    "--json. Decisions often live in replies rather than the parent post; "
    "without this flag consumers only see parent messages.",
)
@click.option(
    "--since",
    default=None,
    help="Only fetch messages at/after this time, as an ISO date "
    "(2026-05-29) or datetime (2026-05-29T10:07:00); naive values are "
    "treated as UTC. Sets the history `oldest` bound. Pair with a larger "
    "--limit to pull a whole window rather than the default 20.",
)
@click.pass_context
def read(
    ctx: click.Context,
    channel: str,
    limit: int,
    as_json: bool,
    with_names: bool,
    expand_thread: bool,
    since: str | None,
) -> None:
    """Read recent messages from a channel."""
    client = get_client(workspace=ctx.obj["workspace"])
    ws = ctx.obj["workspace_name"]
    channel_id = resolve_channel(client, channel, workspace=ws)

    oldest = _parse_since(since) if since else None

    messages: list[dict] = []
    cursor = None
    while len(messages) < limit:
        kwargs: dict = {
            "channel": channel_id,
            "limit": min(limit - len(messages), 200),
        }
        if oldest:
            kwargs["oldest"] = oldest
        if cursor:
            kwargs["cursor"] = cursor
        try:
            resp = client.conversations_history(**kwargs)
        except SlackApiError as exc:
            raise click.ClickException(str(exc)) from exc

        messages.extend(resp.get("messages", []))
        cursor = resp.get("response_metadata", {}).get("next_cursor")
        if not cursor:
            break

    # Messages come newest-first; reverse for chronological display
    messages = messages[:limit]
    messages.reverse()

    # Expand threads *before* emitting. We stash replies on the message dict
    # itself so both renderers can access them alongside the parent; the key
    # is underscore-prefixed to avoid clashing with any Slack field.
    if expand_thread:
        for msg in messages:
            ts = msg.get("ts", "")
            if msg.get("thread_ts") and msg.get("reply_count", 0) and ts:
                msg["_replies"] = _fetch_thread_replies(client, channel_id, ts)

    if as_json:
        _emit_messages_json(
            client, channel, messages, workspace=ws, with_names=with_names
        )
    else:
        _print_messages(client, messages, workspace=ws, with_names=with_names)


def _fetch_thread_replies(
    client: WebClient, channel_id: str, parent_ts: str, max_replies: int = 200
) -> list[dict]:
    """Fetch reply messages for a thread, excluding the parent itself.

    `conversations.replies` always returns the parent as the first message;
    we drop it because callers already have the parent from the top-level
    history fetch. Errors are swallowed so one broken thread doesn't fail
    the whole read — expansion is best-effort.
    """
    all_msgs: list[dict] = []
    cursor = None
    try:
        while len(all_msgs) < max_replies + 1:  # +1 for the parent
            kwargs: dict = {
                "channel": channel_id,
                "ts": parent_ts,
                "limit": min(max_replies + 1 - len(all_msgs), 200),
            }
            if cursor:
                kwargs["cursor"] = cursor
            resp = client.conversations_replies(**kwargs)
            all_msgs.extend(resp.get("messages", []))
            cursor = resp.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break
    except SlackApiError:
        return []

    # Drop the parent (index 0 when present); keep chronological order.
    return [m for m in all_msgs if m.get("ts") != parent_ts][:max_replies]


# -- thread -------------------------------------------------------------------


@cli.command()
@click.argument("channel")
@click.argument("ts")
@click.option("--limit", default=50, help="Number of replies to show.")
@click.option("--dm", "is_dm", is_flag=True, default=False, help="Treat CHANNEL as a user name and resolve to DM channel.")
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    default=False,
    help="Emit structured JSON.",
)
@click.option(
    "--names",
    "with_names",
    is_flag=True,
    default=False,
    help="Resolve user IDs to display names. Default emits raw IDs.",
)
@click.pass_context
def thread(
    ctx: click.Context,
    channel: str,
    ts: str,
    limit: int,
    is_dm: bool,
    as_json: bool,
    with_names: bool,
) -> None:
    """Read thread replies for a given message timestamp."""
    client = get_client(workspace=ctx.obj["workspace"])
    ws = ctx.obj["workspace_name"]

    if is_dm:
        # Resolve user name to DM channel
        user_id = channel
        if not (channel.startswith("U") and channel[1:].isalnum()):
            user_id = _resolve_user_by_name(client, channel, workspace=ws)
        try:
            resp = client.conversations_open(users=[user_id])
        except SlackApiError as exc:
            raise click.ClickException(str(exc)) from exc
        channel_id = resp["channel"]["id"]
    else:
        channel_id = resolve_channel(client, channel, workspace=ws)

    replies: list[dict] = []
    cursor = None
    while len(replies) < limit:
        kwargs: dict = {
            "channel": channel_id,
            "ts": ts,
            "limit": min(limit - len(replies), 200),
        }
        if cursor:
            kwargs["cursor"] = cursor
        try:
            resp = client.conversations_replies(**kwargs)
        except SlackApiError as exc:
            raise click.ClickException(str(exc)) from exc

        replies.extend(resp.get("messages", []))
        cursor = resp.get("response_metadata", {}).get("next_cursor")
        if not cursor:
            break

    replies = replies[:limit]
    if as_json:
        _emit_messages_json(
            client, channel, replies, workspace=ws, with_names=with_names
        )
    else:
        _print_messages(client, replies, workspace=ws, with_names=with_names)


# -- url (permalink reader) ---------------------------------------------------


@cli.command(name="url")
@click.argument("slack_url")
@click.option("--limit", default=50, help="Number of messages to show.")
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    default=False,
    help="Emit structured JSON.",
)
@click.option(
    "--names",
    "with_names",
    is_flag=True,
    default=False,
    help="Resolve user IDs to display names. Default emits raw IDs.",
)
@click.pass_context
def url_command(
    ctx: click.Context,
    slack_url: str,
    limit: int,
    as_json: bool,
    with_names: bool,
) -> None:
    """Read a Slack thread from a permalink URL.

    Parses a Slack permalink and fetches the thread (or surrounding context
    for standalone messages). This lets agents read threads directly from
    pasted URLs without manual channel/ts extraction.
    """
    _workspace, channel_id, message_ts = parse_slack_url(slack_url)
    client = get_client(workspace=ctx.obj["workspace"])
    ws = ctx.obj["workspace_name"]

    # Try fetching as a thread first
    replies: list[dict] = []
    cursor = None
    while len(replies) < limit:
        kwargs: dict = {
            "channel": channel_id,
            "ts": message_ts,
            "limit": min(limit - len(replies), 200),
        }
        if cursor:
            kwargs["cursor"] = cursor
        try:
            resp = client.conversations_replies(**kwargs)
        except SlackApiError as exc:
            raise click.ClickException(str(exc)) from exc

        replies.extend(resp.get("messages", []))
        cursor = resp.get("response_metadata", {}).get("next_cursor")
        if not cursor:
            break

    replies = replies[:limit]
    if as_json:
        _emit_messages_json(
            client, slack_url, replies, workspace=ws, with_names=with_names
        )
    else:
        _print_messages(client, replies, workspace=ws, with_names=with_names)


# -- download -----------------------------------------------------------------


@cli.command()
@click.argument("target")
@click.argument("ts", required=False)
@click.option(
    "--output",
    "-o",
    "output",
    default="slack-downloads",
    help="Directory to save files into (default: ./slack-downloads).",
)
@click.option(
    "--list",
    "list_only",
    is_flag=True,
    default=False,
    help="List attachments without downloading them.",
)
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    default=False,
    help="Emit structured JSON ({files: [...], downloaded: [...]}).",
)
@click.pass_context
def download(
    ctx: click.Context,
    target: str,
    ts: str | None,
    output: str,
    list_only: bool,
    as_json: bool,
) -> None:
    """Download file attachments from a message (or a file ID).

    TARGET may be a Slack permalink, a channel name/ID (then pass TS), or a
    file ID (starts with F). Files are saved into --output. Use --list to only
    enumerate the attachments. The plain `read`/`url`/`thread` commands also
    now surface a `files` array (JSON) and a 📎 line (text) so you can spot
    attachments before fetching them.
    """
    client = get_client(workspace=ctx.obj["workspace"])
    ws = ctx.obj["workspace_name"]

    files: list[dict] = []
    if ts is None and re.fullmatch(r"F[A-Z0-9]+", target):
        # A bare file ID — resolve it directly via files.info.
        try:
            resp = client.api_call("files.info", params={"file": target})
        except SlackApiError as exc:
            raise click.ClickException(str(exc)) from exc
        file_obj = resp.get("file") or {}
        if file_obj:
            files = [file_obj]
    else:
        # A permalink, or a channel + ts pair.
        if "slack.com/archives/" in target:
            _ws, channel_id, message_ts = parse_slack_url(target)
        else:
            if not ts:
                raise click.ClickException(
                    "Provide a message TS after the channel, or pass a Slack "
                    "permalink / a file ID (starts with F)."
                )
            channel_id = resolve_channel(client, target, workspace=ws)
            message_ts = ts
        try:
            resp = client.conversations_replies(
                channel=channel_id, ts=message_ts, limit=50
            )
        except SlackApiError as exc:
            raise click.ClickException(str(exc)) from exc
        msgs = resp.get("messages", [])
        # Prefer the exact message; fall back to scanning the thread so a
        # root-ts that returns its whole thread still yields its own files.
        match = next((m for m in msgs if m.get("ts") == message_ts), None)
        # _collect_raw_files pulls direct uploads *and* files from a quoted /
        # shared message, so downloading a message that forwards another still
        # fetches the original's attachments.
        for m in [match] if match else msgs:
            files.extend(_collect_raw_files(m or {}))

    listing = _extract_files({"files": files})
    if not listing:
        if as_json:
            click.echo(json.dumps({"files": [], "downloaded": []}))
        else:
            console.print("[yellow]No file attachments found.[/]")
        return

    if list_only:
        if as_json:
            click.echo(json.dumps({"files": listing}, ensure_ascii=False))
        else:
            for f in listing:
                kind = f["filetype"] or f["mimetype"] or "file"
                size = f", {f['size']} bytes" if f.get("size") else ""
                # Build with Text so the metadata isn't parsed as Rich markup
                # (bare square brackets would be swallowed as style tags).
                fl = Text("📎 ", style="cyan")
                fl.append(f["name"], style="cyan")
                fl.append(f" ({kind}{size})", style="dim")
                fl.append(f"  id={f['id']}", style="dim")
                console.print(fl)
        return

    dest = Path(output)
    saved: list[str] = []
    for f in files:
        path = _download_file(client, f, dest)
        saved.append(str(path))
        if not as_json:
            console.print(f"[green]saved[/] {path} ({len(path.read_bytes())} bytes)")
    if as_json:
        click.echo(
            json.dumps({"files": listing, "downloaded": saved}, ensure_ascii=False)
        )


# -- permalink ----------------------------------------------------------------


@cli.command()
@click.argument("channel")
@click.argument("ts", nargs=-1, required=True)
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    default=False,
    help="Emit structured JSON ({channel, permalinks: {ts: url}}).",
)
@click.pass_context
def permalink(
    ctx: click.Context, channel: str, ts: tuple[str, ...], as_json: bool
) -> None:
    """Get canonical chat.getPermalink URL(s) for one or more message TS.

    Pass a channel (name or ID) and one or more message timestamps (the
    full-precision `raw_ts` from `read --json`). Unlike a hand-built
    `/p<ts>` URL, the returned permalink is thread-aware — it carries the
    `thread_ts`/`cid` query params a threaded reply needs to navigate, so
    it resolves correctly for replies, not just root messages.
    """
    client = get_client(workspace=ctx.obj["workspace"])
    ws = ctx.obj["workspace_name"]
    channel_id = resolve_channel(client, channel, workspace=ws)

    results: dict[str, str] = {}
    for message_ts in ts:
        try:
            resp = client.chat_getPermalink(
                channel=channel_id, message_ts=message_ts
            )
            results[message_ts] = resp.get("permalink", "")
        except SlackApiError as exc:
            # Record the error against this ts rather than aborting the batch
            # so one bad ts doesn't lose the permalinks for the rest.
            err = (exc.response.data or {}).get("error", str(exc))
            results[message_ts] = f"ERROR: {err}"

    if as_json:
        click.echo(
            json.dumps(
                {"channel": channel_id, "permalinks": results}, ensure_ascii=False
            )
        )
    else:
        for message_ts, url in results.items():
            console.print(f"{message_ts}\t{url}")


# -- users --------------------------------------------------------------------


@cli.command()
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    default=False,
    help="Emit structured JSON.",
)
@click.option(
    "--names",
    "with_names",
    is_flag=True,
    default=False,
    help="Show display names in the primary column. Default shows raw IDs.",
)
@click.pass_context
def users(ctx: click.Context, as_json: bool, with_names: bool) -> None:
    """List workspace members."""
    client = get_client(workspace=ctx.obj["workspace"])

    members: list[dict] = []
    cursor = None
    while True:
        kwargs: dict = {"limit": 200}
        if cursor:
            kwargs["cursor"] = cursor
        try:
            resp = client.users_list(**kwargs)
        except SlackApiError as exc:
            raise click.ClickException(str(exc)) from exc

        for member in resp["members"]:
            # Skip bots and deactivated users for cleaner output
            if member.get("is_bot") or member.get("deleted"):
                continue
            members.append(member)

        cursor = resp.get("response_metadata", {}).get("next_cursor")
        if not cursor:
            break

    if as_json:
        out = []
        for member in members:
            profile = member.get("profile", {})
            out.append({
                "id": member.get("id", ""),
                "name": member.get("name", ""),
                "display_name": profile.get("display_name", ""),
                "real_name": profile.get("real_name", ""),
                "status_emoji": profile.get("status_emoji", ""),
                "status_text": profile.get("status_text", ""),
            })
        click.echo(json.dumps({"users": out}, ensure_ascii=False))
        return

    table = Table(title="Users")
    table.add_column("ID" if not with_names else "Display Name", style="cyan")
    table.add_column("Username")
    table.add_column("Real Name")
    table.add_column("Status")

    for member in members:
        profile = member.get("profile", {})
        primary = (
            (profile.get("display_name") or member.get("name", ""))
            if with_names
            else member.get("id", "")
        )
        username = member.get("name", "")
        real = profile.get("real_name", "")
        status_emoji = profile.get("status_emoji", "")
        status_text = profile.get("status_text", "")
        status = f"{status_emoji} {status_text}".strip()
        table.add_row(primary, username, real, status)

    console.print(table)


# -- user-channels ------------------------------------------------------------


@cli.command(name="user-channels")
@click.argument("user")
@click.option(
    "--type",
    "channel_types",
    default="public_channel,private_channel",
    help="Comma-separated channel types to list.",
)
@click.option(
    "--plain",
    is_flag=True,
    default=False,
    help="Output one channel ID (or name with --names) per line.",
)
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    default=False,
    help="Emit structured JSON.",
)
@click.option(
    "--names",
    "with_names",
    is_flag=True,
    default=False,
    help="Show channel names (and resolve the user header). Default shows raw IDs.",
)
@click.pass_context
def user_channels(
    ctx: click.Context,
    user: str,
    channel_types: str,
    plain: bool,
    as_json: bool,
    with_names: bool,
) -> None:
    """List channels a user is a member of."""
    client = get_client(workspace=ctx.obj["workspace"])
    ws = ctx.obj["workspace_name"]

    # Resolve user name to ID if needed
    user_id = user
    if not (user.startswith("U") and user[1:].isalnum()):
        user_id = _resolve_user_by_name(client, user, workspace=ws)

    # Collect all channels first so both formats can use the same data
    channels_list: list[dict] = []
    cursor = None
    while True:
        kwargs: dict = {"user": user_id, "types": channel_types, "limit": 200}
        if cursor:
            kwargs["cursor"] = cursor
        try:
            resp = client.users_conversations(**kwargs)
        except SlackApiError as exc:
            raise click.ClickException(str(exc)) from exc

        channels_list.extend(resp["channels"])
        cursor = resp.get("response_metadata", {}).get("next_cursor")
        if not cursor:
            break

    if as_json:
        out = [
            {
                "id": ch["id"],
                "name": ch.get("name", ""),
                "type": _channel_type_label(ch),
                "num_members": ch.get("num_members", 0),
                "topic": ch.get("topic", {}).get("value", ""),
            }
            for ch in channels_list
        ]
        click.echo(
            json.dumps({"user": user_id, "channels": out}, ensure_ascii=False)
        )
        return

    if plain:
        for ch in channels_list:
            click.echo(ch.get("name", ch["id"]) if with_names else ch["id"])
        return

    header = (
        resolve_user(client, user_id, workspace=ws) if with_names else user_id
    )
    table = Table(title=f"Channels for {header}")
    table.add_column("ID" if not with_names else "Name", style="cyan")
    table.add_column("Type", style="magenta")
    table.add_column("Members", justify="right")
    table.add_column("Topic")

    for ch in channels_list:
        ch_type = _channel_type_label(ch)
        topic = ch.get("topic", {}).get("value", "")
        if len(topic) > 60:
            topic = topic[:57] + "…"
        primary = ch.get("name", ch["id"]) if with_names else ch["id"]
        table.add_row(
            primary,
            ch_type,
            str(ch.get("num_members", "")),
            topic,
        )

    console.print(table)


# -- send ---------------------------------------------------------------------


@cli.command()
@click.argument("channel")
@click.argument("message")
@click.option("--thread", "thread_ts", default=None, help="Reply in thread (message timestamp).")
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    default=False,
    help="Emit structured JSON.",
)
@click.pass_context
def send(
    ctx: click.Context,
    channel: str,
    message: str,
    thread_ts: str | None,
    as_json: bool,
) -> None:
    """Send a message to a channel. Use --thread to reply in a thread."""
    client = get_client(workspace=ctx.obj["workspace"])
    ws = ctx.obj["workspace_name"]
    channel_id = resolve_channel(client, channel, workspace=ws)

    kwargs: dict = {"channel": channel_id, "text": message}
    if thread_ts:
        kwargs["thread_ts"] = thread_ts

    try:
        resp = client.chat_postMessage(**kwargs)
    except SlackApiError as exc:
        raise click.ClickException(str(exc)) from exc

    ts = resp.get("ts", "")
    if as_json:
        click.echo(
            json.dumps(
                {"ok": True, "channel": channel_id, "ts": ts}, ensure_ascii=False
            )
        )
    else:
        console.print(f"[green]Message sent[/] (ts={ts})")


# -- click (block-kit interactive) -------------------------------------------


def _fetch_message(client: WebClient, channel: str, message_ts: str) -> dict:
    """Fetch a single message by exact ts.

    `inclusive=True` plus latest=oldest=ts returns just that one message.
    Slack only provides this lookup via conversations_history — there is no
    direct `messages.get` endpoint.
    """
    resp = client.conversations_history(
        channel=channel,
        latest=message_ts,
        oldest=message_ts,
        inclusive=True,
        limit=1,
    )
    msgs = resp.get("messages", []) or []
    if not msgs:
        raise click.ClickException(
            f"No message found at ts={message_ts} in channel {channel}."
        )
    return msgs[0]


def _select_action_element(
    msg: dict,
    option_text: str | None,
    option_index: int | None,
    action_id: str | None,
    value: str | None,
) -> tuple[dict, dict, dict | None]:
    """Locate the action element + (for radio/select) the chosen option.

    Returns (block, element, option_or_none). Lookup precedence is the most
    specific identifier first (action_id / value), then visible text, then
    1-based index across all action elements in the message.
    """
    candidates: list[tuple[dict, dict]] = []
    for block in msg.get("blocks", []) or []:
        if block.get("type") != "actions":
            continue
        for el in block.get("elements", []) or []:
            candidates.append((block, el))

    if not candidates:
        raise click.ClickException("Message has no actions block to click.")

    # 1. exact action_id wins
    if action_id:
        for block, el in candidates:
            if el.get("action_id") == action_id:
                # Match an option inside the element if given, otherwise None
                opt = _match_option(el, option_text=option_text, value=value)
                return block, el, opt
        raise click.ClickException(f"action_id {action_id!r} not found on message.")

    # 2. exact value matches a button.value or a radio/select option.value
    if value:
        for block, el in candidates:
            if el.get("type") == "button" and el.get("value") == value:
                return block, el, None
            opt = _match_option(el, value=value)
            if opt:
                return block, el, opt
        raise click.ClickException(f"value {value!r} not found on message.")

    # 3. visible text — match a button label or a radio/select option label
    if option_text:
        for block, el in candidates:
            if el.get("type") == "button" and (el.get("text") or {}).get("text") == option_text:
                return block, el, None
            opt = _match_option(el, option_text=option_text)
            if opt:
                return block, el, opt
        raise click.ClickException(
            f"Option text {option_text!r} not found. "
            "Use `read --json` to see available labels."
        )

    # 4. fallback to 1-based index across all action elements
    if option_index is not None:
        if option_index < 1 or option_index > len(candidates):
            raise click.ClickException(
                f"--index {option_index} out of range (1..{len(candidates)})."
            )
        block, el = candidates[option_index - 1]
        return block, el, None

    raise click.ClickException(
        "Specify which option to click via --option, --index, --action-id, or --value."
    )


def _match_option(el: dict, option_text: str | None = None, value: str | None = None) -> dict | None:
    """Return the radio/select option matching either label or value."""
    if el.get("type") not in ("radio_buttons", "static_select", "checkboxes"):
        return None
    for o in el.get("options", []) or []:
        if value is not None and o.get("value") == value:
            return o
        if option_text is not None and (o.get("text") or {}).get("text") == option_text:
            return o
    return None


def _build_action_payload(el: dict, block_id: str, option: dict | None) -> tuple[list[dict], dict]:
    """Build (`actions`, `state`) JSON values for the blocks.actions form.

    Captured from a real Slack web client request: `actions` is a list with
    one entry describing the click; `state` mirrors the chosen value back so
    Slack can pass it through to the receiving app's interactive handler.
    Buttons skip the state mirror (no persistent selection to remember).
    """
    el_type = el["type"]
    action_id = el["action_id"]

    if el_type == "button":
        action_entry = {
            "action_id": action_id,
            "block_id": block_id,
            "text": el.get("text") or {"type": "plain_text", "text": ""},
            "value": el.get("value", ""),
            "type": "button",
            "action_ts": f"{time.time():.6f}",
        }
        # Slack still expects a state object even when empty.
        state = {"values": {}}
        return [action_entry], state

    if el_type in ("radio_buttons", "static_select"):
        if not option:
            raise click.ClickException(
                f"{el_type} requires an option (use --option, --value, or --action-id with one of those)."
            )
        action_entry = {
            "action_id": action_id,
            "block_id": block_id,
            "selected_option": option,
            "type": el_type,
            "action_ts": f"{time.time():.6f}",
        }
        state = {
            "values": {
                block_id: {
                    action_id: {
                        "type": el_type,
                        "selected_option": option,
                    }
                }
            }
        }
        return [action_entry], state

    raise click.ClickException(
        f"Unsupported action element type {el_type!r}. "
        "Add support by extending _build_action_payload."
    )


def _dispatch_block_action(
    config: dict,
    workspace_name: str,
    channel_id: str,
    msg: dict,
    actions_payload: list[dict],
    state: dict,
    client: WebClient,
) -> dict:
    """POST to /api/blocks.actions exactly the way the Slack web client does.

    This is an internal Slack endpoint (not in the public Web API). The
    multipart form shape was reverse-engineered from a real button click
    captured in DevTools. `_x_*` fields are tracking metadata Slack tags on
    every request — included so the request looks indistinguishable from a
    browser dispatch.
    """
    import requests  # noqa: PLC0415 — local import keeps top-level deps narrow

    ws_cfg = config.get("workspaces", {}).get(workspace_name, {})
    token = ws_cfg.get("token", "")
    cookie = config.get("cookie", "")
    if not token or not cookie:
        raise click.ClickException("Not logged in. Run 'login' first.")

    # `service_team_id` must be the Slack team ID (e.g. TFM7VTADR), not the
    # workspace slug stored in our config. auth.test is the canonical source.
    auth = client.auth_test().data
    team_id = auth.get("team_id", "")

    bot_id = msg.get("bot_id", "")
    app_id = msg.get("app_id", "")
    if not bot_id or not app_id:
        raise click.ClickException(
            "Message has no bot_id/app_id — only bot messages with block kit are clickable."
        )

    container = {
        "type": "message",
        "message_ts": msg["ts"],
        "channel_id": channel_id,
        "is_ephemeral": bool(msg.get("subtype") == "ephemeral"),
    }

    form = {
        "token": token,
        "service_id": bot_id,
        "app_id": app_id,
        "service_team_id": team_id,
        "actions": json.dumps(actions_payload, ensure_ascii=False),
        "container": json.dumps(container, ensure_ascii=False),
        "client_token": f"web-{int(time.time() * 1000)}",
        "state": json.dumps(state, ensure_ascii=False),
        "_x_reason": "dispatch_action_to_developer",
        "_x_mode": "online",
        "_x_sonic": "true",
        "_x_app_name": "client",
    }

    # Multipart body without any files: requests' `files=` accepts (name, value)
    # tuples as form fields when value is `(None, str)`.
    multipart = {k: (None, v) for k, v in form.items()}

    url = f"https://slack.com/api/blocks.actions?slack_route={team_id}"
    headers = {"Cookie": f"d={cookie}"}
    r = requests.post(url, files=multipart, headers=headers, timeout=20)
    try:
        return r.json()
    except ValueError as exc:
        raise click.ClickException(
            f"Non-JSON response from blocks.actions: {r.status_code} {r.text[:200]}"
        ) from exc


@cli.command(name="click")
@click.argument("channel")
@click.argument("message_ts")
@click.option(
    "--option",
    "option_text",
    default=None,
    help="Pick by visible button/option label (e.g. 'A few seconds').",
)
@click.option(
    "--index",
    "option_index",
    type=int,
    default=None,
    help="Pick by 1-based index across all action elements in the message.",
)
@click.option(
    "--action-id",
    default=None,
    help="Pick by exact action_id (precise; pair with --option/--value for radios).",
)
@click.option(
    "--value",
    default=None,
    help="Pick by exact button.value or radio/select option.value.",
)
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    default=False,
    help="Emit structured JSON.",
)
@click.pass_context
def click_cmd(
    ctx: click.Context,
    channel: str,
    message_ts: str,
    option_text: str | None,
    option_index: int | None,
    action_id: str | None,
    value: str | None,
    as_json: bool,
) -> None:
    """Click a block-kit button or pick a radio option on a bot message.

    Use `read --json` to see available action_ids, button labels and option
    values on the target message. Pass either `--option`, `--index`,
    `--action-id`, or `--value` to identify which control to fire.
    """
    config = load_config()
    workspace_name = ctx.obj["workspace_name"]
    client = get_client(config=config, workspace=ctx.obj["workspace"])
    channel_id = resolve_channel(client, channel, workspace=workspace_name)
    msg = _fetch_message(client, channel_id, message_ts)
    block, el, option = _select_action_element(
        msg,
        option_text=option_text,
        option_index=option_index,
        action_id=action_id,
        value=value,
    )
    actions_payload, state = _build_action_payload(el, block["block_id"], option)
    resp = _dispatch_block_action(
        config=config,
        workspace_name=workspace_name,
        channel_id=channel_id,
        msg=msg,
        actions_payload=actions_payload,
        state=state,
        client=client,
    )
    if as_json:
        click.echo(json.dumps(resp, ensure_ascii=False))
    else:
        if resp.get("ok"):
            label = (
                option["text"]["text"] if option else (el.get("text") or {}).get("text", el["action_id"])
            )
            console.print(f"[green]Clicked[/]: {label!r} on ts={message_ts}")
        else:
            console.print(f"[red]Click failed[/]: {resp}")
            raise click.ClickException(resp.get("error", "unknown error"))


# -- upload -------------------------------------------------------------------


@cli.command()
@click.argument("channel")
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--thread", "thread_ts", default=None, help="Upload in thread.")
@click.option("--message", "initial_comment", default=None, help="Message to accompany the file.")
@click.option("--title", default=None, help="File title (defaults to filename).")
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    default=False,
    help="Emit structured JSON.",
)
@click.pass_context
def upload(
    ctx: click.Context,
    channel: str,
    file_path: str,
    thread_ts: str | None,
    initial_comment: str | None,
    title: str | None,
    as_json: bool,
) -> None:
    """Upload a file to a channel."""
    client = get_client(workspace=ctx.obj["workspace"])
    ws = ctx.obj["workspace_name"]
    channel_id = resolve_channel(client, channel, workspace=ws)

    kwargs: dict = {"channel": channel_id, "file": file_path}
    if thread_ts:
        kwargs["thread_ts"] = thread_ts
    if initial_comment:
        kwargs["initial_comment"] = initial_comment
    if title:
        kwargs["title"] = title

    try:
        resp = client.files_upload_v2(**kwargs)
    except SlackApiError as exc:
        raise click.ClickException(str(exc)) from exc

    file_id = resp.get("file", {}).get("id", "unknown")
    if as_json:
        click.echo(
            json.dumps(
                {"ok": True, "channel": channel_id, "file_id": file_id},
                ensure_ascii=False,
            )
        )
    else:
        console.print(f"[green]File uploaded[/] (id={file_id})")


# -- dm -----------------------------------------------------------------------


@cli.command()
@click.argument("user")
@click.argument("message", required=False, default=None)
@click.option("--limit", default=20, help="Messages to show when reading.")
@click.option("--thread", "thread_ts", default=None, help="Reply in thread (message timestamp).")
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    default=False,
    help="Emit structured JSON.",
)
@click.option(
    "--names",
    "with_names",
    is_flag=True,
    default=False,
    help="Resolve user IDs to display names when reading. Default emits raw IDs.",
)
@click.option(
    "--expand-thread",
    is_flag=True,
    default=False,
    help="When reading, also fetch replies for every threaded message and "
    "attach them inline under `replies`. Only meaningful with --json.",
)
@click.pass_context
def dm(
    ctx: click.Context,
    user: str,
    message: str | None,
    limit: int,
    thread_ts: str | None,
    as_json: bool,
    with_names: bool,
    expand_thread: bool,
) -> None:
    """Open a DM with a user. Send a message or read recent history."""
    client = get_client(workspace=ctx.obj["workspace"])
    ws = ctx.obj["workspace_name"]

    # Resolve user name to ID if needed (simple heuristic: IDs start with U)
    user_id = user
    if not (user.startswith("U") and user[1:].isalnum()):
        user_id = _resolve_user_by_name(client, user, workspace=ws)

    # Open (or retrieve) the DM channel
    try:
        resp = client.conversations_open(users=[user_id])
    except SlackApiError as exc:
        raise click.ClickException(str(exc)) from exc

    dm_channel = resp["channel"]["id"]

    if message:
        kwargs: dict = {"channel": dm_channel, "text": message}
        if thread_ts:
            kwargs["thread_ts"] = thread_ts
        try:
            send_resp = client.chat_postMessage(**kwargs)
        except SlackApiError as exc:
            raise click.ClickException(str(exc)) from exc
        ts = send_resp.get("ts", "")
        if as_json:
            click.echo(
                json.dumps(
                    {"ok": True, "channel": dm_channel, "ts": ts},
                    ensure_ascii=False,
                )
            )
        else:
            label = "DM thread reply sent" if thread_ts else "DM sent"
            console.print(f"[green]{label}[/] (ts={ts})")
    else:
        # Read recent DM history
        try:
            hist = client.conversations_history(
                channel=dm_channel, limit=limit
            )
        except SlackApiError as exc:
            raise click.ClickException(str(exc)) from exc
        messages = list(reversed(hist.get("messages", [])))
        if expand_thread:
            for msg in messages:
                ts = msg.get("ts", "")
                if msg.get("thread_ts") and msg.get("reply_count", 0) and ts:
                    msg["_replies"] = _fetch_thread_replies(client, dm_channel, ts)
        if as_json:
            _emit_messages_json(
                client, dm_channel, messages, workspace=ws, with_names=with_names
            )
        else:
            _print_messages(client, messages, workspace=ws, with_names=with_names)


# -- dm-upload ----------------------------------------------------------------


@cli.command(name="dm-upload")
@click.argument("user")
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--thread", "thread_ts", default=None, help="Upload in thread.")
@click.option("--message", "initial_comment", default=None, help="Message to accompany the file.")
@click.option("--title", default=None, help="File title (defaults to filename).")
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    default=False,
    help="Emit structured JSON.",
)
@click.pass_context
def dm_upload(
    ctx: click.Context,
    user: str,
    file_path: str,
    thread_ts: str | None,
    initial_comment: str | None,
    title: str | None,
    as_json: bool,
) -> None:
    """Upload a file to a user via DM."""
    client = get_client(workspace=ctx.obj["workspace"])
    ws = ctx.obj["workspace_name"]

    # Resolve user name to ID if needed (IDs start with U)
    user_id = user
    if not (user.startswith("U") and user[1:].isalnum()):
        user_id = _resolve_user_by_name(client, user, workspace=ws)

    # Open (or retrieve) the DM channel
    try:
        resp = client.conversations_open(users=[user_id])
    except SlackApiError as exc:
        raise click.ClickException(str(exc)) from exc

    dm_channel = resp["channel"]["id"]

    kwargs: dict = {"channel": dm_channel, "file": file_path}
    if thread_ts:
        kwargs["thread_ts"] = thread_ts
    if initial_comment:
        kwargs["initial_comment"] = initial_comment
    if title:
        kwargs["title"] = title

    try:
        upload_resp = client.files_upload_v2(**kwargs)
    except SlackApiError as exc:
        raise click.ClickException(str(exc)) from exc

    file_id = upload_resp.get("file", {}).get("id", "unknown")
    if as_json:
        click.echo(
            json.dumps(
                {"ok": True, "channel": dm_channel, "file_id": file_id},
                ensure_ascii=False,
            )
        )
    else:
        console.print(f"[green]File uploaded via DM[/] (id={file_id})")


def _resolve_user_by_name(
    client: WebClient, name: str, workspace: str = ""
) -> str:
    """Resolve a user by username or display_name, using disk cache."""
    if workspace:
        user_data = _get_user_cache(client, workspace)
        # Check username first, then display name
        uid = user_data.get("name_to_id", {}).get(name)
        if uid:
            return uid
        uid = user_data.get("display_to_id", {}).get(name)
        if uid:
            return uid

    # Cache miss — fall back to paginating the API
    cursor = None
    while True:
        kwargs: dict = {"limit": 200}
        if cursor:
            kwargs["cursor"] = cursor
        resp = client.users_list(**kwargs)
        for member in resp["members"]:
            if member.get("name") == name:
                return member["id"]
            profile = member.get("profile", {})
            if profile.get("display_name") == name:
                return member["id"]
        cursor = resp.get("response_metadata", {}).get("next_cursor")
        if not cursor:
            break
    raise click.ClickException(f"User '{name}' not found.")


# -- search -------------------------------------------------------------------


@cli.command()
@click.argument("query")
@click.option("--count", default=20, help="Results per page.")
@click.option("--page", default=1, help="Page number.")
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    default=False,
    help="Emit structured JSON.",
)
@click.option(
    "--names",
    "with_names",
    is_flag=True,
    default=False,
    help="Show usernames and channel names. Default shows raw user/channel IDs.",
)
@click.pass_context
def search(
    ctx: click.Context,
    query: str,
    count: int,
    page: int,
    as_json: bool,
    with_names: bool,
) -> None:
    """Search messages across the workspace."""
    client = get_client(workspace=ctx.obj["workspace"])

    try:
        # search.messages uses page-based pagination (not cursor)
        resp = client.search_messages(query=query, count=count, page=page)
    except SlackApiError as exc:
        raise click.ClickException(str(exc)) from exc

    matches = resp.get("messages", {})
    total = matches.get("total", 0)
    paging = matches.get("paging", {})
    raw_matches = matches.get("matches", [])

    if as_json:
        out = []
        for match in raw_matches:
            channel = match.get("channel", {}) or {}
            if with_names:
                user_field = match.get("username", "")
                channel_field = channel.get("name", "")
            else:
                user_field = match.get("user", "")
                channel_field = channel.get("id", "")
            out.append({
                "ts": _format_ts(match.get("ts", "")),
                "user": user_field,
                "channel": channel_field,
                "text": match.get("text", ""),
                "permalink": match.get("permalink", ""),
            })
        click.echo(
            json.dumps(
                {
                    "query": query,
                    "page": paging.get("page", page),
                    "pages": paging.get("pages", 1),
                    "total": total,
                    "matches": out,
                },
                ensure_ascii=False,
            )
        )
        return

    console.print(
        f"[bold]Search results for '{query}'[/] "
        f"— page {paging.get('page', page)}/{paging.get('pages', 1)}, "
        f"{total} total matches"
    )

    for match in raw_matches:
        channel = match.get("channel", {}) or {}
        if with_names:
            user_field = match.get("username", "unknown")
            channel_field = f"#{channel.get('name', '?')}"
        else:
            user_field = match.get("user", "?")
            channel_field = channel.get("id", "?")
        text = match.get("text", "")
        ts = match.get("ts", "")
        ts_display = _format_ts(ts)

        line = Text()
        line.append(f"[{ts_display}] ", style="dim")
        line.append(f"{channel_field} ", style="blue")
        line.append(f"{user_field}: ", style="bold")
        line.append(text)
        console.print(line)


# -- canvas -------------------------------------------------------------------


@cli.command()
@click.argument("canvas_url_or_id")
@click.option("--html", "raw_html", is_flag=True, default=False, help="Output raw HTML instead of plain text.")
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    default=False,
    help="Emit structured JSON.",
)
@click.pass_context
def canvas(
    ctx: click.Context,
    canvas_url_or_id: str,
    raw_html: bool,
    as_json: bool,
) -> None:
    """Read a Slack canvas by URL or file ID."""
    client = get_client(workspace=ctx.obj["workspace"])

    # Accept both full URLs and bare file IDs
    if canvas_url_or_id.startswith("http"):
        file_id = parse_canvas_url(canvas_url_or_id)
    else:
        file_id = canvas_url_or_id

    title, html_content = _fetch_canvas_content(client, file_id)

    if as_json:
        payload: dict = {"file_id": file_id, "title": title}
        if raw_html:
            payload["html"] = html_content
        else:
            payload["text"] = _html_to_text(html_content)
        click.echo(json.dumps(payload, ensure_ascii=False))
        return

    if raw_html:
        console.print(f"[bold]{title}[/]\n")
        click.echo(html_content)
    else:
        text = _html_to_text(html_content)
        console.print(f"[bold]{title}[/]\n")
        console.print(text)


@cli.command("canvas-edit")
@click.argument("canvas_url_or_id")
@click.argument("content", required=False)
@click.option(
    "--operation",
    type=click.Choice(
        ["insert_at_end", "insert_at_start", "replace"],
        case_sensitive=False,
    ),
    default="insert_at_end",
    help="Edit operation (default: insert_at_end).",
)
@click.option(
    "--section-id",
    default=None,
    help="Section ID for targeted replace/insert operations.",
)
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    default=False,
    help="Emit structured JSON.",
)
@click.pass_context
def canvas_edit(
    ctx: click.Context,
    canvas_url_or_id: str,
    content: str | None,
    operation: str,
    section_id: str | None,
    as_json: bool,
) -> None:
    """Edit a Slack canvas by URL or file ID.

    Content can be passed as an argument or piped via stdin.
    Accepts markdown — Slack converts it to canvas formatting.

    Examples:

        # Append markdown to a canvas
        slack_user_cli canvas-edit DEADBEEFUUV "## New Section\\nSome text"

        # Replace entire canvas content
        slack_user_cli canvas-edit DEADBEEFUUV "## Fresh Start" --operation replace

        # Pipe content from a file
        cat summary.md | slack_user_cli canvas-edit DEADBEEFUUV --operation replace
    """
    import sys  # noqa: PLC0415

    client = get_client(workspace=ctx.obj["workspace"])

    # Accept both full URLs and bare file IDs.
    if canvas_url_or_id.startswith("http"):
        file_id = parse_canvas_url(canvas_url_or_id)
    else:
        file_id = canvas_url_or_id

    # Read content from argument or stdin.
    if content is None:
        if sys.stdin.isatty():
            raise click.ClickException(
                "No content provided. Pass as argument or pipe via stdin."
            )
        content = sys.stdin.read()

    if not content.strip():
        raise click.ClickException("Content is empty — nothing to write.")

    change: dict = {
        "operation": operation,
        "document_content": {"type": "markdown", "markdown": content},
    }
    if section_id is not None:
        change["section_id"] = section_id

    try:
        resp = client.api_call(
            "canvases.edit",
            json={"canvas_id": file_id, "changes": [change]},
        )
    except SlackApiError as exc:
        raise click.ClickException(str(exc)) from exc

    if not resp.get("ok"):
        error = resp.get("error", "unknown_error")
        detail = resp.get("detail", "")
        raise click.ClickException(f"canvases.edit failed: {error} — {detail}")

    if as_json:
        click.echo(
            json.dumps(
                {"ok": True, "file_id": file_id, "operation": operation},
                ensure_ascii=False,
            )
        )
    else:
        console.print(f"[green]Canvas {file_id} updated ({operation}).[/]")


# -- Output helpers -----------------------------------------------------------


def _format_ts(ts: str) -> str:
    """Convert a Slack timestamp to a human-readable datetime string."""
    try:
        from datetime import datetime, timezone  # noqa: PLC0415

        epoch = float(ts.split(".")[0])
        dt = datetime.fromtimestamp(epoch, tz=timezone.utc)
        return dt.strftime("%Y-%m-%d %H:%M")
    except (ValueError, IndexError):
        return ts


def _parse_since(value: str) -> str:
    """Convert an ISO date/datetime to a Slack `oldest` epoch string.

    Accepts a date (``2026-05-29``) or datetime (``2026-05-29T10:07:00``).
    A value without an explicit timezone is interpreted as UTC, matching how
    Slack timestamps are rendered elsewhere in this CLI.
    """
    from datetime import datetime, timezone  # noqa: PLC0415

    try:
        dt = datetime.fromisoformat(value.strip())
    except ValueError as exc:
        raise click.ClickException(
            f"--since: not an ISO date/datetime: {value!r}"
        ) from exc
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return f"{dt.timestamp():.6f}"


def _print_messages(
    client: WebClient,
    messages: list[dict],
    workspace: str = "",
    with_names: bool = False,
    indent: str = "",
) -> None:
    """Render a list of Slack messages to the console.

    Default shows raw user IDs (and leaves <@UXXX> mention tokens untouched)
    so output is stable for scripts. Pass `with_names=True` to resolve to
    display names. Replies stashed under `_replies` (by --expand-thread) are
    rendered indented beneath their parent.
    """
    for msg in messages:
        user_id = msg.get("user", "")
        if with_names:
            username = (
                resolve_user(client, user_id, workspace=workspace)
                if user_id
                else "bot"
            )
            text = _resolve_mentions(client, msg.get("text", ""), workspace=workspace)
        else:
            username = user_id or "bot"
            text = msg.get("text", "")
        ts = msg.get("ts", "")
        ts_display = _format_ts(ts)
        thread_ts = msg.get("thread_ts")
        reply_count = msg.get("reply_count", 0)

        line = Text(indent)
        line.append(f"[{ts_display}] ", style="dim")
        line.append(f"{username}: ", style="bold")
        line.append(text)
        # Indicate threaded messages
        if thread_ts and reply_count:
            line.append(f" [{reply_count} replies]", style="yellow")
        console.print(line)

        # Surface attachments so a reader knows files exist (and can fetch them
        # with the `download` command); they're otherwise invisible in text.
        for f in _extract_files(msg):
            meta = f.get("filetype") or f.get("mimetype") or ""
            if f.get("size"):
                meta = f"{meta}, {f['size']} bytes" if meta else f"{f['size']} bytes"
            fl = Text(indent + "  ")
            fl.append("📎 ", style="cyan")
            fl.append(f["name"], style="cyan")
            if meta:
                fl.append(f" ({meta})", style="dim")
            if f.get("id"):
                fl.append(f"  id={f['id']}", style="dim")
            console.print(fl)

        # Surface quoted/shared messages and their attachments, so a message
        # that forwards another one doesn't hide the original's files.
        for sh in _extract_shared(msg):
            who = sh.get("author") or "shared message"
            sl = Text(indent + "  ↪ quoted ")
            sl.append(who, style="magenta")
            if sh.get("url"):
                sl.append(f" {sh['url']}", style="dim")
            console.print(sl)
            # Render the full quoted message body, not just its attachments.
            quoted_text = sh.get("text") or ""
            if with_names:
                quoted_text = _resolve_mentions(
                    client, quoted_text, workspace=workspace
                )
            if quoted_text:
                qt = Text(indent + "    ")
                qt.append(quoted_text, style="dim")
                console.print(qt)
            for f in sh.get("files", []) or []:
                meta = f.get("filetype") or f.get("mimetype") or ""
                if f.get("size"):
                    meta = f"{meta}, {f['size']} bytes" if meta else f"{f['size']} bytes"
                fl = Text(indent + "    ")
                fl.append("📎 ", style="cyan")
                fl.append(f["name"], style="cyan")
                if meta:
                    fl.append(f" ({meta})", style="dim")
                if f.get("id"):
                    fl.append(f"  id={f['id']}", style="dim")
                console.print(fl)

        # Plain pasted permalinks to other messages.
        for link in _extract_links(msg):
            ll = Text(indent + "  🔗 ")
            ll.append(link["url"], style="blue")
            console.print(ll)

        replies = msg.get("_replies") or []
        if replies:
            _print_messages(
                client,
                replies,
                workspace=workspace,
                with_names=with_names,
                indent=indent + "  ↳ ",
            )


# Matches Slack user-mention tokens. Slack emits either `<@U0123>` when the
# display name is omitted or `<@U0123|name>` when it's already known; both
# shapes need to become a @displayname so JSON consumers don't see raw IDs.
_USER_MENTION_RE = re.compile(r"<@(?P<id>[UW][A-Z0-9]+)(?:\|[^>]+)?>")


def _resolve_mentions(
    client: WebClient, text: str, workspace: str = ""
) -> str:
    """Replace <@UXXX> user mentions with @displayname.

    Slack's own text payload contains IDs rather than names inside mention
    tokens; `resolve_user` is hit per ID but its cache makes that cheap —
    repeated mentions of the same person become O(1) after the first lookup.
    Other Slack mrkdwn tokens (<#C.../name>, <https://...|label>) are left
    alone for now because they already carry a human-readable label.
    """
    if not text or "<@" not in text:
        return text

    def sub(match: re.Match[str]) -> str:
        name = resolve_user(client, match.group("id"), workspace=workspace)
        return f"@{name}"

    return _USER_MENTION_RE.sub(sub, text)


def _extract_actions(blocks: list[dict]) -> list[dict]:
    """Pull clickable elements (buttons, radio_buttons, static_select) out of block-kit.

    Returned shape is a flat list of dicts ready for use with the `click`
    subcommand. Buttons surface as one entry; radio_buttons / static_select
    surface as a single entry whose `options` lists every choice. Block IDs
    and action IDs are kept verbatim because `blocks.actions` requires them
    byte-for-byte.
    """
    out: list[dict] = []
    for block in blocks or []:
        if block.get("type") != "actions":
            continue
        block_id = block.get("block_id", "")
        for el in block.get("elements", []) or []:
            el_type = el.get("type", "")
            entry: dict = {
                "type": el_type,
                "block_id": block_id,
                "action_id": el.get("action_id", ""),
            }
            if el_type == "button":
                entry["text"] = (el.get("text") or {}).get("text", "")
                entry["value"] = el.get("value", "")
            elif el_type in ("radio_buttons", "static_select", "checkboxes"):
                entry["options"] = [
                    {
                        "text": (o.get("text") or {}).get("text", ""),
                        "value": o.get("value", ""),
                    }
                    for o in el.get("options", []) or []
                ]
            else:
                # Unknown action type — keep raw element so a caller can still
                # construct a payload for it instead of dropping the choice.
                entry["raw"] = el
            out.append(entry)
    return out


def _extract_files(msg: dict) -> list[dict]:
    """Pull a clean attachment list out of a message's `files` array.

    Slack hangs uploaded files (PDFs, images, docs, snippets) off the message
    `files` field. Each entry keeps the file ID, a usable filename, type/size,
    and the `url_private*` endpoints the `download` command needs to fetch the
    bytes. Deleted or access-limited files may lack a download URL; they're
    still listed so the caller knows an attachment was there.
    """
    out: list[dict] = []
    for f in msg.get("files", []) or []:
        out.append(
            {
                "id": f.get("id", ""),
                "name": f.get("name") or f.get("title") or f.get("id", "file"),
                "title": f.get("title", ""),
                "filetype": f.get("filetype", ""),
                "mimetype": f.get("mimetype", ""),
                "size": f.get("size"),
                "url_private": f.get("url_private", ""),
                "url_private_download": f.get("url_private_download", ""),
                "permalink": f.get("permalink", ""),
            }
        )
    return out


# Matches a Slack message permalink in text or an attachment's from_url:
# https://<workspace>.slack.com/archives/<channel>/p<16-digit-ts>
_SLACK_MSG_LINK_RE = re.compile(
    r"https?://[a-z0-9.\-]+\.slack\.com/archives/([CDG][A-Z0-9]+)/p(\d{16})"
)


def _link_parts(url: str) -> dict | None:
    """Turn a Slack message permalink into {url, channel, ts}, or None.

    The `p<digits>` form encodes the ts without its dot; we re-insert it so the
    result is ready for `conversations.replies`, `download`, or `url`.
    """
    m = _SLACK_MSG_LINK_RE.search(url)
    if not m:
        return None
    raw = m.group(2)
    return {"url": url, "channel": m.group(1), "ts": f"{raw[:-6]}.{raw[-6:]}"}


def _extract_shared(msg: dict) -> list[dict]:
    """Surface messages quoted/shared into this one via Slack's "share message".

    When someone shares another message into a channel, Slack stores the
    original inside `attachments` (with `is_share`/`from_url`) — and copies the
    original's `files` array there too. Reading only `msg["files"]` therefore
    misses the attachments of a quoted message entirely. Each returned entry
    identifies the source (url/author/channel/ts) and carries its files so they
    are never silently dropped.
    """
    out: list[dict] = []
    for a in msg.get("attachments", []) or []:
        from_url = a.get("from_url")
        if not (a.get("is_share") or a.get("is_msg_unfurl") or from_url):
            continue
        out.append(
            {
                "url": from_url or "",
                "author": a.get("author_name", ""),
                "channel": a.get("channel_id", ""),
                "ts": a.get("ts", ""),
                "text": a.get("text", ""),
                "files": _extract_files(a),
            }
        )
    return out


def _extract_links(msg: dict) -> list[dict]:
    """Pull Slack message permalinks pasted into a message's text.

    Distinct from `_extract_shared` (Slack's native share/unfurl): this catches
    a plain pasted `<https://…/archives/…/p…>` link so a reference to another
    message — and any attachments it holds — stays visible and fetchable even
    when Slack didn't unfurl it.
    """
    seen: set[str] = set()
    out: list[dict] = []
    for m in _SLACK_MSG_LINK_RE.finditer(msg.get("text", "") or ""):
        url = m.group(0)
        if url in seen:
            continue
        seen.add(url)
        parts = _link_parts(url)
        if parts:
            out.append(parts)
    return out


def _collect_raw_files(msg: dict) -> list[dict]:
    """Every downloadable file on a message: direct uploads + shared-message files.

    `download` uses this so fetching a message that *quotes* another message
    still retrieves the quoted message's attachments (they live under
    `attachments[].files`, not `msg["files"]`).
    """
    files = list(msg.get("files", []) or [])
    for a in msg.get("attachments", []) or []:
        files.extend(a.get("files", []) or [])
    return files


def _download_file(client: WebClient, file_info: dict, dest_dir: Path) -> Path:
    """Download one Slack file into dest_dir using the client's auth.

    File bytes are gated behind `url_private`; the browser-session auth the
    WebClient already carries (xoxc token + d cookie) is exactly what unlocks
    them, so we reuse those headers rather than an unauthenticated request.
    The filename is reduced to its basename to avoid path traversal from a
    Slack-supplied name.
    """
    import requests  # noqa: PLC0415

    url = file_info.get("url_private_download") or file_info.get("url_private")
    if not url:
        raise click.ClickException(
            f"File {file_info.get('id', '?')} has no downloadable URL "
            "(it may be deleted or an external link)."
        )
    headers = dict(client.headers or {})
    headers["Authorization"] = f"Bearer {client.token}"
    resp = requests.get(url, headers=headers, timeout=60)
    resp.raise_for_status()

    dest_dir.mkdir(parents=True, exist_ok=True)
    name = file_info.get("name") or file_info.get("title") or file_info.get("id", "file")
    path = dest_dir / Path(name).name
    path.write_bytes(resp.content)
    return path


def _message_to_entry(
    client: WebClient,
    msg: dict,
    workspace: str,
    with_names: bool,
) -> dict:
    """Build the JSON entry for a single message.

    By default emits raw user IDs and untouched text so consumers see stable
    Slack identifiers. With `with_names=True`, user IDs become display names
    and `<@UXXX>` mention tokens are rewritten to `@displayname`.
    """
    user_id = msg.get("user", "")
    if with_names:
        username = (
            resolve_user(client, user_id, workspace=workspace) if user_id else "bot"
        )
        text = _resolve_mentions(client, msg.get("text", ""), workspace=workspace)
    else:
        username = user_id or "bot"
        text = msg.get("text", "")

    entry: dict = {
        "ts": _format_ts(msg.get("ts", "")),
        # Full-precision Slack ts on every message. The `ts` field above is
        # minute-precision for humans; callers need the microsecond ts to build
        # real permalinks (via the `permalink` command) or to pass back to
        # `click`. Emitted unconditionally so regular messages — not just
        # block-kit ones — are addressable.
        "raw_ts": msg.get("ts", ""),
        "user": username,
        "text": text,
    }
    thread_ts = msg.get("thread_ts")
    if thread_ts:
        entry["thread_ts"] = thread_ts
    reply_count = msg.get("reply_count", 0)
    if thread_ts and reply_count:
        entry["threadCount"] = reply_count
    actions = _extract_actions(msg.get("blocks", []) or [])
    if actions:
        entry["actions"] = actions
        bot_id = msg.get("bot_id")
        app_id = msg.get("app_id")
        if bot_id:
            entry["bot_id"] = bot_id
        if app_id:
            entry["app_id"] = app_id
    # Surface uploaded attachments (PDFs, images, docs). Without this a JSON
    # consumer can't even tell a message carries files, let alone fetch them;
    # the entries here include the IDs and private URLs the `download` command
    # needs.
    files = _extract_files(msg)
    if files:
        entry["files"] = files
    # Messages that quote/share another message carry the original (and its
    # files) under `attachments`; surface them so a quoted message's
    # attachments are never missed.
    shared = _extract_shared(msg)
    if shared:
        if with_names:
            # Resolve <@U…> mentions inside the quoted body too, matching the
            # parent message's text treatment.
            for sh in shared:
                sh["text"] = _resolve_mentions(
                    client, sh.get("text", ""), workspace=workspace
                )
        entry["shared"] = shared
    # Plain pasted Slack permalinks referencing other messages.
    links = _extract_links(msg)
    if links:
        entry["links"] = links
    replies = msg.get("_replies") or []
    if replies:
        entry["replies"] = [
            _message_to_entry(client, r, workspace, with_names) for r in replies
        ]
    return entry


def _emit_messages_json(
    client: WebClient,
    channel: str,
    messages: list[dict],
    workspace: str = "",
    with_names: bool = False,
) -> None:
    """Emit messages as a single JSON object on stdout."""
    parsed = [_message_to_entry(client, m, workspace, with_names) for m in messages]
    click.echo(
        json.dumps({"channel": channel, "messages": parsed}, ensure_ascii=False)
    )


if __name__ == "__main__":
    cli()
