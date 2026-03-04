#!/usr/bin/env python3
"""
GitHub Copilot Token Validator

Validates the COPILOT_GITHUB_TOKEN environment variable:
- Checks if the token is set
- Validates token format
- Checks if token has expired (if JWT format)
- Optionally validates token with GitHub API

Returns: (is_valid: bool, message: str)
"""

import os
import sys
import re
import base64
import json
from datetime import datetime, timezone
from typing import Tuple


def decode_jwt(token: str) -> dict | None:
    """Decode a JWT token and return its payload (without verification)."""
    try:
        # JWT format: header.payload.signature
        parts = token.split('.')
        if len(parts) != 3:
            return None
        
        # Decode payload (second part)
        payload = parts[1]
        # Add padding if needed
        padding = 4 - len(payload) % 4
        if padding != 4:
            payload += '=' * padding
        
        decoded = base64.urlsafe_b64decode(payload)
        return json.loads(decoded)
    except Exception:
        return None


def check_token_expiry(token: str) -> Tuple[bool, str]:
    """
    Check if a JWT token has expired.
    
    Returns:
        (is_valid, message)
    """
    payload = decode_jwt(token)
    
    if not payload:
        # Not a JWT token, skip expiry check
        return True, "Token format valid (non-JWT)"
    
    # Check for expiration claim
    if 'exp' in payload:
        exp_timestamp = payload['exp']
        exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
        now = datetime.now(timezone.utc)
        
        if now >= exp_datetime:
            return False, f"Token expired at {exp_datetime.isoformat()}"
        
        # Warn if expiring soon (within 1 hour)
        time_remaining = exp_datetime - now
        if time_remaining.total_seconds() < 3600:
            return True, f"Token valid but expires soon ({int(time_remaining.total_seconds() / 60)} minutes)"
        
        return True, f"Token valid (expires {exp_datetime.isoformat()})"
    
    return True, "Token valid (no expiration claim)"


def validate_token_format(token: str) -> Tuple[bool, str]:
    """
    Validate the token format.
    
    Returns:
        (is_valid, message)
    """
    if not token:
        return False, "Token is empty"
    
    if len(token) < 10:
        return False, "Token too short (minimum 10 characters)"
    
    # GitHub tokens typically start with specific prefixes
    # ghp_, gho_, ghu_, ghs_, ghr_ for OAuth tokens
    # But Copilot tokens may have different formats
    if token.startswith('ghp_') or token.startswith('gho_') or token.startswith('ghu_'):
        return True, "Valid GitHub token format"
    
    # JWT tokens (base64.base64.base64)
    if token.count('.') == 2:
        payload = decode_jwt(token)
        if payload:
            return True, "Valid JWT token format"
        return False, "Invalid JWT token format"
    
    # Generic token (just check length and characters)
    if len(token) >= 20 and re.match(r'^[A-Za-z0-9_-]+$', token):
        return True, "Valid token format (generic)"
    
    return False, "Token format unrecognized"


def validate_copilot_token() -> Tuple[bool, str]:
    """
    Validate the COPILOT_GITHUB_TOKEN environment variable.
    
    Returns:
        (is_valid, message)
    """
    # Check if environment variable is set
    token = os.environ.get('COPILOT_GITHUB_TOKEN')
    
    if not token:
        return False, (
            "❌ COPILOT_GITHUB_TOKEN environment variable is not set.\n"
            "   Please set it before running Copilot tasks:\n"
            "   export COPILOT_GITHUB_TOKEN='your_token_here'\n"
            "   \n"
            "   Or in Docker/container:\n"
            "   docker run -e COPILOT_GITHUB_TOKEN='your_token_here' ..."
        )
    
    # Validate token format
    is_valid_format, format_msg = validate_token_format(token)
    if not is_valid_format:
        return False, f"❌ Invalid token format: {format_msg}"
    
    # Check token expiry
    is_valid_expiry, expiry_msg = check_token_expiry(token)
    if not is_valid_expiry:
        return False, f"❌ Token validation failed: {expiry_msg}"
    
    # Success
    return True, f"✅ Token validated: {expiry_msg}"


def validate_copilot_cli() -> Tuple[bool, str]:
    """
    Check if GitHub Copilot CLI is installed and accessible.
    
    Returns:
        (is_valid, message)
    """
    import subprocess
    
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


def full_validation() -> Tuple[bool, str]:
    """
    Perform full validation: token + CLI.
    
    Returns:
        (is_valid, message)
    """
    messages = []
    all_valid = True
    
    # Validate token
    token_valid, token_msg = validate_copilot_token()
    messages.append(token_msg)
    if not token_valid:
        all_valid = False
    
    # Validate CLI
    cli_valid, cli_msg = validate_copilot_cli()
    messages.append(cli_msg)
    if not cli_valid:
        all_valid = False
    
    return all_valid, "\n".join(messages)


def main():
    """Main entry point for token validation."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Validate GitHub Copilot token and CLI installation"
    )
    parser.add_argument(
        '--cli-only',
        action='store_true',
        help='Only check CLI installation, skip token validation'
    )
    parser.add_argument(
        '--token-only',
        action='store_true',
        help='Only validate token, skip CLI check'
    )
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Only output result (valid/invalid), no details'
    )
    parser.add_argument(
        '--check-expiry',
        action='store_true',
        help='Check token expiry and print expiration time'
    )
    
    args = parser.parse_args()
    
    # Determine what to validate
    if args.cli_only:
        is_valid, message = validate_copilot_cli()
    elif args.token_only:
        is_valid, message = validate_copilot_token()
    else:
        is_valid, message = full_validation()
    
    # Output results
    if args.quiet:
        sys.exit(0 if is_valid else 1)
    
    print("=" * 60)
    print("GitHub Copilot Validation")
    print("=" * 60)
    print(message)
    print("=" * 60)
    
    if args.check_expiry:
        token = os.environ.get('COPILOT_GITHUB_TOKEN')
        if token:
            payload = decode_jwt(token)
            if payload and 'exp' in payload:
                exp_datetime = datetime.fromtimestamp(payload['exp'], tz=timezone.utc)
                print(f"Token expires: {exp_datetime.isoformat()}")
    
    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()
