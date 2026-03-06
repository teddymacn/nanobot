---
name: beads
description: >
  Interact with the beads (bd) task tracker stored in the repo's .beads folder.
  Use this skill for: checking assigned tasks, claiming work, writing heartbeat
  progress notes into issue notes, and closing completed issues.
  Auto-triggered during heartbeat when idle, and periodically during active work.
---

# Beads Task Tracker Skill

[Beads](https://github.com/steveyegge/beads) (`bd`) is a git-backed, dependency-aware issue tracker
designed for AI agents. Tasks ("issues") live in the `.beads` folder of the current repo.

> **Prerequisites**: 
> - The `bd` CLI must be available on `$PATH`
> - Dolt database server (auto-started by `bd`, or install separately: `brew install dolt`)
>
> **Always check before installing** — installing is expensive and should only happen once.
>
> ```bash
> # Only install if bd is not already present
> if ! command -v bd &>/dev/null; then
>   # Recommended: Quick install script (all platforms)
>   curl -fsSL https://raw.githubusercontent.com/steveyegge/beads/main/scripts/install.sh | bash
>   
>   # Alternative: Homebrew (macOS/Linux)
>   # brew install beads
>   
>   # Alternative: npm (Node.js environments)
>   # npm install -g @beads/bd
>   
>   # Alternative: go install (requires Go 1.24+)
>   # go install github.com/steveyegge/beads/cmd/bd@latest
> fi
> ```

---

## Key Concepts

| Term | Meaning |
|------|---------|
| **Issue type** | `task`, `bug`, `feature`, `epic`, `chore` |
| **Status** | `open`, `in_progress`, `closed` |
| **Priority** | `0`=Critical · `1`=High · `2`=Medium · `3`=Low · `4`=Backlog |
| **`bd ready`** | Lists unblocked, unclaimed issues ready to work on |
| **`--json`** | Always use this flag for programmatic / agent use |

---

## Agent ID

Beads uses an **assignee string** to track which agent owns a task. Always derive the ID
at runtime — do **not** hardcode it.

```bash
# Read agent name from USER.md (the '**Name**' field in Basic Information)
AGENT_NAME=$(grep -m1 '\*\*Name\*\*' USER.md | sed 's/.*\*\*Name\*\*:[[:space:]]*//')

# Get the current machine hostname
AGENT_HOST=$(hostname -s)

# Compose the agent ID
AGENT_ID="${AGENT_NAME}-${AGENT_HOST}"
# e.g. "Coder-macbook-pro" or "Coder-prod-worker-1"
```

Use `$AGENT_ID` wherever `-a` is required below.

---

## Heartbeat: Idle Check — Find Assigned Tasks

When the agent is **idle** (no current task), run the following to find assigned,
incomplete `task`- or `bug`-type issues in `open` or `in_progress` status:

```bash
# Check for issues already assigned to this agent and in_progress — resume these first
# (run once per eligible type; bd list accepts one --type at a time)
bd list --type task --status in_progress --json
bd list --type bug  --status in_progress --json

# Then check for open, unblocked issues ready to be picked up (covers all types)
bd ready --json
```

Parse the JSON output. Filter for `type` in `["task", "bug"]` and status in `["open", "in_progress"]`.
When resuming an `in_progress` task, verify that its `assignee` matches `$AGENT_ID` before
continuing — avoid stealing another agent's work.

**If tasks are found:**
1. Pick the highest-priority, unblocked task (lowest priority number, or in_progress over open).
2. Assign it to this agent and set it in-progress:
   ```bash
   bd update <id> -a "$AGENT_ID" -s in_progress --json
   ```
3. Write an initial progress note (see Heartbeat Notes section below).
4. Begin working on the task.

**If no tasks are found:**
- Log "No beads tasks available" and skip — do not create work from nothing.

---

## Claiming a Task

Use the `--claim` flag for atomic claim (sets assignee + in_progress in one operation):

```bash
# Atomically claim a task (sets assignee to context user + status to in_progress)
bd update <id> --claim --json
```

For explicit agent ID assignment (multi-agent environments):

```bash
# Assign to specific agent and set status to in_progress
bd update <id> -a "$AGENT_ID" -s in_progress --json
```

Only claim **one task at a time**. Do not hold multiple tasks simultaneously.

---

## Heartbeat Progress Notes (every ~15 minutes)

While actively working on a task, write a timestamped progress note into the
issue's **notes** field approximately every 15 minutes to provide a live status
trail. Use `--notes` (which **appends** to existing notes):

```bash
# Append a heartbeat note (use stdin to avoid shell escaping issues)
printf '[%s] Status: <current status>. <brief reason or next step>.\n' \
  "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  | bd update <id> --notes=- --json
```

**Note format** (keep concise, one line per heartbeat):
```
[2026-03-06T12:00:00Z] Status: In progress — implementing X. Next: run tests.
[2026-03-06T12:15:00Z] Status: Tests passing. Finalising documentation.
```

**Stop writing heartbeat notes** when:
- The task is completed (closed) — write a final "Completed" note first.
- You are blocked and cannot continue (write a "Blocked: <reason>" note, then stop).
- The task has been abandoned (write a "Paused: <reason>" note, then stop).

---

## Completing a Task

```bash
# Close with a reason summary
bd close <id> --reason "Implemented X, tests passing, docs updated." --json
```

Always write a final heartbeat note **before** closing, so the audit trail is complete:
```bash
printf '[%s] Status: Completed — <brief summary>.\n' \
  "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  | bd update <id> --notes=- --json

bd close <id> --reason "<summary>" --json
```

---

## Blocked or Cannot Continue

If you cannot continue for any reason (missing info, environment issue, out of scope):

```bash
# Write a blocked note
printf '[%s] Blocked: <reason>. Stopping heartbeat updates.\n' \
  "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  | bd update <id> --notes=- --json

# Update title/notes with blocker details for visibility (optional but helpful)
bd update <id> --notes "Blocked: <reason>" --json
```

Then **stop** writing periodic heartbeat notes for that issue. The next agent session
should check `bd list --status in_progress --json` and decide whether to resume or
re-triage the blocked task.

---

## Discovering New Work

If you discover additional work while executing a task, **do not** create standalone markdown
TODOs. Create a linked beads issue instead:

```bash
bd create "Found: <title>" \
  --description="<what was found>" \
  -t task -p 2 \
  --deps discovered-from:<parent-id> \
  --json
```

---

## Useful Listing Commands

```bash
# All open tasks and bugs
bd list --type task --status open --json
bd list --type bug  --status open --json

# Tasks/bugs currently in_progress
bd list --type task --status in_progress --json
bd list --type bug  --status in_progress --json

# Unblocked tasks ready to work on
bd ready --json

# Show a specific issue (full details including notes)
bd show <id> --json

# Show all issues of any type
bd list --json
```

---

## Important Rules

- ✅ Always use `--json` for programmatic output parsing.
- ✅ Derive `$AGENT_ID` as `{Name from USER.md}-{hostname -s}` at runtime.
- ✅ Use `bd update <id> --claim` for simple atomic claim (recommended for single-agent).
- ✅ Use `-a "$AGENT_ID" -s in_progress` for explicit agent ID assignment (multi-agent).
- ✅ Use `bd update <id> --notes=-` (stdin) to avoid escaping issues with special characters.
- ✅ Write heartbeat notes approximately every 15 minutes while actively working.
- ✅ Stop heartbeat notes when blocked, paused, or completed.
- ✅ Claim only one task at a time.
- ✅ Use `bd ready` before asking "what should I work on?".
- ✅ Run `bd init` in each project before using beads.
- ❌ Do NOT use `bd edit` — it opens an interactive editor that agents cannot use.
- ❌ Do NOT create markdown TODO lists outside of beads.
- ❌ Do NOT duplicate task tracking across multiple systems.

---

## Shell Safety

When writing notes that may contain backticks, `!`, `$`, or nested quotes, always
pipe via stdin to avoid shell expansion:

```bash
# Safe: pipe content via stdin
printf '%s\n' "[2026-03-06T12:00:00Z] Status: Fixed \`foo\` bug." \
  | bd update <id> --notes=- --json

# Or use a here-string
bd update <id> --notes=- --json <<'EOF'
[2026-03-06T12:00:00Z] Status: Updated config with $VAR references.
EOF
```

---

## Editor Integration Setup

After installing `bd`, set up editor integration for your workflow:

```bash
# Initialize beads in your project (creates .beads/ folder)
bd init

# Setup editor hooks (choose one)
bd setup claude   # Claude Code - installs SessionStart hooks
bd setup cursor   # Cursor IDE - creates .cursor/rules/beads.mdc
bd setup aider    # Aider - creates .aider.conf.yml
bd setup codex    # Codex CLI - creates/updates AGENTS.md
bd setup mux      # Mux - creates/updates AGENTS.md
```

**Verify installation:**
```bash
bd version
bd setup claude --check   # Verify Claude Code integration
```

---

## Updating bd

```bash
# Quick install script (recommended)
curl -fsSL https://raw.githubusercontent.com/steveyegge/beads/main/scripts/install.sh | bash

# Homebrew
brew upgrade beads

# npm
npm update -g @beads/bd

# go install
go install github.com/steveyegge/beads/cmd/bd@latest
```
