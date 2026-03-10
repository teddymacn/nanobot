---
name: receiving-code-review
description: >
  Use when receiving code review feedback, implementing fixes, and responding to reviewer comments.
  All responses are attributed with "<br><small>(by receiving-code-review)</small>" suffix.
  Handles inline comment replies, code fixes, and PR updates via gh CLI.
  Use after "code-reviewer" has reviewed your PR or code.
  Trigger patterns: "fix the issues in PR #X", "address review comments", "respond to reviewer", "implement requested changes", PR URLs with review feedback.
---

# Code Review Reception

## Overview

Code review requires technical evaluation, not emotional performance.

**Core principle:** Verify before implementing. Ask before assuming. Technical correctness over social compliance.

**All responses MUST end with:** `<br><small>(by receiving-code-review)</small>`

## Workflow

### 1. Read and Categorize Review Comments

Fetch all review comments and categorize them:

```bash
# Get all inline comments on PR
gh api /repos/${owner}/${repo}/pulls/${pull_number}/comments

# Get all review summaries
gh api /repos/${owner}/${repo}/pulls/${pull_number}/reviews
```

**Categorize each comment:**
- **Critical**: Security issues, bugs, correctness problems (must fix)
- **Major**: Performance, maintainability, significant improvements (should fix)
- **Minor**: Style, naming, nice-to-have enhancements (optional)
- **Question**: Reviewer asking for clarification (respond)
- **Disagreement**: You believe the comment is incorrect (discuss)

**Identify comment source:**
- Comments ending with `<br><small>(by code-reviewer)</small>` are from the reviewer skill
- Comments ending with `<br><small>(by receiving-code-review)</small>` are your previous responses
- Comments without attribution need clarification

### 2. Respond to Each Comment

#### For Inline Comments - Reply Directly

```bash
# Reply to an inline comment
gh api \
  -X POST \
  /repos/${owner}/${repo}/pulls/${pull_number}/comments \
  -F body="Your response explaining fix or reasoning <br><small>(by receiving-code-review)</small>" \
  -F in_reply_to=${comment_id}
```

**Response templates:**

**When fixing the issue:**
```markdown
Good catch! This is indeed a [security/performance/correctness] issue. 

Fixed in commit ${commit_sha} by [brief description of fix].

<br><small>(by receiving-code-review)</small>
```

**When disagreeing (with explanation):**
```markdown
I understand the concern, but here's why this approach is intentional:

[Technical explanation with reasoning]

That said, I've added a comment to clarify this for future readers. Happy to discuss further if you have concerns.

<br><small>(by receiving-code-review)</small>
```

**When more discussion is needed:**
```markdown
This is a good point. I'm considering two approaches:

1. [Option A] - Pros/Cons
2. [Option B] - Pros/Cons

Which do you think fits better with the codebase patterns?

<br><small>(by receiving-code-review)</small>
```

**When the issue is already fixed:**
```markdown
This was addressed in commit ${commit_sha} - can you verify the fix addresses your concern?

<br><small>(by receiving-code-review)</small>
```

### 3. Implement Code Fixes

**For each fixable issue:**

1. **Make the change** in your local codebase
2. **Test thoroughly** - ensure the fix works and doesn't break existing functionality
3. **Write/update tests** if the fix affects testable behavior
4. **Commit with clear message**:
   ```bash
   git add .
   git commit -m "fix: address code review - [brief description]
   
   - [Specific issue addressed]
   - [How it was fixed]
   
   Response to code-reviewer comment on [file:line]"
   git push origin ${branch_name}
   ```

### 4. Update PR with Fixes

After pushing fixes:

```bash
# Add a summary comment on the PR
gh api \
  -X POST \
  /repos/${owner}/${repo}/issues/${pull_number}/comments \
  -F body="## Code Review Fixes Completed

### Addressed Issues
- [x] [Issue 1] - Fixed in commit ${sha}
- [x] [Issue 2] - Fixed in commit ${sha}
- [ ] [Issue 3] - See response inline (disagreement/discussion)

### Summary
[Brief summary of changes made]

Ready for re-review.

<br><small>(by receiving-code-review)</small>"
```

### 5. Request Re-Review

```bash
# Re-request review from reviewer
gh api \
  -X POST \
  /repos/${owner}/${repo}/pulls/${pull_number}/requested_reviewers \
  -F reviewers='["${reviewer_username}"]'

# Or add a comment tagging the reviewer
gh api \
  -X POST \
  /repos/${owner}/${repo}/issues/${pull_number}/comments \
  -F body="@${reviewer_username} Ready for re-review when you have time. <br><small>(by receiving-code-review)</small>"
```

## Handling Different Comment Types

### Security Issues (ALWAYS FIX)
- SQL injection risks
- XSS vulnerabilities
- Authentication/authorization gaps
- Secret exposure
- Unsafe deserialization

**Response:** Fix immediately, no debate on security.

### Performance Issues (USUALLY FIX)
- N+1 queries
- O(n²) algorithms on large datasets
- Missing indexes
- Memory leaks

**Response:** Fix if impact is significant. Discuss if trade-off is intentional.

