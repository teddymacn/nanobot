# Heartbeat Tasks

This file is checked **every minute** by your nanobot agent. If the previous heartbeat run is still in progress, skip immediately — do not start a new run concurrently.

Add periodic tasks below — things you want the agent to work on in the background on a schedule.

If this file has no tasks (only headers and comments), the agent will skip the heartbeat.

---

## Active Tasks

### Beads Task Management

**Pre-condition — skip this entire section if either check fails:**
```bash
# 1. project folder must exist
test -d project || exit 0
# 2. it must be a git repo
test -d project/.git || exit 0
```

Check the [beads](https://github.com/steveyegge/beads) issue tracker (`.beads/` folder) for
assigned work and manage task progress. Use the `beads` skill for all `bd` interactions.

**When idle (no current task):**

1. Read the `beads` skill: `skills/beads/SKILL.md`
2. Derive the agent ID from `USER.md` and the current hostname:
   ```bash
   AGENT_NAME=$(grep -m1 '\*\*Name\*\*' USER.md | sed 's/.*\*\*Name\*\*:[[:space:]]*//')
   AGENT_ID="${AGENT_NAME}-$(hostname -s)"
   ```
3. Check for any `task`- or `bug`-type issues already `in_progress` and assigned to this agent — resume
   these first (verify `assignee == $AGENT_ID` to avoid stealing another agent's task):
   ```bash
   cd project
   bd list --type task --status in_progress --json
   bd list --type bug  --status in_progress --json
   ```
4. If none in progress, check for unblocked `open` issues:
   ```bash
   bd ready --json
   ```
5. If issues are found, pick the highest-priority unblocked one and assign it explicitly:
   ```bash
   bd update <id> -a "$AGENT_ID" -s in_progress --json
   ```
6. Write an initial heartbeat note, then **delegate the implementation** to the `claude-auto` or
   `copilot-auto` skill — do **not** implement the issue directly. Read the skill first, then launch
   it in background mode with a prompt derived from the issue title and description:
   ```
   Read skills/claude-auto/SKILL.md   # or skills/copilot-auto/SKILL.md
   ```
   ```bash
   # Example using claude-auto (prefer this; fall back to copilot-auto if unavailable)
   python skills/claude-auto/scripts/claude_auto.py \
     "Implement beads issue <id>: <title>. <description>" \
     --working-dir project
   # Save the returned job_id for status polling
   ```
7. On each subsequent heartbeat tick while the delegated job is still running, poll its status:
   ```bash
   python skills/claude-auto/scripts/claude_auto.py --status <job_id>
   ```
   Write a progress note to the beads issue **at most once every 15 minutes**
   (check the timestamp of the last note before writing):
   ```bash
   printf '[%s] Status: <delegated job status>. Next: monitoring job <job_id>.\n' \
     "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
     | bd update <id> --notes=- --json
   ```
8. When the delegated job finishes, retrieve its results:
   ```bash
   python skills/claude-auto/scripts/claude_auto.py --results <job_id>
   ```
   Then **record a history entry** in `memory/HISTORY.md` capturing:
   - The beads issue ID and title
   - A concise summary of what was done
   - The key reasoning / thinking from the delegated job's output
   ```bash
   cat >> memory/HISTORY.md << 'EOF'

   [<timestamp>] BEADS TASK COMPLETED — <id>: <title>
     Delegated to: claude-auto (job <job_id>)
     Summary: <one-paragraph summary of what was implemented>
     Thinking: <key reasoning steps or decisions made by the delegated agent>
   EOF
   ```
   Finally, write a closing note to the beads issue and update its status:
   - **Completed successfully:** set status to `done` first, then close:
     ```bash
     bd update <id> -s done --json
     bd close <id> --json
     ```
   - **Failed or blocked:** annotate the failure reason and set status to `blocked` — do not close.
   Stop heartbeat notes once the task is closed, blocked, or paused.

**If no beads issues are available:** skip silently — do not invent work.

---

## Completed

<!-- Move completed tasks here for reference, or delete them. -->
