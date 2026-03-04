#!/usr/bin/env python3
"""
Claude Code Auto Executor - Always runs in background mode.

This is the main entry point for the claude-auto skill.
All tasks are executed in background mode with full auto-approval.

Usage:
    python claude_auto.py "your task description" [--model MODEL] [--working-dir PATH]
    python claude_auto.py --models
    python claude_auto.py --validate-model MODEL

Examples:
    python claude_auto.py "Create a Python Flask app"
    python claude_auto.py "Refactor this code" --model claude-sonnet-4-6
    python claude_auto.py --models
    python claude_auto.py --validate-model claude-opus-4-6
"""

import argparse
import json
import os
import subprocess
import sys
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path


def get_base_url():
    """Get the API base URL from environment or default."""
    return os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com/v1")


def get_auth_headers():
    """Get authentication headers based on environment variables."""
    auth_token = os.environ.get("ANTHROPIC_AUTH_TOKEN")
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    
    headers = {"Content-Type": "application/json"}
    
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    elif api_key:
        headers["X-API-Key"] = api_key
    
    return headers, bool(auth_token or api_key)


def get_default_model():
    """Get the default model from environment variable."""
    return os.environ.get("ANTHROPIC_MODEL")


def list_models():
    """
    Fetch available models from the API with fallback to environment variables.
    
    Fallback order:
    1. API endpoint (/models)
    2. ANTHROPIC_MODELS env var (comma-separated list)
    3. ANTHROPIC_MODEL env var (single default model)
    
    Returns:
        dict: Contains 'models' list, 'default_model', and status info
    """
    base_url = get_base_url()
    headers, has_auth = get_auth_headers()
    
    # If no authentication, return default model from env var
    if not has_auth:
        default_model = get_default_model()
        return {
            "models": [],
            "default_model": default_model,
            "authenticated": False,
            "message": "No authentication provided. Using default model from ANTHROPIC_MODEL env var."
        }
    
    # Try 1: Fetch models from API - try /v1/models endpoint
    # Ensure base_url doesn't already end with /v1
    if base_url.rstrip('/').endswith('/v1'):
        models_url = f"{base_url}/models"
    else:
        models_url = f"{base_url}/v1/models"
    
    try:
        req = urllib.request.Request(models_url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode())
            
            # Handle different API response formats
            if isinstance(data, dict):
                if "data" in data:
                    models_list = data["data"]
                elif "models" in data:
                    models_list = data["models"]
                else:
                    models_list = [data] if "id" in data else []
            elif isinstance(data, list):
                models_list = data
            else:
                models_list = []
            
            # Extract model IDs
            model_ids = []
            for model in models_list:
                if isinstance(model, dict):
                    model_id = model.get("id") or model.get("model_id") or model.get("name")
                    if model_id:
                        model_ids.append(model_id)
                elif isinstance(model, str):
                    model_ids.append(model)
            
            return {
                "models": model_ids,
                "default_model": get_default_model(),
                "authenticated": True,
                "message": None
            }
    
    except urllib.error.HTTPError as e:
        # Try 2: Fallback to ANTHROPIC_MODELS env var (comma-separated list)
        models_env = os.environ.get("ANTHROPIC_MODELS")
        if models_env:
            model_ids = [m.strip() for m in models_env.split(",") if m.strip()]
            if model_ids:
                return {
                    "models": model_ids,
                    "default_model": get_default_model() or (model_ids[0] if model_ids else None),
                    "authenticated": True,
                    "message": f"API returned HTTP {e.code}, using ANTHROPIC_MODELS env var",
                    "warning": f"HTTP {e.code}: {e.reason}"
                }
        
        # Try 3: Fallback to ANTHROPIC_MODEL env var (single default model)
        default_model = get_default_model()
        if default_model:
            return {
                "models": [default_model],
                "default_model": default_model,
                "authenticated": True,
                "message": f"API returned HTTP {e.code}, using ANTHROPIC_MODEL env var",
                "warning": f"HTTP {e.code}: {e.reason}"
            }
        
        return {
            "models": [],
            "default_model": None,
            "authenticated": True,
            "error": f"HTTP {e.code}: {e.reason}",
            "message": f"Failed to fetch models: HTTP {e.code}"
        }
    except urllib.error.URLError as e:
        # Try 2: Fallback to ANTHROPIC_MODELS env var (comma-separated list)
        models_env = os.environ.get("ANTHROPIC_MODELS")
        if models_env:
            model_ids = [m.strip() for m in models_env.split(",") if m.strip()]
            if model_ids:
                return {
                    "models": model_ids,
                    "default_model": get_default_model() or (model_ids[0] if model_ids else None),
                    "authenticated": True,
                    "message": f"API unreachable, using ANTHROPIC_MODELS env var",
                    "warning": str(e.reason)
                }
        
        # Try 3: Fallback to ANTHROPIC_MODEL env var (single default model)
        default_model = get_default_model()
        if default_model:
            return {
                "models": [default_model],
                "default_model": default_model,
                "authenticated": True,
                "message": f"API unreachable, using ANTHROPIC_MODEL env var",
                "warning": str(e.reason)
            }
        
        return {
            "models": [],
            "default_model": None,
            "authenticated": True,
            "error": str(e.reason),
            "message": f"Failed to fetch models: {e.reason}"
        }
    except Exception as e:
        # Try 2: Fallback to ANTHROPIC_MODELS env var (comma-separated list)
        models_env = os.environ.get("ANTHROPIC_MODELS")
        if models_env:
            model_ids = [m.strip() for m in models_env.split(",") if m.strip()]
            if model_ids:
                return {
                    "models": model_ids,
                    "default_model": get_default_model() or (model_ids[0] if model_ids else None),
                    "authenticated": True,
                    "message": f"API error, using ANTHROPIC_MODELS env var",
                    "warning": str(e)
                }
        
        # Try 3: Fallback to ANTHROPIC_MODEL env var (single default model)
        default_model = get_default_model()
        if default_model:
            return {
                "models": [default_model],
                "default_model": default_model,
                "authenticated": True,
                "message": f"API error, using ANTHROPIC_MODEL env var",
                "warning": str(e)
            }
        
        return {
            "models": [],
            "default_model": None,
            "authenticated": True,
            "error": str(e),
            "message": f"Failed to fetch models: {e}"
        }


