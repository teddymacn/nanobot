#!/bin/bash
# GitHub Copilot Autopilot - Quick Launch Script
# Add this to your shell profile or source it directly

# Get the script directory
CPILOT_AUTO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Main copilot command
copilot-auto() {
    python3 "$CPILOT_AUTO_DIR/copilot_auto.py" "$@"
}

# Quick shortcuts
copilot-run() {
    python3 "$CPILOT_AUTO_DIR/copilot_auto.py" "$@"
}

copilot-status() {
    python3 "$CPILOT_AUTO_DIR/copilot_auto.py" --status "$1"
}

copilot-results() {
    python3 "$CPILOT_AUTO_DIR/copilot_auto.py" --results "$1"
}

copilot-list() {
    python3 "$CPILOT_AUTO_DIR/copilot_auto.py" --list
}

copilot-cleanup() {
    python3 "$CPILOT_AUTO_DIR/copilot_auto.py" --cleanup --days "${1:-7}"
}

# Print usage if called without arguments
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "Copilot Auto shell helpers loaded!"
    echo ""
    echo "Available commands:"
    echo "  copilot-auto \"task\"     - Run a Copilot task (background mode)"
    echo "  copilot-run \"task\"      - Alias for copilot-auto"
    echo "  copilot-status <job_id>   - Check task status"
    echo "  copilot-results <job_id>  - Get task results"
    echo "  copilot-list              - List all jobs"
    echo "  copilot-cleanup [days]    - Cleanup old jobs"
    echo ""
    echo "Example:"
    echo "  copilot-auto \"Create a Python Flask app with user authentication\""
    echo "  copilot-status copilot_20260304_111808_70720"
fi
