#!/usr/bin/env python3
"""End-to-end tests for tools/claude-artifacts against a local fake of the frame API."""

import json
import os
import subprocess
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools/claude-artifacts"
TOKEN = "secret-token-value"

PAGE_ID = "00a1b2c3-d4e5-4f60-8172-839405a6b7c8"
PAGE_SHORT = "15XP88Jo9VTAWh7nvU1hh9"
DECK_ID = "5f3c2a1e-9b8d-4c7e-a6f5-0e1d2c3b4a59"
DECK_SHORT = "Cm5jC7fkvZj922fdKDPBoN"


def artifact(slug, title, live):
    return {
        "title": title,
        "live": live,
        "ver": live,
        "history": [live],
        "files": [{"path": "index.html"}],
        "perm": {"mode": "owner"},
        "author": {"email": "owner@example.com"},
        "created_at": "2026-11-01T00:00:00Z",
        "updated_at": "2026-11-02T00:00:00Z",
        "view_count": 1,
        "assetToken": "asset",
    }


class FakeFrame:
    """Answers the routes the CLI uses and records every request."""

    def __init__(self):
        self.requests = []
        self.conflict = False
        fake = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def _answer(self):
                length = int(self.headers.get("content-length") or 0)
                body = json.loads(self.rfile.read(length)) if length else None
                fake.requests.append({"method": self.command, "path": self.path, "headers": dict(self.headers), "body": body})
                status, reply = fake.route(self.command, self.path, body)
                data = json.dumps(reply).encode()
                self.send_response(status)
                self.send_header("content-type", "application/json")
                self.send_header("content-length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            do_GET = do_POST = do_PATCH = do_DELETE = _answer

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}/api/frame"

    def route(self, method, path, body):
        path = path.removeprefix("/api/frame")
        if method == "GET" and path == f"/{PAGE_ID}":
            return 200, artifact(PAGE_ID, "Page", "v-page-1")
        if method == "GET" and path == f"/{DECK_ID}":
            return 200, artifact(DECK_ID, "Deck", "v-deck-1")
        if method == "GET" and path.startswith("/frames"):
            return 200, {
                "frames": [
                    {"slug": PAGE_ID, "title": "Page", "rel": "mine", "audience": "owner", "updatedAt": "2026-11-02T00:00:00Z", "description": "Kept"},
                    {"slug": DECK_ID, "title": "Shared deck", "rel": "shared", "audience": "org", "created_at": "2026-11-03T00:00:00Z"},
                ]
            }
        if method == "POST" and path == "/deploy/direct":
            if self.conflict:
                return 409, {"conflict": True}
            return 200, {"slug": body.get("slug") or PAGE_ID, "version": "v-new"}
        return 404, {"error": "not found"}

    def close(self):
        self.server.shutdown()


