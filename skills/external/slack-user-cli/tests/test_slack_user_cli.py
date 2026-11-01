#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11,<3.12"  # leveldb 0.201 (via slacktokens) uses PyUnicode_AS_UNICODE, removed in 3.12
# dependencies = [
#     "pytest==9.1.1",
#     "slack-sdk==3.41.0",
#     "slacktokens==0.2.6",
#     "click==8.3.2",
#     "rich==14.3.3",
#     "requests==2.33.1",
# ]
#
# [tool.uv]
# exclude-newer = "2026-10-27T00:00:00Z"
# ///
"""Unit tests for slack_user_cli.py.

Each test covers a single assertion. WebClient is mocked throughout
to avoid real API calls.
"""

import json
import shutil
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner
from slack_sdk.errors import SlackApiError

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from slack_user_cli import (
    _channel_type_label,
    _choose_default,
    _collect_raw_files,
    _download_file,
    _extract_block_text,
    _extract_files,
    _extract_links,
    _extract_shared,
    _filter_keep_since,
    _format_ts,
    _link_parts,
    _load_cache,
    _load_permanent,
    _message_to_entry,
    _parse_since,
    _permanent_get,
    _permanent_put,
    _save_cache,
    _snapshot_leveldb,
    _unlocked_slack_leveldb,
    build_channel_cache,
    build_user_cache,
    cli,
    get_client,
    get_workspace_config,
    load_config,
    parse_slack_url,
    resolve_channel,
    resolve_channel_name,
    resolve_user,
    save_config,
)


# -- Fixtures -----------------------------------------------------------------


@pytest.fixture()
def runner():
    """Click CLI test runner."""
    return CliRunner()


@pytest.fixture()
def tmp_config(tmp_path, monkeypatch):
    """Redirect config to a temp directory so tests don't touch real config."""
    monkeypatch.setattr("slack_user_cli.auth_broker", lambda *args: {})
    config_dir = tmp_path / ".config" / "slack-user-cli"
    config_file = config_dir / "config.json"
    monkeypatch.setattr("slack_user_cli.CONFIG_DIR", config_dir)
    monkeypatch.setattr("slack_user_cli.CONFIG_FILE", config_file)
    return config_file


@pytest.fixture()
def saved_config(tmp_config):
    """Write a valid multi-workspace config and return its path."""
    tmp_config.parent.mkdir(parents=True, exist_ok=True)
    tmp_config.write_text(
        json.dumps({
            "cookie": "xoxd-test",
            "default": "testteam",
            "workspaces": {
                "testteam": {
                    "token": "xoxc-test",
                    "team": "testteam",
                    "user": "testuser",
                }
            },
        })
    )
    return tmp_config


@pytest.fixture()
def legacy_config(tmp_config):
    """Write a legacy single-workspace config for migration tests."""
    tmp_config.parent.mkdir(parents=True, exist_ok=True)
    tmp_config.write_text(
        json.dumps({"token": "xoxc-test", "cookie": "xoxd-test", "team": "legacyteam", "user": "legacyuser"})
    )
    return tmp_config


@pytest.fixture()
def mock_client():
    """A mocked WebClient instance."""
    return MagicMock()


@pytest.fixture(autouse=True)
def _clear_user_cache():
    """Reset the module-level user cache between tests."""
    from slack_user_cli import _user_cache

    _user_cache.clear()


# -- Config tests -------------------------------------------------------------


class TestLoadConfig:
    def test_returns_empty_dict_when_missing(self, tmp_config):
        assert load_config() == {}

    def test_returns_workspaces(self, saved_config):
        config = load_config()
        assert "testteam" in config["workspaces"]

    def test_returns_cookie(self, saved_config):
        config = load_config()
        assert config["cookie"] == "xoxd-test"

    def test_migrates_legacy_format(self, legacy_config):
        """Legacy {token, cookie} config is auto-migrated to multi-workspace."""
        config = load_config()
        assert "workspaces" in config

    def test_legacy_migration_preserves_token(self, legacy_config):
        config = load_config()
        assert config["workspaces"]["legacyteam"]["token"] == "xoxc-test"

    def test_legacy_migration_sets_default(self, legacy_config):
        config = load_config()
        assert config["default"] == "legacyteam"


class TestSaveConfig:
    def test_creates_file(self, tmp_config):
        save_config({"cookie": "c", "workspaces": {}})
        assert tmp_config.exists()

    def test_persists_data(self, tmp_config):
        save_config({"cookie": "xoxd-new", "workspaces": {"ws": {"token": "t"}}})
        data = json.loads(tmp_config.read_text())
        assert data["cookie"] == "xoxd-new"

    def test_creates_parent_dirs(self, tmp_config):
        # Ensure parent doesn't exist yet
        assert not tmp_config.parent.exists()
        save_config({"cookie": "c", "workspaces": {}})
        assert tmp_config.parent.exists()


# -- get_workspace_config tests -----------------------------------------------


class TestGetWorkspaceConfig:
    def test_raises_when_no_workspaces(self):
        with pytest.raises(Exception, match="Not logged in"):
            get_workspace_config({}, None)

    def test_raises_when_workspace_not_found(self):
        config = {"workspaces": {"team1": {"token": "t"}}, "cookie": "c"}
        with pytest.raises(Exception, match="not found"):
            get_workspace_config(config, "nonexistent")

    def test_raises_distinct_error_when_no_default_set(self):
        """Workspaces exist but 'default' is unset (e.g. a hand-edited
        config.json) — the error should say so, not report a blank-named
        workspace as 'not found'."""
        config = {"workspaces": {"team1": {"token": "t"}}, "cookie": "c"}
        with pytest.raises(Exception, match="No default workspace set"):
            get_workspace_config(config, None)

    def test_returns_token_and_cookie(self):
        config = {
            "workspaces": {"myteam": {"token": "xoxc-t"}},
            "cookie": "xoxd-c",
            "default": "myteam",
        }
        ws = get_workspace_config(config, None)
        assert ws["token"] == "xoxc-t"

    def test_uses_default_workspace(self):
        config = {
            "workspaces": {"a": {"token": "ta"}, "b": {"token": "tb"}},
            "cookie": "c",
            "default": "b",
        }
        ws = get_workspace_config(config, None)
        assert ws["token"] == "tb"

    def test_explicit_workspace_overrides_default(self):
        config = {
            "workspaces": {"a": {"token": "ta"}, "b": {"token": "tb"}},
            "cookie": "c",
            "default": "a",
        }
        ws = get_workspace_config(config, "b")
        assert ws["token"] == "tb"


class TestChooseDefault:
    def test_single_team_skips_prompt(self, monkeypatch):
        # Even on a real terminal, one team needs no choice
        monkeypatch.setattr("sys.stdin.isatty", lambda: True)
        assert _choose_default(["Alpha"]) == "Alpha"

    def test_non_interactive_picks_first_team(self, monkeypatch):
        # Scripted/non-TTY invocations have no one to prompt
        monkeypatch.setattr("sys.stdin.isatty", lambda: False)
        assert _choose_default(["Alpha", "Beta"]) == "Alpha"

    def test_interactive_prompts_and_honors_choice(self, monkeypatch):
        monkeypatch.setattr("sys.stdin.isatty", lambda: True)
        with patch("click.prompt", return_value="2"):
            assert _choose_default(["Alpha", "Beta"]) == "Beta"

    def test_interactive_default_choice_is_first_team(self, monkeypatch):
        monkeypatch.setattr("sys.stdin.isatty", lambda: True)
        with patch("click.prompt", return_value="1"):
            assert _choose_default(["Alpha", "Beta"]) == "Alpha"

    def test_invalid_choice_falls_back_to_first_team(self, monkeypatch):
        monkeypatch.setattr("sys.stdin.isatty", lambda: True)
        with patch("click.prompt", return_value="not-a-number"):
            assert _choose_default(["Alpha", "Beta"]) == "Alpha"


# -- get_client tests ---------------------------------------------------------


class TestGetClient:
    def test_raises_when_empty_config(self, tmp_config):
        with pytest.raises(Exception, match="Not logged in"):
            get_client({})

    def test_returns_client_with_valid_config(self, saved_config):
        client = get_client()
        assert client is not None


# -- resolve_user tests -------------------------------------------------------


class TestResolveUser:
    def test_returns_display_name(self, mock_client):
        mock_client.users_info.return_value = {
            "user": {
                "profile": {"display_name": "alice"},
                "real_name": "Alice Smith",
            }
        }
        assert resolve_user(mock_client, "U123") == "alice"

    def test_falls_back_to_real_name(self, mock_client):
        mock_client.users_info.return_value = {
            "user": {"profile": {"display_name": ""}, "real_name": "Bob Jones"}
        }
        assert resolve_user(mock_client, "U456") == "Bob Jones"

    def test_falls_back_to_user_id(self, mock_client):
        mock_client.users_info.return_value = {
            "user": {"profile": {"display_name": ""}, "real_name": ""}
        }
        # Empty strings are falsy, should fall back to user_id
        assert resolve_user(mock_client, "U789") == "U789"

    def test_caches_result(self, mock_client):
        mock_client.users_info.return_value = {
            "user": {"profile": {"display_name": "cached"}}
        }
        resolve_user(mock_client, "UCACHE")
        resolve_user(mock_client, "UCACHE")
        # Should only call API once due to caching
        assert mock_client.users_info.call_count == 1

    def test_returns_user_id_on_api_error(self, mock_client):
        mock_client.users_info.side_effect = SlackApiError(
            message="error",
            response=MagicMock(status_code=200, data={"ok": False, "error": "user_not_found"}),
        )
        assert resolve_user(mock_client, "UFAIL") == "UFAIL"


# -- resolve_channel tests ----------------------------------------------------


class TestResolveChannel:
    def test_passes_through_channel_id(self, mock_client):
        assert resolve_channel(mock_client, "C12345ABC") == "C12345ABC"

    def test_passes_through_dm_id(self, mock_client):
        assert resolve_channel(mock_client, "D12345ABC") == "D12345ABC"

    def test_passes_through_group_id(self, mock_client):
        assert resolve_channel(mock_client, "G12345ABC") == "G12345ABC"

    def test_resolves_name_to_id(self, mock_client):
        mock_client.conversations_list.return_value = {
            "channels": [{"id": "C999", "name": "general"}],
            "response_metadata": {"next_cursor": ""},
        }
        assert resolve_channel(mock_client, "general") == "C999"

    def test_raises_when_not_found(self, mock_client):
        mock_client.conversations_list.return_value = {
            "channels": [],
            "response_metadata": {"next_cursor": ""},
        }
        with pytest.raises(Exception, match="not found"):
            resolve_channel(mock_client, "nonexistent")


# -- permanent id→name store tests --------------------------------------------


class TestPermanentStore:
    def test_get_returns_none_without_workspace(self, tmp_config):
        assert _permanent_get("", "users", "U1") is None

    def test_get_returns_none_when_absent(self, tmp_config):
        assert _permanent_get("testteam", "users", "U1") is None

    def test_put_then_get_roundtrips(self, tmp_config):
        _permanent_put("testteam", "users", {"U1": "alice"})
        assert _permanent_get("testteam", "users", "U1") == "alice"

    def test_put_is_noop_without_workspace(self, tmp_config):
        _permanent_put("", "users", {"U1": "alice"})
        assert not _permanent_path_exists()

    def test_put_merges_without_dropping_prior(self, tmp_config):
        _permanent_put("testteam", "channels", {"C1": "general"})
        _permanent_put("testteam", "channels", {"C2": "random"})
        assert _permanent_get("testteam", "channels", "C1") == "general"

    def test_kinds_are_isolated(self, tmp_config):
        _permanent_put("testteam", "users", {"X1": "a-user"})
        assert _permanent_get("testteam", "channels", "X1") is None

    def test_load_always_has_both_kinds(self, tmp_config):
        assert _load_permanent("testteam") == {"users": {}, "channels": {}}


def _permanent_path_exists() -> bool:
    """Helper: does the permanent store file exist for the test workspace?"""
    from slack_user_cli import _permanent_path

    return _permanent_path("").exists()


class TestResolveUserPermanentCache:
    def test_uses_permanent_store_without_api(self, mock_client, tmp_config):
        _permanent_put("testteam", "users", {"UPERM": "stored"})
        assert resolve_user(mock_client, "UPERM", "testteam") == "stored"

    def test_permanent_hit_makes_no_api_call(self, mock_client, tmp_config):
        _permanent_put("testteam", "users", {"UPERM": "stored"})
        resolve_user(mock_client, "UPERM", "testteam")
        assert mock_client.users_info.call_count == 0

    def test_api_resolution_is_persisted(self, mock_client, tmp_config):
        mock_client.users_info.return_value = {"user": {"profile": {"display_name": "fromapi"}}}
        resolve_user(mock_client, "UNEW", "testteam")
        assert _permanent_get("testteam", "users", "UNEW") == "fromapi"

    def test_unresolved_id_is_not_persisted(self, mock_client, tmp_config):
        mock_client.users_info.return_value = {"user": {"profile": {"display_name": ""}, "real_name": ""}}
        resolve_user(mock_client, "UBAD", "testteam")
        assert _permanent_get("testteam", "users", "UBAD") is None


