# Copilot Auto Skill - Quick Reference

## 🚀 Quick Start

```bash
# Set token (required for sandbox/container)
export COPILOT_GITHUB_TOKEN='ghp_your_token_here'

# Run a task (background mode, auto-validates token)
python scripts/copilot_auto.py "Create a Python module"

# Wait for completion
python scripts/copilot_auto.py "Create a Flask app" --wait
```

## 🔐 Token Validation

```bash
# Validate token before running tasks
python scripts/copilot_token.py

# Token only (skip CLI check)
python scripts/copilot_token.py --token-only

# Check token expiry details
python scripts/copilot_token.py --check-expiry

# Quiet mode (exit code only: 0=valid, 1=invalid)
python scripts/copilot_token.py --quiet
```

## 📋 Main Commands

```bash
# Start task (background mode)
python scripts/copilot_auto.py "task description"

# With model
python scripts/copilot_auto.py "task" --model claude-sonnet-4.6

# With working directory
python scripts/copilot_auto.py "task" --working-dir /path/to/project

# Check status
python scripts/copilot_auto.py --status copilot_20260304_112509_74252

# Get results
python scripts/copilot_auto.py --results copilot_20260304_112509_74252

# List all jobs
python scripts/copilot_auto.py --list

# Cleanup old jobs
python scripts/copilot_auto.py --cleanup --days 7

# Validate token only
python scripts/copilot_auto.py --validate-token

# Skip validation (not recommended)
python scripts/copilot_auto.py "task" --skip-validation
```

## 🐳 Docker/Container Usage

```bash
# Run in Docker
docker run -e COPILOT_GITHUB_TOKEN='ghp_your_token' your-image \
  python scripts/copilot_auto.py "task"

# Kubernetes env var
env:
  - name: COPILOT_GITHUB_TOKEN
    value: "ghp_your_token"

# Validate on container startup
python scripts/copilot_token.py || exit 1
```

## 📊 Job Management

```bash
# List all jobs
python scripts/copilot_auto.py --list

# Check specific job
python scripts/copilot_auto.py --status <job_id>

# Get results (when completed)
python scripts/copilot_auto.py --results <job_id>

# Cleanup jobs older than 3 days
python scripts/copilot_auto.py --cleanup --days 3
```

## 🛠️ Shell Aliases (Optional)

Add to `~/.bashrc` or `~/.zshrc`:

```bash
source /path/to/copilot-auto/scripts/copilot-auto.sh
```

Then use:
```bash
copilot-auto "task"
copilot-status <job_id>
copilot-results <job_id>
copilot-list
copilot-cleanup
```

## ⚠️ Error Handling

### Token Not Set
```
❌ COPILOT_GITHUB_TOKEN environment variable is not set.
   Please set it before running Copilot tasks:
   export COPILOT_GITHUB_TOKEN='your_token_here'
```

### Token Expired
```
❌ Token validation failed: Token expired at 2022-01-01T00:00:00+00:00
```

### Invalid Token Format
```
❌ Invalid token format: Token too short (minimum 10 characters)
```

## 📁 File Locations

- **Jobs directory:** `~/.copilot-jobs/`
  - `<job_id>.json` - Job metadata
  - `<job_id>.log` - Output log
  - `<job_id>.pid` - Process ID

- **Scripts:** `/path/to/copilot-auto/scripts/`
  - `copilot_auto.py` - Main entry point
  - `copilot_token.py` - Token validation
  - `copilot_background.py` - Background execution
  - `copilot_run.py` - Direct execution (legacy)
  - `copilot-auto.sh` - Shell helpers

## 🎯 Common Workflows

### 1. Container Startup
```bash
#!/bin/bash
set -e

# Validate token
python scripts/copilot_token.py

# Run tasks
python scripts/copilot_auto.py "Setup project structure" --wait
python scripts/copilot_auto.py "Add unit tests" --wait
```

### 2. CI/CD Pipeline
```yaml
# GitHub Actions example
- name: Run Copilot tasks
  env:
    COPILOT_GITHUB_TOKEN: ${{ secrets.COPILOT_TOKEN }}
  run: |
    python scripts/copilot_auto.py "Generate documentation" --wait
```

### 3. Interactive Development
```bash
# Start task in background
python scripts/copilot_auto.py "Refactor authentication module"

# Check status later
python scripts/copilot_auto.py --list

# Get results when done
python scripts/copilot_auto.py --results copilot_20260304_112509_74252
```

## 🔧 Troubleshooting

```bash
# Check if token is set
echo $COPILOT_GITHUB_TOKEN

# Validate token format
python scripts/copilot_token.py --token-only

# Check CLI installation
python scripts/copilot_token.py --cli-only

# View job logs directly
tail -f ~/.copilot-jobs/<job_id>.log

# Kill stuck job
kill $(cat ~/.copilot-jobs/<job_id>.pid)
```
