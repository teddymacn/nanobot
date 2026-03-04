#!/usr/bin/env python3
"""
GitHub Copilot Autopilot Executor - Always runs in background mode.

This is the main entry point for the copilot-auto skill.
All tasks are executed in background mode with full auto-approval.

Usage:
    python copilot_auto.py "your task description" [--model MODEL] [--working-dir PATH]

Examples:
    python copilot_auto.py "Create a Python Flask app"
    python copilot_auto.py "Refactor this code" --model claude-sonnet-4.6
    python copilot_auto.py "Add tests" --working-dir /path/to/project
"""

import subprocess
import sys
import os
import argparse
import time
from pathlib import Path
from datetime import datetime

# Import token validation
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)
from copilot_token import validate_copilot_token, validate_copilot_cli


def get_script_dir() -> str:
    """Get the directory where this script is located."""
    return os.path.dirname(os.path.abspath(__file__))


def start_background_task(task: str, model: str = None, working_dir: str = None) -> str:
    """Start a Copilot task in background mode."""
    script_dir = get_script_dir()
    background_script = os.path.join(script_dir, "copilot_background.py")
    
    cmd = [sys.executable, background_script, "start", task]
    
    if model and model.lower() != "default":
        cmd.extend(["--model", model])
    
    if working_dir:
        cmd.extend(["--working-dir", working_dir])
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout


def get_status(job_id: str) -> str:
    """Check status of a background job."""
    script_dir = get_script_dir()
    background_script = os.path.join(script_dir, "copilot_background.py")
    
    cmd = [sys.executable, background_script, "status", job_id]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout


def get_results(job_id: str) -> str:
    """Get results of a completed job."""
    script_dir = get_script_dir()
    background_script = os.path.join(script_dir, "copilot_background.py")
    
    cmd = [sys.executable, background_script, "results", job_id]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout


def list_jobs() -> str:
    """List all jobs."""
    script_dir = get_script_dir()
    background_script = os.path.join(script_dir, "copilot_background.py")
    
    cmd = [sys.executable, background_script, "list"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout


def cleanup(days: int = 7) -> str:
    """Cleanup old jobs."""
    script_dir = get_script_dir()
    background_script = os.path.join(script_dir, "copilot_background.py")
    
    cmd = [sys.executable, background_script, "cleanup", "--days", str(days)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout


def main():
    parser = argparse.ArgumentParser(
        description="GitHub Copilot Autopilot Executor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "Create a Python function"
  %(prog)s "Refactor this code" --model claude-sonnet-4.6
  %(prog)s --status copilot_20260304_111808_70720
  %(prog)s --results copilot_20260304_111808_70720
  %(prog)s --list
  %(prog)s --cleanup --days 7
  %(prog)s --validate-token  # Check token before running
        """
    )
    
    parser.add_argument("task", nargs="?", help="Task description to execute")
    parser.add_argument("--model", "-m", help="AI model to use (default: claude-sonnet-4.6)")
    parser.add_argument("--working-dir", "-w", help="Working directory for the task")
    parser.add_argument("--status", "-s", help="Check status of a job by ID")
    parser.add_argument("--results", "-r", help="Get results of a completed job")
    parser.add_argument("--list", "-l", action="store_true", help="List all jobs")
    parser.add_argument("--cleanup", "-c", action="store_true", help="Cleanup old jobs")
    parser.add_argument("--days", "-d", type=int, default=7, help="Days to keep jobs (for cleanup)")
    parser.add_argument("--wait", action="store_true", help="Wait for task completion and show results")
    parser.add_argument("--validate-token", "-v", action="store_true", help="Validate token and CLI before running")
    parser.add_argument("--skip-validation", action="store_true", help="Skip token validation (not recommended)")
    
    args = parser.parse_args()
    
    # Handle different modes
    if args.list:
        print(list_jobs())
        return
    
    if args.status:
        print(get_status(args.status))
        return
    
    if args.results:
        print(get_results(args.results))
        return
    
    if args.cleanup:
        print(cleanup(args.days))
        return
    
    if args.validate_token:
        print("=" * 60)
        print("🔐 Validating GitHub Copilot Token")
        print("=" * 60)
        is_valid, message = validate_copilot_token()
        print(message)
        print("=" * 60)
        sys.exit(0 if is_valid else 1)
    
    if not args.task:
        parser.print_help()
        print("\nError: Please provide a task description or use --status, --results, --list, or --cleanup")
        sys.exit(1)
    
    # Validate token before executing task (unless explicitly skipped)
    if not args.skip_validation:
        is_valid, message = validate_copilot_token()
        if not is_valid:
            print("=" * 60)
            print("❌ Token Validation Failed")
            print("=" * 60)
            print(message)
            print("=" * 60)
            print("\n💡 To skip validation (not recommended), use --skip-validation")
            sys.exit(1)
        # Print success message quietly
        print(f"✅ {message}")
    
    # Start a new task
    print("=" * 60)
    print("🚀 Starting Copilot Autopilot Task")
    print("=" * 60)
    print(f"Task: {args.task}")
    print(f"Model: {args.model or 'default (claude-sonnet-4.6)'}")
    print(f"Working Dir: {args.working_dir or os.getcwd()}")
    print("-" * 60)
    
    output = start_background_task(args.task, args.model, args.working_dir)
    print(output)
    
    # Extract job ID from output
    job_id = None
    for line in output.split("\n"):
        if "Job ID:" in line:
            job_id = line.split("Job ID:")[1].strip()
            break
    
    if args.wait and job_id:
        print("\n⏳ Waiting for task completion...")
        while True:
            time.sleep(5)
            status_output = get_status(job_id)
            if "Status: completed" in status_output or "Status: failed" in status_output:
                print("\n" + "=" * 60)
                print("✅ Task Completed!")
                print("=" * 60)
                print(get_results(job_id))
                break
            elif "Status:" in status_output:
                status_line = [l for l in status_output.split("\n") if "Status:" in l][0]
                print(f"  {status_line.strip()}")
    
    print("\n" + "=" * 60)
    print("💡 Tip: Use --status, --results, or --list to check on tasks")
    print("=" * 60)


if __name__ == "__main__":
    main()
