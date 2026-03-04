---
name: copilot-auto
description: Execute GitHub Copilot CLI in full autopilot mode for coding tasks. **ALWAYS USES BACKGROUND MODE.** Auto-triggered for any task involving GitHub Copilot CLI. Use for code generation, refactoring, debugging, testing, or any development work. All tasks run with --autopilot --yolo flags (full auto-approval, sandbox-safe).
---

# GitHub Copilot Auto Executor

This skill enables automated execution of GitHub Copilot CLI in full autopilot mode for coding tasks.

**⚡ TRIGGER:** This skill is automatically used for ANY task request involving GitHub Copilot CLI. All tasks execute in background mode with full auto-approval (`--yolo` flag).

**🔒 SANDBOX MODE:** Designed for sandbox/container environments. All tasks run with `--autopilot --yolo` flags for fully automated execution.

**🔐 TOKEN VALIDATION:** Before executing any task, the skill validates the `COPILOT_GITHUB_TOKEN` environment variable:
- Checks if token is set
- Validates token format (GitHub token or JWT)
- Checks token expiration (for JWT tokens)
- Fails fast with clear error message if validation fails

## Installation

### Prerequisites

1. **Node.js** (v18 or later):
   ```bash
   # Check if installed
   node --version
   
   # Install via Homebrew (macOS)
   brew install node
   
   # Install via apt (Linux/Debian/Ubuntu)
   sudo apt update && sudo apt install nodejs npm
   
   # Install via dnf (Linux/Fedora)
   sudo dnf install nodejs npm
   ```

2. **GitHub Account** with Copilot subscription

### Install Copilot CLI

**Method 1: npm (Cross-platform)**
```bash
# Install globally via npm
npm install -g @github/copilot

# Verify installation
copilot --version

# Authenticate with GitHub
copilot login
```

**Method 2: Homebrew (macOS)**
```bash
brew install github/copilot/copilot
copilot login
```

**Method 3: GitHub Releases (Linux/macOS)**
```bash
# Download from https://github.com/github/copilot-cli/releases
# Extract and add to PATH
```

**Method 4: Direct binary (Linux)**
```bash
# Download latest release
curl -L https://github.com/github/copilot-cli/releases/latest/download/copilot-linux-amd64 -o copilot
chmod +x copilot
sudo mv copilot /usr/local/bin/
copilot login
```

## Environment Variables

### COPILOT_GITHUB_TOKEN (Required for Sandbox/Container)

In sandbox or container environments, you must set the `COPILOT_GITHUB_TOKEN` environment variable:

```bash
# Export token in shell
export COPILOT_GITHUB_TOKEN='ghp_your_github_token_here'

# Or in Docker
docker run -e COPILOT_GITHUB_TOKEN='ghp_your_token' your-image

# Or in Kubernetes
env:
  - name: COPILOT_GITHUB_TOKEN
    value: "ghp_your_token"
```

**Token Validation:**
- The skill automatically validates the token before each task
- Checks token format (GitHub token prefix or JWT)
- Checks expiration for JWT tokens
- Fails fast with clear error if validation fails

**To skip validation (not recommended):**
```bash
python scripts/copilot_auto.py "task" --skip-validation
```

### Validate Token Manually

```bash
# Validate token and CLI
python scripts/copilot_token.py

# Token only
python scripts/copilot_token.py --token-only

# CLI only
python scripts/copilot_token.py --cli-only

# Check token expiry details
python scripts/copilot_token.py --check-expiry

# Quiet mode (exit code only)
python scripts/copilot_token.py --quiet
```

## Available Models

To list all available models:
```bash
copilot --model invalid
```

Common models include:
- `claude-sonnet-4` / `claude-sonnet-4.5` - Claude Sonnet models
- `claude-haiku-3.5` - Claude Haiku model
- `gpt-4o` - GPT-4 Optimized
- Default model (no --model flag)

## Usage

### ⚡ Quick Start - Main Entry Point

**All tasks run in background mode by default.** Use the main `copilot_auto.py` script:

```bash
# Start a Copilot task (background mode)
python scripts/copilot_auto.py "your task description"

# With specific model
python scripts/copilot_auto.py "refactor this function" --model claude-sonnet-4.6

# Specify working directory
python scripts/copilot_auto.py "add tests" --working-dir /path/to/project

# Wait for completion and show results
python scripts/copilot_auto.py "create a Flask app" --wait
```

### Monitor and Retrieve Results

```bash
# Check job status
python scripts/copilot_auto.py --status <job_id>

# Get complete results (when completed)
python scripts/copilot_auto.py --results <job_id>

# List all jobs
python scripts/copilot_auto.py --list

# Clean up old jobs (older than 7 days)
python scripts/copilot_auto.py --cleanup

# Clean up jobs older than 30 days
python scripts/copilot_auto.py --cleanup --days 30
```

### Shell Aliases (Optional)

Source the shell helpers for convenient commands:

```bash
# Add to ~/.bashrc or ~/.zshrc
source /path/to/copilot-auto/scripts/copilot-auto.sh

# Then use:
copilot-auto "create a Python module"
copilot-status <job_id>
copilot-results <job_id>
copilot-list
copilot-cleanup
```

### Legacy Scripts (Still Available)

The original scripts are still available for direct use:
- `copilot_run.py` - Direct execution (waits for completion)
- `copilot_background.py` - Background execution with manual monitoring

## Command Line Options

### Main Entry Point (copilot_auto.py)