class TestResolveChannelName:
    def test_uses_permanent_store_without_api(self, mock_client, tmp_config):
        _permanent_put("testteam", "channels", {"CPERM": "research"})
        assert resolve_channel_name(mock_client, "CPERM", "testteam") == "research"

    def test_permanent_hit_makes_no_api_call(self, mock_client, tmp_config):
        _permanent_put("testteam", "channels", {"CPERM": "research"})
        resolve_channel_name(mock_client, "CPERM", "testteam")
        assert mock_client.conversations_info.call_count == 0

    def test_api_resolution_is_persisted(self, mock_client, tmp_config):
        mock_client.conversations_info.return_value = {"channel": {"name": "general"}}
        resolve_channel_name(mock_client, "CNEW", "testteam")
        assert _permanent_get("testteam", "channels", "CNEW") == "general"

    def test_returns_id_on_api_error(self, mock_client, tmp_config):
        mock_client.conversations_info.side_effect = SlackApiError(
            message="error",
            response=MagicMock(status_code=200, data={"ok": False, "error": "channel_not_found"}),
        )
        assert resolve_channel_name(mock_client, "CFAIL", "testteam") == "CFAIL"


# -- resolve-name command tests ------------------------------------------------


class TestResolveNameCommand:
    @patch("slack_user_cli.get_client")
    def test_resolves_channel_name(self, mock_get_client, runner, saved_config):
        mock_client = MagicMock()
        mock_client.conversations_list.return_value = {
            "channels": [{"id": "C1", "name": "general"}],
            "response_metadata": {"next_cursor": ""},
        }
        mock_get_client.return_value = mock_client
        result = runner.invoke(cli, ["resolve-name", "general", "--json"])
        assert json.loads(result.output) == {"resolved": {"general": "C1"}}

    @patch("slack_user_cli.get_client")
    def test_resolves_user_name(self, mock_get_client, runner, saved_config):
        mock_client = MagicMock()
        mock_client.users_list.return_value = {
            "members": [{"id": "U1", "name": "alice", "profile": {"display_name": "Alice"}}],
            "response_metadata": {"next_cursor": ""},
        }
        mock_get_client.return_value = mock_client
        result = runner.invoke(cli, ["resolve-name", "alice", "--type", "user", "--json"])
        assert json.loads(result.output) == {"resolved": {"alice": "U1"}}

    @patch("slack_user_cli.get_client")
    def test_unresolved_name_is_null_not_a_batch_abort(self, mock_get_client, runner, saved_config):
        mock_client = MagicMock()
        mock_client.conversations_list.return_value = {
            "channels": [{"id": "C1", "name": "general"}],
            "response_metadata": {"next_cursor": ""},
        }
        mock_get_client.return_value = mock_client
        result = runner.invoke(cli, ["resolve-name", "general", "nonexistent", "--json"])
        assert json.loads(result.output) == {"resolved": {"general": "C1", "nonexistent": None}}

    @patch("slack_user_cli.get_client")
    def test_cache_only_skips_api_on_channel_miss(self, mock_get_client, runner, saved_config):
        mock_client = MagicMock()
        mock_client.conversations_list.return_value = {
            "channels": [{"id": "C1", "name": "general"}],
            "response_metadata": {"next_cursor": ""},
        }
        mock_get_client.return_value = mock_client
        result = runner.invoke(cli, ["resolve-name", "nonexistent", "--cache-only", "--json"])
        assert json.loads(result.output) == {"resolved": {"nonexistent": None}}
        # One list call to build the cache the first time, never a per-name retry.
        assert mock_client.conversations_list.call_count == 1

    @patch("slack_user_cli.get_client")
    def test_cache_only_skips_api_on_user_miss(self, mock_get_client, runner, saved_config):
        mock_client = MagicMock()
        mock_client.users_list.return_value = {"members": [], "response_metadata": {"next_cursor": ""}}
        mock_get_client.return_value = mock_client
        result = runner.invoke(cli, ["resolve-name", "nonexistent", "--type", "user", "--cache-only", "--json"])
        assert json.loads(result.output) == {"resolved": {"nonexistent": None}}
        assert mock_client.users_list.call_count == 1

    @patch("slack_user_cli.get_client")
    def test_text_output_marks_not_found(self, mock_get_client, runner, saved_config):
        mock_client = MagicMock()
        mock_client.conversations_list.return_value = {
            "channels": [],
            "response_metadata": {"next_cursor": ""},
        }
        mock_get_client.return_value = mock_client
        result = runner.invoke(cli, ["resolve-name", "nonexistent"])
        assert "(not found)" in result.output


# -- _channel_type_label tests -----------------------------------------------


class TestChannelTypeLabel:
    def test_im(self):
        assert _channel_type_label({"is_im": True}) == "DM"

    def test_mpim(self):
        assert _channel_type_label({"is_mpim": True}) == "Group DM"

    def test_private(self):
        assert _channel_type_label({"is_private": True}) == "Private"

    def test_public(self):
        assert _channel_type_label({}) == "Public"


# -- _format_ts tests ---------------------------------------------------------


class TestFormatTs:
    def test_valid_timestamp(self):
        # 1700000000 = 2023-11-14 22:13 UTC
        assert _format_ts("1700000000.000000") == "2023-11-14 22:13"

    def test_invalid_timestamp_returns_original(self):
        assert _format_ts("not-a-ts") == "not-a-ts"

    def test_empty_string_returns_original(self):
        assert _format_ts("") == ""


# -- Cache tests --------------------------------------------------------------


class TestSaveCache:
    def test_creates_cache_file(self, tmp_config):
        _save_cache("testws", "channels", {"general": "C1"})
        from slack_user_cli import CONFIG_DIR

        path = CONFIG_DIR / "cache" / "testws" / "channels.json"
        assert path.exists()

    def test_stores_data_with_timestamp(self, tmp_config):
        _save_cache("testws", "channels", {"general": "C1"})
        from slack_user_cli import CONFIG_DIR

        path = CONFIG_DIR / "cache" / "testws" / "channels.json"
        content = json.loads(path.read_text())
        assert content["data"] == {"general": "C1"}

    def test_stores_timestamp(self, tmp_config):
        _save_cache("testws", "channels", {"general": "C1"})
        from slack_user_cli import CONFIG_DIR

        path = CONFIG_DIR / "cache" / "testws" / "channels.json"
        content = json.loads(path.read_text())
        assert "ts" in content


class TestLoadCache:
    def test_returns_none_when_missing(self, tmp_config):
        assert _load_cache("testws", "channels") is None

    def test_returns_data_when_valid(self, tmp_config):
        _save_cache("testws", "channels", {"general": "C1"})
        result = _load_cache("testws", "channels")
        assert result == {"general": "C1"}

    def test_returns_none_when_expired(self, tmp_config):
        _save_cache("testws", "channels", {"general": "C1"})
        from slack_user_cli import CONFIG_DIR

        # Overwrite with an expired timestamp (2 hours ago)
        path = CONFIG_DIR / "cache" / "testws" / "channels.json"
        import time

        expired = json.dumps({"ts": time.time() - 7200, "data": {"general": "C1"}})
        path.write_text(expired)
        assert _load_cache("testws", "channels") is None

    def test_returns_none_on_invalid_json(self, tmp_config):
        from slack_user_cli import CONFIG_DIR

        path = CONFIG_DIR / "cache" / "testws" / "channels.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("not-json")
        assert _load_cache("testws", "channels") is None


class TestBuildChannelCache:
    def test_returns_name_to_id_map(self, mock_client, tmp_config):
        mock_client.conversations_list.return_value = {
            "channels": [
                {"id": "C1", "name": "general"},
                {"id": "C2", "name": "random"},
            ],
            "response_metadata": {"next_cursor": ""},
        }
        result = build_channel_cache(mock_client, "testws")
        assert result == {"general": "C1", "random": "C2"}

    def test_saves_to_disk(self, mock_client, tmp_config):
        mock_client.conversations_list.return_value = {
            "channels": [{"id": "C1", "name": "general"}],
            "response_metadata": {"next_cursor": ""},
        }
        build_channel_cache(mock_client, "testws")
        cached = _load_cache("testws", "channels")
        assert cached == {"general": "C1"}

    def test_follows_pagination(self, mock_client, tmp_config):
        mock_client.conversations_list.side_effect = [
            {
                "channels": [{"id": "C1", "name": "page1"}],
                "response_metadata": {"next_cursor": "cursor1"},
            },
            {
                "channels": [{"id": "C2", "name": "page2"}],
                "response_metadata": {"next_cursor": ""},
            },
        ]
        result = build_channel_cache(mock_client, "testws")
        assert "page1" in result
        assert "page2" in result


class TestBuildUserCache:
    def test_returns_id_to_display(self, mock_client, tmp_config):
        mock_client.users_list.return_value = {
            "members": [
                {
                    "id": "U1",
                    "name": "alice",
                    "real_name": "Alice Smith",
                    "profile": {"display_name": "alice.s"},
                }
            ],
            "response_metadata": {"next_cursor": ""},
        }
        result = build_user_cache(mock_client, "testws")
        assert result["id_to_display"]["U1"] == "alice.s"

    def test_returns_name_to_id(self, mock_client, tmp_config):
        mock_client.users_list.return_value = {
            "members": [
                {
                    "id": "U1",
                    "name": "alice",
                    "profile": {"display_name": "alice.s"},
                }
            ],
            "response_metadata": {"next_cursor": ""},
        }
        result = build_user_cache(mock_client, "testws")
        assert result["name_to_id"]["alice"] == "U1"

    def test_returns_display_to_id(self, mock_client, tmp_config):
        mock_client.users_list.return_value = {
            "members": [
                {
                    "id": "U1",
                    "name": "alice",
                    "profile": {"display_name": "alice.s"},
                }
            ],
            "response_metadata": {"next_cursor": ""},
        }
        result = build_user_cache(mock_client, "testws")
        assert result["display_to_id"]["alice.s"] == "U1"

    def test_saves_to_disk(self, mock_client, tmp_config):
        mock_client.users_list.return_value = {
            "members": [
                {
                    "id": "U1",
                    "name": "bob",
                    "profile": {"display_name": "Bob"},
                }
            ],
            "response_metadata": {"next_cursor": ""},
        }
        build_user_cache(mock_client, "testws")
        cached = _load_cache("testws", "users")
        assert cached["id_to_display"]["U1"] == "Bob"


class TestResolveUserWithCache:
    def test_uses_disk_cache(self, mock_client, tmp_config):
        """When disk cache has the user, don't call the API at all."""
        _save_cache("testws", "users", {
            "id_to_display": {"U1": "alice"},
            "name_to_id": {},
            "display_to_id": {},
        })
        result = resolve_user(mock_client, "U1", workspace="testws")
        assert result == "alice"
        # No API call should have been made
        mock_client.users_info.assert_not_called()

    def test_falls_back_to_api_on_cache_miss(self, mock_client, tmp_config):
        """When disk cache doesn't have the user, fall back to users_info."""
        _save_cache("testws", "users", {
            "id_to_display": {},
            "name_to_id": {},
            "display_to_id": {},
        })
        mock_client.users_info.return_value = {
            "user": {"profile": {"display_name": "bob"}, "real_name": "Bob"}
        }
        result = resolve_user(mock_client, "U999", workspace="testws")
        assert result == "bob"

    def test_no_cache_falls_back_to_api(self, mock_client, tmp_config):
        """When no disk cache exists, fall back to users_info (not build)."""
        mock_client.users_info.return_value = {
            "user": {"profile": {"display_name": "charlie"}}
        }
        result = resolve_user(mock_client, "U1", workspace="testws")
        assert result == "charlie"
        # Should NOT have called users_list (no full cache build)
        mock_client.users_list.assert_not_called()


