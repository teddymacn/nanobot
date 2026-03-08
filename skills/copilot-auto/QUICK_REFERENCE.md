# Copilot Auto - Quick Reference

## Quick Start

```bash
# Set token (required for sandbox/container)
export COPILOT_GITHUB_TOKEN='ghp_your_token_here'

# Run a task
python scripts/copilot_auto.py "Create a Python module"

# Wait for completion
python scripts/copilot_auto.py "Create a Flask app" --wait
```

## Commands

| Command | Description |
|---------|-------------|
| `python scripts/copilot_auto.py "task"` | Start a background task |
| `python scripts/copilot_auto.py "task" --model MODEL` | Run with specific model |
| `python scripts/copilot_auto.py "task" --wait` | Wait for completion |
| `python scripts/copilot_auto.py --status JOB_ID` | Check job status |
| `python scripts/copilot_auto.py --results JOB_ID` | Get job results |
| `python scripts/copilot_auto.py --list` | List all jobs |
| `python scripts/copilot_auto.py --cleanup --days 7` | Cleanup old jobs |
| `python scripts/copilot_auto.py --validate-token` | Validate token only |

## Common Models

- `claude-sonnet-4.6` / `claude-sonnet-4.5` - Claude Sonnet
- `claude-haiku-3.5` - Claude Haiku
- `gpt-4o` - GPT-4 Optimized

## Troubleshooting

```bash
# Check if token is set
echo $COPILOT_GITHUB_TOKEN

# Validate token
python scripts/copilot_auto.py --validate-token

# View job logs
tail -f ~/.copilot-jobs/<job_id>.log

# Kill stuck job
kill $(cat ~/.copilot-jobs/<job_id>.pid)
```

## Copilot CLI Installation

```bash
# Install via npm
npm install -g @github/copilot

# Verify
copilot --version

# Authenticate
copilot login
```
