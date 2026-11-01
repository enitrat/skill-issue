---
name: bx-boxes
description: Run work on short-lived Boat sandboxes with the `bx` CLI. Use when a task needs a clean Linux machine, more parallelism than this Mac allows, or isolation between runs (evals, test shards, agent trials that share /tmp, ports or a browser), or when the user says box, Boat, sandbox, spawn a machine or run it remotely.
---

# Boxes with bx

`bx` starts Boat sandboxes ("boxes") from saved snapshots, registered in herdr.
`bx --help` is the reference. This skill is the procedure.

## 1. Pick the snapshot

Run `bx list`. It prints each snapshot and the repos baked into it.

```
Is the repo you need in a snapshot's REPOS column?
├── Yes → that snapshot. The repo is at ~/<snapshot>/<repo>, deps installed, at the bake's commit.
└── No  → dev, then clone the repo on the box with `gh repo clone`.
```

A snapshot saves the clone and `pnpm install` (about a minute per box). Never bake a new
snapshot for a one-off task: a bake takes 15 minutes.

## 2. Get your code onto the box

The baked repo is at the bake's `main`, not your branch.

```
Is your work committed and pushed?
├── Yes → on the box: git -C ~/<snapshot>/<repo> fetch origin <branch> && git checkout FETCH_HEAD
└── No  → boat push <id> <local-repo> --to /home/user/work/<repo>
```

Then run `pnpm install --frozen-lockfile --prefer-offline` in that directory. It takes
seconds because the snapshot's pnpm store holds the packages. Never `--offline`: pnpm fetches the
version a repo pins into `~/.cache`, which Boat does not keep.

Prefer the git branch: `boat push` copies files but never deletes one, so pushing over the
baked checkout leaves files your branch removed. That is why it goes to a fresh directory.

## 3. Split the work across boxes

One box per shard, never one per trial. A box takes 70 to 100 s to be ready (it waits for its
disk to restore, then checks nix, gh, git and pnpm), so short trials on their own boxes spend
most of their time starting.

- Shards = the number of independent pieces you can run in parallel. Each shard runs its
  pieces one after another, inside its box.
- At most 30 new boxes per minute (the account's start limit). Up to 300 can run at once.
- Name boxes `<task>-<n>`. Names must be unique; `bx ls` shows them.
- Size: `bx new --type large` (8 vCPU, 16 GB, twice the rate) when one shard saturates the
  default 4 vCPU, such as a stack plus a browser plus an agent. Otherwise keep the default.

```bash
for n in 1 2 3 4; do bx new --snapshot zama --name eval-$n > /tmp/eval-$n.id & done; wait
```

`bx new` prints the box id last. It exits non-zero when a check failed. Delete that box
and create it again.

## 4. Run

Run commands over `ssh <id>`. The box's shell has every tool, Claude Code logged in, `gh`
logged in, and your git identity.

A `zama` box explores super-app as the Mac does: `pnpm cli stack start` and the
`zama-app-exploration` skill work there. Its Docker images, Playwright's Chromium and
agent-browser's Chrome are in the snapshot. Give each agent on a box its own `--as` lease and
browser session prefix.

- Under 10 minutes: run in the foreground, `ssh <id> 'cd <dir> && <cmd>'`.
- Longer: detach on the box, so a dropped connection does not kill the run, then poll:

  ```bash
  ssh <id> 'cd <dir> && nohup sh -c "<cmd> > ~/run.log 2>&1; echo \$? > ~/run.exit" >/dev/null 2>&1 &'
  ssh <id> cat ~/run.exit   # repeat until it exists; ~/run.log has the output
  ```

On the first box only, check the assumptions your run makes before starting every shard: a
5-second command that exercises the same tools (a dry run, a check mode, one tiny trial).
Fixing a wrong assumption costs one box, not twenty.

## 5. Bring results back, then delete

```bash
boat scp -r <id>:<results-dir> ./results/<task>-<n>
bx rm <task>-<n>
```

Always `bx rm`, failed runs included: wrap the run in `trap 'bx rm <name>' EXIT`. A box left
alone runs, and bills, until its 4-hour auto-stop. `bx gc` offers to delete boxes stopped
for more than 3 days.

Never `boat snapshot` a task box. It holds your gh and Claude logins, and a saved snapshot
keeps them forever.

## Example: the ds eval in super-app

`tools/ds-eval/eval.ts run` runs agent trials. Locally it must stay at `--concurrency 1`,
because trials `pkill` dev servers and write to `/tmp`. One box per shard isolates them.

1. Snapshot: `zama` (has super-app). Code: the eval branch, pushed, then fetched on each box.
2. Shards: split the task list into N groups, one box each, `--concurrency 1` inside a box.
3. On box 1 first: `bun tools/ds-eval/eval.ts check`. If you grade with `--render`, also run
   `bun tools/ds-eval/eval.ts gold confidential-borrow --render` to confirm a browser works.
4. Each box:
   `bun tools/ds-eval/eval.ts run --tasks <group> --k <k> --judge --yes --concurrency 1 --out ~/ds-eval-out`
   (`--yes` spends API credit: say the cost from the run without `--yes` first).
5. Pull each box's `~/ds-eval-out` into one local directory, then `eval.ts report` it. Before
   sharding for real, check on two tiny shards that `report` reads trials pulled from
   several boxes as one run.
