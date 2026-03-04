#!/usr/bin/env python3
"""
Execute GitHub Copilot CLI in autopilot mode with background monitoring.

Usage:
    python copilot_run.py "your task description" [--model MODEL_NAME] [--working-dir PATH]

Options:
    --model MODEL_NAME   Specify the AI model to use (optional)
    --working-dir PATH   Working directory for the task (default: current directory)
"""

import subprocess
import sys
import os
import time
import argparse
import tempfile
from pathlib import Path


def get_available_models():
    """Get list of available models by running copilot with invalid model."""
    try:
        result = subprocess.run(
            ["copilot", "--model", "invalid"],
            capture_output=True,
            text=True,
            timeout=30
        )
        # The error output contains the list of valid models
        output = result.stderr + result.stdout
        models = []
        
        # Parse the "Allowed choices are" line
        for line in output.split('\n'):
            if 'Allowed choices' in line or 'allowed choices' in line:
                # Extract models after "are"
                parts = line.split('are')
                if len(parts) > 1:
                    models_str = parts[1].strip()
                    # Split by comma and clean up
                    models = [m.strip() for m in models_str.split(',')]
                break
        
        return models if models else ["default"]
    except Exception as e:
        print(f"Warning: Could not fetch model list: {e}")
        return ["default"]


def run_copilot(task: str, model: str = None, working_dir: str = None):
    """
    Run Copilot CLI in autopilot mode.
    
    Args:
        task: The task description to execute
        model: Optional model name to use
        working_dir: Working directory for the task
    """
    
    # Build the command - correct syntax: copilot -p "prompt" --autopilot --yolo
    cmd = ["copilot", "-p", task, "--autopilot", "--yolo"]
    
    if model and model.lower() != "default":
        cmd.extend(["--model", model])
    
    # Set working directory
    cwd = working_dir if working_dir else os.getcwd()
    
    print(f"Executing: {' '.join(cmd)}")
    print(f"Working directory: {cwd}")
    print(f"Task: {task}")
    print("-" * 60)
    
    try:
        # Run the command and stream output
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=cwd,
            bufsize=1
        )
        
        # Stream output in real-time
        output_lines = []
        for line in process.stdout:
            print(line, end='')
            output_lines.append(line)
            sys.stdout.flush()
        
        process.wait()
        
        print("-" * 60)
        print(f"Copilot CLI exited with code: {process.returncode}")
        
        return {
            "returncode": process.returncode,
            "output": ''.join(output_lines),
            "success": process.returncode == 0
        }
        
    except FileNotFoundError:
        print("Error: 'copilot' command not found.")
        print("Please install GitHub Copilot CLI first:")
        print("  npm install -g @github/copilot")
        print("Or visit: https://github.com/github/copilot-cli")
        return {"returncode": 127, "output": "copilot command not found", "success": False}
    except Exception as e:
        print(f"Error executing Copilot CLI: {e}")
        return {"returncode": 1, "output": str(e), "success": False}


def main():
    parser = argparse.ArgumentParser(description="Execute GitHub Copilot CLI in autopilot mode")
    parser.add_argument("task", help="The task description to execute")
    parser.add_argument("--model", help="AI model to use (run 'copilot --model invalid' to see available models)")
    parser.add_argument("--working-dir", help="Working directory for the task")
    parser.add_argument("--list-models", action="store_true", help="List available models")
    
    args = parser.parse_args()
    
    if args.list_models:
        models = get_available_models()
        print("Available models:")
        for model in models:
            print(f"  - {model}")
        return 0
    
    result = run_copilot(args.task, args.model, args.working_dir)
    return 0 if result["success"] else 1


if __name__ == "__main__":
    sys.exit(main())
