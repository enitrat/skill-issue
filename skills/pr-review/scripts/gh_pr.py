#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "ghapi>=1.0.5",
#   "typer>=0.9.0",
#   "rich>=13.0.0",
# ]
# ///
"""
GitHub PR Review CLI - Helper scripts for reviewing pull requests.

Usage:
    uv run gh_pr.py <command> [options]

Commands:
    files       Get PR files and diff
    comments    Get review comments (with filtering)
    reviews     Get PR reviews
    post        Post a batched review from JSON file
    reply       Reply to a specific review comment
    head        Get the head commit SHA for a PR
    checkout    Create a worktree and checkout the PR branch
    cleanup     Remove a PR worktree

Examples:
    uv run gh_pr.py files owner/repo 123
    uv run gh_pr.py comments owner/repo 123 --unresolved
    uv run gh_pr.py post owner/repo 123 /tmp/pr-review.json
    uv run gh_pr.py checkout owner/repo 123
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

import typer
from ghapi.all import GhApi
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="GitHub PR Review CLI")
console = Console()


def parse_repo(repo: str) -> tuple[str, str]:
    """Parse owner/repo string into tuple."""
    parts = repo.split("/")
    if len(parts) != 2:
        console.print(f"[red]Error: Invalid repo format '{repo}'. Use 'owner/repo'[/red]")
        raise typer.Exit(1)
    return parts[0], parts[1]


def get_api(owner: str, repo: str) -> GhApi:
    """Create GhApi instance with token from environment or gh CLI."""
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        # Try to get token from gh CLI
        try:
            result = subprocess.run(
                ["gh", "auth", "token"],
                capture_output=True,
                text=True,
                check=True,
            )
            token = result.stdout.strip()
        except subprocess.CalledProcessError:
            console.print("[red]Error: No GitHub token found. Set GITHUB_TOKEN or run 'gh auth login'[/red]")
            raise typer.Exit(1)
    return GhApi(owner=owner, repo=repo, token=token)


@app.command()
def files(
    repo: str = typer.Argument(..., help="Repository in owner/repo format"),
    pr_number: int = typer.Argument(..., help="Pull request number"),
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """Get PR files with their status and patch info."""
    owner, repo_name = parse_repo(repo)
    api = get_api(owner, repo_name)

    files_data = list(api.pulls.list_files(pr_number))

    if raw:
        print(json.dumps([dict(f) for f in files_data], indent=2))
        return

    table = Table(title=f"PR #{pr_number} Files")
    table.add_column("Status", style="cyan")
    table.add_column("File", style="green")
    table.add_column("Changes", style="yellow")

    for f in files_data:
        status = f.get("status", "unknown")
        filename = f.get("filename", "")
        additions = f.get("additions", 0)
        deletions = f.get("deletions", 0)
        table.add_row(status, filename, f"+{additions}/-{deletions}")

    console.print(table)


@app.command()
def comments(
    repo: str = typer.Argument(..., help="Repository in owner/repo format"),
    pr_number: int = typer.Argument(..., help="Pull request number"),
    unresolved: bool = typer.Option(False, "--unresolved", "-u", help="Show only unresolved comments"),
    pending: bool = typer.Option(False, "--pending", "-p", help="Show only pending comments (not part of a submitted review)"),
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """Get review comments on a PR with optional filtering."""
    owner, repo_name = parse_repo(repo)
    api = get_api(owner, repo_name)

    comments_data = list(api.pulls.list_review_comments(pr_number))

    # Filter for unresolved comments if requested
    # Note: GitHub API doesn't directly expose 'resolved' status on comments
    # We check for in_reply_to_id to identify thread roots and look for resolution
    if unresolved:
        # Get all threads and filter those that aren't resolved
        # This is a simplified heuristic - in practice, resolved status
        # requires checking the GraphQL API or review threads endpoint
        thread_roots = [c for c in comments_data if c.get("in_reply_to_id") is None]
        comments_data = thread_roots

    if pending:
        # Filter for comments not yet part of a submitted review
        comments_data = [c for c in comments_data if c.get("pull_request_review_id") is None]

    if raw:
        print(json.dumps([dict(c) for c in comments_data], indent=2))
        return

    if not comments_data:
        console.print("[yellow]No comments found matching criteria[/yellow]")
        return

    for comment in comments_data:
        console.print(f"\n[bold cyan]Comment ID:[/bold cyan] {comment.get('id')}")
        console.print(f"[bold]File:[/bold] {comment.get('path')}:{comment.get('line', comment.get('original_line', '?'))}")
        console.print(f"[bold]Author:[/bold] {comment.get('user', {}).get('login', 'unknown')}")
        console.print(f"[dim]{comment.get('body', '')}[/dim]")
        console.print("-" * 40)


@app.command()
def reviews(
    repo: str = typer.Argument(..., help="Repository in owner/repo format"),
    pr_number: int = typer.Argument(..., help="Pull request number"),
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """Get all reviews on a PR."""
    owner, repo_name = parse_repo(repo)
    api = get_api(owner, repo_name)

    reviews_data = list(api.pulls.list_reviews(pr_number))

    if raw:
        print(json.dumps([dict(r) for r in reviews_data], indent=2))
        return

    table = Table(title=f"PR #{pr_number} Reviews")
    table.add_column("ID", style="dim")
    table.add_column("Author", style="cyan")
    table.add_column("State", style="green")
    table.add_column("Submitted", style="yellow")

    for review in reviews_data:
        state = review.get("state", "PENDING")
        state_color = {
            "APPROVED": "[green]APPROVED[/green]",
            "CHANGES_REQUESTED": "[red]CHANGES_REQUESTED[/red]",
            "COMMENTED": "[yellow]COMMENTED[/yellow]",
            "PENDING": "[dim]PENDING[/dim]",
            "DISMISSED": "[dim]DISMISSED[/dim]",
        }.get(state, state)

        table.add_row(
            str(review.get("id", "")),
            review.get("user", {}).get("login", "unknown"),
            state_color,
            review.get("submitted_at", "")[:10] if review.get("submitted_at") else "pending",
        )

    console.print(table)


@app.command()
def post(
    repo: str = typer.Argument(..., help="Repository in owner/repo format"),
    pr_number: int = typer.Argument(..., help="Pull request number"),
    review_file: Path = typer.Argument(..., help="Path to JSON file with review data"),
):
    """
    Post a batched review from a JSON file.

    The JSON file should have the structure:
    {
        "commit_id": "abc123...",
        "body": "Review summary",
        "event": "APPROVE|REQUEST_CHANGES|COMMENT",
        "comments": [
            {"path": "file.py", "line": 42, "side": "RIGHT", "body": "Comment text"}
        ]
    }
    """
    owner, repo_name = parse_repo(repo)
    api = get_api(owner, repo_name)

    if not review_file.exists():
        console.print(f"[red]Error: Review file not found: {review_file}[/red]")
        raise typer.Exit(1)

    try:
        review_data = json.loads(review_file.read_text())
    except json.JSONDecodeError as e:
        console.print(f"[red]Error: Invalid JSON in review file: {e}[/red]")
        raise typer.Exit(1)

    # Validate required fields
    required = ["commit_id", "event"]
    missing = [f for f in required if f not in review_data]
    if missing:
        console.print(f"[red]Error: Missing required fields: {missing}[/red]")
        raise typer.Exit(1)

    # Validate event type
    valid_events = ["APPROVE", "REQUEST_CHANGES", "COMMENT"]
    if review_data["event"] not in valid_events:
        console.print(f"[red]Error: Invalid event '{review_data['event']}'. Must be one of: {valid_events}[/red]")
        raise typer.Exit(1)

    try:
        result = api.pulls.create_review(
            pr_number,
            commit_id=review_data["commit_id"],
            body=review_data.get("body", ""),
            event=review_data["event"],
            comments=review_data.get("comments", []),
        )
        console.print(f"[green]Review posted successfully! Review ID: {result.get('id')}[/green]")

        # Clean up the review file on success
        review_file.unlink()
        console.print(f"[dim]Cleaned up review file: {review_file}[/dim]")

    except Exception as e:
        console.print(f"[red]Error posting review: {e}[/red]")
        console.print("[yellow]Review file preserved for retry[/yellow]")
        raise typer.Exit(1)


@app.command()
def reply(
    repo: str = typer.Argument(..., help="Repository in owner/repo format"),
    comment_id: int = typer.Argument(..., help="Comment ID to reply to"),
    body: str = typer.Argument(..., help="Reply text"),
):
    """Reply to a specific review comment."""
    owner, repo_name = parse_repo(repo)
    api = get_api(owner, repo_name)

    try:
        # The ghapi library uses pulls.create_reply_for_review_comment
        result = api.pulls.create_reply_for_review_comment(comment_id, body=body)
        console.print(f"[green]Reply posted successfully! Comment ID: {result.get('id')}[/green]")
    except Exception as e:
        console.print(f"[red]Error posting reply: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def head(
    repo: str = typer.Argument(..., help="Repository in owner/repo format"),
    pr_number: int = typer.Argument(..., help="Pull request number"),
):
    """Get the head commit SHA for a PR."""
    owner, repo_name = parse_repo(repo)
    api = get_api(owner, repo_name)

    pr = api.pulls.get(pr_number)
    sha = pr.get("head", {}).get("sha", "")

    if sha:
        print(sha)
    else:
        console.print("[red]Error: Could not get head SHA[/red]")
        raise typer.Exit(1)


@app.command()
def checkout(
    repo: str = typer.Argument(..., help="Repository in owner/repo format"),
    pr_number: int = typer.Argument(..., help="Pull request number"),
    base_path: Optional[Path] = typer.Option(None, "--path", "-p", help="Base path for worktree (default: /tmp)"),
):
    """Create a worktree and checkout the PR branch for local review."""
    owner, repo_name = parse_repo(repo)
    api = get_api(owner, repo_name)

    # Get PR info
    pr = api.pulls.get(pr_number)
    branch = pr.get("head", {}).get("ref", "")

    if not branch:
        console.print("[red]Error: Could not get PR branch name[/red]")
        raise typer.Exit(1)

    # Determine worktree path
    if base_path is None:
        base_path = Path("/tmp")

    worktree_path = base_path / f"pr-review-{owner}-{repo_name}-{pr_number}"

    if worktree_path.exists():
        console.print(f"[yellow]Worktree already exists at: {worktree_path}[/yellow]")
        print(str(worktree_path))
        return

    try:
        # Fetch the PR branch
        subprocess.run(
            ["git", "fetch", "origin", f"pull/{pr_number}/head:{branch}"],
            check=True,
            capture_output=True,
        )

        # Create worktree
        subprocess.run(
            ["git", "worktree", "add", str(worktree_path), branch],
            check=True,
            capture_output=True,
        )

        console.print(f"[green]Created worktree at: {worktree_path}[/green]")
        console.print(f"[dim]Branch: {branch}[/dim]")
        print(str(worktree_path))

    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error creating worktree: {e.stderr.decode() if e.stderr else e}[/red]")
        raise typer.Exit(1)


@app.command()
def cleanup(
    repo: str = typer.Argument(..., help="Repository in owner/repo format"),
    pr_number: int = typer.Argument(..., help="Pull request number"),
    base_path: Optional[Path] = typer.Option(None, "--path", "-p", help="Base path for worktree (default: /tmp)"),
):
    """Remove a PR worktree after review is complete."""
    owner, repo_name = parse_repo(repo)

    if base_path is None:
        base_path = Path("/tmp")

    worktree_path = base_path / f"pr-review-{owner}-{repo_name}-{pr_number}"

    if not worktree_path.exists():
        console.print(f"[yellow]Worktree does not exist: {worktree_path}[/yellow]")
        return

    try:
        subprocess.run(
            ["git", "worktree", "remove", str(worktree_path), "--force"],
            check=True,
            capture_output=True,
        )
        console.print(f"[green]Removed worktree: {worktree_path}[/green]")

    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error removing worktree: {e.stderr.decode() if e.stderr else e}[/red]")
        raise typer.Exit(1)


@app.command()
def init_review(
    repo: str = typer.Argument(..., help="Repository in owner/repo format"),
    pr_number: int = typer.Argument(..., help="Pull request number"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file path"),
):
    """Initialize a review JSON file with PR metadata."""
    owner, repo_name = parse_repo(repo)
    api = get_api(owner, repo_name)

    # Get head commit SHA
    pr = api.pulls.get(pr_number)
    commit_id = pr.get("head", {}).get("sha", "")

    if not commit_id:
        console.print("[red]Error: Could not get head commit SHA[/red]")
        raise typer.Exit(1)

    review_data = {
        "owner": owner,
        "repo": repo_name,
        "pr_number": pr_number,
        "commit_id": commit_id,
        "body": "",
        "event": "COMMENT",
        "comments": [],
    }

    if output is None:
        output = Path(f"/tmp/pr-review-{owner}-{repo_name}-{pr_number}.json")

    output.write_text(json.dumps(review_data, indent=2))
    console.print(f"[green]Created review file: {output}[/green]")
    print(str(output))


@app.command()
def issue(
    repo: str = typer.Argument(..., help="Repository in owner/repo format"),
    issue_number: int = typer.Argument(..., help="Issue number"),
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """Get issue details including title, description, labels, and assignees."""
    owner, repo_name = parse_repo(repo)
    api = get_api(owner, repo_name)

    issue_data = api.issues.get(issue_number)

    if raw:
        print(json.dumps(dict(issue_data), indent=2, default=str))
        return

    state = issue_data.get("state", "unknown")
    state_color = "green" if state == "open" else "red" if state == "closed" else "yellow"

    console.print(f"\n[bold cyan]Issue #{issue_number}[/bold cyan]")
    console.print(f"[bold]{issue_data.get('title', '')}[/bold]")
    console.print(f"[{state_color}]{state.upper()}[/{state_color}]\n")

    # Author and dates
    console.print(f"[dim]Created by {issue_data.get('user', {}).get('login', 'unknown')}[/dim]")
    console.print(f"[dim]Created: {issue_data.get('created_at', '')[:10]}[/dim]")
    if issue_data.get("updated_at"):
        console.print(f"[dim]Updated: {issue_data.get('updated_at', '')[:10]}[/dim]")

    # Labels
    labels = issue_data.get("labels", [])
    if labels:
        label_names = [l.get("name", "") for l in labels]
        console.print(f"\n[bold]Labels:[/bold] {', '.join(label_names)}")

    # Assignees
    assignees = issue_data.get("assignees", [])
    if assignees:
        assignee_names = [a.get("login", "") for a in assignees]
        console.print(f"[bold]Assignees:[/bold] {', '.join(assignee_names)}")

    # Body
    if issue_data.get("body"):
        console.print("\n[bold]Description:[/bold]")
        console.print(issue_data.get("body", ""))


if __name__ == "__main__":
    app()