class ClaudeArtifactsTests(unittest.TestCase):
    def setUp(self):
        self.fake = FakeFrame()
        self.addCleanup(self.fake.close)
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)
        auth = self.tmp / "auth"
        auth.mkdir()
        (auth / "claude-0000-test@example.com.json").write_text(json.dumps({"access_token": TOKEN}))
        self.env = {
            **os.environ,
            "CLIPROXY_AUTH_DIR": str(auth),
            "CLAUDE_AI_ACCOUNT": "test@example.com",
            "CLAUDE_ARTIFACTS_API": self.fake.url,
        }

    def run_cli(self, *args, env=None):
        done = subprocess.run([str(TOOL), *args], env=env or self.env, capture_output=True, text=True, timeout=120)
        self.assertNotIn(TOKEN, done.stdout + done.stderr)
        return done

    def deploys(self):
        return [r["body"] for r in self.fake.requests if r["path"].endswith("/deploy/direct")]

    def page(self, html="<!doctype html><title> My  page </title><h1>hi</h1>"):
        file = self.tmp / "page.html"
        file.write_text(html)
        return file

    def test_update_by_short_link_sends_a_precondition_and_keeps_the_description(self):
        done = self.run_cli("update", f"https://claude.ai/artifact/{PAGE_SHORT}?sk=x", str(self.page()))
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(done.stdout.strip(), f"https://claude.ai/artifact/{PAGE_SHORT}")
        self.assertIn('Updated "My page" (v-new)', done.stderr)
        [body] = self.deploys()
        self.assertEqual(body["slug"], PAGE_ID)
        self.assertEqual(body["baseVersion"], "v-page-1")
        self.assertEqual(body["title"], "My page")
        self.assertEqual(body["description"], "Kept")
        self.assertEqual(self.fake.requests[0]["headers"]["Authorization"], f"Bearer {TOKEN}")

    def test_publish_creates_without_slug_or_precondition(self):
        done = self.run_cli("publish", str(self.page()), "--title", "Named", "--icon", "chart")
        self.assertEqual(done.returncode, 0, done.stderr)
        [body] = self.deploys()
        self.assertNotIn("slug", body)
        self.assertNotIn("baseVersion", body)
        self.assertNotIn("description", body)
        self.assertEqual((body["title"], body["icon"]), ("Named", "chart"))

    def test_a_conflict_is_reported_not_forced(self):
        self.fake.conflict = True
        done = self.run_cli("update", PAGE_ID, str(self.page()))
        self.assertEqual(done.returncode, 1)
        self.assertIn("changed since it was read", done.stderr)
        self.assertEqual(len(self.deploys()), 1)

    def test_push_patches_named_files_and_removals(self):
        folder = self.tmp / "deck"
        (folder / "project/slides").mkdir(parents=True)
        (folder / "project/deck.json").write_text('{"v":5}')
        (folder / "project/slides/cover.html").write_text('<section id="cover"></section>')
        (folder / ".DS_Store").write_text("x")
        done = self.run_cli("push", DECK_SHORT, str(folder), "--remove", "project/slides/old.html")
        self.assertEqual(done.returncode, 0, done.stderr)
        [body] = self.deploys()
        self.assertEqual((body["slug"], body["baseVersion"], body["mode"], body["title"]), (DECK_ID, "v-deck-1", "patch", "Deck"))
        self.assertEqual(
            body["manifest"],
            {
                "project/deck.json": {"content": '{"v":5}', "contentType": "application/json"},
                "project/slides/cover.html": {"content": '<section id="cover"></section>', "contentType": "text/html"},
                "project/slides/old.html": None,
            },
        )

    def test_push_refuses_binary_files_before_any_request(self):
        folder = self.tmp / "deck"
        folder.mkdir()
        (folder / "logo.png").write_bytes(b"\x89PNG")
        done = self.run_cli("push", DECK_ID, str(folder))
        self.assertEqual(done.returncode, 1)
        self.assertIn("logo.png: only text files", done.stderr)
        self.assertEqual(self.fake.requests, [])

    def test_list_scopes_by_relation(self):
        mine = self.run_cli("list", "--json")
        everything = self.run_cli("list", "--scope", "all", "--json")
        self.assertEqual([r["title"] for r in json.loads(mine.stdout)], ["Page"])
        self.assertEqual([r["title"] for r in json.loads(everything.stdout)], ["Shared deck", "Page"])

    def test_invalid_ids_fail_without_a_request(self):
        for bad in ["not-an-id!", "0OIl", "z" * 23, "zzzzzzzzzzzzzzzzzzzzzz"]:
            done = self.run_cli("read", bad)
            self.assertEqual(done.returncode, 1, bad)
            self.assertIn("not an artifact link or id", done.stderr)
        self.assertEqual(self.fake.requests, [])

    def test_uuid_and_short_link_name_the_same_artifact(self):
        for ref in [PAGE_ID, PAGE_ID.upper(), PAGE_SHORT, f"https://claude.ai/code/artifact/{PAGE_ID}"]:
            done = self.run_cli("read", ref, "--json")
            self.assertEqual(json.loads(done.stdout)["url"], f"https://claude.ai/artifact/{PAGE_SHORT}", ref)

    def test_help_needs_no_token(self):
        env = {k: v for k, v in self.env.items() if k != "CLIPROXY_AUTH_DIR"}
        env["CLIPROXY_AUTH_DIR"] = str(self.tmp / "missing")
        done = self.run_cli("publish", "--help", env=env)
        self.assertEqual(done.returncode, 0, done.stderr)
        missing = self.run_cli("list", env=env)
        self.assertEqual(missing.returncode, 1)
        self.assertIn("no claude.ai token", missing.stderr)


if __name__ == "__main__":
    unittest.main()