class TestRefreshCommand:
    @patch("slack_user_cli.get_client")
    def test_refresh_builds_caches(self, mock_get_client, runner, saved_config):
        mock_client = MagicMock()
        mock_client.conversations_list.return_value = {
            "channels": [{"id": "C1", "name": "general"}],
            "response_metadata": {"next_cursor": ""},
        }
        mock_client.users_list.return_value = {
            "members": [
                {
                    "id": "U1",
                    "name": "alice",
                    "profile": {"display_name": "Alice"},
                }
            ],
            "response_metadata": {"next_cursor": ""},
        }
        mock_get_client.return_value = mock_client

        result = runner.invoke(cli, ["refresh"])
        assert "Cache refreshed" in result.output

    @patch("slack_user_cli.get_client")
    def test_refresh_shows_channel_count(self, mock_get_client, runner, saved_config):
        mock_client = MagicMock()
        mock_client.conversations_list.return_value = {
            "channels": [
                {"id": "C1", "name": "a"},
                {"id": "C2", "name": "b"},
            ],
            "response_metadata": {"next_cursor": ""},
        }
        mock_client.users_list.return_value = {
            "members": [],
            "response_metadata": {"next_cursor": ""},
        }
        mock_get_client.return_value = mock_client

        result = runner.invoke(cli, ["refresh"])
        assert "2" in result.output


# -- CLI command tests --------------------------------------------------------


class TestLoginManual:
    @patch("slack_user_cli.WebClient")
    def test_successful_manual_login(self, mock_wc_cls, runner, tmp_config):
        mock_instance = MagicMock()
        mock_instance.auth_test.return_value = {
            "user": "testuser",
            "team": "testteam",
        }
        mock_wc_cls.return_value = mock_instance

        result = runner.invoke(
            cli,
            ["login", "--manual"],
            input="xoxc-token\nxoxd-cookie\n",
        )
        assert "Logged in as" in result.output

    @patch("slack_user_cli.WebClient")
    def test_saves_config_on_login(self, mock_wc_cls, runner, tmp_config):
        mock_instance = MagicMock()
        mock_instance.auth_test.return_value = {
            "user": "u",
            "team": "t",
        }
        mock_wc_cls.return_value = mock_instance

        runner.invoke(
            cli,
            ["login", "--manual"],
            input="xoxc-tok\nxoxd-cook\n",
        )
        config = json.loads(tmp_config.read_text())
        # Multi-workspace format: token stored under workspaces
        assert config["workspaces"]["t"]["token"] == "xoxc-tok"

    @patch("slack_user_cli.WebClient")
    def test_login_fails_on_auth_error(self, mock_wc_cls, runner, tmp_config):
        mock_instance = MagicMock()
        mock_instance.auth_test.side_effect = SlackApiError(
            message="invalid_auth",
            response=MagicMock(
                status_code=200, data={"ok": False, "error": "invalid_auth"}
            ),
        )
        mock_wc_cls.return_value = mock_instance

        result = runner.invoke(
            cli,
            ["login", "--manual"],
            input="bad-token\nbad-cookie\n",
        )
        assert result.exit_code != 0


class TestLoginBrowser:
    @patch("slack_user_cli.subprocess")
    @patch("slack_user_cli.WebClient")
    def test_imports_all_workspaces(
        self, mock_wc_cls, mock_subprocess, runner, tmp_config
    ):
        mock_instance = MagicMock()
        mock_instance.auth_test.side_effect = [
            {"user": "alice", "team": "Team Alpha"},
            {"user": "alice", "team": "Team Beta"},
        ]
        mock_wc_cls.return_value = mock_instance

        # Mock pbpaste returning clipboard content
        mock_subprocess.run.return_value = MagicMock(
            stdout=json.dumps({
                "teams": {
                    "T001": {"name": "Alpha", "token": "xoxc-alpha"},
                    "T002": {"name": "Beta", "token": "xoxc-beta"},
                }
            })
        )

        # Press Enter to confirm copy, then provide d cookie
        result = runner.invoke(
            cli,
            ["login", "--browser"],
            input="\nxoxd-cookie\n",
        )
        assert "Team Alpha" in result.output

    @patch("slack_user_cli.subprocess")
    @patch("slack_user_cli.WebClient")
    def test_saves_both_workspaces(
        self, mock_wc_cls, mock_subprocess, runner, tmp_config
    ):
        mock_instance = MagicMock()
        mock_instance.auth_test.side_effect = [
            {"user": "u1", "team": "WS1"},
            {"user": "u2", "team": "WS2"},
        ]
        mock_wc_cls.return_value = mock_instance

        mock_subprocess.run.return_value = MagicMock(
            stdout=json.dumps({
                "teams": {
                    "T1": {"name": "ws1", "token": "xoxc-1"},
                    "T2": {"name": "ws2", "token": "xoxc-2"},
                }
            })
        )

        runner.invoke(
            cli,
            ["login", "--browser"],
            input="\nxoxd-c\n",
        )
        config = json.loads(tmp_config.read_text())
        assert len(config["workspaces"]) == 2

    @patch("slack_user_cli._choose_default", return_value="WS2")
    @patch("slack_user_cli.subprocess")
    @patch("slack_user_cli.WebClient")
    def test_wires_chosen_default_into_config(
        self, mock_wc_cls, mock_subprocess, mock_choose_default, runner, tmp_config
    ):
        """Whatever _choose_default() picks ends up as config['default'].
        _choose_default's own interactive-vs-non-interactive logic is
        covered directly in TestChooseDefault, without fighting CliRunner
        over sys.stdin."""
        mock_instance = MagicMock()
        mock_instance.auth_test.side_effect = [
            {"user": "u1", "team": "WS1"},
            {"user": "u2", "team": "WS2"},
        ]
        mock_wc_cls.return_value = mock_instance

        mock_subprocess.run.return_value = MagicMock(
            stdout=json.dumps({
                "teams": {
                    "T1": {"name": "ws1", "token": "xoxc-1"},
                    "T2": {"name": "ws2", "token": "xoxc-2"},
                }
            })
        )

        runner.invoke(
            cli,
            ["login", "--browser"],
            input="\nxoxd-c\n",
        )
        config = json.loads(tmp_config.read_text())
        assert config["default"] == "WS2"
        mock_choose_default.assert_called_once_with(["WS1", "WS2"])

    @patch("slack_user_cli.subprocess")
    @patch("slack_user_cli.WebClient")
    def test_rejects_invalid_json(
        self, mock_wc_cls, mock_subprocess, runner, tmp_config
    ):
        mock_subprocess.run.return_value = MagicMock(stdout="not-json")

        result = runner.invoke(
            cli,
            ["login", "--browser"],
            input="\n",
        )
        assert result.exit_code != 0

    @patch("slack_user_cli.subprocess")
    @patch("slack_user_cli.WebClient")
    def test_rejects_empty_clipboard(
        self, mock_wc_cls, mock_subprocess, runner, tmp_config
    ):
        mock_subprocess.run.return_value = MagicMock(stdout="")

        result = runner.invoke(
            cli,
            ["login", "--browser"],
            input="\n",
        )
        assert result.exit_code != 0

    @patch("slacktokens.get_cookie")
    @patch("slack_user_cli.subprocess")
    @patch("slack_user_cli.WebClient")
    def test_skips_cookie_prompt_when_already_stored(
        self, mock_wc_cls, mock_subprocess, mock_get_cookie, runner, saved_config
    ):
        """When desktop-app cookie extraction fails but a cookie is already
        in config, reuse it (accepting the default) instead of demanding a
        fresh paste."""
        mock_instance = MagicMock()
        mock_instance.auth_test.return_value = {
            "user": "u", "team": "New Team"
        }
        mock_wc_cls.return_value = mock_instance

        mock_subprocess.run.return_value = MagicMock(
            stdout=json.dumps({
                "teams": {"T1": {"name": "new", "token": "xoxc-new"}}
            })
        )

        # No desktop app / browser to extract a fresh cookie from
        mock_get_cookie.side_effect = Exception("no browser found")

        # Enter to confirm copy, then Enter again to accept the stored
        # cookie as the prompt's default
        result = runner.invoke(
            cli,
            ["login", "--browser"],
            input="\n\n",
        )
        assert "New Team" in result.output
        config = json.loads(saved_config.read_text())
        assert config["cookie"] == "xoxd-test"


class TestLoginAuto:
    """slacktokens returns nested dicts, not plain strings:

    tokens: {workspace_url: {'token': str, 'name': str}, ...}
    cookie: {'name': 'd', 'value': str}

    _login_auto must unwrap both before handing them to WebClient/config.
    """

    @patch("slacktokens.get_tokens_and_cookie")
    @patch("slack_user_cli.WebClient")
    def test_passes_plain_string_token_to_webclient(
        self, mock_wc_cls, mock_get_tokens_and_cookie, runner, tmp_config
    ):
        mock_instance = MagicMock()
        mock_instance.auth_test.return_value = {"user": "u", "team": "Team Alpha"}
        mock_wc_cls.return_value = mock_instance
        mock_get_tokens_and_cookie.return_value = {
            "tokens": {"T001": {"token": "xoxc-alpha", "name": "Alpha"}},
            "cookie": {"name": "d", "value": "xoxd-cookie"},
        }

        result = runner.invoke(cli, ["login", "--auto"])

        assert result.exit_code == 0
        _, kwargs = mock_wc_cls.call_args
        assert kwargs["token"] == "xoxc-alpha"

    @patch("slacktokens.get_tokens_and_cookie")
    @patch("slack_user_cli.WebClient")
    def test_saves_plain_string_cookie(
        self, mock_wc_cls, mock_get_tokens_and_cookie, runner, tmp_config
    ):
        mock_instance = MagicMock()
        mock_instance.auth_test.return_value = {"user": "u", "team": "Team Alpha"}
        mock_wc_cls.return_value = mock_instance
        mock_get_tokens_and_cookie.return_value = {
            "tokens": {"T001": {"token": "xoxc-alpha", "name": "Alpha"}},
            "cookie": {"name": "d", "value": "xoxd-cookie"},
        }

        runner.invoke(cli, ["login", "--auto"])

        config = json.loads(tmp_config.read_text())
        assert config["cookie"] == "xoxd-cookie"

    @patch("slacktokens.get_tokens_and_cookie")
    @patch("slack_user_cli.WebClient")
    def test_saves_all_workspaces_by_name(
        self, mock_wc_cls, mock_get_tokens_and_cookie, runner, tmp_config
    ):
        mock_instance = MagicMock()
        mock_instance.auth_test.side_effect = [
            {"user": "u1", "team": "Team Alpha"},
            {"user": "u2", "team": "Team Beta"},
        ]
        mock_wc_cls.return_value = mock_instance
        mock_get_tokens_and_cookie.return_value = {
            "tokens": {
                "T001": {"token": "xoxc-alpha", "name": "Alpha"},
                "T002": {"token": "xoxc-beta", "name": "Beta"},
            },
            "cookie": {"name": "d", "value": "xoxd-cookie"},
        }

        runner.invoke(cli, ["login", "--auto"])

        config = json.loads(tmp_config.read_text())
        assert len(config["workspaces"]) == 2

    @patch("slacktokens.get_tokens_and_cookie")
    def test_raises_when_no_tokens_found(
        self, mock_get_tokens_and_cookie, runner, tmp_config
    ):
        mock_get_tokens_and_cookie.return_value = {"tokens": {}, "cookie": {}}

        result = runner.invoke(cli, ["login", "--auto"])

        assert result.exit_code != 0

    @patch("slacktokens.get_tokens_and_cookie")
    def test_skips_malformed_token_entries(
        self, mock_get_tokens_and_cookie, runner, tmp_config
    ):
        """A workspace entry missing its 'token' key must be filtered out,
        not passed through to WebClient (which would blow up on empty auth)."""
        mock_get_tokens_and_cookie.return_value = {
            "tokens": {"T001": {"name": "Alpha"}},
            "cookie": {"name": "d", "value": "xoxd-cookie"},
        }

        result = runner.invoke(cli, ["login", "--auto"])

        assert result.exit_code != 0
        assert "No tokens found" in result.output

    @patch("slacktokens.get_tokens_and_cookie")
    @patch("slack_user_cli.WebClient")
    def test_positional_auto_exits_zero(
        self, mock_wc_cls, mock_get_tokens_and_cookie, runner, tmp_config
    ):
        mock_instance = MagicMock()
        mock_instance.auth_test.return_value = {"user": "u", "team": "Team Alpha"}
        mock_wc_cls.return_value = mock_instance
        mock_get_tokens_and_cookie.return_value = {
            "tokens": {"T001": {"token": "xoxc-alpha", "name": "Alpha"}},
            "cookie": {"name": "d", "value": "xoxd-cookie"},
        }

        result = runner.invoke(cli, ["login", "auto"])

        assert result.exit_code == 0

    def test_rejects_conflicting_modes(self, runner, tmp_config):
        result = runner.invoke(cli, ["login", "auto", "--manual"])

        assert result.exit_code != 0

    @patch("slacktokens.get_tokens_and_cookie")
    def test_desktop_extraction_error_is_click_exception(
        self, mock_get_tokens_and_cookie, runner, tmp_config
    ):
        mock_get_tokens_and_cookie.side_effect = RuntimeError(
            "Slack's Local Storage database appears to be locked. Have you quit Slack?"
        )

        result = runner.invoke(cli, ["login", "auto"])

        assert "Traceback" not in result.output


