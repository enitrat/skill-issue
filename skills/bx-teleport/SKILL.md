---
name: bx-teleport
description: Move the current Claude Code session to a new Boat box and resume it there in herdr, with its repo as it is on disk (local commits and uncommitted changes) and its scratchpad. Use when the user says teleport, move this session to a box, continue this on Boat, or /bx-teleport.
---

# Teleport this session to a box

`bx teleport` does the work. It starts a box, ships the code, the transcript and the
scratchpad, makes them appear at the same paths as on this Mac, and resumes this session
in the box's herdr pane. This skill runs it and hands the session over. `bx-boxes` covers
boxes in general.

## 1. Check what will not travel

Before starting a box, tell the user in one or two lines what will not reach it, so they
can stop you:

- Gitignored files (`.env`, local config, build output). Nothing is pushed or committed;
  only tracked and untracked-but-not-ignored files travel, as a patch.
- Uncommitted changes inside submodules.
- Local MCP servers, plugins and hooks the box does not have.

When none of that applies, say nothing and go on.

## 2. Run it

```bash
bx teleport --session ${CLAUDE_SESSION_ID}
```

Run it in the background and wait for it to exit: it takes 2 to 10 minutes, most of it
the box restoring its disk. Pass `--name <name>` when the user named the box, `--snapshot`
when they chose one, and `--type default` only for light work (see `bx-boxes`).

The command copies the transcript once the box is ready, so the box gets this session up
to the command itself. Make no further changes to the repo once it starts: they would not
reach the box.

```
Exit status?
├── 0 → the last line on stdout is the box id. Go to 3.
├── 3 → Claude on the box stopped at a dialog. Read it:
│       herdr --machine <name> agent read claude --source visible
│       Show it to the user and ask before answering. Never answer it yourself.
└── other → read the bx: lines. Each failure prints how to inspect and delete the box.
            Report the failure; delete the box only if the user agrees.
```

## 3. Hand over

Tell the user, in this order:

1. The session runs on box `<name>`: attach with `herdr --remote <id>`, or pick `<name>`
   in herdr's machine list.
2. Exit this local session now. Two live copies of one session diverge, and work done here
   from now on is not on the box.
3. The box stops after 4 hours; extend it with `boat extend <id> --hours <n>`, and delete
   it with `bx rm <name>` when done. After a stop and resume, start Claude again in its
   pane with `CLAUDE_CODE_TMPDIR=/private/tmp claude --resume ${CLAUDE_SESSION_ID}` from
   the same directory.

Then stop. Do not edit files, run commands or answer further work in this session.

## How the paths match

Claude Code finds a session by its resolved working directory, and the transcript names
Mac paths. On the box the checkout is bind-mounted at the Mac path (`/Users/...`), and the
scratchpad data, kept in `~/.local/share/bx-teleport`, is bind-mounted at both the Mac's
`/private/tmp/claude-<mac uid>` and the box's `/private/tmp/claude-<box uid>`; the resumed
Claude runs with `CLAUDE_CODE_TMPDIR=/private/tmp`. `bx-teleport-mounts.service` restores
the mounts after a resume, once Boat has restored `/home/user`.
