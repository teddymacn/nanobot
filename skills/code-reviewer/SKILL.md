---
name: code-reviewer
description: >
  Professional yet rigorous code reviews for remote GitHub PRs via gh cli only.
  Triggered by any message about reviewing a GitHub PR number or PR URL that matches the GitHub PR URL pattern.
  Combines thorough workflow with adversarial security/performance analysis.
  Supports Python, R, JavaScript/TypeScript, SQL, and front-end code.
  All comments are attributed with a styled separator: `<br><small>(by code-reviewer)</small>`.
---

# Code Reviewer

## ⚠️ CRITICAL: Common Mistakes to Avoid

**DO NOT skip these steps — reviews missing these will be rejected:**

1. **JIRA TICKETS (Step 2):** If the PR title/body contains a Jira ticket ID (e.g., `EFEKTA-12345`, `ABC-999`), you MUST fetch the ticket details using the `jira` skill BEFORE analyzing code. Use this context to evaluate if changes meet requirements.

2. **INLINE COMMENTS FIRST (Step 5):** You MUST post ALL inline comments on specific lines FIRST using appropriate `gh` CLI commands (e.g., `gh api`). ONLY after all inline comments are posted, submit the final review with `gh pr review`. Summary-only reviews without inline comments are INVALID.

3. **WORKFLOW ORDER:** Steps must be completed in exact order: (1) PR metadata → (2) Jira context → (3) Code diffs → (4) Decision matrix → (5) Inline comments + review submission → (6) Cleanup.

---

This skill guides the agent in conducting professional code reviews with a focus on security, performance, and correctness. It uses the `gh` cli exclusively for remote GitHub PRs.

## ⚠️ MANDATORY WORKFLOW CHECKLIST

**Before submitting any review, verify you have completed ALL steps:**

- [ ] **Step 1:** Fetched PR metadata (title, body, author, branches, commits) via `gh` CLI
- [ ] **Step 2:** Scanned PR for Jira ticket IDs; fetched Jira context if found
- [ ] **Step 3:** Fetched and analyzed code diffs using language-specific checklists
- [ ] **Step 4:** Applied Decision Matrix to determine review action (REQUEST_CHANGES/COMMENT/APPROVE)
- [ ] **Step 5:** Posted ALL inline comments FIRST, then submitted review with summary
- [ ] **Step 6:** Deleted ALL temporary files created during the process

**Logging Rule:** Print `echo` log for each major step/decision before proceeding.

**Comment Attribution:** ALL comments must end with `<br><small>(by code-reviewer)</small>`

---

## Workflow

**STRICT RULE:** You MUST follow these steps in exact order. Do NOT skip to Step 3 before completing Steps 1 and 2.

**GH CLI KNOWLEDGE:** For instructions on how to use the `gh` cli (e.g., fetching PR metadata, fetching diffs, adding inline comments, or submitting reviews), refer to the `github` skill in the `nanobot/skills` directory.

**SESSION & LOGGING RULE:** For every major workflow step and decision (e.g., finding Jira context, identifying issues, classifying severity, choosing PR action), you MUST print a log to the terminal using `echo` detailing the decision before moving on.

### 1. Fetch PR Metadata
Use the `gh` cli to fetch the PR metadata, including the title, body, author, branch names, and commits.
*(Hint: Use the knowledge from the `github` skill to perform this action).*

#### Example:
```bash
# Fetch core metadata and commits to identify the head SHA
gh pr view 123 --json title,body,author,headRefName,commits
```

### 2. Scan and Fetch Jira Context

**Step 2a: Extract JIRA Ticket IDs from PR Metadata**

Parse the PR title, body, and branch name to find any JIRA ticket IDs (e.g., `ABC-123`).
If this outputs any JIRA ticket IDs, you MUST proceed to Step 2b. If not, proceed to Step 2c.

**Step 2b: Fetch Jira Ticket Details**

If any ticket IDs are found:
- Check if the `jira` skill exists in the workspace (`skills/jira/SKILL.md`) and if its required ENV VARs are set.
- If it exists and the ENV VARs are set, use the `jira` skill to fetch all ticket details BEFORE fetching or analyzing code diffs. Use this context to evaluate if the changes meet the original requirements.