class TestSnapshotLeveldb:
    """Copy Slack's LevelDB without LOCK so login works while the app is running."""

    def _seed_db(self, path: Path):
        import leveldb

        path.mkdir()
        db = leveldb.LevelDB(str(path))
        db.Put(b"k", b"v")
        return db

    def test_omits_lock_file(self, tmp_path):
        src = tmp_path / "src"
        db = self._seed_db(src)
        del db
        snap = _snapshot_leveldb(src)
        try:
            omitted = not (snap / "LOCK").exists()
        finally:
            shutil.rmtree(snap.parent, ignore_errors=True)
        assert omitted

    def test_copy_readable_while_source_locked(self, tmp_path):
        import leveldb

        src = tmp_path / "src"
        holder = self._seed_db(src)
        snap = _snapshot_leveldb(src)
        try:
            reader = leveldb.LevelDB(str(snap))
            value = reader.Get(b"k")
            del reader
        finally:
            del holder
            shutil.rmtree(snap.parent, ignore_errors=True)
        assert value == b"v"

    def test_unlocked_context_reads_locked_source(self, tmp_path):
        import leveldb

        src = tmp_path / "src"
        holder = self._seed_db(src)
        try:
            with _unlocked_slack_leveldb():
                db = leveldb.LevelDB(str(src))
                value = db.Get(b"k")
                del db
        finally:
            del holder
        assert value == b"v"

    def test_unlocked_context_deletes_snapshot(self, tmp_path):
        import leveldb
        import tempfile

        src = tmp_path / "src"
        holder = self._seed_db(src)
        before = set(Path(tempfile.gettempdir()).glob("slack-user-cli-leveldb-*"))
        try:
            with _unlocked_slack_leveldb():
                db = leveldb.LevelDB(str(src))
                db.Get(b"k")
                del db
            after = set(Path(tempfile.gettempdir()).glob("slack-user-cli-leveldb-*"))
        finally:
            del holder
        assert after == before

    def test_snapshot_cleans_up_on_copy_failure(self, tmp_path):
        import tempfile

        before = set(Path(tempfile.gettempdir()).glob("slack-user-cli-leveldb-*"))
        with pytest.raises(Exception):
            _snapshot_leveldb(tmp_path / "missing")
        after = set(Path(tempfile.gettempdir()).glob("slack-user-cli-leveldb-*"))
        assert after == before


class TestWhoamiCommand:
    @pytest.fixture()
    def auth_client(self):
        """A client whose auth.test succeeds with a full identity payload."""
        client = MagicMock()
        client.auth_test.return_value = {
            "ok": True,
            "user": "alice",
            "user_id": "U123",
            "team": "testteam",
            "team_id": "T456",
            "url": "https://testteam.slack.com/",
        }
        return client

    @patch("slack_user_cli.get_client")
    def test_shows_user_name(self, mock_get_client, auth_client, runner, saved_config):
        mock_get_client.return_value = auth_client
        result = runner.invoke(cli, ["whoami"])
        assert "alice" in result.output

    @patch("slack_user_cli.get_client")
    def test_shows_user_id(self, mock_get_client, auth_client, runner, saved_config):
        mock_get_client.return_value = auth_client
        result = runner.invoke(cli, ["whoami"])
        assert "U123" in result.output

    @patch("slack_user_cli.get_client")
    def test_json_reports_user_id(self, mock_get_client, auth_client, runner, saved_config):
        mock_get_client.return_value = auth_client
        result = runner.invoke(cli, ["whoami", "--json"])
        assert json.loads(result.output)["user_id"] == "U123"

    @patch("slack_user_cli.get_client")
    def test_json_reports_team_id(self, mock_get_client, auth_client, runner, saved_config):
        mock_get_client.return_value = auth_client
        result = runner.invoke(cli, ["whoami", "--json"])
        assert json.loads(result.output)["team_id"] == "T456"

    @patch("slack_user_cli.get_client")
    def test_json_reports_active_workspace(
        self, mock_get_client, auth_client, runner, saved_config
    ):
        """The workspace name comes from local config, not the API response —
        it is the key the caches and -w flag are addressed by."""
        mock_get_client.return_value = auth_client
        result = runner.invoke(cli, ["whoami", "--json"])
        assert json.loads(result.output)["workspace"] == "testteam"

    @patch("slack_user_cli.get_client")
    def test_missing_fields_render_as_empty(self, mock_get_client, runner, saved_config):
        mock_client = MagicMock()
        mock_client.auth_test.return_value = {"ok": True, "user": "alice"}
        mock_get_client.return_value = mock_client
        result = runner.invoke(cli, ["whoami", "--json"])
        assert json.loads(result.output)["team_id"] == ""

    @patch("slack_user_cli.get_client")
    def test_expired_credentials_exit_nonzero(self, mock_get_client, runner, saved_config):
        mock_client = MagicMock()
        mock_client.auth_test.side_effect = SlackApiError(
            "invalid_auth", {"ok": False, "error": "invalid_auth"}
        )
        mock_get_client.return_value = mock_client
        result = runner.invoke(cli, ["whoami"])
        assert result.exit_code != 0

    @patch("slack_user_cli.get_client")
    def test_expired_credentials_suggest_login(
        self, mock_get_client, runner, saved_config
    ):
        mock_client = MagicMock()
        mock_client.auth_test.side_effect = SlackApiError(
            "invalid_auth", {"ok": False, "error": "invalid_auth"}
        )
        mock_get_client.return_value = mock_client
        result = runner.invoke(cli, ["whoami"])
        assert "invalid_auth" in result.output

    def test_not_logged_in_exits_nonzero(self, runner, tmp_config):
        result = runner.invoke(cli, ["whoami"])
        assert result.exit_code != 0


class TestChannelsCommand:
    @patch("slack_user_cli.get_client")
    def test_lists_joined_channels(self, mock_get_client, runner, saved_config):
        mock_client = MagicMock()
        mock_client.conversations_list.return_value = {
            "channels": [
                {
                    "id": "C1",
                    "name": "general",
                    "is_member": True,
                    "num_members": 42,
                    "topic": {"value": "General discussion"},
                }
            ],
            "response_metadata": {"next_cursor": ""},
        }
        mock_get_client.return_value = mock_client

        result = runner.invoke(cli, ["channels", "--names"])
        assert "general" in result.output

    @patch("slack_user_cli.get_client")
    def test_default_emits_channel_id(
        self, mock_get_client, runner, saved_config
    ):
        mock_client = MagicMock()
        mock_client.conversations_list.return_value = {
            "channels": [
                {
                    "id": "C1",
                    "name": "general",
                    "is_member": True,
                    "num_members": 1,
                    "topic": {"value": ""},
                }
            ],
            "response_metadata": {"next_cursor": ""},
        }
        mock_get_client.return_value = mock_client

        result = runner.invoke(cli, ["channels"])
        assert "C1" in result.output

    @patch("slack_user_cli.get_client")
    def test_json_emits_id_and_name(
        self, mock_get_client, runner, saved_config
    ):
        mock_client = MagicMock()
        mock_client.conversations_list.return_value = {
            "channels": [
                {
                    "id": "C1",
                    "name": "general",
                    "is_member": True,
                    "num_members": 1,
                    "topic": {"value": ""},
                }
            ],
            "response_metadata": {"next_cursor": ""},
        }
        mock_get_client.return_value = mock_client

        result = runner.invoke(cli, ["channels", "--json"])
        payload = json.loads(result.output)
        assert payload["channels"][0]["id"] == "C1"

    @patch("slack_user_cli.get_client")
    def test_hides_unjoined_channels_by_default(
        self, mock_get_client, runner, saved_config
    ):
        mock_client = MagicMock()
        mock_client.conversations_list.return_value = {
            "channels": [
                {
                    "id": "C1",
                    "name": "joined",
                    "is_member": True,
                    "num_members": 5,
                    "topic": {"value": ""},
                },
                {
                    "id": "C2",
                    "name": "not-joined",
                    "is_member": False,
                    "num_members": 100,
                    "topic": {"value": ""},
                },
            ],
            "response_metadata": {"next_cursor": ""},
        }
        mock_get_client.return_value = mock_client

        result = runner.invoke(cli, ["channels"])
        assert "not-joined" not in result.output

    @patch("slack_user_cli.get_client")
    def test_all_flag_shows_unjoined(
        self, mock_get_client, runner, saved_config
    ):
        mock_client = MagicMock()
        mock_client.conversations_list.return_value = {
            "channels": [
                {
                    "id": "C2",
                    "name": "not-joined",
                    "is_member": False,
                    "num_members": 100,
                    "topic": {"value": ""},
                },
            ],
            "response_metadata": {"next_cursor": ""},
        }
        mock_get_client.return_value = mock_client

        result = runner.invoke(cli, ["channels", "--all", "--names"])
        assert "not-joined" in result.output

    @patch("slack_user_cli.get_client")
    def test_shows_member_count(self, mock_get_client, runner, saved_config):
        mock_client = MagicMock()
        mock_client.conversations_list.return_value = {
            "channels": [
                {
                    "id": "C1",
                    "name": "dev",
                    "is_member": True,
                    "num_members": 15,
                    "topic": {"value": ""},
                }
            ],
            "response_metadata": {"next_cursor": ""},
        }
        mock_get_client.return_value = mock_client

        result = runner.invoke(cli, ["channels"])
        assert "15" in result.output


class TestReadCommand:
    @patch("slack_user_cli.get_client")
    def test_read_displays_messages(self, mock_get_client, runner, saved_config):
        mock_client = MagicMock()
        # resolve_channel: pass through ID
        mock_client.conversations_list.return_value = {
            "channels": [{"id": "C1", "name": "general"}],
            "response_metadata": {"next_cursor": ""},
        }
        mock_client.conversations_history.return_value = {
            "messages": [
                {"user": "U1", "text": "hello world", "ts": "1700000000.000"},
            ],
            "response_metadata": {"next_cursor": ""},
        }
        mock_client.users_info.return_value = {
            "user": {"profile": {"display_name": "alice"}}
        }
        mock_get_client.return_value = mock_client

        result = runner.invoke(cli, ["read", "general", "--limit", "5"])
        assert "hello world" in result.output

    @patch("slack_user_cli.get_client")
    def test_read_resolves_usernames(
        self, mock_get_client, runner, saved_config
    ):
        mock_client = MagicMock()
        mock_client.conversations_list.return_value = {
            "channels": [{"id": "C1", "name": "general"}],
            "response_metadata": {"next_cursor": ""},
        }
        mock_client.conversations_history.return_value = {
            "messages": [
                {"user": "U1", "text": "hi", "ts": "1700000000.000"},
            ],
            "response_metadata": {"next_cursor": ""},
        }
        mock_client.users_info.return_value = {
            "user": {"profile": {"display_name": "bob"}}
        }
        mock_get_client.return_value = mock_client

        result = runner.invoke(cli, ["read", "general", "--names"])
        assert "bob" in result.output

    @patch("slack_user_cli.get_client")
    def test_read_default_emits_user_id(
        self, mock_get_client, runner, saved_config
    ):
        mock_client = MagicMock()
        mock_client.conversations_list.return_value = {
            "channels": [{"id": "C1", "name": "general"}],
            "response_metadata": {"next_cursor": ""},
        }
        mock_client.conversations_history.return_value = {
            "messages": [{"user": "U99", "text": "hi", "ts": "1700000000.000"}],
            "response_metadata": {"next_cursor": ""},
        }
        mock_get_client.return_value = mock_client

        result = runner.invoke(cli, ["read", "general"])
        assert "U99" in result.output
        # Without --names we must not call users_info
        mock_client.users_info.assert_not_called()

    @patch("slack_user_cli.get_client")
    def test_read_json_emits_raw_user_id(
        self, mock_get_client, runner, saved_config
    ):
        mock_client = MagicMock()
        mock_client.conversations_list.return_value = {
            "channels": [{"id": "C1", "name": "general"}],
            "response_metadata": {"next_cursor": ""},
        }
        mock_client.conversations_history.return_value = {
            "messages": [{"user": "U99", "text": "hi", "ts": "1700000000.000"}],
            "response_metadata": {"next_cursor": ""},
        }
        mock_get_client.return_value = mock_client

        result = runner.invoke(cli, ["read", "general", "--json"])
        payload = json.loads(result.output)
        assert payload["messages"][0]["user"] == "U99"

    @patch("slack_user_cli.get_client")
    def test_keep_since_drops_fully_stale_thread(
        self, mock_get_client, runner, saved_config
    ):
        mock_client = MagicMock()
        mock_client.conversations_list.return_value = {
            "channels": [{"id": "C1", "name": "general"}],
            "response_metadata": {"next_cursor": ""},
        }
        mock_client.conversations_history.return_value = {
            "messages": [{"user": "U1", "text": "old", "ts": "1700000000.000000"}],
            "response_metadata": {"next_cursor": ""},
        }
        mock_get_client.return_value = mock_client

        result = runner.invoke(
            cli, ["read", "general", "--keep-since", "2026-01-01", "--json"]
        )
        assert json.loads(result.output)["messages"] == []

    @patch("slack_user_cli.get_client")
    def test_keep_since_keeps_thread_with_post_cutoff_reply(
        self, mock_get_client, runner, saved_config
    ):
        mock_client = MagicMock()
        mock_client.conversations_list.return_value = {
            "channels": [{"id": "C1", "name": "general"}],
            "response_metadata": {"next_cursor": ""},
        }
        mock_client.conversations_history.return_value = {
            "messages": [
                {
                    "user": "U1",
                    "text": "old parent",
                    "ts": "1700000000.000000",
                    "thread_ts": "1700000000.000000",
                    "reply_count": 1,
                }
            ],
            "response_metadata": {"next_cursor": ""},
        }
        # cutoff = 2026-01-01T00:00:00Z; reply lands well after it.
        mock_client.conversations_replies.return_value = {
            "messages": [
                {"user": "U1", "text": "old parent", "ts": "1700000000.000000"},
                {"user": "U2", "text": "new reply", "ts": "1790000000.000000"},
            ],
            "response_metadata": {"next_cursor": ""},
        }
        mock_get_client.return_value = mock_client

        result = runner.invoke(
            cli, ["read", "general", "--keep-since", "2026-01-01", "--json"]
        )
        payload = json.loads(result.output)
        assert len(payload["messages"]) == 1
        parent = payload["messages"][0]
        assert parent["after_cutoff"] is False
        assert parent["replies"][0]["after_cutoff"] is True

    @patch("slack_user_cli.get_client")
    def test_keep_since_implies_thread_expansion(
        self, mock_get_client, runner, saved_config
    ):
        """--keep-since must see reply timestamps even without --expand-thread."""
        mock_client = MagicMock()
        mock_client.conversations_list.return_value = {
            "channels": [{"id": "C1", "name": "general"}],
            "response_metadata": {"next_cursor": ""},
        }
        mock_client.conversations_history.return_value = {
            "messages": [
                {
                    "user": "U1",
                    "text": "old parent",
                    "ts": "1700000000.000000",
                    "thread_ts": "1700000000.000000",
                    "reply_count": 1,
                }
            ],
            "response_metadata": {"next_cursor": ""},
        }
        mock_client.conversations_replies.return_value = {
            "messages": [
                {"user": "U1", "text": "old parent", "ts": "1700000000.000000"},
                {"user": "U2", "text": "new reply", "ts": "1790000000.000000"},
            ],
            "response_metadata": {"next_cursor": ""},
        }
        mock_get_client.return_value = mock_client

        result = runner.invoke(
            cli, ["read", "general", "--keep-since", "2026-01-01", "--json"]
        )
        assert mock_client.conversations_replies.called
        assert len(json.loads(result.output)["messages"]) == 1