| Option | Description |
|--------|-------------|
| `task` | The task description to execute (required) |
| `--model MODEL`, `-m` | AI model to use (optional, uses default if not specified) |
| `--working-dir PATH`, `-w` | Working directory for the task |
| `--wait` | Wait for task completion and show results |
| `--validate-token`, `-v` | Validate token and exit (don't run task) |
| `--skip-validation` | Skip token validation (not recommended) |
| `--status`, `-s` | Check status of a job by ID |
| `--results`, `-r` | Get results of a completed job |
| `--list`, `-l` | List all jobs |
| `--cleanup`, `-c` | Cleanup old jobs |
| `--days`, `-d` | Days to keep jobs for cleanup (default: 7) |

### Token Validation (copilot_token.py)

| Option | Description |
|--------|-------------|
| `--cli-only` | Only check CLI installation, skip token validation |
| `--token-only` | Only validate token, skip CLI check |
| `--quiet`, `-q` | Only output result (valid/invalid), no details |
| `--check-expiry` | Check token expiry and print expiration time |

### Direct Execution (copilot_run.py)

| Option | Description |
|--------|-------------|
| `task` | The task description to execute (required) |
| `--model MODEL` | AI model to use (optional, uses default if not specified) |
| `--working-dir PATH` | Working directory for the task |
| `--list-models` | List available models |

### Background Execution (copilot_background.py)

**Start:**
| Option | Description |
|--------|-------------|
| `task` | The task description to execute (required) |
| `--model MODEL` | AI model to use |
| `--working-dir PATH` | Working directory for the task |

**Status/Results:**
| Option | Description |
|--------|-------------|
| `job_id` | The job ID returned when starting the task |

**List:** No options required

**Cleanup:**
| Option | Description |
|--------|-------------|
| `--days N` | Keep jobs from the last N days (default: 7) |

## Copilot CLI Flags

The skill uses these flags by default:

| Flag | Description |
|------|-------------|
| `-p` | Execute prompt in non-interactive mode (exits after completion) |
| `--autopilot` | Enable autopilot continuation mode |
| `--yolo` | Auto-approve all suggestions (use with caution) |
| `--model MODEL` | Specify AI model (optional) |

**Note:** The correct command syntax is:
```bash
copilot -p "your task" --autopilot --yolo [--model MODEL]
```

## Examples

### Example 0: Validate Token First (Recommended for Containers)
```bash
# Check if token is set and valid
python scripts/copilot_token.py

# Or validate before running a task
python scripts/copilot_auto.py --validate-token

# Run task with token validation (automatic)
export COPILOT_GITHUB_TOKEN='ghp_your_token'
python scripts/copilot_auto.py "Create a module"
```

### Example 1: Simple Code Generation
```bash
python scripts/copilot_run.py "Create a Python function to sort a list of dictionaries by a key"
```

### Example 2: Refactoring with Specific Model
```bash
python scripts/copilot_run.py "Refactor this code to use async/await" --model claude-sonnet-4.5
```

### Example 3: Long-Running Background Task
```bash
# Start the task
JOB_ID=$(python scripts/copilot_background.py start "Add comprehensive error handling to all API endpoints" --model claude-sonnet-4.5)

# Check status periodically
python scripts/copilot_background.py status $JOB_ID

# Get results when done
python scripts/copilot_background.py results $JOB_ID
```

### Example 4: Working in Specific Directory
```bash
python scripts/copilot_background.py start "Write unit tests for all modules" --working-dir /Users/teddyma/projects/myapp
```

## Job Files Location

Background jobs are stored in `~/.copilot-jobs/`:
- `<job_id>.json` - Job metadata and status
- `<job_id>.log` - Complete output log
- `<job_id>.pid` - Process ID file

## Safety Considerations

⚠️ **The `--yolo` flag auto-approves all Copilot suggestions.** Use with caution:

1. Review changes before committing to version control
2. Test generated code thoroughly
3. Use in development environments first
4. Consider removing `--yolo` for critical code changes

## Troubleshooting

### Copilot Command Not Found
```bash
# Verify installation
which copilot

# Reinstall if needed
npm install -g @github/copilot
```

### Authentication Issues
```bash
# Re-authenticate
copilot auth login

# Check auth status
copilot auth status
```

### Job Stuck or Not Completing
```bash
# Check job status
python scripts/copilot_background.py status <job_id>

# View live logs
tail -f ~/.copilot-jobs/<job_id>.log

# Kill the process if needed
kill <pid>  # PID found in <job_id>.pid file
```

### Model Not Available
```bash
# List available models
copilot --model invalid

# Or use the script
python scripts/copilot_run.py "test" --list-models
```

## Workflow Integration

### For nanobot Agent

When a user requests Copilot automation:

1. **Determine task complexity:**
   - Simple/quick tasks → Use `copilot_run.py` for direct execution
   - Complex/long tasks → Use `copilot_background.py start` for background execution

2. **Check model requirements:**
   - If user specifies a model → Use `--model` flag
   - If no model specified → Use default (omit `--model` flag)

3. **Monitor background jobs:**
   - Periodically check status using `copilot_background.py status`
   - Report results when job completes

4. **Clean up:**
   - Run cleanup periodically to remove old job files

## Related Commands

```bash
# Native Copilot CLI commands
copilot --help           # Show help
copilot auth login       # Authenticate
copilot auth status      # Check auth status
copilot --model invalid  # List models
copilot autopilot --help # Autopilot help
```
