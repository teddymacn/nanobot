# Heartbeat Tasks

This file is checked **every minute** by your nanobot agent. If the previous heartbeat run is still in progress, skip immediately — do not start a new run concurrently.

Add periodic tasks below — things you want the agent to work on in the background on a schedule.

If this file has no tasks (only headers and comments), the agent will skip the heartbeat.

---

## Active Tasks

### Beads Task Management

> ⚠️ **CRITICAL: This heartbeat agent is a TASK MANAGER only.**
> 
> **🚫 NEVER DO THE FOLLOWING:**
> - NEVER implement beads issues directly
> - NEVER write code, edit files, or make changes yourself
> - NEVER use general coding skills to implement tasks
> 
> **✅ ALWAYS DO THE FOLLOWING:**
> - ALWAYS delegate implementation to `claude-auto` or `copilot-auto` skills
> - ALWAYS launch delegated jobs in background mode
> - ALWAYS poll job status and record progress
> - ALWAYS write progress notes every 15 minutes while job is running
> 
> **Your role:** Claim tasks → Launch delegated jobs → Poll status → Record results → Close issues
> 
> **Delegated agent's role:** All actual implementation work (coding, editing, testing, etc.)

#### Delegation Workflow Summary

```
1. CLAIM: Find unassigned/open beads issue → Assign to self (status: in_progress)
2. DELEGATE: Launch claude-auto (or copilot-auto fallback) with issue details
3. POLL: Check job status on each heartbeat while running
4. REPORT: Write progress note to beads issue every 15 minutes (max)
5. RECORD: When done, save summary to memory/HISTORY.md
6. CLOSE: Close beads issue (status becomes closed automatically)
```

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
6. **DELEGATE IMPLEMENTATION (DO NOT WORK DIRECTLY):**
   
   > 🚫 **STOP! DO NOT proceed with any implementation yourself.**
   > 
   > This is the most critical step: **You must delegate, not implement.**
   > If you find yourself writing code, editing files, or making changes — STOP and delegate instead.
   
   **Step 6a: Read the auto-coding skill documentation**
   ```
   Read skills/claude-auto/SKILL.md   # Primary choice
   Read skills/copilot-auto/SKILL.md  # Fallback if claude-auto unavailable
   ```
   
   **Step 6b: Launch claude-auto (PREFERRED) in background mode**
   ```bash
   # IMPORTANT: This launches a SEPARATE agent to do the actual work
   # The job runs in background mode — do not wait for completion
   python skills/claude-auto/scripts/claude_auto.py \
     "Implement beads issue <id>: <title>. <description>" \
     --working-dir project
   # Save the returned job_id for status polling (e.g., job_12345)
   ```
   
   **Step 6c: Fallback to copilot-auto if claude-auto is unavailable**
   ```bash
   # Use this if claude-auto fails or is not configured
   python skills/copilot-auto/scripts/copilot_auto.py \
     "Implement beads issue <id>: <title>. <description>" \
     --working-dir project
   # Save the returned job_id for status polling
   ```
   
   > ✅ **CORRECT:** Launch delegated job, save job_id, continue to polling
   > 
   > 🚫 **INCORRECT:** Start coding, editing files, or implementing the issue yourself
   
   **Remember:** Your job is done once the delegated job is launched. The delegated agent handles all implementation.

7. **POLL STATUS AND WRITE PROGRESS NOTES:**
   
   On each subsequent heartbeat tick while the delegated job is still running:
   
   **Step 7a: Poll job status**
   ```bash
   # For claude-auto jobs
   python skills/claude-auto/scripts/claude_auto.py --status <job_id>
   
   # For copilot-auto jobs
   python skills/copilot-auto/scripts/copilot_auto.py --status <job_id>
   ```
   
   **Step 7b: Write progress note (every 15 minutes MAX)**
   
   > ⏰ **CRITICAL: Progress notes must be written at most once every 15 minutes.**
   > 
   > Before writing a note, check the timestamp of the last note on the beads issue.
   > If less than 15 minutes have passed, SKIP writing a new note.
   > This prevents spamming the issue with frequent updates.
   
   ```bash
   # Check last note timestamp first, then write if 15+ minutes have passed
   printf '[%s] Status: <delegated job status>. Next: monitoring job <job_id>.\n' \
     "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
     | bd update <id> --notes=- --json
   ```
   
   **Example: Checking last note timestamp**
   ```bash
   # Get the last note timestamp from the beads issue
   LAST_NOTE=$(bd show <id> --json | jq '.notes[-1].timestamp')
   # Compare with current time - only write if 15+ minutes have elapsed
   ```
8. **RECORD RESULTS AND CLOSE ISSUE:**
   
   When the delegated job finishes (status shows "completed" or similar):
   
   **Step 8a: Retrieve job results**
   ```bash
   # For claude-auto jobs
   python skills/claude-auto/scripts/claude_auto.py --results <job_id>
   
   # For copilot-auto jobs
   python skills/copilot-auto/scripts/copilot_auto.py --results <job_id>
   ```
   
   **Step 8b: Record history entry**
   
   **Record a history entry** in `memory/HISTORY.md` capturing:
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
   
   **Step 8c: Update beads issue status and close**
   
   Write a closing note to the beads issue and close it:
   
   - **✅ Completed successfully:** Close the issue (status becomes `closed` automatically):
     ```bash
     bd close <id> --reason "..." --json
     ```
   
   - **❌ Failed or blocked:** Annotate the failure reason and set status to `blocked` — do NOT close:
     ```bash
     printf '[%s] FAILED: <failure reason>. Job <job_id> did not complete successfully.\n' \
       "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
       | bd update <id> --notes=- --json
     bd update <id> -s blocked --json
     ```
   
   > 🛑 **Stop heartbeat notes once the task is closed, blocked, or paused.**
   > Do not continue polling or writing notes after the issue is resolved.

**If no beads issues are available:** skip silently — do not invent work.

---

### Troubleshooting Delegation Issues

| Problem | Solution |
|---------|----------|
| claude-auto not available | Fall back to `copilot-auto` skill |
| Job stuck in "running" state | Check job logs, consider cleanup and re-delegate |
| Progress notes too frequent | Enforce 15-minute minimum between notes |
| Delegated job fails | Record failure, set status to `blocked`, do not close |
| Cannot find job_id | Check `~/.claude-jobs/` or `~/.copilot-jobs/` directories |
| Agent starts implementing directly | **STOP** — re-read the CRITICAL warning box above |

**Remember:** If you're doing any implementation work yourself, you're doing it wrong. Always delegate.

---

## Completed

<!-- Move completed tasks here for reference, or delete them. -->