# A real Grafana on-call handoff: `text` is a one-line summary and every useful
# field lives in the section blocks.
HANDOFF_BLOCKS = [
    {
        "type": "section",
        "text": {"type": "mrkdwn", "text": "On-call shifts update for schedule *Product On-Call*"},
    },
    {
        "type": "section",
        "text": {"type": "mrkdwn", "text": "*New on-call shift*\nsethschmidt (<@U1>)"},
    },
    {"type": "actions", "elements": [{"type": "button"}]},
]


class TestExtractBlockText:
    def test_returns_section_text(self):
        assert "sethschmidt (<@U1>)" in _extract_block_text(HANDOFF_BLOCKS)

    def test_joins_sections_in_order(self):
        assert _extract_block_text(HANDOFF_BLOCKS).startswith("On-call shifts update")

    def test_skips_non_text_blocks(self):
        assert "button" not in _extract_block_text(HANDOFF_BLOCKS)

    def test_reads_section_fields(self):
        blocks = [{"type": "section", "fields": [{"text": "shift: 13:00"}]}]
        assert _extract_block_text(blocks) == "shift: 13:00"

    def test_reads_header_blocks(self):
        blocks = [{"type": "header", "text": {"text": "Shift changed"}}]
        assert _extract_block_text(blocks) == "Shift changed"

    @pytest.mark.parametrize("blocks", [None, [], [{"type": "divider"}]])
    def test_returns_empty_when_nothing_to_extract(self, blocks):
        assert _extract_block_text(blocks) == ""


class TestReadBlocksFlag:
    @staticmethod
    def _client(message):
        client = MagicMock()
        client.conversations_list.return_value = {
            "channels": [{"id": "C1", "name": "general"}],
            "response_metadata": {"next_cursor": ""},
        }
        client.conversations_history.return_value = {
            "messages": [message],
            "response_metadata": {"next_cursor": ""},
        }
        client.users_info.return_value = {"user": {"profile": {"display_name": "grafana"}}}
        return client

    @patch("slack_user_cli.get_client")
    def test_blocks_flag_emits_block_text(self, mock_get_client, runner, saved_config):
        mock_get_client.return_value = self._client(
            {"user": "U1", "text": "shift changed", "ts": "1700000000.000",
             "blocks": HANDOFF_BLOCKS}
        )
        result = runner.invoke(cli, ["read", "general", "--json", "--blocks"])
        entry = json.loads(result.output)["messages"][0]
        assert "sethschmidt" in entry["block_text"]

    @patch("slack_user_cli.get_client")
    def test_without_flag_block_text_is_absent(self, mock_get_client, runner, saved_config):
        mock_get_client.return_value = self._client(
            {"user": "U1", "text": "shift changed", "ts": "1700000000.000",
             "blocks": HANDOFF_BLOCKS}
        )
        result = runner.invoke(cli, ["read", "general", "--json"])
        assert "block_text" not in json.loads(result.output)["messages"][0]

    @patch("slack_user_cli.get_client")
    def test_omits_block_text_that_only_restates_text(
        self, mock_get_client, runner, saved_config
    ):
        mock_get_client.return_value = self._client(
            {"user": "U1", "text": "hello", "ts": "1700000000.000",
             "blocks": [{"type": "section", "text": {"text": "hello"}}]}
        )
        result = runner.invoke(cli, ["read", "general", "--json", "--blocks"])
        assert "block_text" not in json.loads(result.output)["messages"][0]


class TestFilterKeepSince:
    def test_drops_thread_with_nothing_after_cutoff(self):
        messages = [{"ts": "100.0", "_replies": [{"ts": "150.0"}]}]
        assert _filter_keep_since(messages, "200.0") == []

    def test_keeps_thread_whose_parent_is_after_cutoff(self):
        messages = [{"ts": "300.0"}]
        kept = _filter_keep_since(messages, "200.0")
        assert kept[0]["after_cutoff"] is True

    def test_keeps_thread_whose_only_a_reply_is_after_cutoff(self):
        messages = [{"ts": "100.0", "_replies": [{"ts": "300.0"}]}]
        kept = _filter_keep_since(messages, "200.0")
        assert len(kept) == 1
        assert kept[0]["after_cutoff"] is False
        assert kept[0]["_replies"][0]["after_cutoff"] is True

    def test_tags_every_reply_independently(self):
        messages = [
            {"ts": "300.0", "_replies": [{"ts": "100.0"}, {"ts": "400.0"}]}
        ]
        kept = _filter_keep_since(messages, "200.0")
        replies = kept[0]["_replies"]
        assert replies[0]["after_cutoff"] is False
        assert replies[1]["after_cutoff"] is True

    def test_string_comparison_matches_numeric_at_equal_width(self):
        # Guards the string-compare shortcut: only valid because both sides
        # are fixed-width "<10 digits>.<6 digits>" — this pins that shape.
        assert _filter_keep_since([{"ts": "1699999999.999999"}], "1700000000.000000") == []
        assert _filter_keep_since([{"ts": "1700000000.000000"}], "1700000000.000000") != []


class TestThreadCommand:
    @patch("slack_user_cli.get_client")
    def test_thread_displays_replies(
        self, mock_get_client, runner, saved_config
    ):
        mock_client = MagicMock()
        mock_client.conversations_replies.return_value = {
            "messages": [
                {
                    "user": "U1",
                    "text": "parent message",
                    "ts": "1700000000.000",
                },
                {
                    "user": "U2",
                    "text": "reply here",
                    "ts": "1700000001.000",
                },
            ],
            "response_metadata": {"next_cursor": ""},
        }
        mock_client.users_info.return_value = {
            "user": {"profile": {"display_name": "charlie"}}
        }
        mock_get_client.return_value = mock_client

        result = runner.invoke(
            cli, ["thread", "C12345ABC", "1700000000.000"]
        )
        assert "reply here" in result.output


class TestUsersCommand:
    @patch("slack_user_cli.get_client")
    def test_lists_users(self, mock_get_client, runner, saved_config):
        mock_client = MagicMock()
        mock_client.users_list.return_value = {
            "members": [
                {
                    "id": "U1",
                    "name": "alice",
                    "profile": {
                        "display_name": "Alice",
                        "real_name": "Alice Smith",
                        "status_emoji": "",
                        "status_text": "",
                    },
                }
            ],
            "response_metadata": {"next_cursor": ""},
        }
        mock_get_client.return_value = mock_client

        result = runner.invoke(cli, ["users", "--names"])
        assert "Alice" in result.output

    @patch("slack_user_cli.get_client")
    def test_users_default_emits_id(
        self, mock_get_client, runner, saved_config
    ):
        mock_client = MagicMock()
        mock_client.users_list.return_value = {
            "members": [
                {
                    "id": "U1",
                    "name": "alice",
                    "profile": {
                        "display_name": "Alice",
                        "real_name": "Alice Smith",
                        "status_emoji": "",
                        "status_text": "",
                    },
                }
            ],
            "response_metadata": {"next_cursor": ""},
        }
        mock_get_client.return_value = mock_client

        result = runner.invoke(cli, ["users"])
        assert "U1" in result.output

    @patch("slack_user_cli.get_client")
    def test_skips_bots(self, mock_get_client, runner, saved_config):
        mock_client = MagicMock()
        mock_client.users_list.return_value = {
            "members": [
                {
                    "id": "U1",
                    "name": "slackbot",
                    "is_bot": True,
                    "profile": {
                        "display_name": "Slackbot",
                        "real_name": "Slackbot",
                        "status_emoji": "",
                        "status_text": "",
                    },
                },
                {
                    "id": "U2",
                    "name": "human",
                    "profile": {
                        "display_name": "Human",
                        "real_name": "Human User",
                        "status_emoji": "",
                        "status_text": "",
                    },
                },
            ],
            "response_metadata": {"next_cursor": ""},
        }
        mock_get_client.return_value = mock_client

        result = runner.invoke(cli, ["users"])
        assert "Slackbot" not in result.output


class TestSendCommand:
    @patch("slack_user_cli.get_client")
    def test_send_message(self, mock_get_client, runner, saved_config):
        mock_client = MagicMock()
        mock_client.conversations_list.return_value = {
            "channels": [{"id": "C1", "name": "general"}],
            "response_metadata": {"next_cursor": ""},
        }
        mock_client.chat_postMessage.return_value = {"ts": "123.456"}
        mock_get_client.return_value = mock_client

        result = runner.invoke(cli, ["send", "general", "hello"])
        assert "Message sent" in result.output

    @patch("slack_user_cli.get_client")
    def test_send_calls_api_with_text(
        self, mock_get_client, runner, saved_config
    ):
        mock_client = MagicMock()
        mock_client.conversations_list.return_value = {
            "channels": [{"id": "C1", "name": "general"}],
            "response_metadata": {"next_cursor": ""},
        }
        mock_client.chat_postMessage.return_value = {"ts": "1.0"}
        mock_get_client.return_value = mock_client

        runner.invoke(cli, ["send", "general", "test msg"])
        mock_client.chat_postMessage.assert_called_once_with(
            channel="C1", text="test msg"
        )


