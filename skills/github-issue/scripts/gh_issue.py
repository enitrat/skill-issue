#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "ghapi>=1.0.5",
#   "typer>=0.9.0",
#   "rich>=13.0.0",
#   "pyyaml>=6.0",
# ]
# ///
"""
GitHub Issue CLI - Helper scripts for creating and managing issues.

Usage:
    uv run gh_issue.py <command> [options]

Commands:
    create          Create a new issue
    create-sub      Create a sub-issue linked to a parent
    edit            Edit an existing issue's title or body
    view            View issue details
    list            List issues in a repository
    list-subissues  List all sub-issues of a parent (GraphQL API)
    dump-tree       Dump issue and all sub-issues to markdown files with frontmatter
    push            Push/sync an issue from markdown file with frontmatter to GitHub
    link            Link two issues (parent/child relationship)
    close           Close an issue
    comment         Add a comment to an issue
    labels          Manage issue labels
    init            Initialize an issue body template

Frontmatter Format:
    dump-tree and push commands use YAML frontmatter for metadata:

    ---
    title: "feat(auth): add OAuth2 support"
    repo: owner/repo
    number: 123          # omit for new issues
    state: open
    labels:
      - enhancement
    assignees:
      - username
    milestone: "Q1 2026"
    project: "My Project"
    parent: owner/repo#100
    ---

    Body content here...

Examples:
    uv run gh_issue.py create owner/repo --title "Bug: login fails" --body-file /tmp/issue.md
    uv run gh_issue.py create-sub owner/repo --parent 10 --title "Sub-task" --body "..."
    uv run gh_issue.py dump-tree owner/repo 123 ./issues/
    uv run gh_issue.py push ./issues/123-my-issue.md
    uv run gh_issue.py view owner/repo 123
    uv run gh_issue.py link owner/repo --parent 10 --child 42
"""

import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import typer
import yaml
from ghapi.all import GhApi
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax

app = typer.Typer(help="GitHub Issue CLI")
console = Console()


# =============================================================================
# Frontmatter Types and Utilities
# =============================================================================

