#!/usr/bin/env python3
"""
Execute GitHub Copilot CLI in background mode with result checking.

This script handles long-running Copilot tasks by:
1. Starting the task in a background process
2. Saving the process ID and output file location
3. Providing commands to check status and retrieve results

Usage:
    # Start a background task:
    python copilot_background.py start "your task description" [--model MODEL]
    
    # Check status:
    python copilot_background.py status <job_id>
    
    # Get results:
    python copilot_background.py results <job_id>
    
    # List all jobs:
    python copilot_background.py list
"""

import subprocess
import sys
import os
import time
import argparse
import json
import signal
from pathlib import Path
from datetime import datetime

# Import token validation
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)
from copilot_token import validate_copilot_token


JOBS_DIR = Path.home() / ".copilot-jobs"


def ensure_jobs_dir():
    """Ensure the jobs directory exists."""
    JOBS_DIR.mkdir(parents=True, exist_ok=True)


def generate_job_id():
    """Generate a unique job ID."""
    return f"copilot_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.getpid()}"


def start_job(task: str, model: str = None, working_dir: str = None, skip_validation: bool = False):
    """Start a Copilot task in the background."""
    ensure_jobs_dir()
    
    # Validate token before starting (unless explicitly skipped)
    # Note: When called from copilot_auto.py, validation is done there first
    if not skip_validation:
        is_valid, message = validate_copilot_token()
        if not is_valid:
            print("=" * 60)
            print("❌ Token Validation Failed")
            print("=" * 60)
            print(message)
            print("=" * 60)
            print("\n💡 To skip validation (not recommended), use --skip-validation")
            sys.exit(1)
        # Only print if running standalone (not called from copilot_auto.py)
        import inspect
        caller_frame = inspect.stack()[1]
        if 'copilot_auto.py' not in caller_frame.filename:
            print(f"✅ {message}")
    
    job_id = generate_job_id()
    job_file = JOBS_DIR / f"{job_id}.json"
    output_file = JOBS_DIR / f"{job_id}.log"
    pid_file = JOBS_DIR / f"{job_id}.pid"
    
    # Build the command - correct syntax: copilot -p "prompt" --autopilot --yolo
    cmd = ["copilot", "-p", task, "--autopilot", "--yolo"]
    
    if model and model.lower() != "default":
        cmd.extend(["--model", model])
    
    cwd = working_dir if working_dir else os.getcwd()
    
    # Create job metadata
    job_info = {
        "job_id": job_id,
        "task": task,
        "model": model or "default",
        "working_dir": cwd,
        "start_time": datetime.now().isoformat(),
        "status": "running",
        "output_file": str(output_file),
        "pid_file": str(pid_file)
    }
    
    # Save job metadata
    with open(job_file, 'w') as f:
        json.dump(job_info, f, indent=2)
    
    print(f"Starting Copilot task in background...")
    print(f"Job ID: {job_id}")
    print(f"Task: {task}")
    print(f"Model: {model or 'default'}")
    print(f"Working directory: {cwd}")
    print(f"Output log: {output_file}")
    print("-" * 60)
    
    # Start the process in background
    with open(output_file, 'w') as log_file:
        process = subprocess.Popen(
            cmd,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=cwd,
            start_new_session=True  # Create new process group
        )
    
    # Save PID
    with open(pid_file, 'w') as f:
        f.write(str(process.pid))
    
    # Update job info with PID
    job_info["pid"] = process.pid
    with open(job_file, 'w') as f:
        json.dump(job_info, f, indent=2)
    
    print(f"Process started with PID: {process.pid}")
    print(f"\nTo check status: python copilot_background.py status {job_id}")
    print(f"To view logs: tail -f {output_file}")
    
    return job_id


def check_job_status(job_id: str):
    """Check the status of a background job."""
    ensure_jobs_dir()
    
    job_file = JOBS_DIR / f"{job_id}.json"
    pid_file = JOBS_DIR / f"{job_id}.pid"
    output_file = JOBS_DIR / f"{job_id}.log"
    
    if not job_file.exists():
        print(f"Error: Job {job_id} not found")
        return None
    
    with open(job_file, 'r') as f:
        job_info = json.load(f)
    
    # Check if process is still running
    pid = job_info.get("pid")
    if pid:
        try:
            os.kill(pid, 0)  # Check if process exists
            job_info["status"] = "running"
        except ProcessLookupError:
            job_info["status"] = "completed"
            job_info["end_time"] = datetime.now().isoformat()
            # Update job file
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


def get_job_results(job_id: str):
    """Get the complete results of a completed job."""
    ensure_jobs_dir()
    
    job_file = JOBS_DIR / f"{job_id}.json"
    output_file = JOBS_DIR / f"{job_id}.log"
    
    if not job_file.exists():
        print(f"Error: Job {job_id} not found")
        return None
    
    with open(job_file, 'r') as f:
        job_info = json.load(f)
    
    # Check status first
    pid = job_info.get("pid")
    if pid:
        try:
            os.kill(pid, 0)
            print("Warning: Job is still running!")
            print("Use 'status' command to check progress.")
            return None
        except ProcessLookupError:
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
    
    for job_file in sorted(jobs):
        try:
            with open(job_file, 'r') as f:
                job_info = json.load(f)
            print(f"{job_info['job_id']:<40} {job_info['status']:<12} {job_info['model']:<20} {job_info['start_time']}")
        except Exception as e:
            print(f"{job_file.name}: Error reading - {e}")


def cleanup_old_jobs(days: int = 7):
    """Clean up job files older than specified days."""
    ensure_jobs_dir()
    
    cutoff = time.time() - (days * 24 * 60 * 60)
    cleaned = 0
    
    for job_file in JOBS_DIR.glob("*.json"):
        if job_file.stat().st_mtime < cutoff:
            job_id = job_file.stem
            # Remove all related files
            for ext in ['.json', '.log', '.pid']:
                file_to_remove = JOBS_DIR / f"{job_id}{ext}"
                if file_to_remove.exists():
                    file_to_remove.unlink()
            cleaned += 1
    
    print(f"Cleaned up {cleaned} old job(s)")


def main():
    parser = argparse.ArgumentParser(description="Execute GitHub Copilot CLI in background mode")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Start command
    start_parser = subparsers.add_parser("start", help="Start a new background task")
    start_parser.add_argument("task", help="The task description to execute")
    start_parser.add_argument("--model", help="AI model to use")
    start_parser.add_argument("--working-dir", help="Working directory for the task")
    start_parser.add_argument("--skip-validation", action="store_true", help="Skip token validation (not recommended)")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Check job status")
    status_parser.add_argument("job_id", help="Job ID to check")
    
    # Results command
    results_parser = subparsers.add_parser("results", help="Get job results")
    results_parser.add_argument("job_id", help="Job ID to get results for")
    
    # List command
    subparsers.add_parser("list", help="List all jobs")
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser("cleanup", help="Clean up old jobs")
    cleanup_parser.add_argument("--days", type=int, default=7, help="Days to keep jobs (default: 7)")
    
    args = parser.parse_args()
    
    if args.command == "start":
        job_id = start_job(args.task, args.model, args.working_dir, args.skip_validation)
        print(f"\nJob started: {job_id}")
    elif args.command == "status":
        check_job_status(args.job_id)
    elif args.command == "results":
        get_job_results(args.job_id)
    elif args.command == "list":
        list_jobs()
    elif args.command == "cleanup":
        cleanup_old_jobs(args.days)
    else:
        parser.print_help()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