class TestDmCommand:
    @patch("slack_user_cli.get_client")
    def test_dm_send(self, mock_get_client, runner, saved_config):
        mock_client = MagicMock()
        mock_client.conversations_open.return_value = {
            "channel": {"id": "D99"}
        }
        mock_client.chat_postMessage.return_value = {"ts": "1.0"}
        mock_get_client.return_value = mock_client

        result = runner.invoke(cli, ["dm", "U12345ABC", "hi there"])
        assert "DM sent" in result.output

    @patch("slack_user_cli.get_client")
    def test_dm_read_when_no_message(
        self, mock_get_client, runner, saved_config
    ):
        mock_client = MagicMock()
        mock_client.conversations_open.return_value = {
            "channel": {"id": "D99"}
        }
        mock_client.conversations_history.return_value = {
            "messages": [
                {"user": "U1", "text": "old msg", "ts": "1700000000.000"}
            ]
        }
        mock_client.users_info.return_value = {
            "user": {"profile": {"display_name": "peer"}}
        }
        mock_get_client.return_value = mock_client

        result = runner.invoke(cli, ["dm", "U12345ABC"])
        assert "old msg" in result.output

    @patch("slack_user_cli.get_client")
    def test_dm_keep_since_drops_stale_history(
        self, mock_get_client, runner, saved_config
    ):
        mock_client = MagicMock()
        mock_client.conversations_open.return_value = {"channel": {"id": "D99"}}
        mock_client.conversations_history.return_value = {
            "messages": [{"user": "U1", "text": "old msg", "ts": "1700000000.000000"}]
        }
        mock_get_client.return_value = mock_client

        result = runner.invoke(
            cli, ["dm", "U12345ABC", "--keep-since", "2026-01-01", "--json"]
        )
        assert json.loads(result.output)["messages"] == []

    @patch("slack_user_cli.get_client")
    def test_dm_keep_since_implies_thread_expansion(
        self, mock_get_client, runner, saved_config
    ):
        mock_client = MagicMock()
        mock_client.conversations_open.return_value = {"channel": {"id": "D99"}}
        mock_client.conversations_history.return_value = {
            "messages": [
                {
                    "user": "U1",
                    "text": "old parent",
                    "ts": "1700000000.000000",
                    "thread_ts": "1700000000.000000",
                    "reply_count": 1,
                }
            ]
        }
        mock_client.conversations_replies.return_value = {
            "messages": [
                {"user": "U1", "text": "old parent", "ts": "1700000000.000000"},
                {"user": "U2", "text": "new reply", "ts": "1790000000.000000"},
            ],
            "response_metadata": {"next_cursor": ""},
        }
        mock_get_client.return_value = mock_client

        result = runner.invoke(
            cli, ["dm", "U12345ABC", "--keep-since", "2026-01-01", "--json"]
        )
        payload = json.loads(result.output)
        assert len(payload["messages"]) == 1
        assert payload["messages"][0]["replies"][0]["after_cutoff"] is True


class TestSearchCommand:
    @patch("slack_user_cli.get_client")
    def test_search_displays_results(
        self, mock_get_client, runner, saved_config
    ):
        mock_client = MagicMock()
        mock_client.search_messages.return_value = {
            "messages": {
                "total": 1,
                "paging": {"page": 1, "pages": 1},
                "matches": [
                    {
                        "username": "alice",
                        "text": "found it",
                        "channel": {"name": "general"},
                        "ts": "1700000000.000",
                    }
                ],
            }
        }
        mock_get_client.return_value = mock_client

        result = runner.invoke(cli, ["search", "keyword"])
        assert "found it" in result.output

    @patch("slack_user_cli.get_client")
    def test_search_shows_total(self, mock_get_client, runner, saved_config):
        mock_client = MagicMock()
        mock_client.search_messages.return_value = {
            "messages": {
                "total": 42,
                "paging": {"page": 1, "pages": 3},
                "matches": [],
            }
        }
        mock_get_client.return_value = mock_client

        result = runner.invoke(cli, ["search", "query"])
        assert "42 total matches" in result.output

    @patch("slack_user_cli.get_client")
    def test_search_json_carries_raw_ts(
        self, mock_get_client, runner, saved_config
    ):
        mock_client = MagicMock()
        mock_client.search_messages.return_value = {
            "messages": {
                "total": 1,
                "paging": {"page": 1, "pages": 1},
                "matches": [
                    {
                        "user": "U1",
                        "text": "found it",
                        "channel": {"id": "C1"},
                        "ts": "1777887012.881539",
                    }
                ],
            }
        }
        mock_get_client.return_value = mock_client

        result = runner.invoke(cli, ["search", "keyword", "--json"])
        assert json.loads(result.output)["matches"][0]["raw_ts"] == "1777887012.881539"


# -- Pagination tests ---------------------------------------------------------


class TestPagination:
    @patch("slack_user_cli.get_client")
    def test_channels_follows_cursor(
        self, mock_get_client, runner, saved_config
    ):
        mock_client = MagicMock()
        # First page returns a cursor, second page is empty
        mock_client.conversations_list.side_effect = [
            {
                "channels": [
                    {
                        "id": "C1",
                        "name": "page1",
                        "is_member": True,
                        "num_members": 1,
                        "topic": {"value": ""},
                    }
                ],
                "response_metadata": {"next_cursor": "abc123"},
            },
            {
                "channels": [
                    {
                        "id": "C2",
                        "name": "page2",
                        "is_member": True,
                        "num_members": 2,
                        "topic": {"value": ""},
                    }
                ],
                "response_metadata": {"next_cursor": ""},
            },
        ]
        mock_get_client.return_value = mock_client

        result = runner.invoke(cli, ["channels", "--names"])
        assert "page1" in result.output

    @patch("slack_user_cli.get_client")
    def test_channels_shows_second_page(
        self, mock_get_client, runner, saved_config
    ):
        mock_client = MagicMock()
        mock_client.conversations_list.side_effect = [
            {
                "channels": [
                    {
                        "id": "C1",
                        "name": "first",
                        "is_member": True,
                        "num_members": 1,
                        "topic": {"value": ""},
                    }
                ],
                "response_metadata": {"next_cursor": "next"},
            },
            {
                "channels": [
                    {
                        "id": "C2",
                        "name": "second",
                        "is_member": True,
                        "num_members": 2,
                        "topic": {"value": ""},
                    }
                ],
                "response_metadata": {"next_cursor": ""},
            },
        ]
        mock_get_client.return_value = mock_client

        result = runner.invoke(cli, ["channels", "--names"])
        assert "second" in result.output


# -- Workspace management tests -----------------------------------------------


class TestWorkspacesCommand:
    def test_lists_workspaces(self, runner, saved_config):
        result = runner.invoke(cli, ["workspaces"])
        assert "testteam" in result.output

    def test_shows_default_marker(self, runner, saved_config):
        result = runner.invoke(cli, ["workspaces"])
        assert "yes" in result.output

    def test_errors_when_no_workspaces(self, runner, tmp_config):
        result = runner.invoke(cli, ["workspaces"])
        assert result.exit_code != 0


class TestDefaultCommand:
    def test_sets_default(self, runner, saved_config):
        result = runner.invoke(cli, ["default", "testteam"])
        assert "Default workspace set to" in result.output

    def test_errors_on_unknown_workspace(self, runner, saved_config):
        result = runner.invoke(cli, ["default", "nonexistent"])
        assert result.exit_code != 0


class TestWorkspaceSwitch:
    @patch("slack_user_cli.get_client")
    def test_workspace_flag_passed_to_get_client(
        self, mock_get_client, runner, saved_config
    ):
        mock_client = MagicMock()
        mock_client.conversations_list.return_value = {
            "channels": [],
            "response_metadata": {"next_cursor": ""},
        }
        mock_get_client.return_value = mock_client

        runner.invoke(cli, ["-w", "testteam", "channels"])
        mock_get_client.assert_called_once_with(workspace="testteam")


# -- parse_slack_url tests ----------------------------------------------------


class TestParseSlackUrl:
    def test_extracts_channel_id(self):
        _ws, channel_id, _ts = parse_slack_url(
            "https://acme.slack.com/archives/C01234ABCDE/p1700000000000123"
        )
        assert channel_id == "C01234ABCDE"

    def test_extracts_ts(self):
        _ws, _ch, ts = parse_slack_url(
            "https://acme.slack.com/archives/C01234ABCDE/p1700000000000123"
        )
        assert ts == "1700000000.000123"

    def test_extracts_workspace(self):
        workspace, _ch, _ts = parse_slack_url(
            "https://acme.slack.com/archives/C01234ABCDE/p1700000000000123"
        )
        assert workspace == "acme"

    def test_rejects_non_slack_url(self):
        with pytest.raises(Exception, match="Not a Slack URL"):
            parse_slack_url("https://example.com/archives/C123/p1234567890123456")

    def test_rejects_malformed_path(self):
        with pytest.raises(Exception, match="Malformed Slack permalink"):
            parse_slack_url("https://team.slack.com/messages/C123")


# -- url command tests --------------------------------------------------------


class TestUrlCommand:
    @patch("slack_user_cli.get_client")
    def test_reads_thread(self, mock_get_client, runner, saved_config):
        """url command calls conversations_replies with parsed channel+ts."""
        mock_client = MagicMock()
        mock_client.conversations_replies.return_value = {
            "messages": [
                {"user": "U1", "text": "parent", "ts": "1700000000.000123"},
                {"user": "U2", "text": "reply", "ts": "1700000000.000456"},
            ],
            "response_metadata": {"next_cursor": ""},
        }
        mock_client.users_info.return_value = {
            "user": {"profile": {"display_name": "alice"}}
        }
        mock_get_client.return_value = mock_client

        result = runner.invoke(
            cli,
            ["url", "https://acme.slack.com/archives/C01234ABCDE/p1700000000000123"],
        )
        mock_client.conversations_replies.assert_called_once()

    @patch("slack_user_cli.get_client")
    def test_shows_message_text(self, mock_get_client, runner, saved_config):
        mock_client = MagicMock()
        mock_client.conversations_replies.return_value = {
            "messages": [
                {"user": "U1", "text": "important update", "ts": "1700000000.000123"},
                {"user": "U2", "text": "thanks!", "ts": "1700000000.000456"},
            ],
            "response_metadata": {"next_cursor": ""},
        }
        mock_client.users_info.return_value = {
            "user": {"profile": {"display_name": "bob"}}
        }
        mock_get_client.return_value = mock_client

        result = runner.invoke(
            cli,
            ["url", "https://acme.slack.com/archives/C01234ABCDE/p1700000000000123"],
        )
        assert "important update" in result.output


# -- click / block-kit tests --------------------------------------------------


from slack_user_cli import (  # noqa: E402
    _build_action_payload,
    _extract_actions,
    _select_action_element,
)


class TestExtractActions:
    def test_pulls_button(self):
        blocks = [
            {
                "type": "actions",
                "block_id": "blk1",
                "elements": [
                    {
                        "type": "button",
                        "action_id": "act1",
                        "text": {"type": "plain_text", "text": "Continue"},
                        "value": "v1",
                    }
                ],
            }
        ]
        actions = _extract_actions(blocks)
        assert actions == [
            {
                "type": "button",
                "block_id": "blk1",
                "action_id": "act1",
                "text": "Continue",
                "value": "v1",
            }
        ]

    def test_pulls_radio_buttons(self):
        blocks = [
            {
                "type": "actions",
                "block_id": "blk1",
                "elements": [
                    {
                        "type": "radio_buttons",
                        "action_id": "act1",
                        "options": [
                            {"text": {"type": "plain_text", "text": "Yes"}, "value": "y"},
                            {"text": {"type": "plain_text", "text": "No"}, "value": "n"},
                        ],
                    }
                ],
            }
        ]
        actions = _extract_actions(blocks)
        assert actions[0]["options"] == [
            {"text": "Yes", "value": "y"},
            {"text": "No", "value": "n"},
        ]

    def test_skips_non_actions_blocks(self):
        blocks = [{"type": "section", "text": {"type": "plain_text", "text": "hello"}}]
        assert _extract_actions(blocks) == []

    def test_handles_no_blocks(self):
        assert _extract_actions([]) == []