@dataclass
class IssueMetadata:
    """Structured metadata for an issue stored in YAML frontmatter."""
    title: str
    repo: str
    number: int | None = None  # None for new issues
    state: str = "open"
    labels: list[str] = field(default_factory=list)
    assignees: list[str] = field(default_factory=list)
    milestone: str | None = None
    project: str | None = None
    parent: str | None = None  # Format: "owner/repo#number" or just "#number" for same repo
    # Read-only fields (for reference, ignored on push)
    created_at: str | None = None
    author: str | None = None
    url: str | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary for YAML serialization."""
        d = {
            "title": self.title,
            "repo": self.repo,
        }
        if self.number is not None:
            d["number"] = self.number
        d["state"] = self.state
        if self.labels:
            d["labels"] = self.labels
        if self.assignees:
            d["assignees"] = self.assignees
        if self.milestone:
            d["milestone"] = self.milestone
        if self.project:
            d["project"] = self.project
        if self.parent:
            d["parent"] = self.parent
        # Read-only fields
        if self.created_at:
            d["created_at"] = self.created_at
        if self.author:
            d["author"] = self.author
        if self.url:
            d["url"] = self.url
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "IssueMetadata":
        """Create from dictionary (parsed YAML)."""
        return cls(
            title=d.get("title", ""),
            repo=d.get("repo", ""),
            number=d.get("number"),
            state=d.get("state", "open"),
            labels=d.get("labels", []) or [],
            assignees=d.get("assignees", []) or [],
            milestone=d.get("milestone"),
            project=d.get("project"),
            parent=d.get("parent"),
            created_at=d.get("created_at"),
            author=d.get("author"),
            url=d.get("url"),
        )


def parse_frontmatter(content: str) -> tuple[IssueMetadata | None, str]:
    """Parse YAML frontmatter from markdown content.

    Args:
        content: Full markdown content with optional frontmatter

    Returns:
        Tuple of (metadata, body). metadata is None if no frontmatter found.
    """
    content = content.strip()
    if not content.startswith("---"):
        return None, content

    # Find the closing ---
    lines = content.split("\n")
    end_idx = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_idx = i
            break

    if end_idx is None:
        return None, content

    # Parse YAML
    yaml_content = "\n".join(lines[1:end_idx])
    body = "\n".join(lines[end_idx + 1:]).strip()

    try:
        metadata_dict = yaml.safe_load(yaml_content) or {}
        metadata = IssueMetadata.from_dict(metadata_dict)
        return metadata, body
    except yaml.YAMLError:
        return None, content


def format_frontmatter(metadata: IssueMetadata, body: str) -> str:
    """Format metadata and body into markdown with YAML frontmatter.

    Args:
        metadata: Issue metadata
        body: Markdown body content

    Returns:
        Full markdown content with frontmatter
    """
    yaml_content = yaml.dump(
        metadata.to_dict(),
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
    )
    return f"---\n{yaml_content}---\n\n{body}"

# Conventional commit pattern: type(scope): description or type: description
CONVENTIONAL_COMMIT_PATTERN = re.compile(
    r"^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\([a-zA-Z0-9_-]+\))?!?: .+$"
)


def validate_title(title: str) -> tuple[bool, str]:
    """Validate title follows conventional commit format."""
    if CONVENTIONAL_COMMIT_PATTERN.match(title):
        return True, ""

    return False, (
        "Title must follow conventional commit format:\n"
        "  <type>(<scope>): <description>\n"
        "  or <type>: <description>\n\n"
        "Valid types: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert\n"
        "Examples:\n"
        "  feat(auth): add OAuth2 support\n"
        "  fix: resolve memory leak in parser\n"
        "  chore(deps): update dependencies"
    )


def preview_issue(title: str, body: str, labels: list[str] | None, assignees: list[str] | None, repo: str) -> bool:
    """Preview issue and ask for confirmation. Returns True if user confirms."""
    console.print("\n" + "=" * 60)
    console.print("[bold cyan]ISSUE PREVIEW[/bold cyan]")
    console.print("=" * 60)

    console.print(f"\n[bold]Repository:[/bold] {repo}")
    console.print(f"[bold]Title:[/bold] {title}")

    if labels:
        console.print(f"[bold]Labels:[/bold] {', '.join(labels)}")
    if assignees:
        console.print(f"[bold]Assignees:[/bold] {', '.join(assignees)}")

    console.print("\n[bold]Body:[/bold]")
    console.print("-" * 40)
    console.print(Markdown(body))
    console.print("-" * 40)

    console.print("\n[yellow]Create this issue?[/yellow]")
    console.print("  [green]y[/green] = create issue")
    console.print("  [red]n[/red] = cancel")
    console.print("  [cyan]e[/cyan] = edit (saves to /tmp/issue-body.md for editing)")

    while True:
        response = input("\nChoice [y/n/e]: ").strip().lower()
        if response in ("y", "yes"):
            return True
        elif response in ("n", "no"):
            console.print("[yellow]Issue creation cancelled.[/yellow]")
            return False
        elif response in ("e", "edit"):
            # Save to temp file for editing
            edit_path = Path("/tmp/issue-body.md")
            edit_path.write_text(body)
            console.print(f"[cyan]Body saved to {edit_path}[/cyan]")
            console.print("[cyan]Edit the file and re-run the command with --body-file /tmp/issue-body.md[/cyan]")
            return False
        else:
            console.print("[red]Invalid choice. Please enter y, n, or e.[/red]")


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


def get_token() -> str:
    """Get GitHub token from environment or gh CLI."""
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
    return token


@app.command()
def create(
    repo: str = typer.Argument(..., help="Repository in owner/repo format"),
    title: str = typer.Option(..., "--title", "-t", help="Issue title (conventional commit format)"),
    body: str = typer.Option("", "--body", "-b", help="Issue body"),
    body_file: Optional[Path] = typer.Option(None, "--body-file", "-f", help="Read body from file"),
    labels: Optional[str] = typer.Option(None, "--labels", "-l", help="Comma-separated labels"),
    assignees: Optional[str] = typer.Option(None, "--assignees", "-a", help="Comma-separated assignees"),
    milestone: Optional[str] = typer.Option(None, "--milestone", "-m", help="Milestone name or number"),
    project: Optional[str] = typer.Option(None, "--project", "-p", help="Project name to add issue to"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
    skip_validation: bool = typer.Option(False, "--skip-validation", help="Skip title format validation"),
):
    """Create a new GitHub issue.

    Title must follow conventional commit format: type(scope): description
    Valid types: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert
    """
    # Validate title format
    if not skip_validation:
        valid, error_msg = validate_title(title)
        if not valid:
            console.print(f"[red]Invalid title format:[/red]\n{error_msg}")
            raise typer.Exit(1)

    owner, repo_name = parse_repo(repo)

    # Get body from file if specified
    if body_file:
        if not body_file.exists():
            console.print(f"[red]Error: Body file not found: {body_file}[/red]")
            raise typer.Exit(1)
        body = body_file.read_text()

    # Parse labels and assignees for preview
    label_list = [l.strip() for l in labels.split(",")] if labels else None
    assignee_list = [a.strip().lstrip("@") for a in assignees.split(",")] if assignees else None

    # Preview and confirm unless --yes flag is set
    if not yes:
        if not preview_issue(title, body, label_list, assignee_list, repo):
            raise typer.Exit(0)

    api = get_api(owner, repo_name)

    try:
        # Build issue kwargs
        issue_kwargs = {"title": title, "body": body}

        if labels:
            issue_kwargs["labels"] = [l.strip() for l in labels.split(",")]

        if assignees:
            issue_kwargs["assignees"] = [a.strip().lstrip("@") for a in assignees.split(",")]

        if milestone:
            # Try to parse as number, otherwise look up by name
            try:
                issue_kwargs["milestone"] = int(milestone)
            except ValueError:
                # Look up milestone by name
                milestones = list(api.issues.list_milestones(state="open"))
                found = next((m for m in milestones if m.get("title") == milestone), None)
                if found:
                    issue_kwargs["milestone"] = found.get("number")
                else:
                    console.print(f"[yellow]Warning: Milestone '{milestone}' not found[/yellow]")

        issue = api.issues.create(**issue_kwargs)
        issue_number = issue.get("number")
        issue_url = issue.get("html_url")

        console.print(f"[green]Issue #{issue_number} created successfully![/green]")
        console.print(f"[dim]URL: {issue_url}[/dim]")

        # Add to project if specified (requires gh CLI as ghapi doesn't support projects v2 well)
        if project:
            try:
                subprocess.run(
                    ["gh", "issue", "edit", str(issue_number), "--add-project", project, "-R", repo],
                    check=True,
                    capture_output=True,
                )
                console.print(f"[dim]Added to project: {project}[/dim]")
            except subprocess.CalledProcessError:
                console.print(f"[yellow]Warning: Could not add to project '{project}'[/yellow]")

        print(issue_url)

    except Exception as e:
        console.print(f"[red]Error creating issue: {e}[/red]")
        raise typer.Exit(1)


@app.command("create-sub")
def create_sub(
    repo: str = typer.Argument(..., help="Repository in owner/repo format"),
    parent: int = typer.Option(..., "--parent", "-p", help="Parent issue number"),
    title: str = typer.Option(..., "--title", "-t", help="Issue title (conventional commit format)"),
    body: str = typer.Option("", "--body", "-b", help="Issue body"),
    body_file: Optional[Path] = typer.Option(None, "--body-file", "-f", help="Read body from file"),
    labels: Optional[str] = typer.Option(None, "--labels", "-l", help="Comma-separated labels"),
    assignees: Optional[str] = typer.Option(None, "--assignees", "-a", help="Comma-separated assignees"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
    skip_validation: bool = typer.Option(False, "--skip-validation", help="Skip title format validation"),
):
    """Create a sub-issue linked to a parent issue.

    Title must follow conventional commit format: type(scope): description
    Valid types: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert
    """
    # Validate title format
    if not skip_validation:
        valid, error_msg = validate_title(title)
        if not valid:
            console.print(f"[red]Invalid title format:[/red]\n{error_msg}")
            raise typer.Exit(1)

    owner, repo_name = parse_repo(repo)

    # Get body from file if specified
    if body_file:
        if not body_file.exists():
            console.print(f"[red]Error: Body file not found: {body_file}[/red]")
            raise typer.Exit(1)
        body = body_file.read_text()

    # Prepend parent reference to body
    body_with_parent = f"Parent: #{parent}\n\n{body}"

    # Parse labels and assignees for preview
    label_list = [l.strip() for l in labels.split(",")] if labels else None
    assignee_list = [a.strip().lstrip("@") for a in assignees.split(",")] if assignees else None

    # Preview and confirm unless --yes flag is set
    if not yes:
        console.print(f"[dim]This issue will be linked to parent #{parent}[/dim]")
        if not preview_issue(title, body_with_parent, label_list, assignee_list, repo):
            raise typer.Exit(0)

    api = get_api(owner, repo_name)

    try:
        # Build issue kwargs
        issue_kwargs = {"title": title, "body": body_with_parent}

        if labels:
            issue_kwargs["labels"] = [l.strip() for l in labels.split(",")]

        if assignees:
            issue_kwargs["assignees"] = [a.strip().lstrip("@") for a in assignees.split(",")]

        issue = api.issues.create(**issue_kwargs)
        issue_number = issue.get("number")
        issue_url = issue.get("html_url")

        console.print(f"[green]Sub-issue #{issue_number} created![/green]")
        console.print(f"[dim]Linked to parent #{parent}[/dim]")

        # Try to create formal sub-issue relationship via GraphQL
        try:
            # Get node IDs
            parent_data = api.issues.get(parent)
            parent_node_id = parent_data.get("node_id")
            child_node_id = issue.get("node_id")

            if parent_node_id and child_node_id:
                # Use gh CLI for GraphQL mutation
                query = f"""
                    mutation {{
                        addSubIssue(input: {{issueId: "{parent_node_id}", subIssueId: "{child_node_id}"}}) {{
                            issue {{ number }}
                        }}
                    }}
                """
                subprocess.run(
                    ["gh", "api", "graphql", "-f", f"query={query}"],
                    check=True,
                    capture_output=True,
                )
                console.print("[dim]Created formal sub-issue link[/dim]")
        except Exception:
            console.print("[yellow]Note: Could not create formal sub-issue link (may require GitHub Enterprise)[/yellow]")

        print(issue_url)

    except Exception as e:
        console.print(f"[red]Error creating sub-issue: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def edit(
    repo: str = typer.Argument(..., help="Repository in owner/repo format"),
    issue_number: int = typer.Argument(..., help="Issue number"),
    title: Optional[str] = typer.Option(None, "--title", "-t", help="New issue title"),
    body: Optional[str] = typer.Option(None, "--body", "-b", help="New issue body"),
    body_file: Optional[Path] = typer.Option(None, "--body-file", "-f", help="Read body from file"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
    skip_validation: bool = typer.Option(False, "--skip-validation", help="Skip title format validation"),
):
    """Edit an existing issue's title or body.

    If title is provided, it must follow conventional commit format unless --skip-validation is set.
    """
    owner, repo_name = parse_repo(repo)
    api = get_api(owner, repo_name)

    # Fetch current issue
    try:
        issue = api.issues.get(issue_number)
    except Exception as e:
        console.print(f"[red]Error fetching issue #{issue_number}: {e}[/red]")
        raise typer.Exit(1)

    current_title = issue.get("title", "")
    current_body = issue.get("body", "")

    # Determine new values
    new_title = title if title is not None else current_title
    new_body = body

    if body_file:
        if not body_file.exists():
            console.print(f"[red]Error: Body file not found: {body_file}[/red]")
            raise typer.Exit(1)
        new_body = body_file.read_text()

    if new_body is None:
        new_body = current_body

    # Check if anything changed
    if new_title == current_title and new_body == current_body:
        console.print("[yellow]No changes specified. Nothing to update.[/yellow]")
        raise typer.Exit(0)

    # Validate title format if changed
    if new_title != current_title and not skip_validation:
        valid, error_msg = validate_title(new_title)
        if not valid:
            console.print(f"[red]Invalid title format:[/red]\n{error_msg}")
            raise typer.Exit(1)

    # Preview changes
    if not yes:
        console.print("\n" + "=" * 60)
        console.print("[bold cyan]EDIT PREVIEW[/bold cyan]")
        console.print("=" * 60)

        console.print(f"\n[bold]Repository:[/bold] {repo}")
        console.print(f"[bold]Issue:[/bold] #{issue_number}")

        if new_title != current_title:
            console.print(f"\n[bold]Title:[/bold]")
            console.print(f"  [red]- {current_title}[/red]")
            console.print(f"  [green]+ {new_title}[/green]")
        else:
            console.print(f"\n[bold]Title:[/bold] {current_title} [dim](unchanged)[/dim]")

        if new_body != current_body:
            console.print(f"\n[bold]Body:[/bold] [yellow](changed)[/yellow]")
            console.print("-" * 40)
            console.print(Markdown(new_body))
            console.print("-" * 40)
        else:
            console.print(f"\n[bold]Body:[/bold] [dim](unchanged)[/dim]")

        console.print("\n[yellow]Apply these changes?[/yellow]")
        console.print("  [green]y[/green] = apply changes")
        console.print("  [red]n[/red] = cancel")
        console.print("  [cyan]e[/cyan] = edit (saves body to /tmp/issue-body.md for editing)")

        while True:
            response = input("\nChoice [y/n/e]: ").strip().lower()
            if response in ("y", "yes"):
                break
            elif response in ("n", "no"):
                console.print("[yellow]Edit cancelled.[/yellow]")
                raise typer.Exit(0)
            elif response in ("e", "edit"):
                edit_path = Path("/tmp/issue-body.md")
                edit_path.write_text(new_body)
                console.print(f"[cyan]Body saved to {edit_path}[/cyan]")
                console.print("[cyan]Edit the file and re-run with --body-file /tmp/issue-body.md[/cyan]")
                raise typer.Exit(0)
            else:
                console.print("[red]Invalid choice. Please enter y, n, or e.[/red]")

    try:
        update_kwargs = {}
        if new_title != current_title:
            update_kwargs["title"] = new_title
        if new_body != current_body:
            update_kwargs["body"] = new_body

        api.issues.update(issue_number, **update_kwargs)
        console.print(f"[green]Issue #{issue_number} updated successfully![/green]")
        console.print(f"[dim]URL: {issue.get('html_url')}[/dim]")

    except Exception as e:
        console.print(f"[red]Error updating issue: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def view(
    repo: str = typer.Argument(..., help="Repository in owner/repo format"),
    issue_number: int = typer.Argument(..., help="Issue number"),
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """View issue details."""
    owner, repo_name = parse_repo(repo)
    api = get_api(owner, repo_name)

    issue = api.issues.get(issue_number)

    if raw:
        print(json.dumps(dict(issue), indent=2, default=str))
        return

    state = issue.get("state", "unknown")
    state_color = "green" if state == "open" else "red"

    labels = ", ".join(l.get("name", "") for l in issue.get("labels", []))
    assignees = ", ".join(a.get("login", "") for a in issue.get("assignees", []))

    console.print(Panel(
        f"[bold]{issue.get('title', '')}[/bold]\n\n"
        f"[{state_color}]{state.upper()}[/{state_color}]\n\n"
        f"[dim]#{issue_number} opened by {issue.get('user', {}).get('login', 'unknown')}[/dim]\n"
        f"[dim]Labels: {labels or 'none'}[/dim]\n"
        f"[dim]Assignees: {assignees or 'none'}[/dim]",
        title=f"Issue #{issue_number}",
    ))

    if issue.get("body"):
        console.print("\n[bold]Description:[/bold]")
        console.print(Markdown(issue.get("body", "")))


@app.command(name="list")
def list_issues(
    repo: str = typer.Argument(..., help="Repository in owner/repo format"),
    state: str = typer.Option("open", "--state", "-s", help="Filter by state: open, closed, all"),
    labels: Optional[str] = typer.Option(None, "--labels", "-l", help="Filter by labels (comma-separated)"),
    assignee: Optional[str] = typer.Option(None, "--assignee", "-a", help="Filter by assignee"),
    creator: Optional[str] = typer.Option(None, "--creator", "-c", help="Filter by creator"),
    limit: int = typer.Option(30, "--limit", "-n", help="Max number of issues"),
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """List issues in a repository."""
    owner, repo_name = parse_repo(repo)
    api = get_api(owner, repo_name)

    list_kwargs = {"state": state, "per_page": limit}

    if labels:
        list_kwargs["labels"] = labels

    if assignee:
        list_kwargs["assignee"] = assignee

    if creator:
        list_kwargs["creator"] = creator

    issues = list(api.issues.list_for_repo(**list_kwargs))

    # Filter out PRs (they come through issues API)
    issues = [i for i in issues if "pull_request" not in i]

    if raw:
        print(json.dumps([dict(i) for i in issues], indent=2, default=str))
        return

    if not issues:
        console.print("[yellow]No issues found[/yellow]")
        return

    table = Table(title=f"Issues ({state})")
    table.add_column("#", style="dim")
    table.add_column("Title", style="cyan", max_width=50)
    table.add_column("Labels", style="green")
    table.add_column("Assignee", style="yellow")
    table.add_column("Updated", style="dim")

    for issue in issues[:limit]:
        labels_str = ", ".join(l.get("name", "")[:10] for l in issue.get("labels", [])[:2])
        assignees = issue.get("assignees", [])
        assignee_str = assignees[0].get("login", "") if assignees else ""

        table.add_row(
            str(issue.get("number", "")),
            issue.get("title", "")[:50],
            labels_str[:20],
            assignee_str[:15],
            issue.get("updated_at", "")[:10] if issue.get("updated_at") else "",
        )

    console.print(table)


@app.command()
def link(
    repo: str = typer.Argument(..., help="Repository in owner/repo format"),
    parent: int = typer.Option(..., "--parent", "-p", help="Parent issue number"),
    child: int = typer.Option(..., "--child", "-c", help="Child issue number"),
):
    """Link two issues as parent/child (sub-issue relationship)."""
    owner, repo_name = parse_repo(repo)
    api = get_api(owner, repo_name)

    try:
        # Get node IDs for both issues
        parent_issue = api.issues.get(parent)
        child_issue = api.issues.get(child)

        parent_node_id = parent_issue.get("node_id")
        child_node_id = child_issue.get("node_id")

        if not parent_node_id or not child_node_id:
            console.print("[red]Error: Could not get issue node IDs[/red]")
            raise typer.Exit(1)

        # Use gh CLI for GraphQL mutation
        query = """
            mutation($parentId: ID!, $childId: ID!) {
                addSubIssue(input: {issueId: $parentId, subIssueId: $childId}) {
                    issue { number }
                }
            }
        """
        result = subprocess.run(
            [
                "gh", "api", "graphql",
                "-f", f"parentId={parent_node_id}",
                "-f", f"childId={child_node_id}",
                "-f", f"query={query}",
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            console.print(f"[green]Linked issue #{child} as sub-issue of #{parent}[/green]")
        else:
            # Fall back to adding a comment reference
            console.print("[yellow]Note: Formal sub-issue linking may require GitHub Enterprise[/yellow]")
            console.print("[dim]Adding reference comment instead...[/dim]")

            api.issues.create_comment(child, body=f"Parent issue: #{parent}")
            console.print(f"[green]Added parent reference to issue #{child}[/green]")

    except Exception as e:
        console.print(f"[red]Error linking issues: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def close(
    repo: str = typer.Argument(..., help="Repository in owner/repo format"),
    issue_number: int = typer.Argument(..., help="Issue number"),
    reason: str = typer.Option("completed", "--reason", "-r", help="Close reason: completed, not_planned"),
    comment: Optional[str] = typer.Option(None, "--comment", "-c", help="Add a closing comment"),
):
    """Close an issue."""
    owner, repo_name = parse_repo(repo)
    api = get_api(owner, repo_name)

    try:
        # Add comment if provided
        if comment:
            api.issues.create_comment(issue_number, body=comment)

        # Close the issue
        api.issues.update(issue_number, state="closed", state_reason=reason)
        console.print(f"[green]Issue #{issue_number} closed ({reason})[/green]")

    except Exception as e:
        console.print(f"[red]Error closing issue: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def comment(
    repo: str = typer.Argument(..., help="Repository in owner/repo format"),
    issue_number: int = typer.Argument(..., help="Issue number"),
    body: str = typer.Argument(..., help="Comment text"),
):
    """Add a comment to an issue."""
    owner, repo_name = parse_repo(repo)
    api = get_api(owner, repo_name)

    try:
        result = api.issues.create_comment(issue_number, body=body)
        console.print(f"[green]Comment added to issue #{issue_number}[/green]")
        console.print(f"[dim]Comment ID: {result.get('id')}[/dim]")

    except Exception as e:
        console.print(f"[red]Error adding comment: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def labels(
    repo: str = typer.Argument(..., help="Repository in owner/repo format"),
    issue_number: int = typer.Argument(..., help="Issue number"),
    add: Optional[str] = typer.Option(None, "--add", "-a", help="Labels to add (comma-separated)"),
    remove: Optional[str] = typer.Option(None, "--remove", "-r", help="Labels to remove (comma-separated)"),
):
    """Add or remove labels from an issue."""
    owner, repo_name = parse_repo(repo)
    api = get_api(owner, repo_name)

    try:
        if add:
            label_list = [l.strip() for l in add.split(",")]
            api.issues.add_labels(issue_number, labels=label_list)
            console.print(f"[green]Added labels: {', '.join(label_list)}[/green]")

        if remove:
            label_list = [l.strip() for l in remove.split(",")]
            for label in label_list:
                try:
                    api.issues.remove_label(issue_number, label)
                except Exception:
                    pass  # Label may not exist
            console.print(f"[green]Removed labels: {', '.join(label_list)}[/green]")

        if not add and not remove:
            # List current labels
            issue = api.issues.get(issue_number)
            labels = issue.get("labels", [])
            if labels:
                console.print("[bold]Current labels:[/bold]")
                for label in labels:
                    console.print(f"  - {label.get('name', '')}")
            else:
                console.print("[yellow]No labels on this issue[/yellow]")

    except Exception as e:
        console.print(f"[red]Error managing labels: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def init(
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file path"),
    template: str = typer.Option("default", "--template", "-t", help="Template: default, bug, feature"),
):
    """Initialize an issue body file with the Why/What/How template."""
    templates = {
        "default": """## Why

