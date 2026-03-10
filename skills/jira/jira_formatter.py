#!/usr/bin/env python3
"""
Jira Issue Formatter

Parses Jira API JSON response and converts it to human-readable Markdown format,
including all custom fields with non-empty values.

Usage:
    # From curl response
    curl -s "https://.../issue/HPS-342" -u "..." | python3 jira_formatter.py
    
    # From file
    python3 jira_formatter.py < response.json
    python3 jira_formatter.py response.json

Environment Variables (for field name resolution):
    JIRA_DOMAIN: Your Jira domain (e.g., efcloud.atlassian.net)
    JIRA_EMAIL: Your Jira email
    JIRA_API_TOKEN: Your Jira API token
"""

import json
import sys
import os
from typing import Any, Optional


def get_custom_field_names(domain: str, email: str, token: str) -> dict:
    """Fetch custom field names from Jira API."""
    import urllib.request
    import base64
    
    try:
        url = f"https://{domain}/rest/api/3/field"
        auth_string = f"{email}:{token}"
        auth_bytes = base64.b64encode(auth_string.encode()).decode()
        
        req = urllib.request.Request(url)
        req.add_header("Authorization", f"Basic {auth_bytes}")
        req.add_header("Accept", "application/json")
        
        with urllib.request.urlopen(req, timeout=10) as response:
            fields = json.loads(response.read().decode())
            
        # Build mapping: customfield_XXXX -> field name
        field_names = {}
        for field in fields:
            field_id = field.get("id", "")
            if field_id.startswith("customfield_"):
                field_names[field_id] = field.get("name", "Unknown")
        
        return field_names
    except Exception as e:
        # Return empty dict on error - will use IDs instead of names
        return {}


def format_value(value: Any, indent: int = 0) -> str:
    """Format a field value for markdown output."""
    if value is None:
        return "null"
    
    if isinstance(value, bool):
        return str(value)
    
    if isinstance(value, (int, float)):
        return str(value)
    
    if isinstance(value, str):
        # Check if it's a short string
        if len(value) < 100 and '\n' not in value:
            return f'"{value}"'
        else:
            # Multi-line string - use code block
            return f"```\n{value}\n```"
    
    if isinstance(value, list):
        if len(value) == 0:
            return "[]"
        items = []
        for item in value:
            if isinstance(item, dict) and 'value' in item:
                items.append(f"- {item['value']}")
            elif isinstance(item, dict) and 'name' in item:
                items.append(f"- {item['name']}")
            elif isinstance(item, str):
                items.append(f"- {item}")
            else:
                items.append(f"- {json.dumps(item)}")
        return "\n" + "\n".join(items)
    
    if isinstance(value, dict):
        # Check for common Jira field patterns
        if 'value' in value and len(value) == 1:
            return format_value(value['value'])
        
        if 'name' in value and len(value) <= 3:
            name = value.get('name', '')
            if 'displayName' in value:
                return f"{name} ({value['displayName']})"
            return name
        
        if 'displayName' in value:
            return value['displayName']
        
        if 'key' in value:
            return f"{value.get('key', '')} - {value.get('summary', '')}"
        
        # Rich text document (Atlassian document format)
        if value.get('type') == 'doc':
            return extract_text_from_doc(value)
        
        # Generic dict - format as key-value pairs
        lines = []
        for k, v in value.items():
            if v is not None:
                lines.append(f"  - {k}: {format_value(v)}")
        if lines:
            return "\n" + "\n".join(lines)
        return json.dumps(value)
    
    return str(value)


def extract_text_from_doc(doc: dict) -> str:
    """Extract plain text from Atlassian document format."""
    text_parts = []
    
    def traverse(node):
        if isinstance(node, dict):
            content = node.get('content', [])
            for child in content:
                traverse(child)
            if node.get('type') == 'text':
                text = node.get('text', '')
                marks = node.get('marks', [])
                for mark in marks:
                    if mark.get('type') == 'strong':
                        text = f"**{text}**"
                    elif mark.get('type') == 'em':
                        text = f"*{text}*"
                text_parts.append(text)
        elif isinstance(node, list):
            for item in node:
                traverse(item)
    
    traverse(doc)
    return ' '.join(text_parts)


def is_empty_value(value: Any) -> bool:
    """Check if a value should be considered empty."""
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    if isinstance(value, list) and len(value) == 0:
        return True
    if isinstance(value, dict) and value == {}:
        return True
    return False