def validate_model(model_name):
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
    
    # If not authenticated, check against default model
    if not result["authenticated"]:
        default_model = result["default_model"]
        if default_model and model_name == default_model:
            return {
                "valid": True,
                "message": f"Model '{model_name}' matches default model from ANTHROPIC_MODEL env var"
            }
        elif default_model:
            return {
                "valid": False,
                "message": f"Model '{model_name}' does not match default model '{default_model}'",
                "default_model": default_model
            }
        else:
            return {
                "valid": False,
                "message": "No authentication and no ANTHROPIC_MODEL env var set"
            }
    
    # If authenticated but API error (and no fallback), fall back to default model validation
    if result.get("error") and not result.get("models"):
        default_model = result["default_model"]
        if default_model and model_name == default_model:
            return {
                "valid": True,
                "message": f"Model '{model_name}' matches default model from ANTHROPIC_MODEL env var (API unavailable)",
                "warning": result["message"]
            }
        elif default_model:
            return {
                "valid": False,
                "message": f"Model '{model_name}' does not match default model '{default_model}'",
                "default_model": default_model,
                "warning": result["message"]
            }
        else:
            return {
                "valid": False,
                "message": "API unavailable and no ANTHROPIC_MODEL env var set",
                "error": result["error"]
            }
    
    available_models = result["models"]
    
    if not available_models:
        # No models from API, use default model
        default_model = result["default_model"]
        if default_model and model_name == default_model:
            return {
                "valid": True,
                "message": f"Model '{model_name}' matches default model from ANTHROPIC_MODEL env var"
            }
        elif default_model:
            return {
                "valid": False,
                "message": f"Model '{model_name}' does not match default model '{default_model}'",
                "default_model": default_model
            }
        else:
            return {
                "valid": False,
                "message": "No models available from API and no ANTHROPIC_MODEL env var set"
            }
    
    if model_name in available_models:
        return {
            "valid": True,
            "message": f"Model '{model_name}' is available"
        }
    
    return {
        "valid": False,
        "message": f"Model '{model_name}' is not available",
        "available_models": available_models,
        "default_model": result["default_model"]
    }


def get_job_dir():
    """Get the directory for storing job files."""
    return Path.home() / ".claude-jobs"