Currently, [describe current state/behavior].

This causes [specific problem or bottleneck], which [impact on users/system/workflow].

Addressing this will [concrete benefit - improved metrics, unlocked capabilities, better UX].

## What

[Verb] [specific thing] to [achieve outcome].

Scope:
- [In scope item 1]
- [In scope item 2]

Out of scope:
- [Explicitly excluded item]

## How

Approach: [brief strategy - e.g., "Extend existing X pattern", "Add new Y component"]

Key areas:
1. [Component/file] - [what changes here]
2. [Component/file] - [what changes here]

## Acceptance Criteria

- [ ] [Observable behavior or state that confirms completion]
- [ ] [Integration with existing system works as expected]
- [ ] [Edge case or error condition handled]

## Testing Plan

- [ ] [How to manually verify the change]
- [ ] [Key integration scenario to test]
""",
        "bug": """## Bug Description

**Current behavior**: [What happens now]

**Expected behavior**: [What should happen]

**Steps to reproduce**:
1. [Step 1]
2. [Step 2]
3. [Observe error]

## Environment

- Version: [version]
- OS: [operating system]
- Browser: [if applicable]

## Additional Context

[Any error messages, logs, screenshots]

## Acceptance Criteria

- [ ] Bug no longer reproduces with steps above
- [ ] No regression in related functionality
""",
        "feature": """## Why