def format_issue(issue_data: dict, custom_field_names: dict = None) -> str:
    """Format a Jira issue as Markdown."""
    fields = issue_data.get('fields', {})
    
    lines = []
    
    # Header
    key = issue_data.get('key', 'Unknown')
    summary = fields.get('summary', 'No summary')
    lines.append(f"# {key}: {summary}")
    lines.append("")
    
    # Standard fields (in priority order)
    standard_fields = [
        ('issuetype', 'Issue Type', lambda v: v.get('name', '')),
        ('status', 'Status', lambda v: v.get('name', '')),
        ('priority', 'Priority', lambda v: v.get('name', '')),
        ('resolution', 'Resolution', lambda v: v.get('name', '') if v else 'Unresolved'),
        ('assignee', 'Assignee', lambda v: v.get('displayName', 'Unassigned') if v else 'Unassigned'),
        ('reporter', 'Reporter', lambda v: v.get('displayName', '') if v else ''),
        ('created', 'Created', lambda v: v),
        ('updated', 'Updated', lambda v: v),
        ('resolved', 'Resolved', lambda v: v),
        ('duedate', 'Due Date', lambda v: v),
        ('parent', 'Parent', lambda v: f"{v.get('key', '')} - {v.get('fields', {}).get('summary', '')}" if v else ''),
        ('subtasks', 'Subtasks', lambda v: f"{len(v)} subtask(s)" if v else ''),
        ('labels', 'Labels', lambda v: ', '.join(v) if v else ''),
        ('components', 'Components', lambda v: ', '.join([c.get('name', '') for c in v]) if v else ''),
        ('versions', 'Fix Versions', lambda v: ', '.join([ver.get('name', '') for ver in v]) if v else ''),
        ('description', 'Description', lambda v: extract_text_from_doc(v) if isinstance(v, dict) and v.get('type') == 'doc' else str(v)),
    ]
    
    lines.append("## Basic Information")
    lines.append("")
    
    for field_id, label, formatter in standard_fields:
        value = fields.get(field_id)
        if value is not None and not is_empty_value(value):
            formatted = formatter(value)
            if formatted:
                lines.append(f"- **{label}**: {formatted}")
    
    # Custom fields
    custom_fields = {k: v for k, v in fields.items() 
                     if k.startswith('customfield') and not is_empty_value(v)}
    
    if custom_fields:
        lines.append("")
        lines.append("## Custom Fields")
        lines.append("")
        
        for field_id in sorted(custom_fields.keys()):
            value = custom_fields[field_id]
            # Try to get field name from cache
            field_name = custom_field_names.get(field_id, 'Unknown') if custom_field_names else 'Unknown'
            formatted_value = format_value(value)
            
            # Format: Field Name (customfield_XXXX): value
            lines.append(f"### {field_name} `{field_id}`")
            lines.append("")
            lines.append(formatted_value)
            lines.append("")
    
    return "\n".join(lines)


def main():
    # Read JSON input
    if len(sys.argv) > 1:
        # From file
        with open(sys.argv[1], 'r') as f:
            data = json.load(f)
    else:
        # From stdin
        data = json.load(sys.stdin)
    
    # Handle both single issue and search results
    if 'issues' in data:
        # Search results (JQL)
        custom_field_names = {}
        if os.environ.get('JIRA_DOMAIN') and os.environ.get('JIRA_API_TOKEN'):
            domain = os.environ['JIRA_DOMAIN'].replace('.atlassian.net', '')
            custom_field_names = get_custom_field_names(
                f"{domain}.atlassian.net",
                os.environ.get('JIRA_EMAIL', ''),
                os.environ.get('JIRA_API_TOKEN', '')
            )
        
        issues = data.get('issues', [])
        total = data.get('total', len(issues))
        
        print(f"# Search Results ({len(issues)} of {total} issues)")
        print("")
        
        for issue in issues:
            print(format_issue(issue, custom_field_names))
            print("---")
            print("")
    else:
        # Single issue
        custom_field_names = {}
        if os.environ.get('JIRA_DOMAIN') and os.environ.get('JIRA_API_TOKEN'):
            domain = os.environ['JIRA_DOMAIN'].replace('.atlassian.net', '')
            custom_field_names = get_custom_field_names(
                f"{domain}.atlassian.net",
                os.environ.get('JIRA_EMAIL', ''),
                os.environ.get('JIRA_API_TOKEN', '')
            )
        
        print(format_issue(data, custom_field_names))


if __name__ == '__main__':
    main()
