---
name: copilot-auto
description: Execute GitHub Copilot CLI in autopilot mode. Runs tasks in background with --autopilot --yolo flags. Use for code generation, refactoring, debugging, and testing.
---

# GitHub Copilot Auto Executor

Executes GitHub Copilot CLI in full autopilot mode for coding tasks. All tasks run in background with `--autopilot --yolo` flags.

## Prerequisites

1. **Copilot CLI installed**: `npm install -g @github/copilot`
2. **Token set** (for sandbox/container): `export COPILOT_GITHUB_TOKEN='ghp_...'`

## Usage

### Basic Usage

```bash
# Run a task (background mode, auto-validates token)
python scripts/copilot_auto.py "Create a Python module"

# With specific model (validated against available models)
python scripts/copilot_auto.py "Refactor this" --model claude-sonnet-4.6

# Specify working directory
python scripts/copilot_auto.py "Add tests" --working-dir /path/to/project

# Wait for completion
python scripts/copilot_auto.py "Create a Flask app" --wait
```

### Model Management

```bash
# List available models
python scripts/copilot_auto.py --models

# Validate a model name
python scripts/copilot_auto.py --validate-model claude-sonnet-4.6
```

### Job Management

```bash
# Check status
python scripts/copilot_auto.py --status <job_id>

# Get incremental logs
python scripts/copilot_auto.py --logs <job_id> --checkpoint 0 --json

# Get results (when completed)
python scripts/copilot_auto.py --results <job_id>

# List all jobs
python scripts/copilot_auto.py --list

# Cleanup old jobs (default: 7 days)
python scripts/copilot_auto.py --cleanup --days 30

# Validate token only
python scripts/copilot_auto.py --validate-token
```

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `COPILOT_GITHUB_TOKEN` | GitHub token for sandbox/container environments |
| `COPILOT_MODEL` | Default model name (fallback when CLI unavailable) |
| `COPILOT_MODELS` | Comma-separated list of available models (fallback) |

## Model Configuration

### Model Selection Order

1. `--model` flag passed to the script (validated against available models)
2. `COPILOT_MODEL` environment variable (default model)
3. Copilot CLI default

### Model Listing Fallback

When listing available models, the skill uses the following fallback order:

1. **Copilot CLI error output** - Runs CLI with invalid model to extract available models from error message
2. **`COPILOT_MODELS` env var** - Comma-separated list (e.g., `claude-sonnet-4-6,claude-opus-4-6`)
3. **`COPILOT_MODEL` env var** - Single default model

### Model Validation

When a model is specified:
- The skill runs the CLI with an invalid model to get the list of available models
- Falls back to `COPILOT_MODELS` env var if CLI doesn't provide model list
- Falls back to `COPILOT_MODEL` env var if no other source available
- Invalid models are rejected with an error message
- Available models are displayed for reference

## Job Storage

Jobs are stored in `~/.copilot-jobs/`:
- `<job_id>.json` - Job metadata
- `<job_id>.log` - Output log
- `<job_id>.pid` - Process ID

## Examples

```bash
# Simple code generation
python scripts/copilot_auto.py "Create a Python function to sort a list of dictionaries by key"

# Refactoring with specific model
python scripts/copilot_auto.py "Refactor to use async/await" --model claude-sonnet-4.6

# Long-running task in background
python scripts/copilot_auto.py "Add error handling to all API endpoints"
# Check status later
python scripts/copilot_auto.py --status copilot_20260308_120000_123

# List available models
python scripts/copilot_auto.py --models

# Validate a model before using
python scripts/copilot_auto.py --validate-model gpt-4
```

## Safety

The `--yolo` flag auto-approves all Copilot suggestions. Always:
1. Review changes before committing
2. Test generated code thoroughly
3. Use in development environments first

## See Also

- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Complete command reference and troubleshooting