[Background and motivation for this feature]

**User story**: As a [type of user], I want [goal] so that [benefit].

## What

[Specific feature description]

Scope:
- [Feature aspect 1]
- [Feature aspect 2]

Out of scope:
- [What this does NOT include]

## How

Approach: [High-level implementation strategy]

Key components:
1. [Component] - [purpose]
2. [Component] - [purpose]

## Acceptance Criteria

- [ ] [User can do X]
- [ ] [System behaves as Y]
- [ ] [Edge case Z handled]

## Testing Plan

- [ ] [Manual verification steps]
- [ ] [Integration test scenario]
""",
    }

    if template not in templates:
        console.print(f"[red]Error: Unknown template '{template}'. Available: {', '.join(templates.keys())}[/red]")
        raise typer.Exit(1)

    content = templates[template]

    if output is None:
        output = Path("/tmp/issue-body.md")

    output.write_text(content)
    console.print(f"[green]Created issue template: {output}[/green]")
    console.print(f"[dim]Template: {template}[/dim]")
    print(str(output))


def _fetch_subissues_graphql(owner: str, repo_name: str, issue_number: int) -> list[dict]:
    """Fetch actual sub-issues using GitHub's GraphQL API.

    Returns only formal sub-issues, not all cross-referenced issues.
    """
    query = """
    query($owner: String!, $repo: String!, $number: Int!) {
        repository(owner: $owner, name: $repo) {
            issue(number: $number) {
                subIssues(first: 100) {
                    nodes {
                        number
                        title
                        state
                        url
                        repository {
                            nameWithOwner
                        }
                    }
                }
            }
        }
    }
    """

    result = subprocess.run(
        [
            "gh", "api", "graphql",
            "-f", f"query={query}",
            "-F", f"owner={owner}",
            "-F", f"repo={repo_name}",
            "-F", f"number={issue_number}",
        ],
        capture_output=True,
        text=True,
        check=True
    )

    data = json.loads(result.stdout)
    sub_issues_data = data.get("data", {}).get("repository", {}).get("issue", {}).get("subIssues", {}).get("nodes", [])

    subissues = []
    for node in sub_issues_data:
        subissues.append({
            "repo": node["repository"]["nameWithOwner"],
            "number": node["number"],
            "title": node["title"],
            "url": node["url"],
            "state": node["state"].lower()
        })

    return subissues


@app.command()
def list_subissues(
    repo: str = typer.Argument(..., help="Repository in format 'owner/repo'"),
    issue_number: int = typer.Argument(..., help="Parent issue number"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """List all sub-issues of a parent issue.

    Uses GitHub's native sub-issues feature (GraphQL API) to fetch only
    actual sub-issues, not all cross-referenced issues.

    Examples:
        uv run gh_issue.py list-subissues owner/repo 123
        uv run gh_issue.py list-subissues owner/repo 123 --json
    """
    owner, repo_name = parse_repo(repo)

    try:
        subissues = _fetch_subissues_graphql(owner, repo_name, issue_number)

        if json_output:
            print(json.dumps(subissues, indent=2))
        else:
            if not subissues:
                console.print("[yellow]No sub-issues found[/yellow]")
                return

            console.print(f"\n[bold cyan]Sub-issues for {owner}/{repo_name}#{issue_number}:[/bold cyan]\n")
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Reference", style="cyan")
            table.add_column("Title", style="white")
            table.add_column("State", style="green")

            for sub in subissues:
                ref = f"{sub['repo']}#{sub['number']}"
                state_style = "green" if sub["state"] == "open" else "dim"
                table.add_row(ref, sub["title"], f"[{state_style}]{sub['state'].upper()}[/{state_style}]")

            console.print(table)
            console.print(f"\n[dim]Total: {len(subissues)} sub-issues[/dim]\n")

    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error fetching sub-issues: {e.stderr}[/red]")
        raise typer.Exit(1)
    except json.JSONDecodeError as e:
        console.print(f"[red]Error parsing JSON response: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def dump_tree(
    repo: str = typer.Argument(..., help="Repository in format 'owner/repo'"),
    issue_number: int = typer.Argument(..., help="Parent issue number"),
    output_dir: Path = typer.Argument(..., help="Output directory for markdown files"),
    skip_validation: bool = typer.Option(False, "--skip-validation", help="Skip title validation"),
):
    """Dump an issue and all its sub-issues to markdown files with frontmatter.

    Creates a directory structure with markdown files containing YAML frontmatter
    for metadata (labels, assignees, milestone, etc.) and clean body content.

    The frontmatter format enables round-trip editing: export → edit → push back.

    Examples:
        uv run gh_issue.py dump-tree owner/repo 123 thoughts/shared/issues/
    """
    owner, repo_name = parse_repo(repo)

    # Create output directory based on issue title
    try:
        result = subprocess.run(
            ["gh", "api", f"repos/{owner}/{repo_name}/issues/{issue_number}"],
            capture_output=True,
            text=True,
            check=True
        )
        parent_issue = json.loads(result.stdout)

        # Create safe directory name
        title = parent_issue["title"]
        safe_title = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:60]
        issue_dir = output_dir / f"{issue_number}-{safe_title}"
        issue_dir.mkdir(parents=True, exist_ok=True)

        console.print(f"[cyan]Creating issue tree in: {issue_dir}[/cyan]\n")

        # Save parent issue with same naming convention as sub-issues
        parent_filename = f"{issue_number}-{safe_title}.md"
        parent_file = issue_dir / parent_filename
        parent_content = _format_issue_markdown(parent_issue, repo=repo)
        parent_file.write_text(parent_content)
        console.print(f"[green]✓[/green] Saved parent: {parent_file.name}")

        # Fetch actual sub-issues via GraphQL (not cross-references)
        subissues = _fetch_subissues_graphql(owner, repo_name, issue_number)

        # Parent reference for sub-issues
        parent_ref = f"{repo}#{issue_number}"

        # Fetch and save each sub-issue
        for sub in subissues:
            sub_repo = sub["repo"]
            sub_number = sub["number"]

            try:
                # Fetch sub-issue with full metadata using gh issue view
                result = subprocess.run(
                    ["gh", "issue", "view", str(sub_number), "--repo", sub_repo,
                     "--json", "number,title,body,state,labels,createdAt,author,url,assignees,milestone"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                sub_issue = json.loads(result.stdout)

                # Create safe filename
                sub_title = sub_issue["title"]
                safe_sub_title = re.sub(r"[^a-z0-9]+", "-", sub_title.lower()).strip("-")[:80]
                filename = f"{sub_number}-{safe_sub_title}.md"

                # Format and save with frontmatter
                sub_content = _format_issue_markdown(
                    sub_issue,
                    repo=sub_repo,
                    is_gh_cli_format=True,
                    parent=parent_ref,
                )
                sub_file = issue_dir / filename
                sub_file.write_text(sub_content)
                console.print(f"[green]✓[/green] Saved sub-issue: {filename}")

            except subprocess.CalledProcessError as e:
                console.print(f"[yellow]⚠[/yellow] Failed to fetch {sub_repo}#{sub_number}: {e.stderr.strip()}")
                continue

        console.print(f"\n[bold green]Done![/bold green] Dumped to: {issue_dir}")
        console.print(f"[dim]Total files: {len(list(issue_dir.glob('*.md')))}[/dim]\n")

    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error: {e.stderr}[/red]")
        raise typer.Exit(1)
    except json.JSONDecodeError as e:
        console.print(f"[red]Error parsing JSON: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def push(
    file_path: Path = typer.Argument(..., help="Path to markdown file with frontmatter"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
    skip_validation: bool = typer.Option(False, "--skip-validation", help="Skip title format validation"),
):
    """Push an issue from a markdown file with frontmatter to GitHub.

    Reads metadata from YAML frontmatter and body from markdown content.
    Creates a new issue if no 'number' in frontmatter, or updates existing.

    Frontmatter fields:
      - title: Issue title (required)
      - repo: Repository in owner/repo format (required)
      - number: Issue number (omit for new issues)
      - labels: List of labels to apply
      - assignees: List of GitHub usernames
      - milestone: Milestone name or number
      - project: Project name to add issue to
      - parent: Parent issue reference (e.g., "owner/repo#123")

    Examples:
        uv run gh_issue.py push issue.md
        uv run gh_issue.py push issue.md --yes
    """
    if not file_path.exists():
        console.print(f"[red]Error: File not found: {file_path}[/red]")
        raise typer.Exit(1)

    content = file_path.read_text()
    metadata, body = parse_frontmatter(content)

    if metadata is None:
        console.print("[red]Error: No valid YAML frontmatter found in file[/red]")
        console.print("[dim]Frontmatter should be between --- markers at the start of the file[/dim]")
        raise typer.Exit(1)

    if not metadata.title:
        console.print("[red]Error: 'title' is required in frontmatter[/red]")
        raise typer.Exit(1)

    if not metadata.repo:
        console.print("[red]Error: 'repo' is required in frontmatter[/red]")
        raise typer.Exit(1)

    # Validate title format
    if not skip_validation:
        valid, error_msg = validate_title(metadata.title)
        if not valid:
            console.print(f"[red]Invalid title format:[/red]\n{error_msg}")
            raise typer.Exit(1)

    owner, repo_name = parse_repo(metadata.repo)
    is_update = metadata.number is not None

    # Preview
    if not yes:
        console.print("\n" + "=" * 60)
        action = "UPDATE" if is_update else "CREATE"
        console.print(f"[bold cyan]ISSUE {action} PREVIEW[/bold cyan]")
        console.print("=" * 60)

        console.print(f"\n[bold]Repository:[/bold] {metadata.repo}")
        console.print(f"[bold]Title:[/bold] {metadata.title}")
        if is_update:
            console.print(f"[bold]Issue #:[/bold] {metadata.number}")
        if metadata.labels:
            console.print(f"[bold]Labels:[/bold] {', '.join(metadata.labels)}")
        if metadata.assignees:
            console.print(f"[bold]Assignees:[/bold] {', '.join(metadata.assignees)}")
        if metadata.milestone:
            console.print(f"[bold]Milestone:[/bold] {metadata.milestone}")
        if metadata.project:
            console.print(f"[bold]Project:[/bold] {metadata.project}")
        if metadata.parent:
            console.print(f"[bold]Parent:[/bold] {metadata.parent}")

        console.print("\n[bold]Body:[/bold]")
        console.print("-" * 40)
        console.print(Markdown(body))
        console.print("-" * 40)

        console.print(f"\n[yellow]{action.lower().capitalize()} this issue?[/yellow]")
        response = input("Choice [y/n]: ").strip().lower()
        if response not in ("y", "yes"):
            console.print("[yellow]Cancelled.[/yellow]")
            raise typer.Exit(0)

    api = get_api(owner, repo_name)

    try:
        if is_update:
            # Update existing issue
            update_kwargs = {"title": metadata.title, "body": body}

            # Update labels (replace all)
            if metadata.labels is not None:
                update_kwargs["labels"] = metadata.labels

            # Update assignees (replace all)
            if metadata.assignees is not None:
                update_kwargs["assignees"] = metadata.assignees

            # Update milestone
            if metadata.milestone:
                try:
                    update_kwargs["milestone"] = int(metadata.milestone)
                except ValueError:
                    milestones = list(api.issues.list_milestones(state="open"))
                    found = next((m for m in milestones if m.get("title") == metadata.milestone), None)
                    if found:
                        update_kwargs["milestone"] = found.get("number")
                    else:
                        console.print(f"[yellow]Warning: Milestone '{metadata.milestone}' not found[/yellow]")

            api.issues.update(metadata.number, **update_kwargs)
            console.print(f"[green]Issue #{metadata.number} updated successfully![/green]")
            issue_url = f"https://github.com/{metadata.repo}/issues/{metadata.number}"

        else:
            # Create new issue
            issue_kwargs = {"title": metadata.title, "body": body}

            if metadata.labels:
                issue_kwargs["labels"] = metadata.labels

            if metadata.assignees:
                issue_kwargs["assignees"] = metadata.assignees

            if metadata.milestone:
                try:
                    issue_kwargs["milestone"] = int(metadata.milestone)
                except ValueError:
                    milestones = list(api.issues.list_milestones(state="open"))
                    found = next((m for m in milestones if m.get("title") == metadata.milestone), None)
                    if found:
                        issue_kwargs["milestone"] = found.get("number")
                    else:
                        console.print(f"[yellow]Warning: Milestone '{metadata.milestone}' not found[/yellow]")

            issue = api.issues.create(**issue_kwargs)
            issue_number = issue.get("number")
            issue_url = issue.get("html_url")

            console.print(f"[green]Issue #{issue_number} created successfully![/green]")

            # Link to parent if specified
            if metadata.parent:
                _link_to_parent(api, metadata.repo, issue_number, issue.get("node_id"), metadata.parent)

        # Add to project if specified
        if metadata.project:
            issue_num = metadata.number if is_update else issue_number
            try:
                subprocess.run(
                    ["gh", "issue", "edit", str(issue_num), "--add-project", metadata.project,
                     "-R", metadata.repo],
                    check=True,
                    capture_output=True,
                )
                console.print(f"[dim]Added to project: {metadata.project}[/dim]")
            except subprocess.CalledProcessError:
                console.print(f"[yellow]Warning: Could not add to project '{metadata.project}'[/yellow]")

        console.print(f"[dim]URL: {issue_url}[/dim]")
        print(issue_url)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


def _link_to_parent(api: GhApi, child_repo: str, child_number: int, child_node_id: str, parent_ref: str):
    """Link an issue to a parent issue.

    Args:
        api: GhApi instance
        child_repo: Child issue repo (owner/repo)
        child_number: Child issue number
        child_node_id: Child issue GraphQL node ID
        parent_ref: Parent reference like "owner/repo#123" or "#123" (same repo)
    """
    # Parse parent reference
    if parent_ref.startswith("#"):
        # Same repo
        parent_repo = child_repo
        parent_number = int(parent_ref[1:])
    elif "#" in parent_ref:
        parent_repo, parent_num_str = parent_ref.rsplit("#", 1)
        parent_number = int(parent_num_str)
    else:
        console.print(f"[yellow]Warning: Invalid parent reference '{parent_ref}'[/yellow]")
        return

    try:
        # Get parent node ID
        parent_owner, parent_repo_name = parent_repo.split("/")
        parent_api = get_api(parent_owner, parent_repo_name)
        parent_issue = parent_api.issues.get(parent_number)
        parent_node_id = parent_issue.get("node_id")

        if parent_node_id and child_node_id:
            # Use GraphQL to create sub-issue relationship
            query = """
                mutation($parentId: ID!, $childId: ID!) {
                    addSubIssue(input: {issueId: $parentId, subIssueId: $childId}) {
                        issue { number }
                    }
                }
            """
            result = subprocess.run(
                [
                    "gh", "api", "graphql",
                    "-f", f"parentId={parent_node_id}",
                    "-f", f"childId={child_node_id}",
                    "-f", f"query={query}",
                ],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                console.print(f"[dim]Linked as sub-issue of {parent_ref}[/dim]")
            else:
                console.print(f"[yellow]Note: Could not create formal sub-issue link[/yellow]")

    except Exception as e:
        console.print(f"[yellow]Warning: Could not link to parent: {e}[/yellow]")


def _format_issue_markdown(
    issue: dict,
    repo: str,
    is_gh_cli_format: bool = False,
    parent: str | None = None,
) -> str:
    """Format issue data as markdown with YAML frontmatter.

    Args:
        issue: Issue data from GitHub API
        repo: Repository in owner/repo format
        is_gh_cli_format: True if from gh CLI (different field names)
        parent: Parent issue reference (e.g., "owner/repo#123")

    Returns:
        Markdown content with YAML frontmatter containing metadata
    """
    if is_gh_cli_format:
        # gh CLI format
        title = issue["title"]
        url = issue["url"]
        state = issue["state"]
        labels = [label["name"] for label in issue.get("labels", [])]
        created = issue["createdAt"]
        author = issue["author"]["login"] if issue.get("author") else None
        body = issue.get("body", "") or ""
        assignees = [a["login"] for a in issue.get("assignees", [])]
        milestone = issue.get("milestone", {}).get("title") if issue.get("milestone") else None
        number = issue.get("number")
    else:
        # gh api format
        title = issue["title"]
        url = issue["html_url"]
        state = issue["state"]
        labels = [label["name"] for label in issue.get("labels", [])]
        created = issue["created_at"]
        author = issue["user"]["login"] if issue.get("user") else None
        body = issue.get("body", "") or ""
        assignees = [a["login"] for a in issue.get("assignees", [])]
        milestone = issue.get("milestone", {}).get("title") if issue.get("milestone") else None
        number = issue.get("number")

    metadata = IssueMetadata(
        title=title,
        repo=repo,
        number=number,
        state=state.lower(),
        labels=labels,
        assignees=assignees,
        milestone=milestone,
        parent=parent,
        created_at=created,
        author=author,
        url=url,
    )

    return format_frontmatter(metadata, body)


if __name__ == "__main__":
    app()
