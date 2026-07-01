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
GitHub PR Author CLI - Helper scripts for creating and managing pull requests.

Usage:
    uv run gh_pr.py <command> [options]

Commands:
    create      Create a new pull request
    view        View PR details
    list        List PRs in a repository
    checks      Get PR check status
    comments    Get review comments on a PR
    reply       Reply to a review comment
    resolve     Resolve or unresolve a review thread
    merge       Merge a PR
    reviewers   Add reviewers to a PR

Examples:
    uv run gh_pr.py create owner/repo --title "feat: add feature" --body "Description"
    uv run gh_pr.py view owner/repo 123
    uv run gh_pr.py comments owner/repo 123 --actionable
    uv run gh_pr.py reply owner/repo 456 "[AUTOMATED] Done"
    uv run gh_pr.py resolve owner/repo 123 --comment-id 456
"""

import json
import os
import subprocess
import sys
from urllib.parse import urlparse
from pathlib import Path
from typing import Optional

import typer
from ghapi.all import GhApi
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown

app = typer.Typer(help="GitHub PR Author CLI")
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


def extract_pull_number_from_url(url: Optional[str]) -> Optional[int]:
    """Extract PR number from a GitHub pull request API URL."""
    if not url:
        return None
    path = urlparse(url).path
    parts = [part for part in path.split("/") if part]
    if "pulls" in parts:
        idx = parts.index("pulls")
        if idx + 1 < len(parts) and parts[idx + 1].isdigit():
            return int(parts[idx + 1])
    for part in reversed(parts):
        if part.isdigit():
            return int(part)
    return None


def get_pull_number_from_comment(api: GhApi, comment_id: int) -> int:
    """Fetch PR number for a given review comment."""
    try:
        comment = api.pulls.get_review_comment(comment_id)
    except Exception as e:
        console.print(f"[red]Error fetching review comment {comment_id}: {e}[/red]")
        raise typer.Exit(1)
    pull_number = extract_pull_number_from_url(
        comment.get("pull_request_url") or comment.get("pull_request_review_url")
    )
    if pull_number is None:
        console.print(f"[red]Error: Could not determine PR number for comment ID {comment_id}[/red]")
        raise typer.Exit(1)
    return pull_number


def find_review_thread_id(
    api: GhApi,
    owner: str,
    repo: str,
    pr_number: int,
    comment_id: int,
) -> tuple[Optional[str], Optional[bool]]:
    """Find the GraphQL review thread ID for a given review comment database ID."""
    query = """
    query($owner: String!, $repo: String!, $number: Int!, $after: String) {
      repository(owner: $owner, name: $repo) {
        pullRequest(number: $number) {
          reviewThreads(first: 100, after: $after) {
            nodes {
              id
              isResolved
              comments(first: 50) {
                nodes {
                  databaseId
                }
              }
            }
            pageInfo {
              hasNextPage
              endCursor
            }
          }
        }
      }
    }
    """

    after: Optional[str] = None
    while True:
        data = api.graphql(query, owner=owner, repo=repo, number=pr_number, after=after)
        threads = (
            data.get("repository", {})
            .get("pullRequest", {})
            .get("reviewThreads", {})
            .get("nodes", [])
        )
        for thread in threads:
            comments = thread.get("comments", {}).get("nodes", [])
            for comment in comments:
                if comment.get("databaseId") == comment_id:
                    return thread.get("id"), thread.get("isResolved")
        page_info = (
            data.get("repository", {})
            .get("pullRequest", {})
            .get("reviewThreads", {})
            .get("pageInfo", {})
        )
        if not page_info.get("hasNextPage"):
            break
        after = page_info.get("endCursor")

    return None, None


def get_current_branch() -> str:
    """Get the current git branch name."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return ""