class TestSelectActionElement:
    @pytest.fixture
    def msg_with_button(self):
        return {
            "blocks": [
                {
                    "type": "actions",
                    "block_id": "blk1",
                    "elements": [
                        {
                            "type": "button",
                            "action_id": "act_a",
                            "text": {"type": "plain_text", "text": "OK"},
                            "value": "ok_value",
                        },
                        {
                            "type": "button",
                            "action_id": "act_b",
                            "text": {"type": "plain_text", "text": "Cancel"},
                            "value": "cancel_value",
                        },
                    ],
                }
            ]
        }

    @pytest.fixture
    def msg_with_radio(self):
        return {
            "blocks": [
                {
                    "type": "actions",
                    "block_id": "blk1",
                    "elements": [
                        {
                            "type": "radio_buttons",
                            "action_id": "act_radio",
                            "options": [
                                {"text": {"type": "plain_text", "text": "Yes"}, "value": "y"},
                                {"text": {"type": "plain_text", "text": "No"}, "value": "n"},
                            ],
                        }
                    ],
                }
            ]
        }

    def test_button_match_by_text(self, msg_with_button):
        block, el, opt = _select_action_element(
            msg_with_button, option_text="Cancel", option_index=None,
            action_id=None, value=None,
        )
        assert el["action_id"] == "act_b"
        assert opt is None

    def test_button_match_by_index(self, msg_with_button):
        block, el, opt = _select_action_element(
            msg_with_button, option_text=None, option_index=1,
            action_id=None, value=None,
        )
        assert el["action_id"] == "act_a"

    def test_button_match_by_value(self, msg_with_button):
        block, el, opt = _select_action_element(
            msg_with_button, option_text=None, option_index=None,
            action_id=None, value="cancel_value",
        )
        assert el["action_id"] == "act_b"

    def test_radio_match_by_option_text(self, msg_with_radio):
        block, el, opt = _select_action_element(
            msg_with_radio, option_text="No", option_index=None,
            action_id=None, value=None,
        )
        assert opt["value"] == "n"

    def test_raises_when_no_actions_block(self):
        msg = {"blocks": [{"type": "section"}]}
        with pytest.raises(Exception, match="no actions block"):
            _select_action_element(msg, None, None, None, None)

    def test_raises_when_no_selector(self, msg_with_button):
        with pytest.raises(Exception, match="Specify which option"):
            _select_action_element(msg_with_button, None, None, None, None)

    def test_raises_on_unknown_text(self, msg_with_button):
        with pytest.raises(Exception, match="not found"):
            _select_action_element(msg_with_button, "Nope", None, None, None)


class TestBuildActionPayload:
    def test_button_payload_shape(self):
        el = {
            "type": "button",
            "action_id": "act1",
            "text": {"type": "plain_text", "text": "OK"},
            "value": "ok",
        }
        actions, state = _build_action_payload(el, "blk1", None)
        assert len(actions) == 1
        assert actions[0]["type"] == "button"
        assert actions[0]["action_id"] == "act1"
        assert actions[0]["block_id"] == "blk1"
        assert actions[0]["value"] == "ok"
        assert state == {"values": {}}

    def test_radio_payload_includes_state(self):
        el = {"type": "radio_buttons", "action_id": "act_r"}
        opt = {"text": {"type": "plain_text", "text": "Yes"}, "value": "y"}
        actions, state = _build_action_payload(el, "blk1", opt)
        assert actions[0]["selected_option"] == opt
        assert state["values"]["blk1"]["act_r"]["selected_option"] == opt

    def test_radio_without_option_raises(self):
        el = {"type": "radio_buttons", "action_id": "act_r"}
        with pytest.raises(Exception, match="requires an option"):
            _build_action_payload(el, "blk1", None)


# -- raw_ts in JSON output ----------------------------------------------------


class TestReadJsonRawTs:
    @patch("slack_user_cli.get_client")
    def test_regular_message_includes_raw_ts(
        self, mock_get_client, runner, saved_config
    ):
        """Every --json message carries the full-precision ts, not just block-kit ones."""
        mock_client = MagicMock()
        mock_client.conversations_list.return_value = {
            "channels": [{"id": "C1", "name": "general"}],
            "response_metadata": {"next_cursor": ""},
        }
        mock_client.conversations_history.return_value = {
            "messages": [{"user": "U1", "text": "hi", "ts": "1700000000.123456"}],
            "response_metadata": {"next_cursor": ""},
        }
        mock_get_client.return_value = mock_client

        result = runner.invoke(cli, ["read", "general", "--json"])
        payload = json.loads(result.output)
        assert payload["messages"][0]["raw_ts"] == "1700000000.123456"

    @patch("slack_user_cli.get_client")
    def test_thread_ts_surfaced_when_present(
        self, mock_get_client, runner, saved_config
    ):
        mock_client = MagicMock()
        mock_client.conversations_list.return_value = {
            "channels": [{"id": "C1", "name": "general"}],
            "response_metadata": {"next_cursor": ""},
        }
        mock_client.conversations_history.return_value = {
            "messages": [
                {
                    "user": "U1",
                    "text": "hi",
                    "ts": "1700000001.000000",
                    "thread_ts": "1700000000.000000",
                    "reply_count": 2,
                }
            ],
            "response_metadata": {"next_cursor": ""},
        }
        mock_get_client.return_value = mock_client

        result = runner.invoke(cli, ["read", "general", "--json"])
        payload = json.loads(result.output)
        assert payload["messages"][0]["thread_ts"] == "1700000000.000000"


# -- read --since -------------------------------------------------------------


class TestReadSince:
    @patch("slack_user_cli.get_client")
    def test_since_passes_oldest(self, mock_get_client, runner, saved_config):
        mock_client = MagicMock()
        mock_client.conversations_list.return_value = {
            "channels": [{"id": "C1", "name": "general"}],
            "response_metadata": {"next_cursor": ""},
        }
        mock_client.conversations_history.return_value = {
            "messages": [],
            "response_metadata": {"next_cursor": ""},
        }
        mock_get_client.return_value = mock_client

        runner.invoke(cli, ["read", "general", "--since", "2026-05-29"])
        assert mock_client.conversations_history.call_args.kwargs["oldest"] == _parse_since(
            "2026-05-29"
        )

    @patch("slack_user_cli.get_client")
    def test_no_since_omits_oldest(self, mock_get_client, runner, saved_config):
        mock_client = MagicMock()
        mock_client.conversations_list.return_value = {
            "channels": [{"id": "C1", "name": "general"}],
            "response_metadata": {"next_cursor": ""},
        }
        mock_client.conversations_history.return_value = {
            "messages": [],
            "response_metadata": {"next_cursor": ""},
        }
        mock_get_client.return_value = mock_client

        runner.invoke(cli, ["read", "general"])
        assert "oldest" not in mock_client.conversations_history.call_args.kwargs


# -- _parse_since -------------------------------------------------------------


class TestParseSince:
    def test_date_only_is_utc_midnight(self):
        # 1970-01-02 00:00 UTC = 86400 seconds since epoch
        assert _parse_since("1970-01-02") == "86400.000000"

    def test_naive_datetime_treated_as_utc(self):
        # 1970-01-01 01:00 UTC = 3600 seconds since epoch
        assert _parse_since("1970-01-01T01:00:00") == "3600.000000"

    def test_invalid_value_raises(self):
        with pytest.raises(Exception, match="not an ISO"):
            _parse_since("last tuesday")


# -- permalink command --------------------------------------------------------


class TestPermalinkCommand:
    @patch("slack_user_cli.get_client")
    def test_calls_get_permalink(self, mock_get_client, runner, saved_config):
        mock_client = MagicMock()
        mock_client.chat_getPermalink.return_value = {"permalink": "https://x/p1"}
        mock_get_client.return_value = mock_client

        runner.invoke(cli, ["permalink", "C12345ABC", "1700000000.000000"])
        mock_client.chat_getPermalink.assert_called_once_with(
            channel="C12345ABC", message_ts="1700000000.000000"
        )

    @patch("slack_user_cli.get_client")
    def test_outputs_url(self, mock_get_client, runner, saved_config):
        mock_client = MagicMock()
        mock_client.chat_getPermalink.return_value = {"permalink": "https://x/p1"}
        mock_get_client.return_value = mock_client

        result = runner.invoke(cli, ["permalink", "C12345ABC", "1700000000.000000"])
        assert "https://x/p1" in result.output

    @patch("slack_user_cli.get_client")
    def test_json_shape(self, mock_get_client, runner, saved_config):
        mock_client = MagicMock()
        mock_client.chat_getPermalink.return_value = {"permalink": "https://x/p1"}
        mock_get_client.return_value = mock_client

        result = runner.invoke(
            cli, ["permalink", "C12345ABC", "1700000000.000000", "--json"]
        )
        payload = json.loads(result.output)
        assert payload["permalinks"]["1700000000.000000"] == "https://x/p1"

    @patch("slack_user_cli.get_client")
    def test_multiple_ts_each_resolved(
        self, mock_get_client, runner, saved_config
    ):
        mock_client = MagicMock()
        mock_client.chat_getPermalink.return_value = {"permalink": "https://x/p"}
        mock_get_client.return_value = mock_client

        runner.invoke(
            cli, ["permalink", "C12345ABC", "1700000000.000000", "1700000001.000000"]
        )
        assert mock_client.chat_getPermalink.call_count == 2

    @patch("slack_user_cli.get_client")
    def test_api_error_recorded_not_raised(
        self, mock_get_client, runner, saved_config
    ):
        mock_client = MagicMock()
        mock_client.chat_getPermalink.side_effect = SlackApiError(
            message="boom",
            response=MagicMock(
                status_code=200, data={"ok": False, "error": "message_not_found"}
            ),
        )
        mock_get_client.return_value = mock_client

        result = runner.invoke(
            cli, ["permalink", "C12345ABC", "1700000000.000000", "--json"]
        )
        payload = json.loads(result.output)
        assert "message_not_found" in payload["permalinks"]["1700000000.000000"]


# -- file attachment tests ----------------------------------------------------


class TestExtractFiles:
    def test_returns_empty_when_no_files(self):
        assert _extract_files({"text": "hi"}) == []

    def test_surfaces_file_name(self):
        msg = {"files": [{"id": "F1", "name": "quote.pdf"}]}
        assert _extract_files(msg)[0]["name"] == "quote.pdf"

    def test_falls_back_to_title_when_no_name(self):
        msg = {"files": [{"id": "F1", "title": "Q3.pdf"}]}
        assert _extract_files(msg)[0]["name"] == "Q3.pdf"

    def test_keeps_download_url(self):
        msg = {"files": [{"id": "F1", "url_private_download": "https://x/dl"}]}
        assert _extract_files(msg)[0]["url_private_download"] == "https://x/dl"

    def test_preserves_size(self):
        msg = {"files": [{"id": "F1", "name": "a.pdf", "size": 1234}]}
        assert _extract_files(msg)[0]["size"] == 1234


class TestMessageToEntryFiles:
    def test_entry_includes_files_key(self, mock_client):
        msg = {"ts": "1.0", "user": "U1", "files": [{"id": "F1", "name": "a.pdf"}]}
        entry = _message_to_entry(mock_client, msg, "", with_names=False)
        assert entry["files"][0]["name"] == "a.pdf"

    def test_entry_omits_files_key_when_none(self, mock_client):
        msg = {"ts": "1.0", "user": "U1", "text": "hi"}
        entry = _message_to_entry(mock_client, msg, "", with_names=False)
        assert "files" not in entry


class TestDownloadFile:
    @patch("requests.get")
    def test_writes_bytes_to_dest(self, mock_get, mock_client, tmp_path):
        mock_get.return_value = MagicMock(content=b"PDFDATA", raise_for_status=lambda: None)
        mock_client.headers = {"cookie": "d=abc"}
        mock_client.token = "xoxc-1"
        path = _download_file(
            mock_client,
            {"id": "F1", "name": "a.pdf", "url_private_download": "https://x/dl"},
            tmp_path,
        )
        assert path.read_bytes() == b"PDFDATA"

    def test_raises_without_url(self, mock_client, tmp_path):
        with pytest.raises(Exception, match="no downloadable URL"):
            _download_file(mock_client, {"id": "F1", "name": "a.pdf"}, tmp_path)

    @patch("requests.get")
    def test_strips_path_traversal_from_name(self, mock_get, mock_client, tmp_path):
        mock_get.return_value = MagicMock(content=b"x", raise_for_status=lambda: None)
        mock_client.headers = {}
        mock_client.token = "t"
        path = _download_file(
            mock_client,
            {"id": "F1", "name": "../../evil.pdf", "url_private": "https://x/p"},
            tmp_path,
        )
        assert path.parent == tmp_path


class TestDownloadCommand:
    @patch("slack_user_cli.get_client")
    def test_list_json_returns_attachments(self, mock_get_client, runner, saved_config):
        mock_client = MagicMock()
        mock_client.conversations_replies.return_value = {
            "messages": [
                {"ts": "1700000000.000000", "files": [{"id": "F1", "name": "q.pdf"}]}
            ]
        }
        mock_get_client.return_value = mock_client
        result = runner.invoke(
            cli,
            ["download", "C123", "1700000000.000000", "--list", "--json"],
        )
        payload = json.loads(result.output)
        assert payload["files"][0]["id"] == "F1"

    @patch("slack_user_cli.get_client")
    def test_requires_ts_for_channel(self, mock_get_client, runner, saved_config):
        mock_get_client.return_value = MagicMock()
        result = runner.invoke(cli, ["download", "C123"])
        assert "Provide a message TS" in result.output

    @patch("slack_user_cli.get_client")
    def test_file_id_uses_files_info(self, mock_get_client, runner, saved_config):
        mock_client = MagicMock()
        mock_client.api_call.return_value = {"file": {"id": "F0123456789", "name": "m.pdf"}}
        mock_get_client.return_value = mock_client
        runner.invoke(cli, ["download", "F0123456789", "--list"])
        assert mock_client.api_call.call_args[0][0] == "files.info"

    @patch("requests.get")
    @patch("slack_user_cli.get_client")
    def test_downloads_to_output_dir(
        self, mock_get_client, mock_get, runner, saved_config, tmp_path
    ):
        mock_client = MagicMock()
        mock_client.conversations_replies.return_value = {
            "messages": [
                {
                    "ts": "1700000000.000000",
                    "files": [
                        {
                            "id": "F1",
                            "name": "q.pdf",
                            "url_private_download": "https://x/dl",
                        }
                    ],
                }
            ]
        }
        mock_get_client.return_value = mock_client
        mock_get.return_value = MagicMock(content=b"DATA", raise_for_status=lambda: None)
        out = tmp_path / "dl"
        runner.invoke(
            cli,
            ["download", "C123", "1700000000.000000", "-o", str(out)],
        )
        assert (out / "q.pdf").read_bytes() == b"DATA"


