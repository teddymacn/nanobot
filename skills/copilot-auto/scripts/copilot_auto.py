#!/usr/bin/env python3
"""
GitHub Copilot Auto Executor - Always runs in background mode.

This is the main entry point for the copilot-auto skill.
All tasks are executed in background mode with full auto-approval (--yolo flag).

Usage:
    python copilot_auto.py "your task description" [--model MODEL] [--working-dir PATH]
    python copilot_auto.py --models
    python copilot_auto.py --validate-model MODEL
    python copilot_auto.py --status <job_id>
    python copilot_auto.py --results <job_id>
    python copilot_auto.py --list
    python copilot_auto.py --cleanup --days 7

Examples:
    python copilot_auto.py "Create a Python Flask app"
    python copilot_auto.py "Refactor this code" --model claude-sonnet-4.6
    python copilot_auto.py "Add tests" --working-dir /path/to/project
    python copilot_auto.py --models
    python copilot_auto.py --validate-model claude-sonnet-4.6
"""

import argparse
import base64
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Tuple


# =============================================================================
# Token Validation Functions
# =============================================================================

def decode_jwt(token: str) -> dict | None:
    """Decode a JWT token and return its payload (without verification)."""
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        payload = parts[1]
        padding = 4 - len(payload) % 4
        if padding != 4:
            payload += '=' * padding
        decoded = base64.urlsafe_b64decode(payload)
        return json.loads(decoded)
    except Exception:
        return None


def check_token_expiry(token: str) -> Tuple[bool, str]:
    """Check if a JWT token has expired."""
    payload = decode_jwt(token)
    if not payload:
        return True, "Token format valid (non-JWT)"

    if 'exp' in payload:
        exp_timestamp = payload['exp']
        exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
        now = datetime.now(timezone.utc)

        if now >= exp_datetime:
            return False, f"Token expired at {exp_datetime.isoformat()}"

        time_remaining = exp_datetime - now
        if time_remaining.total_seconds() < 3600:
            return True, f"Token valid but expires soon ({int(time_remaining.total_seconds() / 60)} minutes)"

        return True, f"Token valid (expires {exp_datetime.isoformat()})"

    return True, "Token valid (no expiration claim)"


def validate_token_format(token: str) -> Tuple[bool, str]:
    """Validate the token format."""
    if not token:
        return False, "Token is empty"

    if len(token) < 10:
        return False, "Token too short (minimum 10 characters)"

    if token.startswith('ghp_') or token.startswith('gho_') or token.startswith('ghu_'):
        return True, "Valid GitHub token format"

    if token.count('.') == 2:
        payload = decode_jwt(token)
        if payload:
            return True, "Valid JWT token format"
        return False, "Invalid JWT token format"

    if len(token) >= 20 and re.match(r'^[A-Za-z0-9_-]+$', token):
        return True, "Valid token format (generic)"

    return False, "Token format unrecognized"


def validate_copilot_token() -> Tuple[bool, str]:
    """Validate the COPILOT_GITHUB_TOKEN environment variable."""
    token = os.environ.get('COPILOT_GITHUB_TOKEN')

    if not token:
        return False, (
            "COPILOT_GITHUB_TOKEN environment variable is not set.\n"
            "Please set it: export COPILOT_GITHUB_TOKEN='your_token_here'\n"
            "Or in Docker: docker run -e COPILOT_GITHUB_TOKEN='your_token' ..."
        )

    is_valid_format, format_msg = validate_token_format(token)
    if not is_valid_format:
        return False, f"Invalid token format: {format_msg}"

    is_valid_expiry, expiry_msg = check_token_expiry(token)
    if not is_valid_expiry:
        return False, f"Token validation failed: {expiry_msg}"

    return True, f"Token validated: {expiry_msg}"


