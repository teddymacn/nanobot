---
name: jira
description: Jira Cloud REST API via curl. Use this skill to search, read, and view issues, projects, and workflows in Jira. STRICTLY READ-ONLY. NEVER perform write operations.
vm0_secrets:
  - JIRA_API_TOKEN
vm0_vars:
  - JIRA_DOMAIN
  - JIRA_EMAIL
---

# Jira API

Use the Jira Cloud REST API via direct `curl` calls to **read and view** issues, projects, and workflows.

> Official docs: `https://developer.atlassian.com/cloud/jira/platform/rest/v3/`

---

## 🛑 STRICTLY READ-ONLY RESTRICTION
**WARNING:** This skill is strictly restricted to read-only operations. You are **NEVER** allowed to perform any write operations. 
- **DO NOT** use POST, PUT, DELETE, or PATCH requests to modify Jira data (except for strictly read-only endpoints like `/search/jql` which use POST for complex queries).
- **DO NOT** create, update, delete, transition, assign, or comment on any issues.
- **DO NOT** modify projects, users, or workflows.

---

## When to Use

Use this skill when you need to:

- **Search issues** using JQL (Jira Query Language)
- **Get issue details** and read comments
- **List projects** and their metadata
- **Read issue types** for a project
- **Search users**
- **Get available transitions** (Read-only view)

---

## Prerequisites

1. Go to [Atlassian Account Settings](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click **Create API token**
3. Copy the generated token (you won't see it again)

```bash
export JIRA_DOMAIN="mycompany" # e.g., "mycompany" or "mycompany.atlassian.net"
export JIRA_EMAIL="you@example.com" # Your Atlassian account email
export JIRA_API_TOKEN="your-api-token" # API token from step 2
```

### Rate Limits

Jira Cloud has rate limits that vary by endpoint. For most REST API calls, expect limits around 100-500 requests per minute.

---

> **Important:** When using `$VAR` in a command that pipes to another command, wrap the command containing `$VAR` in `bash -c '...'`. Due to a Claude Code bug, environment variables are silently cleared when pipes are used directly.
> ```bash
> bash -c 'curl -s "https://api.example.com" -H "Authorization: Bearer $API_KEY"' | jq '.field'
> ```

## How to Use

All examples below assume `JIRA_DOMAIN`, `JIRA_EMAIL`, and `JIRA_API_TOKEN` are set.

Base URL: `https://${JIRA_DOMAIN%.atlassian.net}.atlassian.net/rest/api/3`

> Note: `${JIRA_DOMAIN%.atlassian.net}` strips the suffix if present, so both `mycompany` and `mycompany.atlassian.net` work.

---

### 1. Get Current User

Verify your authentication:

```bash
bash -c 'curl -s "https://${JIRA_DOMAIN%.atlassian.net}.atlassian.net/rest/api/3/myself" -u "${JIRA_EMAIL}:${JIRA_API_TOKEN}" --header "Accept: application/json"'
```

---

### 2. List Projects

Get all projects you have access to:

```bash
bash -c 'curl -s "https://${JIRA_DOMAIN%.atlassian.net}.atlassian.net/rest/api/3/project" -u "${JIRA_EMAIL}:${JIRA_API_TOKEN}" --header "Accept: application/json"'
```

---

### 3. Get Project Details

Get details for a specific project:

```bash
PROJECT_KEY="PROJ"

bash -c 'curl -s "https://${JIRA_DOMAIN%.atlassian.net}.atlassian.net/rest/api/3/project/${PROJECT_KEY}" -u "${JIRA_EMAIL}:${JIRA_API_TOKEN}" --header "Accept: application/json"'
```

---

### 4. Get Issue Types for Project

List available issue types (Task, Bug, Story, etc.):

```bash
PROJECT_KEY="PROJ"

bash -c 'curl -s "https://${JIRA_DOMAIN%.atlassian.net}.atlassian.net/rest/api/3/project/${PROJECT_KEY}" -u "${JIRA_EMAIL}:${JIRA_API_TOKEN}" --header "Accept: application/json"'
```

---

### 5. Search Issues with JQL

Search issues using Jira Query Language:

Write to `/tmp/jira_request.json`:

```json
{
  "jql": "project = PROJ AND status NOT IN (Done) ORDER BY created DESC",
  "maxResults": 10,
  "fields": ["key", "summary", "status", "assignee", "priority"]
}
```

Then run:

```bash
bash -c 'curl -s -X POST "https://${JIRA_DOMAIN%.atlassian.net}.atlassian.net/rest/api/3/search/jql" -u "${JIRA_EMAIL}:${JIRA_API_TOKEN}" --header "Accept: application/json" --header "Content-Type: application/json" -d @/tmp/jira_request.json' | jq '.issues[] | {key, summary: .fields.summary, status: .fields.status.name, assignee: .fields.assignee.displayName, priority: .fields.priority.name}'
```

Common JQL examples:
- `project = PROJ` - Issues in project
- `assignee = currentUser()` - Your issues
- `status = "In Progress"` - By status
- `status NOT IN (Done, Closed)` - Exclude statuses
- `created >= -7d` - Created in last 7 days
- `labels = bug` - By label
- `priority = High` - By priority

---

### 6. Get Issue Details

Get full details of an issue (formatted as Markdown):

```bash
ISSUE_KEY="PROJ-123"

bash -c 'curl -s "https://${JIRA_DOMAIN%.atlassian.net}.atlassian.net/rest/api/3/issue/${ISSUE_KEY}" -u "${JIRA_EMAIL}:${JIRA_API_TOKEN}" --header "Accept: application/json" | python3 skills/jira/jira_formatter.py'
```

> **Note:** The `jira_formatter.py` script automatically formats the JSON response into readable Markdown with all custom fields.

---

### 7. Get Available Transitions

Get possible status transitions for an issue (Read-only view of workflow options):

```bash
ISSUE_KEY="PROJ-123"

bash -c 'curl -s "https://${JIRA_DOMAIN%.atlassian.net}.atlassian.net/rest/api/3/issue/${ISSUE_KEY}/transitions" -u "${JIRA_EMAIL}:${JIRA_API_TOKEN}" --header "Accept: application/json"'
```

---

### 8. Get Issue Comments

List all comments on an issue:

```bash
ISSUE_KEY="PROJ-123"

bash -c 'curl -s "https://${JIRA_DOMAIN%.atlassian.net}.atlassian.net/rest/api/3/issue/${ISSUE_KEY}/comment" -u "${JIRA_EMAIL}:${JIRA_API_TOKEN}" --header "Accept: application/json"'
```

---

### 9. Search Users

Find users by email or name:

Write to `/tmp/jira_search.txt`:

```
john
```

```bash
bash -c 'curl -s -G "https://${JIRA_DOMAIN%.atlassian.net}.atlassian.net/rest/api/3/user/search" -u "${JIRA_EMAIL}:${JIRA_API_TOKEN}" --header "Accept: application/json" --data-urlencode "query@/tmp/jira_search.txt"'
```

---

## Guidelines

1. **STRICTLY READ-ONLY**: Do not attempt to use `curl` to update, create, or delete anything. The agent is explicitly restricted from making modifications to Jira.
2. **Use JQL for complex queries**: JQL is powerful for filtering issues by any field combination.
3. **Handle pagination**: Use `startAt` and `maxResults` for large result sets.
4. **Use account IDs**: Jira Cloud uses account IDs (not usernames) for user references.
5. **Rate limiting**: Implement exponential backoff if you receive 429 responses.