@app.command()
def create(
    repo: str = typer.Argument(..., help="Repository in owner/repo format"),
    title: str = typer.Option(..., "--title", "-t", help="PR title"),
    body: str = typer.Option("", "--body", "-b", help="PR body/description"),
    body_file: Optional[Path] = typer.Option(None, "--body-file", "-f", help="Read body from file"),
    base: str = typer.Option("main", "--base", help="Base branch to merge into"),
    head: Optional[str] = typer.Option(None, "--head", "-h", help="Head branch (default: current branch)"),
    draft: bool = typer.Option(False, "--draft", "-d", help="Create as draft PR"),
    labels: Optional[str] = typer.Option(None, "--labels", "-l", help="Comma-separated labels"),
    reviewers: Optional[str] = typer.Option(None, "--reviewers", "-r", help="Comma-separated reviewers"),
    assignees: Optional[str] = typer.Option(None, "--assignees", "-a", help="Comma-separated assignees"),
):
    """Create a new pull request."""
    owner, repo_name = parse_repo(repo)
    api = get_api(owner, repo_name)

    # Get body from file if specified
    if body_file:
        if not body_file.exists():
            console.print(f"[red]Error: Body file not found: {body_file}[/red]")
            raise typer.Exit(1)
        body = body_file.read_text()

    # Use current branch if head not specified
    if not head:
        head = get_current_branch()
        if not head:
            console.print("[red]Error: Could not determine current branch. Specify --head[/red]")
            raise typer.Exit(1)

    try:
        pr = api.pulls.create(
            title=title,
            body=body,
            head=head,
            base=base,
            draft=draft,
        )

        pr_number = pr.get("number")
        console.print(f"[green]PR #{pr_number} created successfully![/green]")
        console.print(f"[dim]URL: {pr.get('html_url')}[/dim]")

        # Add labels if specified
        if labels:
            label_list = [l.strip() for l in labels.split(",")]
            api.issues.add_labels(pr_number, labels=label_list)
            console.print(f"[dim]Added labels: {', '.join(label_list)}[/dim]")

        # Add reviewers if specified
        if reviewers:
            reviewer_list = [r.strip() for r in reviewers.split(",")]
            api.pulls.request_reviewers(pr_number, reviewers=reviewer_list)
            console.print(f"[dim]Requested reviewers: {', '.join(reviewer_list)}[/dim]")

        # Add assignees if specified
        if assignees:
            assignee_list = [a.strip().lstrip("@") for a in assignees.split(",")]
            api.issues.add_assignees(pr_number, assignees=assignee_list)
            console.print(f"[dim]Added assignees: {', '.join(assignee_list)}[/dim]")

        print(pr.get("html_url"))

    except Exception as e:
        console.print(f"[red]Error creating PR: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def view(
    repo: str = typer.Argument(..., help="Repository in owner/repo format"),
    pr_number: int = typer.Argument(..., help="Pull request number"),
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """View PR details."""
    owner, repo_name = parse_repo(repo)
    api = get_api(owner, repo_name)

    pr = api.pulls.get(pr_number)

    if raw:
        print(json.dumps(dict(pr), indent=2, default=str))
        return

    state = pr.get("state", "unknown")
    state_color = "green" if state == "open" else "red" if state == "closed" else "yellow"
    merged = pr.get("merged", False)

    console.print(Panel(
        f"[bold]{pr.get('title', '')}[/bold]\n\n"
        f"[{state_color}]{state.upper()}{'  MERGED' if merged else ''}[/{state_color}]\n\n"
        f"[dim]#{pr_number} opened by {pr.get('user', {}).get('login', 'unknown')}[/dim]\n"
        f"[dim]{pr.get('head', {}).get('ref', '')} → {pr.get('base', {}).get('ref', '')}[/dim]",
        title=f"PR #{pr_number}",
    ))

    if pr.get("body"):
        console.print("\n[bold]Description:[/bold]")
        console.print(Markdown(pr.get("body", "")))

    # Show review status
    reviews = list(api.pulls.list_reviews(pr_number))
    if reviews:
        console.print("\n[bold]Reviews:[/bold]")
        for review in reviews:
            state = review.get("state", "PENDING")
            icon = {"APPROVED": "✓", "CHANGES_REQUESTED": "✗", "COMMENTED": "💬"}.get(state, "○")
            console.print(f"  {icon} {review.get('user', {}).get('login', 'unknown')}: {state}")


@app.command(name="list")
def list_prs(
    repo: str = typer.Argument(..., help="Repository in owner/repo format"),
    state: str = typer.Option("open", "--state", "-s", help="Filter by state: open, closed, all"),
    author: Optional[str] = typer.Option(None, "--author", "-a", help="Filter by author"),
    limit: int = typer.Option(30, "--limit", "-n", help="Max number of PRs to show"),
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """List PRs in a repository."""
    owner, repo_name = parse_repo(repo)
    api = get_api(owner, repo_name)

    prs = list(api.pulls.list(state=state, per_page=limit))

    if author:
        prs = [p for p in prs if p.get("user", {}).get("login", "").lower() == author.lower()]

    if raw:
        print(json.dumps([dict(p) for p in prs], indent=2, default=str))
        return

    table = Table(title=f"Pull Requests ({state})")
    table.add_column("#", style="dim")
    table.add_column("Title", style="cyan", max_width=50)
    table.add_column("Author", style="green")
    table.add_column("Branch", style="yellow")
    table.add_column("Updated", style="dim")

    for pr in prs[:limit]:
        table.add_row(
            str(pr.get("number", "")),
            pr.get("title", "")[:50],
            pr.get("user", {}).get("login", "unknown"),
            pr.get("head", {}).get("ref", "")[:20],
            pr.get("updated_at", "")[:10] if pr.get("updated_at") else "",
        )

    console.print(table)


@app.command()
def checks(
    repo: str = typer.Argument(..., help="Repository in owner/repo format"),
    pr_number: int = typer.Argument(..., help="Pull request number"),
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """Get PR check status."""
    owner, repo_name = parse_repo(repo)
    api = get_api(owner, repo_name)

    # Get the head SHA
    pr = api.pulls.get(pr_number)
    head_sha = pr.get("head", {}).get("sha", "")

    if not head_sha:
        console.print("[red]Error: Could not get PR head commit[/red]")
        raise typer.Exit(1)

    # Get check runs for the commit
    checks_data = api.checks.list_for_ref(head_sha)
    check_runs = checks_data.get("check_runs", [])

    if raw:
        print(json.dumps([dict(c) for c in check_runs], indent=2, default=str))
        return

    if not check_runs:
        console.print("[yellow]No checks found for this PR[/yellow]")
        return

    table = Table(title=f"PR #{pr_number} Checks")
    table.add_column("Status", style="bold")
    table.add_column("Name", style="cyan")
    table.add_column("Conclusion", style="green")

    for check in check_runs:
        status = check.get("status", "unknown")
        conclusion = check.get("conclusion", "pending")

        status_icon = {
            "completed": "✓" if conclusion == "success" else "✗" if conclusion in ["failure", "cancelled"] else "○",
            "in_progress": "⋯",
            "queued": "○",
        }.get(status, "?")

        conclusion_color = {
            "success": "[green]success[/green]",
            "failure": "[red]failure[/red]",
            "cancelled": "[yellow]cancelled[/yellow]",
            "skipped": "[dim]skipped[/dim]",
        }.get(conclusion, conclusion or "[dim]pending[/dim]")

        table.add_row(status_icon, check.get("name", ""), conclusion_color)

    console.print(table)


@app.command()
def comments(
    repo: str = typer.Argument(..., help="Repository in owner/repo format"),
    pr_number: int = typer.Argument(..., help="Pull request number"),
    actionable: bool = typer.Option(False, "--actionable", "-a", help="Show only actionable comments (exclude 'Nit:', 'FYI:', etc.)"),
    by_file: bool = typer.Option(False, "--by-file", help="Group comments by file"),
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """Get review comments on a PR for addressing feedback."""
    owner, repo_name = parse_repo(repo)
    api = get_api(owner, repo_name)

    comments_data = list(api.pulls.list_review_comments(pr_number))

    if actionable:
        # Filter out non-blocking comments
        non_blocking_prefixes = ["nit:", "optional:", "fyi:", "consider:"]
        comments_data = [
            c for c in comments_data
            if not any(c.get("body", "").lower().strip().startswith(p) for p in non_blocking_prefixes)
        ]

    if raw:
        print(json.dumps([dict(c) for c in comments_data], indent=2, default=str))
        return

    if not comments_data:
        console.print("[green]No comments to address![/green]" if actionable else "[yellow]No comments found[/yellow]")
        return

    if by_file:
        # Group by file
        from collections import defaultdict
        by_file_dict = defaultdict(list)
        for c in comments_data:
            by_file_dict[c.get("path", "unknown")].append(c)

        for file_path, file_comments in by_file_dict.items():
            console.print(f"\n[bold cyan]{file_path}[/bold cyan]")
            for comment in file_comments:
                line = comment.get("line", comment.get("original_line", "?"))
                console.print(f"  [dim]Line {line}[/dim] (ID: {comment.get('id')})")
                console.print(f"    {comment.get('body', '')[:100]}...")
    else:
        for comment in comments_data:
            console.print(f"\n[bold cyan]Comment ID:[/bold cyan] {comment.get('id')}")
            console.print(f"[bold]File:[/bold] {comment.get('path')}:{comment.get('line', comment.get('original_line', '?'))}")
            console.print(f"[bold]Author:[/bold] {comment.get('user', {}).get('login', 'unknown')}")
            console.print(f"[dim]{comment.get('body', '')}[/dim]")
            console.print("-" * 40)


@app.command()
def reply(
    repo: str = typer.Argument(..., help="Repository in owner/repo format"),
    comment_id: int = typer.Argument(..., help="Comment ID to reply to"),
    body: str = typer.Argument(..., help="Reply text (remember to prefix with [AUTOMATED])"),
):
    """Reply to a review comment."""
    owner, repo_name = parse_repo(repo)
    api = get_api(owner, repo_name)

    # Ensure the reply is prefixed
    if not body.startswith("[AUTOMATED]"):
        console.print("[yellow]Warning: Reply should start with [AUTOMATED] prefix[/yellow]")

    try:
        pull_number = get_pull_number_from_comment(api, comment_id)
        result = api.pulls.create_reply_for_review_comment(
            pull_number=pull_number, comment_id=comment_id, body=body
        )
        console.print(f"[green]Reply posted successfully! Comment ID: {result.get('id')}[/green]")
    except Exception as e:
        console.print(f"[red]Error posting reply: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def resolve(
    repo: str = typer.Argument(..., help="Repository in owner/repo format"),
    pr_number: int = typer.Argument(..., help="Pull request number"),
    comment_id: Optional[int] = typer.Option(None, "--comment-id", "-c", help="Review comment ID to resolve"),
    thread_id: Optional[str] = typer.Option(None, "--thread-id", "-t", help="Review thread node ID (GraphQL ID)"),
    unresolve: bool = typer.Option(False, "--unresolve", help="Mark the thread as unresolved"),
):
    """Resolve or unresolve a review thread."""
    owner, repo_name = parse_repo(repo)
    api = get_api(owner, repo_name)

    if (comment_id is None and thread_id is None) or (comment_id is not None and thread_id is not None):
        console.print("[red]Error: Provide exactly one of --comment-id or --thread-id[/red]")
        raise typer.Exit(1)

    is_resolved: Optional[bool] = None
    if comment_id is not None:
        thread_id, is_resolved = find_review_thread_id(api, owner, repo_name, pr_number, comment_id)
        if not thread_id:
            console.print(f"[red]Error: Could not find a review thread for comment ID {comment_id}[/red]")
            raise typer.Exit(1)

    if is_resolved is not None:
        if is_resolved and not unresolve:
            console.print("[yellow]Thread is already resolved[/yellow]")
            return
        if not is_resolved and unresolve:
            console.print("[yellow]Thread is already unresolved[/yellow]")
            return

    mutation_name = "unresolveReviewThread" if unresolve else "resolveReviewThread"
    mutation = f"""
    mutation($threadId: ID!) {{
      {mutation_name}(input: {{threadId: $threadId}}) {{
        thread {{
          id
          isResolved
        }}
      }}
    }}
    """

    try:
        result = api.graphql(mutation, threadId=thread_id)
        payload = result.get(mutation_name, {})
        thread = payload.get("thread", {})
        console.print(
            f"[green]Thread {thread.get('id', thread_id)} is now "
            f"{'resolved' if thread.get('isResolved') else 'unresolved'}[/green]"
        )
    except Exception as e:
        console.print(f"[red]Error updating thread resolution: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def comment(
    repo: str = typer.Argument(..., help="Repository in owner/repo format"),
    pr_number: int = typer.Argument(..., help="Pull request number"),
    body: str = typer.Argument(..., help="Comment text"),
):
    """Add a general comment to a PR (not tied to specific line)."""
    owner, repo_name = parse_repo(repo)
    api = get_api(owner, repo_name)

    try:
        result = api.issues.create_comment(pr_number, body=body)
        console.print(f"[green]Comment posted successfully! Comment ID: {result.get('id')}[/green]")
    except Exception as e:
        console.print(f"[red]Error posting comment: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def merge(
    repo: str = typer.Argument(..., help="Repository in owner/repo format"),
    pr_number: int = typer.Argument(..., help="Pull request number"),
    method: str = typer.Option("squash", "--method", "-m", help="Merge method: merge, squash, rebase"),
    message: Optional[str] = typer.Option(None, "--message", help="Commit message for merge"),
    delete_branch: bool = typer.Option(True, "--delete-branch/--no-delete-branch", help="Delete branch after merge"),
):
    """Merge a PR."""
    owner, repo_name = parse_repo(repo)
    api = get_api(owner, repo_name)

    valid_methods = ["merge", "squash", "rebase"]
    if method not in valid_methods:
        console.print(f"[red]Error: Invalid merge method '{method}'. Must be one of: {valid_methods}[/red]")
        raise typer.Exit(1)

    try:
        # Get PR info first
        pr = api.pulls.get(pr_number)
        head_ref = pr.get("head", {}).get("ref", "")

        # Merge the PR
        merge_kwargs = {"merge_method": method}
        if message:
            merge_kwargs["commit_message"] = message

        result = api.pulls.merge(pr_number, **merge_kwargs)

        if result.get("merged"):
            console.print(f"[green]PR #{pr_number} merged successfully![/green]")

            # Delete branch if requested
            if delete_branch and head_ref:
                try:
                    api.git.delete_ref(f"heads/{head_ref}")
                    console.print(f"[dim]Deleted branch: {head_ref}[/dim]")
                except Exception:
                    console.print(f"[yellow]Could not delete branch: {head_ref}[/yellow]")
        else:
            console.print(f"[yellow]PR was not merged: {result.get('message', 'unknown reason')}[/yellow]")

    except Exception as e:
        console.print(f"[red]Error merging PR: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def reviewers(
    repo: str = typer.Argument(..., help="Repository in owner/repo format"),
    pr_number: int = typer.Argument(..., help="Pull request number"),
    add: Optional[str] = typer.Option(None, "--add", "-a", help="Comma-separated reviewers to add"),
    remove: Optional[str] = typer.Option(None, "--remove", "-r", help="Comma-separated reviewers to remove"),
):
    """Add or remove reviewers from a PR."""
    owner, repo_name = parse_repo(repo)
    api = get_api(owner, repo_name)

    if add:
        reviewer_list = [r.strip() for r in add.split(",")]
        try:
            api.pulls.request_reviewers(pr_number, reviewers=reviewer_list)
            console.print(f"[green]Added reviewers: {', '.join(reviewer_list)}[/green]")
        except Exception as e:
            console.print(f"[red]Error adding reviewers: {e}[/red]")

    if remove:
        reviewer_list = [r.strip() for r in remove.split(",")]
        try:
            api.pulls.remove_requested_reviewers(pr_number, reviewers=reviewer_list)
            console.print(f"[green]Removed reviewers: {', '.join(reviewer_list)}[/green]")
        except Exception as e:
            console.print(f"[red]Error removing reviewers: {e}[/red]")

    if not add and not remove:
        # List current reviewers
        pr = api.pulls.get(pr_number)
        requested = pr.get("requested_reviewers", [])
        if requested:
            console.print("[bold]Requested reviewers:[/bold]")
            for r in requested:
                console.print(f"  - {r.get('login', 'unknown')}")
        else:
            console.print("[yellow]No reviewers requested[/yellow]")


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
