#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Super-Ralph workflow initializer.

Usage:
  uv run scripts/init_super_ralph.py <target-dir> --root <repo-root> [OPTIONS]

Sets up a super-ralph workflow template in <target-dir> that drives
ticket-based development against <repo-root>.

Examples:
  uv run scripts/init_super_ralph.py ./scripts/workflow --root ../..
  uv run scripts/init_super_ralph.py ./workflow --root . --name "My Project" --id my-project
  uv run scripts/init_super_ralph.py ./workflow --root ../.. --no-install
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

TEMPLATE_DIR = Path(__file__).parent.parent / "template"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Initialize a super-ralph workflow.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("target", help="Directory to create the workflow in")
    parser.add_argument(
        "--root",
        required=True,
        help="Relative path from <target> to the git repository root (e.g. '../..')",
    )
    parser.add_argument("--name", help="Human-readable project name", default=None)
    parser.add_argument("--id", help="Kebab-case project ID", default=None)
    parser.add_argument(
        "--no-install", action="store_true", help="Skip bun install"
    )
    parser.add_argument(
        "--no-jj", action="store_true", help="Skip jj init"
    )
    return parser.parse_args()


def copy_template(src: Path, dst: Path) -> None:
    if not src.exists():
        print(f"ERROR: Template dir not found: {src}", file=sys.stderr)
        sys.exit(1)
    dst.mkdir(parents=True, exist_ok=True)
    for item in src.rglob("*"):
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


def compute_url_depth(root_relative: str) -> str:
    """Convert a filesystem relative path to a URL-relative path for import.meta.url.

    From components/workflow.tsx we need one extra '../' because the file is
    inside a components/ subdirectory of the workflow dir.
    """
    # Normalise: e.g. "../.." → 2 levels up from workflow dir
    parts = Path(root_relative).parts
    ups = sum(1 for p in parts if p == "..")
    # +1 because workflow.tsx is inside components/
    return "/".join([".."] * (ups + 1))


def patch_placeholders(target: Path, project_id: str, project_name: str, root_relative: str) -> None:
    """Replace {{PLACEHOLDER}} tokens in all text files."""
    url_depth = compute_url_depth(root_relative)
    replacements = {
        "{{PROJECT_ID}}": project_id,
        "{{PROJECT_NAME}}": project_name,
        "{{ROOT_RELATIVE}}": root_relative,
        "{{ROOT_URL_DEPTH}}": url_depth,
    }
    for fpath in target.rglob("*"):
        if fpath.is_dir() or "node_modules" in fpath.parts:
            continue
        # Only patch text files
        if fpath.suffix not in (".ts", ".tsx", ".json", ".toml", ".md"):
            continue
        try:
            content = fpath.read_text()
        except UnicodeDecodeError:
            continue
        original = content
        for placeholder, value in replacements.items():
            content = content.replace(placeholder, value)
        if content != original:
            fpath.write_text(content)


def find_repo_root(start: Path) -> Path | None:
    current = start.resolve()
    while True:
        if (current / ".git").exists():
            return current
        parent = current.parent
        if parent == current:
            return None
        current = parent


def init_jj(target: Path) -> None:
    repo_root = find_repo_root(target)
    if repo_root is None:
        print("  No git repo found — skipping jj init")
        return
    if (repo_root / ".jj").exists():
        print(f"  jj already initialized at {repo_root}")
        return
    if not shutil.which("jj"):
        print("  jj not on PATH — install: brew install jj")
        return
    print(f"  Running jj git init --colocate in {repo_root}...")
    subprocess.run(["jj", "git", "init", "--colocate"], cwd=repo_root, capture_output=False)


def run_bun_install(target: Path) -> None:
    print("  Running bun install...")
    result = subprocess.run(["bun", "install"], cwd=target, capture_output=False)
    if result.returncode != 0:
        print("  WARNING: bun install failed. Run it manually.", file=sys.stderr)


def main() -> None:
    args = parse_args()

    target = Path(args.target).resolve()
    project_id = args.id or target.name
    project_name = args.name or project_id.replace("-", " ").title()
    root_relative = args.root

    print(f"\nInitializing super-ralph workflow:")
    print(f"  Target     : {target}")
    print(f"  Project ID : {project_id}")
    print(f"  Name       : {project_name}")
    print(f"  Repo root  : {root_relative} (from target dir)")
    print()

    if target.exists() and any(target.iterdir()):
        answer = input(f"  {target} already exists. Overwrite? [y/N] ").strip().lower()
        if answer != "y":
            print("  Aborted.")
            sys.exit(0)

    copy_template(TEMPLATE_DIR, target)
    patch_placeholders(target, project_id, project_name, root_relative)

    if not args.no_jj:
        init_jj(target)

    if not args.no_install:
        if shutil.which("bun"):
            run_bun_install(target)
        else:
            print("  bun not on PATH — run `bun install` manually.")

    # Display path
    try:
        rel = target.relative_to(Path.cwd())
    except ValueError:
        rel = target

    print(f"""
Done! Next steps:

  1. Edit focuses:
       {rel}/components/focuses.ts
     Replace the placeholder focuses with your project's actual domain areas.

  2. Customize the workflow:
       {rel}/components/workflow.tsx
     Fill in the TODO sections:
       - Agent system prompts (planning, implementation, testing, reviewing)
       - specsPath, referenceFiles
       - buildCmds, testCmds
       - codeStyle, reviewChecklist
       - Agent models and timeouts

  3. Run:
       cd {rel} && bun run index.ts
""")


if __name__ == "__main__":
    main()