### Code Quality Issues (OFTEN FIX)
- Unclear naming
- Long functions
- Missing tests
- Inconsistent patterns

**Response:** Fix most of them. Discuss if there's a good reason for deviation.

### Style Preferences (DISCUSS IF NEEDED)
- Formatting opinions
- Architectural preferences
- Library choices (if working)

**Response:** Be open to feedback, but push back if you have strong technical reasons.

### Factual Errors in Review (CORRECT POLITELY)
- Reviewer misunderstood the code
- Reviewer's suggestion would break things
- Reviewer's technical claim is incorrect

**Response:**
```markdown
I think there might be a misunderstanding here. [Explain what the code actually does]

Your suggestion would [explain the problem]. Instead, I've [alternative approach].

Let me know if I'm missing something in your concern.

<small>(by receiving-code-review)</small>
```

## Comment Attribution System

**CRITICAL**: Every single response must have attribution:

1. **All inline replies**: End with `<br><small>(by receiving-code-review)</small>`
2. **All PR comments**: End with `<br><small>(by receiving-code-review)</small>`
3. **All review responses**: End with `<br><small>(by receiving-code-review)</small>`

**Recognizing comment sources:**
| Suffix | Source | How to respond |
|--------|--------|----------------|
| `<br><small>(by code-reviewer)</small>` | Reviewer skill | Address the issue or discuss |
| `<br><small>(by receiving-code-review)</small>` | Your previous comment | No action needed (your own comment) |
| No suffix | Unknown/manual comment | Treat as reviewer feedback |

## Iteration Loop

```
1. Receive review from code-reviewer
2. Categorize all comments
3. For each comment:
   - If valid: Fix code → Commit → Push
   - If needs discussion: Reply inline with explanation
   - If unclear: Ask for clarification
4. Push all fixes
5. Add summary comment
6. Request re-review
7. Repeat until code-reviewer approves
```

## GitHub CLI Quick Reference

### Reply to Inline Comment
```bash
gh api \
  -X POST \
  /repos/${owner}/${repo}/pulls/${pull_number}/comments \
  -F body="Response text <br><small>(by receiving-code-review)</small>" \
  -F in_reply_to=${comment_id}
```

### Add PR Comment
```bash
gh api \
  -X POST \
  /repos/${owner}/${repo}/issues/${pull_number}/comments \
  -F body="Comment text <br><small>(by receiving-code-review)</small>"
```

### Push Fixes
```bash
git add .
git commit -m "fix: address code review feedback"
git push origin ${branch_name}
```

### Request Re-Review
```bash
gh pr edit ${pull_number} --add-reviewer ${reviewer}
```

### Get Comment Thread
```bash
gh api /repos/${owner}/${repo}/pulls/${pull_number}/comments \
  | jq '.[] | select(.in_reply_to == null or .in_reply_to == ${comment_id})'
```

## Example: Full Review Response Flow

### Step 1: Fetch Comments
```bash
comments=$(gh api /repos/myorg/myrepo/pulls/42/comments)
```

### Step 2: Process Each Comment
```markdown
Comment 1 (line 23, auth.py): "Missing input validation on user_id" <br><small>(by code-reviewer)</small>
→ Action: Fix by adding validation
→ Response: "Fixed - added validation for user_id format and range <br><small>(by receiving-code-review)</small>"

Comment 2 (line 45, db.py): "SQL injection risk with f-string" <br><small>(by code-reviewer)</small>
→ Action: CRITICAL - Fix immediately with parameterized query
→ Response: "Good catch - switched to parameterized query <br><small>(by receiving-code-review)</small>"

Comment 3 (line 67, utils.py): "Why is this async?" <br><small>(by code-reviewer)</small>
→ Action: Explain reasoning
→ Response: "This is async to handle concurrent I/O operations. Added comment to clarify <br><small>(by receiving-code-review)</small>"
```

### Step 3: Commit and Push
```bash
git add .
git commit -m "fix: address code review feedback

- Add input validation for user_id (auth.py)
- Fix SQL injection vulnerability (db.py)
- Add clarifying comment on async function (utils.py)"
git push origin feature/my-feature
```

### Step 4: Summary Comment
```markdown
## Code Review Fixes Completed

### Addressed Issues
- [x] Missing input validation - Fixed in commit abc123
- [x] SQL injection risk - Fixed in commit abc123
- [x] Async function clarity - Added comment in commit abc123

All critical and major issues have been addressed. Ready for re-review.

<small>(by receiving-code-review)</small>
```

### Step 5: Request Re-Review
```bash
gh pr edit 42 --add-reviewer code-reviewer-bot
```

## Final Checklist

Before marking review as complete:
- [ ] All comments have `<br><small>(by receiving-code-review)</small>` attribution
- [ ] Critical issues are fixed
- [ ] Major issues are fixed or discussed
- [ ] Minor issues are addressed or consciously deferred
- [ ] All responses are technically accurate
- [ ] Code is tested after fixes
- [ ] Commits are clear and atomic
- [ ] Re-review is requested

---
**Remember**: Code review is a dialogue, not a verdict. Engage thoughtfully, fix genuinely, and push back respectfully when needed. <br><small>(by receiving-code-review)</small>
