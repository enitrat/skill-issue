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
GitHub Issue CLI - Helper scripts for creating and managing issues.

Usage:
    uv run gh_issue.py <command> [options]

Commands:
    create      Create a new issue
    create-sub  Create a sub-issue linked to a parent
    view        View issue details
    list        List issues in a repository
    link        Link two issues (parent/child relationship)
    close       Close an issue
    comment     Add a comment to an issue
    labels      Manage issue labels

Examples:
    uv run gh_issue.py create owner/repo --title "Bug: login fails" --body-file /tmp/issue.md
    uv run gh_issue.py create-sub owner/repo --parent 10 --title "Sub-task" --body "..."
    uv run gh_issue.py view owner/repo 123
    uv run gh_issue.py link owner/repo --parent 10 --child 42
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

import typer
from ghapi.all import GhApi
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax

app = typer.Typer(help="GitHub Issue CLI")
console = Console()

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


if __name__ == "__main__":
    app()
