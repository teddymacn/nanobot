# Tool Usage Notes

Tool signatures are provided automatically via function calling.
This file documents non-obvious constraints, usage patterns, and coder-specific guidance.

---

## exec — Shell Commands

- **Timeout**: Default 60 s. Long-running builds or tests may need `timeout` prefix or background mode via skills.
- **Blocked commands**: Destructive commands (`rm -rf /`, `format`, `dd`, `shutdown`, `mkfs`, etc.) are blocked.
- **Output limit**: Truncated at 10,000 characters. Pipe through `head`, `tail`, or `grep` for large outputs.
- **Workspace restriction**: `restrictToWorkspace` config can limit file access to the workspace directory.
- **Always check exit codes**: A non-zero exit is a signal to diagnose before retrying.

### Common patterns

```bash
# Install dependencies (Node)
npm ci

# Install dependencies (Python)
pip install -e ".[dev]"  # or: uv sync

# Run tests
npm test          # Node
pytest -x -q      # Python (fail-fast, quiet)

# Type check
npx tsc --noEmit  # TypeScript
mypy src/         # Python

# Lint / format
npx eslint src/
ruff check src/ && ruff format src/

# Build
npm run build
```

---

## read_file / write_file / edit_file — File Operations

- **Read before writing.** Never overwrite a file without reading it first.
- **edit_file** is preferred over write_file for partial changes — it is safer and creates a cleaner diff.
- **Re-read after writing** when correctness of the final content matters (e.g. config files, code).
- File paths must be absolute or workspace-relative. Be explicit.

---

## search / grep — Code Navigation

Use these to orient yourself in an unfamiliar codebase before making changes:

- `grep` for function/class names, import paths, or error strings.
- `find` / `list_dir` to understand project structure.
- Read `package.json`, `pyproject.toml`, `Makefile`, or `README.md` first in any new project.

---

## Sub-agent Delegation — Skill Selection

When a coding task should be delegated to a sub-agent CLI, use the following decision rule:

### Which skill to use?

| Situation | Skill to use |
|-----------|--------------|
| User explicitly says **"use claude"** or **"with claude"** | `claude-auto` |
| User explicitly says **"use copilot"** or **"with copilot"** | `copilot-auto` |
| No specific tool mentioned (default) | `claude-auto` |

> **Rule**: Honour the user's explicit choice. If neither is mentioned, default to `claude-auto`.

---

## claude-auto Skill

Use for autonomous coding tasks when Claude Code CLI is appropriate (default choice):

- **When to use**: Multi-file refactors, test generation, feature scaffolding, or anything requiring many steps — unless the user asks for copilot specifically.
- **Always use background mode**: The skill runs tasks as background jobs to avoid timeouts.
- **Check status**: Use `--status <job_id>` to poll, `--results <job_id>` to retrieve output.
- **Do NOT call `claude` directly** via exec unless the skill is unavailable (see `AGENTS.md`).

Skill location: `/root/.nanobot/workspace/skills/claude-auto/SKILL.md`

---

## copilot-auto Skill

Use when the user explicitly requests GitHub Copilot CLI, or when the task is Copilot-specific:

- **Do NOT call `gh copilot` directly** via exec unless the skill is unavailable.
- All other background-mode and status-polling rules from `claude-auto` apply equally.

Skill location: `/root/.nanobot/workspace/skills/copilot-auto/SKILL.md`

---

## cron — Scheduled Reminders

- Use the built-in `cron` tool, do **not** call `nanobot cron` via exec.
- Refer to the cron skill for full usage.

---

## git — Version Control

- Use `exec` to run git commands. Always check `git status` and `git diff` before committing.
- Never `git push --force` on shared branches.
- Prefer `git add -p` (patch mode) for atomic commits — pipe `yes` if non-interactive.
- If in doubt about the current branch or remote, run `git remote -v && git branch -a` first.

---

## Environment & Secrets

- **Never hardcode secrets.** Use environment variables or secret manager references.
- Read `.env` files via `exec` with `cat .env | grep -v '^#'` to understand available variables.
- Do not log or print full secret values — mask them in output.

---

## Language / Stack — Quick Reference

| Language   | Package manager    | Test runner     | Linter/Formatter      |
|------------|--------------------|-----------------|-----------------------|
| TypeScript | npm / pnpm / yarn  | jest / vitest   | eslint + prettier     |
| Python     | pip / uv / poetry  | pytest          | ruff                  |
| Go         | go mod             | go test         | golangci-lint         |
| Rust       | cargo              | cargo test      | clippy + rustfmt      |
| Shell      | —                  | bats / shunit2  | shellcheck            |