# -- quoted / shared message tests --------------------------------------------

# A message that shares another message: the original (with its files) lands in
# `attachments`, not in the top-level `files` field.
SHARED_MSG = {
    "ts": "1.0",
    "user": "U1",
    "text": "Forwarding this",
    "attachments": [
        {
            "is_share": True,
            "from_url": "https://x.slack.com/archives/C0SRC/p1780306198826489",
            "author_name": "Genia Shipova",
            "channel_id": "C0SRC",
            "ts": "1780306198.826489",
            "text": "here are the quotes",
            "files": [{"id": "F1", "name": "quote.pdf", "url_private": "https://x/p"}],
        }
    ],
}


class TestExtractShared:
    def test_surfaces_shared_files(self):
        assert _extract_shared(SHARED_MSG)[0]["files"][0]["name"] == "quote.pdf"

    def test_captures_source_url(self):
        assert _extract_shared(SHARED_MSG)[0]["channel"] == "C0SRC"

    def test_captures_author(self):
        assert _extract_shared(SHARED_MSG)[0]["author"] == "Genia Shipova"

    def test_captures_full_text(self):
        assert _extract_shared(SHARED_MSG)[0]["text"] == "here are the quotes"

    def test_ignores_plain_attachments(self):
        msg = {"attachments": [{"title": "a link preview", "text": "no share here"}]}
        assert _extract_shared(msg) == []

    def test_empty_when_no_attachments(self):
        assert _extract_shared({"text": "hi"}) == []


class TestCollectRawFiles:
    def test_includes_shared_message_files(self):
        assert _collect_raw_files(SHARED_MSG)[0]["name"] == "quote.pdf"

    def test_includes_direct_and_shared(self):
        msg = {"files": [{"id": "D1", "name": "direct.pdf"}], **SHARED_MSG}
        names = {f.get("name") for f in _collect_raw_files(msg)}
        assert names == {"direct.pdf", "quote.pdf"}


class TestExtractLinks:
    def test_parses_permalink_from_text(self):
        msg = {"text": "see <https://x.slack.com/archives/C9/p1700000000000000>"}
        assert _extract_links(msg)[0]["channel"] == "C9"

    def test_reinserts_ts_dot(self):
        msg = {"text": "https://x.slack.com/archives/C9/p1700000000000000"}
        assert _extract_links(msg)[0]["ts"] == "1700000000.000000"

    def test_empty_when_no_link(self):
        assert _extract_links({"text": "just words"}) == []


class TestLinkParts:
    def test_returns_none_for_non_permalink(self):
        assert _link_parts("https://example.com/foo") is None


class TestMessageToEntryShared:
    def test_entry_includes_shared(self, mock_client):
        entry = _message_to_entry(mock_client, SHARED_MSG, "", with_names=False)
        assert entry["shared"][0]["files"][0]["name"] == "quote.pdf"


class TestDownloadQuotedMessage:
    @patch("requests.get")
    @patch("slack_user_cli.get_client")
    def test_download_fetches_shared_files(
        self, mock_get_client, mock_get, runner, saved_config, tmp_path
    ):
        mock_client = MagicMock()
        mock_client.conversations_replies.return_value = {
            "messages": [{**SHARED_MSG, "ts": "1700000000.000000"}]
        }
        mock_get_client.return_value = mock_client
        mock_get.return_value = MagicMock(content=b"PDF", raise_for_status=lambda: None)
        out = tmp_path / "dl"
        runner.invoke(cli, ["download", "C123", "1700000000.000000", "-o", str(out)])
        assert (out / "quote.pdf").read_bytes() == b"PDF"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, *sys.argv[1:]]))


# -- Drafts -------------------------------------------------------------------


@pytest.fixture()
def draft_client():
    """Client stub whose channel cache knows #general and whose drafts.create answers."""
    client = MagicMock()
    client.conversations_list.return_value = {
        "channels": [{"id": "C1", "name": "general"}],
        "response_metadata": {"next_cursor": ""},
    }
    client.api_call.return_value = {"ok": True, "draft": {"id": "Dr1"}}
    return client


@pytest.fixture()
def listed_drafts():
    """drafts.list payload: one thread draft with a mention, one sent draft."""
    return {
        "ok": True,
        "drafts": [
            {
                "id": "Dr1",
                "last_updated_ts": "10.5",
                "is_sent": False,
                "is_deleted": False,
                "destinations": [{"channel_id": "C1", "thread_ts": "9.1", "broadcast": False}],
                "blocks": [
                    {
                        "type": "rich_text",
                        "elements": [
                            {
                                "type": "rich_text_section",
                                "elements": [
                                    {"type": "user", "user_id": "U1"},
                                    {"type": "text", "text": " ok"},
                                ],
                            }
                        ],
                    }
                ],
            },
            {"id": "Dr2", "last_updated_ts": "11.0", "is_sent": True, "destinations": [{}], "blocks": []},
        ],
    }


class TestDraftBlocks:
    def test_plain_text_is_one_text_element(self):
        from slack_user_cli import _draft_blocks

        assert _draft_blocks("hi")[0]["elements"][0]["elements"] == [{"type": "text", "text": "hi"}]

    def test_mention_becomes_user_element(self):
        from slack_user_cli import _draft_blocks

        assert _draft_blocks("<@U12AB> yes")[0]["elements"][0]["elements"][0] == {"type": "user", "user_id": "U12AB"}

    def test_text_after_mention_is_kept(self):
        from slack_user_cli import _draft_blocks

        assert _draft_blocks("<@U12AB> yes")[0]["elements"][0]["elements"][1] == {"type": "text", "text": " yes"}


class TestDraftCommand:
    @patch("slack_user_cli.get_client")
    def test_draft_calls_drafts_create(self, mock_get_client, draft_client, runner, saved_config):
        mock_get_client.return_value = draft_client
        runner.invoke(cli, ["draft", "general", "hello"])
        assert draft_client.api_call.call_args.args[0] == "drafts.create"

    @patch("slack_user_cli.get_client")
    def test_draft_never_posts(self, mock_get_client, draft_client, runner, saved_config):
        mock_get_client.return_value = draft_client
        runner.invoke(cli, ["draft", "general", "hello"])
        draft_client.chat_postMessage.assert_not_called()

    @patch("slack_user_cli.get_client")
    def test_draft_targets_resolved_channel(self, mock_get_client, draft_client, runner, saved_config):
        mock_get_client.return_value = draft_client
        runner.invoke(cli, ["draft", "general", "hello"])
        destinations = json.loads(draft_client.api_call.call_args.kwargs["data"]["destinations"])
        assert destinations == [{"channel_id": "C1"}]

    @patch("slack_user_cli.get_client")
    def test_draft_thread_sets_thread_ts(self, mock_get_client, draft_client, runner, saved_config):
        mock_get_client.return_value = draft_client
        runner.invoke(cli, ["draft", "general", "hello", "--thread", "9.1"])
        destinations = json.loads(draft_client.api_call.call_args.kwargs["data"]["destinations"])
        assert destinations == [{"channel_id": "C1", "thread_ts": "9.1", "broadcast": False}]

    @patch("slack_user_cli.get_client")
    def test_draft_json_reports_id(self, mock_get_client, draft_client, runner, saved_config):
        mock_get_client.return_value = draft_client
        result = runner.invoke(cli, ["draft", "general", "hello", "--json"])
        assert json.loads(result.output)["id"] == "Dr1"


class TestDraftsCommand:
    @patch("slack_user_cli.get_client")
    def test_drafts_skips_sent(self, mock_get_client, mock_client, listed_drafts, runner, saved_config):
        mock_client.api_call.return_value = listed_drafts
        mock_get_client.return_value = mock_client
        result = runner.invoke(cli, ["drafts", "--json"])
        assert [d["id"] for d in json.loads(result.output)["drafts"]] == ["Dr1"]

    @patch("slack_user_cli.get_client")
    def test_drafts_flattens_mentions(self, mock_get_client, mock_client, listed_drafts, runner, saved_config):
        mock_client.api_call.return_value = listed_drafts
        mock_get_client.return_value = mock_client
        result = runner.invoke(cli, ["drafts", "--json"])
        assert json.loads(result.output)["drafts"][0]["text"] == "<@U1> ok"

    @patch("slack_user_cli.get_client")
    def test_drafts_reports_thread(self, mock_get_client, mock_client, listed_drafts, runner, saved_config):
        mock_client.api_call.return_value = listed_drafts
        mock_get_client.return_value = mock_client
        result = runner.invoke(cli, ["drafts", "--json"])
        assert json.loads(result.output)["drafts"][0]["thread_ts"] == "9.1"


class TestDraftDeleteCommand:
    @patch("slack_user_cli.get_client")
    def test_delete_targets_draft_id(self, mock_get_client, mock_client, listed_drafts, runner, saved_config):
        mock_client.api_call.return_value = listed_drafts
        mock_get_client.return_value = mock_client
        runner.invoke(cli, ["draft-delete", "Dr1"])
        assert mock_client.api_call.call_args.kwargs["data"]["draft_id"] == "Dr1"

    @patch("slack_user_cli.get_client")
    def test_delete_client_ts_is_newer_than_draft(self, mock_get_client, mock_client, listed_drafts, runner, saved_config):
        mock_client.api_call.return_value = listed_drafts
        mock_get_client.return_value = mock_client
        runner.invoke(cli, ["draft-delete", "Dr1"])
        assert float(mock_client.api_call.call_args.kwargs["data"]["client_last_updated_ts"]) > 10.5

    @patch("slack_user_cli.get_client")
    def test_delete_unknown_id_fails(self, mock_get_client, mock_client, listed_drafts, runner, saved_config):
        mock_client.api_call.return_value = listed_drafts
        mock_get_client.return_value = mock_client
        result = runner.invoke(cli, ["draft-delete", "DrNOPE"])
        assert result.exit_code != 0


@pytest.fixture()
def occupied_client(listed_drafts):
    """Client stub where #general's thread 9.1 already holds draft Dr1."""
    client = MagicMock()
    client.conversations_list.return_value = {
        "channels": [{"id": "C1", "name": "general"}],
        "response_metadata": {"next_cursor": ""},
    }
    occupied = [True]

    def api_call(method, **kwargs):
        if method == "drafts.list":
            return listed_drafts
        if method == "drafts.delete":
            occupied[0] = False
            return {"ok": True}
        if occupied[0]:
            raise SlackApiError("exists", {"ok": False, "error": "attached_draft_exists"})
        return {"ok": True, "draft": {"id": "Dr9"}}

    client.api_call.side_effect = api_call
    return client


class TestDraftReplace:
    @patch("slack_user_cli.get_client")
    def test_occupied_without_replace_fails(self, mock_get_client, occupied_client, runner, saved_config):
        mock_get_client.return_value = occupied_client
        result = runner.invoke(cli, ["draft", "general", "hi", "--thread", "9.1"])
        assert "--replace" in result.output

    @patch("slack_user_cli.get_client")
    def test_replace_deletes_existing(self, mock_get_client, occupied_client, runner, saved_config):
        mock_get_client.return_value = occupied_client
        runner.invoke(cli, ["draft", "general", "hi", "--thread", "9.1", "--replace"])
        deleted = [c.kwargs["data"]["draft_id"] for c in occupied_client.api_call.call_args_list if c.args[0] == "drafts.delete"]
        assert deleted == ["Dr1"]

    @patch("slack_user_cli.get_client")
    def test_replace_creates_new_draft(self, mock_get_client, occupied_client, runner, saved_config):
        mock_get_client.return_value = occupied_client
        result = runner.invoke(cli, ["draft", "general", "hi", "--thread", "9.1", "--replace", "--json"])
        assert json.loads(result.output)["id"] == "Dr9"