def generate_job_id():
    """Generate a unique job ID based on timestamp and PID."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pid = os.getpid()
    return f"claude_{timestamp}_{pid}"


def save_job_metadata(job_id, task, model, working_dir):
    """Save job metadata to a JSON file."""
    job_dir = get_job_dir()
    job_dir.mkdir(parents=True, exist_ok=True)
    
    meta = {
        "job_id": job_id,
        "task": task,
        "model": model,
        "working_dir": str(working_dir),
        "start_time": datetime.now().isoformat(),
        "status": "running"
    }
    
    meta_file = job_dir / f"{job_id}.meta.json"
    with open(meta_file, "w") as f:
        json.dump(meta, f, indent=2)


def update_job_status(job_id, status):
    """Update job status in metadata file."""
    job_dir = get_job_dir()
    meta_file = job_dir / f"{job_id}.meta.json"
    
    if meta_file.exists():
        with open(meta_file, "r") as f:
            meta = json.load(f)
        meta["status"] = status
        with open(meta_file, "w") as f:
            json.dump(meta, f, indent=2)


def start_claude_task(task, model, working_dir):
    """Start a Claude Code task in the background."""
    job_id = generate_job_id()
    job_dir = get_job_dir()
    job_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = job_dir / f"{job_id}.log"
    pid_file = job_dir / f"{job_id}.pid"
    
    # Save metadata
    save_job_metadata(job_id, task, model, working_dir)
    
    # Build Claude command
    cmd = ["claude", "-p", task, "--dangerously-skip-permissions"]
    
    if model:
        cmd.extend(["--model", model])
    
    cmd.extend(["--add-dir", str(working_dir)])
    
    # Start process in background
    with open(log_file, "w") as log:
        process = subprocess.Popen(
            cmd,
            stdout=log,
            stderr=subprocess.STDOUT,
            cwd=working_dir,
            start_new_session=True
        )
    
    # Save PID
    with open(pid_file, "w") as f:
        f.write(str(process.pid))
    
    return job_id, process.pid


def check_job_status(job_id):
    """Check the status of a job."""
    job_dir = get_job_dir()
    meta_file = job_dir / f"{job_id}.meta.json"
    pid_file = job_dir / f"{job_id}.pid"
    log_file = job_dir / f"{job_id}.log"
    
    if not meta_file.exists():
        print(f"❌ Job not found: {job_id}")
        return None
    
    with open(meta_file, "r") as f:
        meta = json.load(f)
    
    # Check if process is still running
    is_running = False
    if pid_file.exists():
        with open(pid_file, "r") as f:
            pid = int(f.read().strip())
        try:
            os.kill(pid, 0)
            is_running = True
        except OSError:
            is_running = False
            update_job_status(job_id, "completed")
    
    meta["is_running"] = is_running
    
    print(f"Job ID: {job_id}")
    print(f"Task: {meta.get('task', 'N/A')}")
    print(f"Model: {meta.get('model', 'default')}")
    print(f"Status: {'running' if is_running else 'completed'}")
    print(f"Start time: {meta.get('start_time', 'N/A')}")
    print(f"Output log: {log_file}")
    
    if log_file.exists():
        print("\n--- Last 20 lines of output ---")
        with open(log_file, "r") as f:
            lines = f.readlines()
            for line in lines[-20:]:
                print(line.rstrip())
    
    return meta


def get_job_results(job_id):
    """Get the results of a completed job."""
    job_dir = get_job_dir()
    log_file = job_dir / f"{job_id}.log"
    meta_file = job_dir / f"{job_id}.meta.json"
    
    if not log_file.exists():
        print(f"❌ Log file not found for job: {job_id}")
        return
    
    if not meta_file.exists():
        print(f"❌ Metadata not found for job: {job_id}")
        return
    
    with open(meta_file, "r") as f:
        meta = json.load(f)
    
    # Check if still running
    pid_file = job_dir / f"{job_id}.pid"
    if pid_file.exists():
        with open(pid_file, "r") as f:
            pid = int(f.read().strip())
        try:
            os.kill(pid, 0)
            print("⚠️  Warning: Job is still running!")
            print("Use 'status' command to check progress.")
            return
        except OSError:
            pass
    
    print(f"=== Results for job: {job_id} ===")
    print(f"Task: {meta.get('task', 'N/A')}")
    print(f"Model: {meta.get('model', 'default')}")
    print(f"Start time: {meta.get('start_time', 'N/A')}")
    print("\n" + "=" * 50 + "\n")
    
    with open(log_file, "r") as f:
        print(f.read())


def list_jobs():
    """List all jobs."""
    job_dir = get_job_dir()
    
    if not job_dir.exists():
        print("No jobs found.")
        return
    
    meta_files = list(job_dir.glob("*.meta.json"))
    
    if not meta_files:
        print("No jobs found.")
        return
    
    print(f"{'Job ID':<40} {'Status':<12} {'Model':<20} {'Start Time'}")
    print("-" * 100)
    
    for meta_file in sorted(meta_files, key=lambda x: x.stat().st_mtime, reverse=True):
        with open(meta_file, "r") as f:
            meta = json.load(f)
        
        job_id = meta.get("job_id", "unknown")
        model = meta.get("model") or "default"
        start_time = meta.get("start_time", "unknown")[:19]
        status = meta.get("status", "unknown")
        
        # Check if running
        pid_file = job_dir / f"{job_id}.pid"
        if pid_file.exists():
            try:
                with open(pid_file, "r") as f:
                    pid = int(f.read().strip())
                os.kill(pid, 0)
                status = "running"
            except OSError:
                status = "completed"
        
        print(f"{job_id:<40} {status:<12} {model:<20} {start_time}")


def cleanup_jobs(days=7):
    """Clean up old job files."""
    job_dir = get_job_dir()
    
    if not job_dir.exists():
        print("No jobs to clean up.")
        return
    
    from datetime import timedelta
    
    cutoff = datetime.now() - timedelta(days=days)
    cleaned = 0
    
    for meta_file in job_dir.glob("*.meta.json"):
        try:
            with open(meta_file, "r") as f:
                meta = json.load(f)
            
            start_time = datetime.fromisoformat(meta.get("start_time", ""))
            
            if start_time < cutoff:
                job_id = meta.get("job_id", "")
                # Remove all related files
                for ext in [".meta.json", ".pid", ".log"]:
                    file_path = job_dir / f"{job_id}{ext}"
                    if file_path.exists():
                        file_path.unlink()
                cleaned += 1
        except Exception:
            continue
    
    print(f"Cleaned up {cleaned} old job(s)")


def main():
    parser = argparse.ArgumentParser(
        description="Claude Code Auto Executor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python claude_auto.py "Create a Python Flask app"
    python claude_auto.py "Refactor this code" --model claude-sonnet-4-6
    python claude_auto.py --models
    python claude_auto.py --validate-model claude-opus-4-6
    python claude_auto.py --status claude_20260304_120000_123
    python claude_auto.py --results claude_20260304_120000_123
    python claude_auto.py --list
    python claude_auto.py --cleanup --days 7
        """
    )
    
    parser.add_argument("task", nargs="?", help="Task description to execute")
    parser.add_argument("--model", help="Model to use (e.g., claude-sonnet-4-6)")
    parser.add_argument("--working-dir", help="Working directory for the task")
    parser.add_argument("--models", action="store_true", help="List available models")
    parser.add_argument("--validate-model", metavar="MODEL", help="Validate if a model is available")
    parser.add_argument("--status", metavar="JOB_ID", help="Check status of a job")
    parser.add_argument("--results", metavar="JOB_ID", help="Get results of a job")
    parser.add_argument("--list", action="store_true", help="List all jobs")
    parser.add_argument("--cleanup", action="store_true", help="Clean up old jobs")
    parser.add_argument("--days", type=int, default=7, help="Days to keep jobs (for cleanup)")
    
    args = parser.parse_args()
    
    if args.models:
        result = list_models()
        print("=" * 60)
        print("Available Models")
        print("=" * 60)
        
        if result.get("message"):
            print(f"Note: {result['message']}")
        
        if result.get("warning"):
            print(f"Warning: {result['warning']}")
        
        if result.get("error"):
            print(f"Error: {result['error']}")
        
        print(f"\nAuthenticated: {result['authenticated']}")
        print(f"Default Model: {result['default_model'] or 'None'}")
        
        if result["models"]:
            print(f"\nAvailable Models ({len(result['models'])}):")
            for model in result["models"]:
                marker = " (default)" if model == result["default_model"] else ""
                print(f"  - {model}{marker}")
        else:
            print("\nNo models available from API")
        
    elif args.validate_model:
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
        
    elif args.status:
        check_job_status(args.status)
    elif args.results:
        get_job_results(args.results)
    elif args.list:
        list_jobs()
    elif args.cleanup:
        cleanup_jobs(args.days)
    elif args.task:
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
        
        # Start a new task
        working_dir = Path(args.working_dir).resolve() if args.working_dir else Path.cwd()
        model = args.model  # None means use default
        
        print("✅ " + "=" * 60)
        print("🚀 Starting Claude Code Auto Task")
        print("=" * 60)
        print(f"Task: {args.task}")
        print(f"Model: {model if model else 'default'}")
        print(f"Working Dir: {working_dir}")
        print("-" * 60)
        
        job_id, pid = start_claude_task(args.task, model, working_dir)
        
        print(f"✅ Job started in background")
        print(f"Job ID: {job_id}")
        print(f"PID: {pid}")
        print(f"Log file: {get_job_dir() / f'{job_id}.log'}")
        print("-" * 60)
        print(f"Check status: python {sys.argv[0]} --status {job_id}")
        print(f"Get results: python {sys.argv[0]} --results {job_id}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
