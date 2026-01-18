"""Tests for env-protection hook."""

import json
import subprocess
import tempfile
from pathlib import Path

import pytest

HOOK_DIR = Path(__file__).parent
WRAPPER_SCRIPT = HOOK_DIR / "wrapper.sh"


def run_hook(tool_name: str, file_path: str, cwd: str | None = None) -> dict:
    """Run the hook with given input and return parsed JSON output."""
    input_data = {
        "tool_name": tool_name,
        "tool_input": {"file_path": file_path},
        "cwd": cwd or "/tmp",
    }

    result = subprocess.run(
        [str(WRAPPER_SCRIPT)],
        input=json.dumps(input_data),
        capture_output=True,
        text=True,
        timeout=30,
    )

    if result.returncode != 0:
        raise RuntimeError(f"Hook failed: {result.stderr}")

    return json.loads(result.stdout) if result.stdout.strip() else {}


def is_blocked(output: dict) -> bool:
    """Check if hook output indicates blocking."""
    hook_output = output.get("hookSpecificOutput", {})
    return hook_output.get("permissionDecision") == "deny"


def get_block_reason(output: dict) -> str:
    """Get the blocking reason from hook output."""
    hook_output = output.get("hookSpecificOutput", {})
    return hook_output.get("permissionDecisionReason", "")


class TestEnvFileBlocking:
    """Test that .env files are always blocked."""

    def test_blocks_dot_env(self):
        """Exact .env file should always be blocked."""
        output = run_hook("Read", "/project/.env")
        assert is_blocked(output)
        assert ".env file" in get_block_reason(output)

    def test_blocks_dot_env_in_subdirectory(self):
        """".env in subdirectory should be blocked."""
        output = run_hook("Read", "/project/config/.env")
        assert is_blocked(output)

    def test_blocks_dot_env_absolute_path(self):
        """.env with various path formats should be blocked."""
        output = run_hook("Read", "/home/user/app/.env")
        assert is_blocked(output)


class TestNonEnvFilesAllowed:
    """Test that non-.env files pass through."""

    def test_allows_config_json(self):
        """Regular config files should be allowed."""
        output = run_hook("Read", "/project/config.json")
        assert not is_blocked(output)

    def test_allows_env_in_name(self):
        """Files with 'env' in name but not .env pattern should be allowed."""
        output = run_hook("Read", "/project/environment.ts")
        assert not is_blocked(output)

    def test_allows_dotenv_package(self):
        """dotenv package file should be allowed (doesn't start with .env)."""
        output = run_hook("Read", "/project/node_modules/dotenv/index.js")
        assert not is_blocked(output)


class TestNonReadToolsPassThrough:
    """Test that non-Read tools are not affected."""

    def test_allows_write_to_env(self):
        """Write tool should not be blocked (hook only checks Read)."""
        output = run_hook("Write", "/project/.env")
        assert not is_blocked(output)

    def test_allows_edit_to_env(self):
        """Edit tool should not be blocked."""
        output = run_hook("Edit", "/project/.env")
        assert not is_blocked(output)

    def test_allows_bash(self):
        """Bash tool should not be blocked."""
        output = run_hook("Bash", "cat .env")
        assert not is_blocked(output)


class TestGitignoreIntegration:
    """Test .env* files with gitignore detection."""

    @pytest.fixture
    def git_repo_with_gitignore(self):
        """Create a temporary git repo with specific .gitignore."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Initialize git repo
            subprocess.run(["git", "init", "-q"], cwd=tmpdir, check=True)

            # Create .gitignore that ignores .env.local but not .env.example
            gitignore_path = Path(tmpdir) / ".gitignore"
            gitignore_path.write_text(".env\n.env.local\n.env.production\n")

            # Create the files
            (Path(tmpdir) / ".env.local").touch()
            (Path(tmpdir) / ".env.example").touch()
            (Path(tmpdir) / ".env.production").touch()

            yield tmpdir

    @pytest.fixture
    def git_repo_with_wildcard_gitignore(self):
        """Create a temporary git repo with .env* in gitignore."""
        with tempfile.TemporaryDirectory() as tmpdir:
            subprocess.run(["git", "init", "-q"], cwd=tmpdir, check=True)

            gitignore_path = Path(tmpdir) / ".gitignore"
            gitignore_path.write_text(".env*\n")

            (Path(tmpdir) / ".env.local").touch()
            (Path(tmpdir) / ".env.example").touch()

            yield tmpdir

    def test_blocks_env_local_in_gitignore(self, git_repo_with_gitignore):
        """.env.local in gitignore should be blocked."""
        output = run_hook("Read", ".env.local", cwd=git_repo_with_gitignore)
        assert is_blocked(output)
        assert "gitignore" in get_block_reason(output).lower()

    def test_allows_env_example_not_in_gitignore(self, git_repo_with_gitignore):
        """.env.example NOT in gitignore should be allowed."""
        output = run_hook("Read", ".env.example", cwd=git_repo_with_gitignore)
        assert not is_blocked(output)

    def test_blocks_env_production_in_gitignore(self, git_repo_with_gitignore):
        """.env.production in gitignore should be blocked."""
        output = run_hook("Read", ".env.production", cwd=git_repo_with_gitignore)
        assert is_blocked(output)

    def test_wildcard_gitignore_blocks_all_env_variants(
        self, git_repo_with_wildcard_gitignore
    ):
        """When .env* is in gitignore, all variants should be blocked."""
        output = run_hook(
            "Read", ".env.local", cwd=git_repo_with_wildcard_gitignore
        )
        assert is_blocked(output)

        output = run_hook(
            "Read", ".env.example", cwd=git_repo_with_wildcard_gitignore
        )
        assert is_blocked(output)


class TestEdgeCases:
    """Test edge cases and malformed input."""

    def test_empty_file_path(self):
        """Empty file path should pass through."""
        output = run_hook("Read", "")
        assert not is_blocked(output)

    def test_handles_missing_cwd(self):
        """Hook should block when gitignore status can't be determined."""
        output = run_hook("Read", ".env.local", cwd="/nonexistent/path")
        assert is_blocked(output)

    def test_blocks_env_local_outside_git_repo(self):
        """Without a git repo, .env* should be blocked by default."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output = run_hook("Read", ".env.local", cwd=tmpdir)
            assert is_blocked(output)

    def test_dot_env_always_blocked_regardless_of_gitignore(self):
        """Exact .env should be blocked even without gitignore check."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # No git repo, no gitignore
            output = run_hook("Read", ".env", cwd=tmpdir)
            assert is_blocked(output)
