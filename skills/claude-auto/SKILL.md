---
name: claude-auto
description: Execute Claude Code CLI in full auto mode for coding tasks. Runs in background mode with --dangerously-skip-permissions flag. Use for code generation, refactoring, debugging, testing, or any development work.
---

# Claude Code Auto Executor

This skill enables automated execution of Claude Code CLI in full auto mode for coding tasks.

**Important:** This skill always runs tasks in background mode to avoid timeout issues with long-running tasks.

## Usage

### Basic Usage (via nanobot)

Just describe your task naturally. The skill will automatically:
- Run in background mode
- Use `--dangerously-skip-permissions` for full auto-approval
- Add the working directory with `--add-dir`
- Validate the model against available models
- Use the default model (or specified model)

### Direct CLI Usage

```bash
# Start a task (background mode)
python scripts/claude_auto.py "your task description"

# With specific model (validated against available models)
python scripts/claude_auto.py "your task" --model <model-name>

# With custom working directory
python scripts/claude_auto.py "your task" --working-dir /path/to/project

# List available models
python scripts/claude_auto.py --models

# Validate a model name
python scripts/claude_auto.py --validate-model <model-name>

# Check status
python scripts/claude_auto.py --status <job_id>

# Get incremental logs since a checkpoint
python scripts/claude_auto.py --logs <job_id> --checkpoint <offset> --json

# Get results
python scripts/claude_auto.py --results <job_id>

# List all jobs
python scripts/claude_auto.py --list

# Cleanup old jobs
python scripts/claude_auto.py --cleanup --days 7
```

## Flags Used

- `-p` / `--print`: Non-interactive mode (exit on completion)
- `--dangerously-skip-permissions`: Full auto-approval mode
- `--add-dir <path>`: Auto-trust the working directory
- `--model <model>`: Specify model (optional, validated against available models)

## Model Configuration

### Environment Variables

- `ANTHROPIC_BASE_URL`: API base URL (default: `https://api.anthropic.com/v1`)
- `ANTHROPIC_AUTH_TOKEN`: Bearer token for authentication
- `ANTHROPIC_API_KEY`: API key for authentication (fallback if no auth token)
- `ANTHROPIC_MODEL`: Default model name (used when no auth or model not specified)
- `ANTHROPIC_MODELS`: Comma-separated list of available models (fallback when API unavailable)

### Model Selection Order

1. `--model` flag passed to the script (validated against available models)
2. `ANTHROPIC_MODEL` environment variable (default model)
3. Claude Code CLI default

### Model Listing Fallback

When listing available models, the skill uses the following fallback order:

1. **API endpoint** (`{base_url}/models`) - Fetches models from the API
2. **`ANTHROPIC_MODELS` env var** - Comma-separated list (e.g., `claude-opus-4-6,claude-sonnet-4-6`)
3. **`ANTHROPIC_MODEL` env var** - Single default model (e.g., `qwen3.5-plus`)

This ensures the skill works even when the API doesn't support model listing (e.g., custom endpoints like DashScope).

### Model Validation

When a model is specified:
- The skill fetches available models from the API (`{base_url}/models`)
- If the API returns an error (e.g., HTTP 404), falls back to `ANTHROPIC_MODELS` env var
- If `ANTHROPIC_MODELS` is not set, falls back to `ANTHROPIC_MODEL` env var
- Invalid models are rejected with an error message
- Available models are displayed for reference

## Job Storage

Jobs are stored in `~/.claude-jobs/` with:
- `<job_id>.log` - Output log
- `<job_id>.pid` - Process ID
- `<job_id>.meta.json` - Metadata (task, model, start time, etc.)

## Incremental Log Polling

When a background job is still running and you need more detail than `--status` provides, use incremental log polling:

```bash
python scripts/claude_auto.py --logs <job_id> --checkpoint <offset> --json
```

Recommended polling flow:

1. Start with checkpoint `0`
2. Save the returned `next_checkpoint`
3. On the next poll, pass that value back to `--checkpoint`
4. Repeat until `status` is `completed`

Example JSON fields returned by `--logs --json`:

- `content` - New log content since the last checkpoint
- `next_checkpoint` - Offset to use on the next poll
- `has_new_content` - Whether anything new was written
- `truncated` - Whether output was capped by `--max-bytes`
- `status` / `is_running` - Current job state

You can also control response size with:

```bash
python scripts/claude_auto.py --logs <job_id> --checkpoint <offset> --max-bytes 8000 --json
```

Use this when the agent needs to understand what the running background job is doing without re-reading the entire log file every time.

## Requirements

- Claude Code CLI installed (`npm install -g @anthropic-ai/claude-code`)
- Authentication configured via `ANTHROPIC_AUTH_TOKEN` or `ANTHROPIC_API_KEY` environment variables
- `ANTHROPIC_MODEL` env var set (for fallback when API unavailable)
