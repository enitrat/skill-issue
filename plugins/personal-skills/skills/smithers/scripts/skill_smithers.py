#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Smithers workflow factory initializer.

Usage:
  uv run scripts/skill_smithers.py <target-dir> [--name <workflow-name>] [--no-install]

Sets up a smithers workflow template in <target-dir>.
The template includes the full phase pipeline (research, plan, implement, test, review, final-review).
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


TEMPLATE_DIR = Path(__file__).parent.parent / "template"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Initialize a smithers workflow in a target directory.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run scripts/skill_smithers.py ./scripts/my-workflow
  uv run scripts/skill_smithers.py ./scripts/my-workflow --name my-workflow
  uv run scripts/skill_smithers.py ./scripts/my-workflow --no-install
        """,
    )
    parser.add_argument(
        "target",
        help="Target directory to initialize the smithers workflow in",
    )
    parser.add_argument(
        "--name",
        help="Workflow name (defaults to the target directory name)",
        default=None,
    )
    parser.add_argument(
        "--no-install",
        action="store_true",
        help="Skip running `bun install` after copying files",
    )
    return parser.parse_args()


def copy_template(src: Path, dst: Path) -> None:
    """Copy template directory to target, skipping node_modules."""
    if not src.exists():
        print(f"ERROR: Template directory not found: {src}", file=sys.stderr)
        sys.exit(1)

    dst.mkdir(parents=True, exist_ok=True)

    for item in src.rglob("*"):
        # Skip node_modules anywhere in the tree
        if "node_modules" in item.parts:
            continue

        relative = item.relative_to(src)
        target_path = dst / relative

        if item.is_dir():
            target_path.mkdir(parents=True, exist_ok=True)
        else:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target_path)

    print(f"  Copied template → {dst}")


def patch_package_json(target: Path, workflow_name: str) -> None:
    """Replace the {{WORKFLOW_NAME}} placeholder in package.json."""
    pkg = target / "package.json"
    if not pkg.exists():
        return
    content = pkg.read_text()
    content = content.replace("{{WORKFLOW_NAME}}", workflow_name)
    pkg.write_text(content)
    print(f"  Set workflow name → {workflow_name!r}")


def find_repo_root(start: Path) -> Path | None:
    """Walk up from start to find the nearest directory containing .git."""
    current = start.resolve()
    while True:
        if (current / ".git").exists():
            return current
        parent = current.parent
        if parent == current:
            return None
        current = parent


def init_vcs(target: Path) -> None:
    """Initialize git (if no repo found) and jj --colocate (if not already set up).

    Git is initialized at target.parent (the workspace root), not inside the engine dir.
    This keeps the engine as a plain subdirectory of a monorepo-style workspace.
    """
    # Search upward from the parent so the engine dir is never itself the repo root
    repo_root = find_repo_root(target.parent)

    if repo_root is None:
        workspace_root = target.parent
        print(f"  No git repo found — running git init in {workspace_root}...")
        result = subprocess.run(["git", "init"], cwd=workspace_root, capture_output=False)
        if result.returncode != 0:
            print("  WARNING: git init failed. Run it manually.", file=sys.stderr)
            return
        repo_root = workspace_root
    else:
        print(f"  git repo found at {repo_root} (skipping git init)")

    if (repo_root / ".jj").exists():
        print(f"  jj already initialized at {repo_root} (skipping)")
        return

    if not shutil.which("jj"):
        print("  jj not found on PATH — install via: brew install jj")
        print("  Then run: jj git init --colocate")
        return

    print(f"  Running jj git init --colocate in {repo_root}...")
    result = subprocess.run(
        ["jj", "git", "init", "--colocate"], cwd=repo_root, capture_output=False
    )
    if result.returncode != 0:
        print("  WARNING: jj git init failed. Run it manually.", file=sys.stderr)
    else:
        print(f"  jj initialized at {repo_root}")


def run_bun_install(target: Path) -> None:
    """Run bun install in the target directory."""
    print("  Running bun install...")
    result = subprocess.run(
        ["bun", "install"],
        cwd=target,
        capture_output=False,
    )
    if result.returncode != 0:
        print("WARNING: bun install failed. Run it manually.", file=sys.stderr)
    else:
        print("  bun install complete")



def main() -> None:
    args = parse_args()

    target = Path(args.target).resolve()
    workflow_name = args.name or target.name

    print("\nInitializing smithers workflow:")
    print(f"  Target  : {target}")
    print(f"  Name    : {workflow_name}")
    print()

    # Check if target already exists and has content
    if target.exists() and any(target.iterdir()):
        print(f"WARNING: {target} already exists and is not empty.")
        answer = input("Continue and overwrite? [y/N] ").strip().lower()
        if answer != "y":
            print("Aborted.")
            sys.exit(0)

    copy_template(TEMPLATE_DIR, target)
    patch_package_json(target, workflow_name)
    init_vcs(target)

    if not args.no_install:
        bun_path = shutil.which("bun")
        if bun_path:
            run_bun_install(target)
        else:
            print(
                "  bun not found on PATH — skipping install. Run `bun install` manually."
            )

    # Compute a sensible relative path for display
    try:
        rel = target.relative_to(Path.cwd())
    except ValueError:
        rel = target

    print()
    print("Done! Next steps:")
    print()
    print("  1. Create a project config directory (outside the workflow engine):")
    print("       projects/<my-project>/smithers-config/")
    print(f"         config.ts          ← ProjectConfig (see {rel}/types/project.ts)")
    print("         instructions/      ← per-step MDX injected into component prompts")
    print("           research.mdx, plan.mdx, implement.mdx, test.mdx,")
    print("           code-review.mdx, prd-review.mdx, review-fix.mdx,")
    print("           final-review.mdx, update-progress.mdx")
    print("         output/context/    ← runtime context docs (create empty)")
    print("         output/plans/      ← runtime plan docs (create empty)")
    print("         run.sh             ← launcher")
    print()
    print("  2. Write run.sh (see README.md for full template with resume/discard prompts):")
    print("       #!/usr/bin/env bash")
    print("       SCRIPT_DIR=\"$(cd \"$(dirname \"${BASH_SOURCE[0]}\")\" && pwd)\"")
    print(f"       cd \"{target}\"")
    print("       export SMITHERS_PROJECT=\"$SCRIPT_DIR/config.js\"")
    print("       # <paste resume/discard block from README — handles cancelled/running runs>")
    print("       bunx smithers run workflow.tsx")
    print()
    print("  3. Run:")
    print("       ./projects/<my-project>/smithers-config/run.sh")


if __name__ == "__main__":
    main()