def validate_copilot_cli() -> Tuple[bool, str]:
    """Check if GitHub Copilot CLI is installed and accessible."""
    try:
        result = subprocess.run(
            ['copilot', '--version'],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            version = result.stdout.strip()
            return True, f"Copilot CLI installed: {version}"
        else:
            return False, f"Copilot CLI error: {result.stderr.strip()}"

    except FileNotFoundError:
        return False, "Copilot CLI not found. Please install it first."
    except subprocess.TimeoutExpired:
        return False, "Copilot CLI check timed out."
    except Exception as e:
        return False, f"Copilot CLI check failed: {str(e)}"


# =============================================================================
# Model Listing and Validation Functions
# =============================================================================

def get_copilot_models() -> dict:
    """
    Get available Copilot models by running copilot with an invalid model.
    
    The CLI will return an error listing available models.
    
    Returns:
        dict: Contains 'models' list, 'default_model', and status info
    """
    # Try to get models from environment variable first
    models_env = os.environ.get("COPILOT_MODELS")
    if models_env:
        model_ids = [m.strip() for m in models_env.split(",") if m.strip()]
        if model_ids:
            default_model = os.environ.get("COPILOT_MODEL") or model_ids[0]
            return {
                "models": model_ids,
                "default_model": default_model,
                "source": "COPILOT_MODELS env var",
                "message": None
            }
    
    # Try to get models by running copilot with invalid model
    try:
        result = subprocess.run(
            ['copilot', '-p', 'test', '--model', '__INVALID_MODEL__', '--autopilot', '--yolo'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Parse error output to extract available models
        error_output = result.stderr + result.stdout
        
        # Look for patterns like "Available models:" or "valid models are:"
        models_list = []
        
        # Pattern 1: "Allowed choices are model1, model2, model3" (Copilot CLI format)
        match = re.search(r'[Aa]llowed\s+choices\s+[Aa]re?:?\s*([^\n]+)', error_output)
        if match:
            models_str = match.group(1)
            models_list = [m.strip() for m in re.split(r'[,\n]', models_str) if m.strip()]
        
        # Pattern 2: "Available models: model1, model2, model3"
        if not models_list:
            match = re.search(r'[Aa]vailable\s+models?:?\s*([^\n]+)', error_output)
            if match:
                models_str = match.group(1)
                models_list = [m.strip() for m in re.split(r'[,\n]', models_str) if m.strip()]
        
        # Pattern 3: "valid models are: model1, model2"
        if not models_list:
            match = re.search(r'[Vv]alid\s+models?\s+[Aa]re?:?\s*([^\n]+)', error_output)
            if match:
                models_str = match.group(1)
                models_list = [m.strip() for m in re.split(r'[,\n]', models_str) if m.strip()]
        
        # Pattern 4: Look for model names in quotes or backticks
        if not models_list:
            # Common Copilot model patterns
            model_patterns = [
                r'["\']([a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+)["\']',  # "org/model" format
                r'["\']([a-zA-Z0-9._-]+)["\']',  # Simple model names
                r'`([a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+)`',  # `org/model` format
            ]
            
            for pattern in model_patterns:
                matches = re.findall(pattern, error_output)
                if matches:
                    # Filter to likely model names
                    for m in matches:
                        if any(kw in m.lower() for kw in ['claude', 'gpt', 'sonnet', 'opus', 'mistral', 'llama', 'gemini', 'codex']):
                            models_list.append(m)
        
        # Clean up model list - remove duplicates and invalid entries
        models_list = list(dict.fromkeys(models_list))  # Remove duplicates
        models_list = [m for m in models_list if m and m != '__INVALID_MODEL__']
        
        # If we found models, return them
        if models_list:
            default_model = os.environ.get("COPILOT_MODEL") or models_list[0]
            return {
                "models": models_list,
                "default_model": default_model,
                "source": "copilot CLI error output",
                "message": None
            }
        
        # If no models found in error output, return empty with info
        return {
            "models": [],
            "default_model": os.environ.get("COPILOT_MODEL"),
            "source": "copilot CLI",
            "message": "No models found in CLI error output. Set COPILOT_MODELS env var.",
            "raw_error": error_output[:500] if error_output else None
        }
        
    except subprocess.TimeoutExpired:
        return {
            "models": [],
            "default_model": os.environ.get("COPILOT_MODEL"),
            "source": "copilot CLI",
            "error": "CLI command timed out",
            "message": "Failed to get models - CLI command timed out"
        }
    except FileNotFoundError:
        return {
            "models": [],
            "default_model": os.environ.get("COPILOT_MODEL"),
            "source": "copilot CLI",
            "error": "Copilot CLI not found",
            "message": "Copilot CLI not installed"
        }
    except Exception as e:
        return {
            "models": [],
            "default_model": os.environ.get("COPILOT_MODEL"),
            "source": "copilot CLI",
            "error": str(e),
            "message": f"Failed to get models: {e}"
        }


def list_models() -> dict:
    """
    List available Copilot models.
    
    Returns:
        dict: Contains 'models' list and metadata
    """
    return get_copilot_models()


def validate_model(model_name: str) -> dict:
    """
    Validate if a model is available.
    
    Args:
        model_name: The model name to validate
        
    Returns:
        dict: Contains 'valid' boolean, 'message', and 'available_models' if invalid
    """
    if not model_name:
        return {
            "valid": False,
            "message": "No model name provided"
        }
    
    result = list_models()
    
    available_models = result.get("models", [])
    default_model = result.get("default_model")
    
    # If no models from CLI, check against default model from env var
    if not available_models:
        if default_model and model_name == default_model:
            return {
                "valid": True,
                "message": f"Model '{model_name}' matches default model from COPILOT_MODEL env var",
                "warning": result.get("message")
            }
        elif default_model:
            return {
                "valid": False,
                "message": f"Model '{model_name}' does not match default model '{default_model}'",
                "default_model": default_model,
                "warning": result.get("message")
            }
        else:
            return {
                "valid": False,
                "message": "No models available and no COPILOT_MODEL env var set",
                "error": result.get("error") or result.get("message")
            }
    
    # Check if model is in available list
    if model_name in available_models:
        return {
            "valid": True,
            "message": f"Model '{model_name}' is available"
        }
    
    return {
        "valid": False,
        "message": f"Model '{model_name}' is not available",
        "available_models": available_models,
        "default_model": default_model
    }


# =============================================================================
# Job Management Functions
# =============================================================================

JOBS_DIR = Path.home() / ".copilot-jobs"


def is_process_running(pid: int) -> bool:
    """
    Check if a process is actually running (not a zombie).
    
    Args:
        pid: Process ID to check
        
    Returns:
        True if process is running, False if dead or zombie
    """
    try:
        # First check if process exists
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except OSError:
        return False
    
    # Process exists, but check if it's a zombie
    # Zombie processes still pass kill(pid, 0) but are not actually running
    try:
        status_file = Path(f"/proc/{pid}/status")
        if status_file.exists():
            with open(status_file, "r") as f:
                for line in f:
                    if line.startswith("State:"):
                        # State: Z means zombie
                        return "Z" not in line
    except (IOError, PermissionError):
        # If we can't read status, assume running if kill succeeded
        pass
    
    return True


def ensure_jobs_dir():
    """Ensure the jobs directory exists."""
    JOBS_DIR.mkdir(parents=True, exist_ok=True)


def generate_job_id():
    """Generate a unique job ID."""
    return f"copilot_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.getpid()}"


def start_background_task(task: str, model: str = None, working_dir: str = None) -> Tuple[str, int]:
    """Start a Copilot task in the background."""
    ensure_jobs_dir()

    job_id = generate_job_id()
    job_file = JOBS_DIR / f"{job_id}.json"
    output_file = JOBS_DIR / f"{job_id}.log"
    pid_file = JOBS_DIR / f"{job_id}.pid"

    # Build the command: copilot -p "prompt" --autopilot --yolo
    cmd = ["copilot", "-p", task, "--autopilot", "--yolo"]

    if model and model.lower() != "default":
        cmd.extend(["--model", model])

    cwd = Path(working_dir).resolve() if working_dir else Path.cwd()

    # Create job metadata
    job_info = {
        "job_id": job_id,
        "task": task,
        "model": model or "default",
        "working_dir": str(cwd),
        "start_time": datetime.now().isoformat(),
        "status": "running",
        "output_file": str(output_file),
    }

    # Save job metadata
    with open(job_file, 'w') as f:
        json.dump(job_info, f, indent=2)

    # Start the process in background
    with open(output_file, 'w') as log_file:
        process = subprocess.Popen(
            cmd,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=cwd,
            start_new_session=True
        )

    # Save PID
    with open(pid_file, 'w') as f:
        f.write(str(process.pid))

    # Update job info with PID
    job_info["pid"] = process.pid
    with open(job_file, 'w') as f:
        json.dump(job_info, f, indent=2)

    return job_id, process.pid


def check_job_status(job_id: str) -> dict | None:
    """Check the status of a background job."""
    ensure_jobs_dir()

    job_file = JOBS_DIR / f"{job_id}.json"
    pid_file = JOBS_DIR / f"{job_id}.pid"
    output_file = JOBS_DIR / f"{job_id}.log"

    if not job_file.exists():
        print(f"Job not found: {job_id}")
        return None

    with open(job_file, 'r') as f:
        job_info = json.load(f)

    # Check if process is still running (not zombie)
    pid = job_info.get("pid")
    if pid:
        if is_process_running(pid):
            job_info["status"] = "running"
        else:
            job_info["status"] = "completed"
            job_info["end_time"] = datetime.now().isoformat()
            with open(job_file, 'w') as f:
                json.dump(job_info, f, indent=2)

    print(f"Job ID: {job_info['job_id']}")
    print(f"Task: {job_info['task']}")
    print(f"Model: {job_info['model']}")
    print(f"Status: {job_info['status']}")
    print(f"Start time: {job_info['start_time']}")
    if "end_time" in job_info:
        print(f"End time: {job_info['end_time']}")
    print(f"Output log: {job_info['output_file']}")

    # Show last few lines of output
    if output_file.exists():
        print("\n--- Last 20 lines of output ---")
        try:
            with open(output_file, 'r') as f:
                lines = f.readlines()
                for line in lines[-20:]:
                    print(line, end='')
        except Exception as e:
            print(f"Could not read output: {e}")

    return job_info


def get_job_results(job_id: str) -> dict | None:
    """Get the complete results of a completed job."""
    ensure_jobs_dir()

    job_file = JOBS_DIR / f"{job_id}.json"
    output_file = JOBS_DIR / f"{job_id}.log"

    if not job_file.exists():
        print(f"Job not found: {job_id}")
        return None

    with open(job_file, 'r') as f:
        job_info = json.load(f)

    # Check status
    pid = job_info.get("pid")
    if pid:
        if is_process_running(pid):
            print("Warning: Job is still running!")
            print("Use --status to check progress.")
            return None
        else:
            job_info["status"] = "completed"

    print(f"=== Results for Job: {job_id} ===")
    print(f"Task: {job_info['task']}")
    print(f"Model: {job_info['model']}")
    print(f"Status: {job_info['status']}")
    print(f"Duration: {job_info['start_time']} to {job_info.get('end_time', 'N/A')}")
    print("=" * 60)

    if output_file.exists():
        with open(output_file, 'r') as f:
            print(f.read())
    else:
        print("No output file found")

    return job_info


def list_jobs():
    """List all Copilot jobs."""
    ensure_jobs_dir()

    jobs = list(JOBS_DIR.glob("*.json"))

    if not jobs:
        print("No jobs found")
        return

    print(f"{'Job ID':<40} {'Status':<12} {'Model':<20} {'Start Time'}")
    print("-" * 100)

    for job_file in sorted(jobs, key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            with open(job_file, 'r') as f:
                job_info = json.load(f)

            # Check if running (not zombie)
            pid = job_info.get("pid")
            status = job_info.get("status", "unknown")
            if pid:
                status = "running" if is_process_running(pid) else "completed"

            print(f"{job_info['job_id']:<40} {status:<12} {job_info['model']:<20} {job_info['start_time'][:19]}")
        except Exception as e:
            print(f"{job_file.name}: Error - {e}")


def cleanup_jobs(days: int = 7):
    """Clean up job files older than specified days."""
    ensure_jobs_dir()

    cutoff = time.time() - (days * 24 * 60 * 60)
    cleaned = 0

    for job_file in JOBS_DIR.glob("*.json"):
        if job_file.stat().st_mtime < cutoff:
            job_id = job_file.stem
            for ext in ['.json', '.log', '.pid']:
                file_to_remove = JOBS_DIR / f"{job_id}{ext}"
                if file_to_remove.exists():
                    file_to_remove.unlink()
            cleaned += 1

    print(f"Cleaned up {cleaned} old job(s)")


# =============================================================================
# Main Entry Point
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="GitHub Copilot Auto Executor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python copilot_auto.py "Create a Python module"
    python copilot_auto.py "Refactor this" --model claude-sonnet-4.6
    python copilot_auto.py --models
    python copilot_auto.py --validate-model claude-sonnet-4.6
    python copilot_auto.py --status copilot_20260308_120000_123
    python copilot_auto.py --results copilot_20260308_120000_123
    python copilot_auto.py --list
    python copilot_auto.py --cleanup --days 7
    python copilot_auto.py --validate-token
        """
    )

    parser.add_argument("task", nargs="?", help="Task description to execute")
    parser.add_argument("--model", "-m", help="AI model to use")
    parser.add_argument("--working-dir", "-w", help="Working directory for the task")
    parser.add_argument("--models", action="store_true", help="List available models")
    parser.add_argument("--validate-model", metavar="MODEL", help="Validate if a model is available")
    parser.add_argument("--status", "-s", metavar="JOB_ID", help="Check status of a job")
    parser.add_argument("--results", "-r", metavar="JOB_ID", help="Get results of a job")
    parser.add_argument("--list", "-l", action="store_true", help="List all jobs")
    parser.add_argument("--cleanup", "-c", action="store_true", help="Cleanup old jobs")
    parser.add_argument("--days", "-d", type=int, default=7, help="Days to keep jobs")
    parser.add_argument("--wait", action="store_true", help="Wait for task completion")
    parser.add_argument("--validate-token", "-v", action="store_true", help="Validate token and CLI")
    parser.add_argument("--skip-validation", action="store_true", help="Skip token validation")

    args = parser.parse_args()

    # Handle --models flag
    if args.models:
        result = list_models()
        print("=" * 60)
        print("Available Copilot Models")
        print("=" * 60)
        
        if result.get("message"):
            print(f"Note: {result['message']}")
        
        if result.get("warning"):
            print(f"Warning: {result['warning']}")
        
        if result.get("error"):
            print(f"Error: {result['error']}")
        
        print(f"\nSource: {result.get('source', 'unknown')}")
        print(f"Default Model: {result['default_model'] or 'None'}")
        
        if result["models"]:
            print(f"\nAvailable Models ({len(result['models'])}):")
            for model in result["models"]:
                marker = " (default)" if model == result["default_model"] else ""
                print(f"  - {model}{marker}")
        else:
            print("\nNo models available from CLI")
            if result.get("raw_error"):
                print(f"\nRaw error output:\n{result['raw_error']}")
        
        return

    # Handle --validate-model flag
    if args.validate_model:
        result = validate_model(args.validate_model)
        print("=" * 60)
        print(f"Model Validation: {args.validate_model}")
        print("=" * 60)
        
        if result["valid"]:
            print(f"✅ Valid: {result['message']}")
        else:
            print(f"❌ Invalid: {result['message']}")
            
            if result.get("available_models"):
                print(f"\nAvailable Models ({len(result['available_models'])}):")
                for model in result["available_models"]:
                    marker = " (default)" if model == result.get("default_model") else ""
                    print(f"  - {model}{marker}")
            
            if result.get("default_model"):
                print(f"\nDefault Model: {result['default_model']}")
        
        sys.exit(0 if result["valid"] else 1)

    # Handle validation mode
    if args.validate_token:
        print("=" * 60)
        print("GitHub Copilot Validation")
        print("=" * 60)

        is_valid, message = validate_copilot_token()
        print(f"Token: {message}")

        cli_valid, cli_msg = validate_copilot_cli()
        print(f"CLI: {cli_msg}")

        print("=" * 60)
        sys.exit(0 if (is_valid and cli_valid) else 1)

    # Handle list mode
    if args.list:
        list_jobs()
        return

    # Handle status mode
    if args.status:
        check_job_status(args.status)
        return

    # Handle results mode
    if args.results:
        get_job_results(args.results)
        return

    # Handle cleanup mode
    if args.cleanup:
        cleanup_jobs(args.days)
        return

    # Require task for execution
    if not args.task:
        parser.print_help()
        print("\nError: Please provide a task or use --status, --results, --list, --cleanup, --validate-token, or --models")
        sys.exit(1)

    # Validate model if specified
    if args.model:
        validation = validate_model(args.model)
        if not validation["valid"]:
            print(f"❌ Error: {validation['message']}")
            if validation.get("available_models"):
                print(f"\nAvailable models:")
                for m in validation["available_models"][:10]:  # Show first 10
                    print(f"  - {m}")
                if len(validation["available_models"]) > 10:
                    print(f"  ... and {len(validation['available_models']) - 10} more")
            sys.exit(1)
        print(f"✅ Model validation passed: {validation['message']}")

    # Validate token before executing (unless skipped)
    if not args.skip_validation:
        is_valid, message = validate_copilot_token()
        if not is_valid:
            print("=" * 60)
            print("Token Validation Failed")
            print("=" * 60)
            print(message)
            print("=" * 60)
            print("\nTip: Use --skip-validation to bypass (not recommended)")
            sys.exit(1)

    # Start the task
    print("=" * 60)
    print("Starting Copilot Autopilot Task")
    print("=" * 60)
    print(f"Task: {args.task}")
    print(f"Model: {args.model or 'default'}")
    print(f"Working Dir: {args.working_dir or Path.cwd()}")
    print("-" * 60)

    job_id, pid = start_background_task(args.task, args.model, args.working_dir)

    print(f"Job started in background")
    print(f"Job ID: {job_id}")
    print(f"PID: {pid}")
    print(f"Log: {JOBS_DIR / f'{job_id}.log'}")
    print("-" * 60)
    print(f"Check status: python {sys.argv[0]} --status {job_id}")
    print(f"Get results: python {sys.argv[0]} --results {job_id}")

    # Wait mode
    if args.wait:
        print("\nWaiting for task completion...")
        while True:
            time.sleep(5)
            job_file = JOBS_DIR / f"{job_id}.json"
            if not job_file.exists():
                print("Job file not found!")
                break

            with open(job_file, 'r') as f:
                job_info = json.load(f)

            # Check if still running (not zombie)
            pid = job_info.get("pid")
            is_running = is_process_running(pid) if pid else False

            if not is_running:
                print("\nTask completed!")
                get_job_results(job_id)
                break
            else:
                status_line = f"Status: {job_info.get('status', 'running')}..."
                print(status_line)


if __name__ == "__main__":
    main()
