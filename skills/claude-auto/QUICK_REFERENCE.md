# Claude Auto - Quick Reference

## Start a Task

```bash
# Basic task
python scripts/claude_auto.py "your task description"

# With specific model (validated against available models)
python scripts/claude_auto.py "your task" --model claude-sonnet-4-6

# With custom working directory
python scripts/claude_auto.py "your task" --working-dir /path/to/project
```

## Model Management

```bash
# List available models
python scripts/claude_auto.py --models

# Validate a model name
python scripts/claude_auto.py --validate-model <model-name>
```

## Monitor Jobs

```bash
# Check status
python scripts/claude_auto.py --status <job_id>

# Get incremental logs since last checkpoint
python scripts/claude_auto.py --logs <job_id> --checkpoint <offset> --json

# Get results (waits for completion)
python scripts/claude_auto.py --results <job_id>

# List all jobs
python scripts/claude_auto.py --list
```

## Maintenance

```bash
# Clean up old jobs (default: 7 days)
python scripts/claude_auto.py --cleanup --days 7
```

## Flags Used

| Flag | Purpose |
|------|---------|
| `-p` / `--print` | Non-interactive mode |
| `--dangerously-skip-permissions` | Full auto-approval |
| `--add-dir <path>` | Trust working directory |
| `--model <model>` | Specify model (validated) |

## Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `ANTHROPIC_BASE_URL` | API base URL | `https://api.anthropic.com/v1` |
| `ANTHROPIC_AUTH_TOKEN` | Bearer token for auth | - |
| `ANTHROPIC_API_KEY` | API key for auth (fallback) | - |
| `ANTHROPIC_MODEL` | Default model name | - |
| `ANTHROPIC_MODELS` | Comma-separated model list (fallback) | - |

## Job Storage

Jobs are stored in `~/.claude-jobs/`:
- `<job_id>.log` - Output log
- `<job_id>.pid` - Process ID
- `<job_id>.meta.json` - Metadata

## Incremental Log Polling

- First poll: use `--checkpoint 0`
- Next polls: reuse the returned `next_checkpoint`
- Add `--max-bytes <n>` if you want a larger chunk
- Prefer `--json` so the caller can parse `content`, `next_checkpoint`, `status`, and `truncated`

## Model Listing Fallback

When the API doesn't support model listing, the skill falls back in this order:

1. API endpoint (`{base_url}/v1/models`)
2. `ANTHROPIC_MODELS` env var (comma-separated)
3. `ANTHROPIC_MODEL` env var (single default)

## Model Validation

- Models are validated against the API's available models list
- If API returns error, falls back to `ANTHROPIC_MODELS` env var
- If not set, falls back to `ANTHROPIC_MODEL` env var
- Invalid models are rejected before task execution