#### Example:
```bash
# 1. PR Title: "[PROJ-1234] Implement user login"
# 2. Ticket ID: PROJ-1234
# 3. Fetch details via Jira skill
ISSUE_KEY="PROJ-1234"
bash -c 'curl -s "https://${JIRA_DOMAIN%.atlassian.net}.atlassian.net/rest/api/3/issue/${ISSUE_KEY}" -u "${JIRA_EMAIL}:${JIRA_API_TOKEN}" --header "Accept: application/json" | python3 skills/jira/jira_formatter.py'
```

**Step 2c: Log and Communicate the Jira Decision (MANDATORY)**

Before proceeding to Step 3, you MUST explicitly log your decision regarding the Jira context using an `echo` command so it shows up in the user's run logs.

- If Jira tickets were fetched, log: `echo "Successfully fetched details for <TICKET_IDs>"` and tell the user in the session what tickets were found.
- If no Jira tickets were found, or the `jira` skill/ENV VARs are unavailable, log: `echo "Proceeding to code diffs."`.

#### Example Log:
```bash
echo "Successfully fetched details for PROJ-1234"
```

### 3. Fetch Code Diffs and Analyze Changes

Now that you have the Jira context (if any), fetch the code diffs and files to analyze using the `gh` cli *(refer to the `github` skill for the exact commands)*.

- Read the diff carefully
- Identify all files changed
- For each file, check for issues in these categories:

#### Python
- [ ] SQL injection via f-strings
- [ ] Missing input validation
- [ ] Hardcoded credentials or secrets
- [ ] No logging or excessive logging
- [ ] Thread-safety issues with shared state

#### JavaScript/TypeScript
- [ ] `any` types instead of proper types
- [ ] Missing null/undefined checks
- [ ] Unhandled Promise rejections
- [ ] XSS via `innerHTML` or `dangerouslySetInnerHTML`
- [ ] Missing async/await error handling
- [ ] Memory leaks from unclosed subscriptions
- [ ] Hardcoded API keys in client code

#### General Security
- [ ] SQL injection
- [ ] XSS vulnerabilities
- [ ] CSRF missing tokens
- [ ] Insecure direct object references
- [ ] Missing authentication/authorization checks
- [ ] Sensitive data in logs/URLs
- [ ] Weak cryptography (MD5, SHA1, DES)
- [ ] Hardcoded secrets

#### Example:
```bash
# Fetch the diff to a temporary file for analysis
gh pr diff 123 > /tmp/pr_123.diff

# Analyze the diff for language-specific issues
# If SQL injection is found in src/db.py on line 42:
echo "Identified Critical Severity issue: SQL injection in src/db.py:42"
```

### 4. Decision Matrix

Based on issues found:

| Issue Severity | Action |
|----------------|--------|
| Critical security issue (hardcoded secrets, SQL injection, auth bypass) | `REQUEST_CHANGES` |
| Major bug (data loss, crash, incorrect logic) | `REQUEST_CHANGES` |
| Multiple moderate issues | `REQUEST_CHANGES` |
| Minor issues only (style, naming, small improvements) | `COMMENT` |
| No issues found | `APPROVE` (check Approval Policy below) |

#### Example Logic:
- **Scenario:** Found 1 hardcoded API key (Critical) and 1 minor documentation typo (Minor).
- **Action:** `REQUEST_CHANGES` because at least one issue is Critical/Major.

**Approval Policy:**
- **Single Reviewer (Only You):** If no issues are found, `APPROVE` by default.
- **Multiple Reviewers:** If other reviewers are assigned or have already added comments/reviews, do **NOT** `APPROVE` by default. Instead, use `COMMENT` even if no issues are found, unless the user explicitly instructed: "APPROVE the PR after review if no issues found".

**Permission Check:** You cannot request changes or approve your own PR. In these cases:
- Submit comments only (no formal review event)
- Add "APPROVED" or "REQUESTS CHANGES" text in the summary comment body

### 5. Comment Strategy

**Reviewer Pre-requisite:** Before adding any comments or submitting a review, check if you are already assigned as a reviewer using the `gh` cli. If you are not a reviewer of the PR yet, you MUST add yourself as an additional reviewer first. Refer to the `github` skill for how to execute these checks and edits.

**CRITICAL RULE: One issue = One comment**

**IMPORTANT: Use inline comments for ALL specific line issues**

**Order of operations:**
1. Post ALL inline comments first (one per specific line issue)
2. Then submit review with summary event (REQUEST_CHANGES/COMMENT/APPROVE)

- **Single issue in one location:** Add ONE inline comment at that line using the `gh` cli (refer to the `github` skill). Do NOT use general PR comments.
- **Same issue type in multiple locations:** Add separate inline comments for each location (each explains the specific instance).
- **General/cross-cutting concerns:** Add ONE summary comment at the PR level (only for issues that don't map to specific lines).

**DO NOT:**
- Add both an inline comment AND a summary comment for the same single issue
- Use general PR comments for issues on specific lines — these MUST be inline comments
- Duplicate the same feedback in multiple places
- Add inline comments when a single summary comment would suffice (e.g., "add tests" for the whole PR)
- Add duplicate comments if you or another reviewer has already added a comment on the same issue with a similar explanation

**Summary Comment:** Always add ONE summary comment at the end of the review with:
- Overall assessment
- List of issues found (with severity)
- Recommendation (approve/changes needed)
- Attribution

#### Example Execution Flow:
1. **Comment 1 (Inline):** `gh api repos/:owner/:repo/pulls/123/comments -f body="CRITICAL: Hardcoded secret.<br><small>(by code-reviewer)</small>" -f commit_id="abc1234" -f path="config.py" -f line=42 -f side="RIGHT"`
2. **Comment 2 (Inline):** `gh api repos/:owner/:repo/pulls/123/comments -f body="Minor: Typo in comment.<br><small>(by code-reviewer)</small>" -f commit_id="abc1234" -f path="main.py" -f line=10 -f side="RIGHT"`
3. **Submit Review (Final):** `gh pr review 123 --request-changes --body "Review complete. Found 1 critical security issue and 1 minor typo.<br><small>(by code-reviewer)</small>"`

### 6. Deliver Feedback

**CRITICAL MANDATE:** You MUST physically publish your feedback to the GitHub PR using the `gh` cli. **DO NOT** simply output the review details as a text response in the chat. This skill exists to automate the GitHub PR reviewing process.

**ALL comments MUST include attribution with separator:**

```

<small>(by code-reviewer)</small>
```

#### Inline Comments — PRIMARY METHOD

**Use this for ALL line-specific issues. Do NOT use general summary comments for these.**

**Inline comment format:**
- Be specific about the line/code in question
- Explain WHY it's an issue (security, performance, correctness)
- Provide a concrete suggested fix when possible
- Keep it concise - one paragraph + code example if needed

*(Refer to the `github` skill for instructions on posting inline comments using the `gh` cli)*

#### Summary Comments (PR review)

**Use ONLY for overall assessment after inline comments are posted. Do NOT use for line-specific issues.**

*(Refer to the `github` skill for instructions on submitting a review event using the `gh` cli)*

**Review events:**
- `REQUEST_CHANGES` - For critical/major issues (blocks merge)
- `COMMENT` - For minor issues or questions (doesn't block)
- `APPROVE` - When all issues are resolved or ready to merge

### 7. Comment Attribution Rules

**CRITICAL**: Every single comment must have attribution:

1. **Inline comments**: End with the separator
2. **Summary comments**: Include the separator at the end
3. **PR comments (fallback)**: Include the separator at the end

Format:
```markdown
[Your comment content]

<small>(by code-reviewer)</small>
```

### 8. Cleanup

**MANDATORY:** After completing the code review and posting all comments:
- Delete any temporary files created during the process (e.g. diff files, downloaded patches, standalone scripts used for analysis).
- Ensure the workspace is restored to a clean state.

#### Example:
```bash
rm /tmp/pr_123.diff /tmp/analysis_results.txt
```

## Examples

### Example 1: Single Security Issue (Correct)

**Scenario:** PR has one file with hardcoded API key on line 6.

**Actions:**
1. Fetch PR metadata and commits to get the commit SHA.
2. Add ONE inline comment on line 6 (refer to `github` skill for `gh` commands).
3. Submit review with `REQUEST_CHANGES` event and brief summary.
4. Summary lists the issue but doesn't duplicate the inline comment detail.

**WRONG:** Posting a general comment for a line-specific issue
**CORRECT:** Using inline comments mapping to the specific path and line parameters.

### Example 2: Multiple Issues in Same File (Correct)

**Scenario:** PR has one file with hardcoded key (line 6) and SQL injection (line 15).

**Actions:**
1. Add inline comment on line 6 for hardcoded key
2. Add inline comment on line 15 for SQL injection
3. Submit review with `REQUEST_CHANGES` and summary listing both issues

### Example 3: No Issues Found (Correct)

**Actions:**
1. Submit review with `APPROVE` event
2. Brief positive summary comment
