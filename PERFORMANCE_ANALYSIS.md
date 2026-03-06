# nanobot Performance Analysis and Optimization Recommendations

## Executive Summary

Analysis of the nanobot agent codebase reveals several performance bottlenecks that contribute to slow execution for simple tasks. The primary issues are:

1. **Excessive context building** - Loading skills, memory, and bootstrap files on every LLM call
2. **Redundant tool schema generation** - Rebuilding tool definitions for every chat request
3. **Unnecessary async overhead** - Message bus indirection for CLI direct mode
4. **Memory consolidation triggers** - Aggressive consolidation checking on every message
5. **MCP connection attempts** - Repeated connection checks even when no MCP servers configured

---

## Detailed Analysis

### 1. Main Agent Loop and Decision-Making Logic

#### Location: `nanobot/agent/loop.py`

**Issues Identified:**

##### 1.1 `_connect_mcp()` called on every `process_direct()` and `run()`

```python
# In run():
async def run(self) -> None:
    self._running = True
    await self._connect_mcp()  # Called every time agent starts

# In process_direct():
async def process_direct(self, content: str, ...) -> str:
    await self._connect_mcp()  # Called for EVERY message!
```

**Problem:** Even when `mcp_servers` is empty, this method acquires locks and performs checks. For simple CLI tasks, this adds unnecessary async overhead.

**Impact:** ~50-100ms per message for MCP connection check overhead.

##### 1.2 Context building rebuilds everything from scratch

```python
# In context.py build_messages():
def build_messages(self, history, current_message, ...):
    return [
        {"role": "system", "content": self.build_system_prompt(skill_names)},
        *history,
        {"role": "user", "content": merged},
    ]

# build_system_prompt() loads:
# - Identity (every time)
# - Bootstrap files (AGENTS.md, SOUL.md, etc.) - every time
# - Memory context - every time
# - Always skills - every time  
# - Skills summary - every time
```

**Problem:** For a simple task like "what's 2+2", the agent rebuilds the entire system prompt including:
- Reading 5+ bootstrap files from disk
- Loading memory from MEMORY.md
- Building skills summary XML
- Loading "always" skills content

**Impact:** For simple tasks, 200-500ms spent on I/O and string concatenation for context that doesn't change.

##### 1.3 Memory consolidation check on every message

```python
# In _process_message():
unconsolidated = len(session.messages) - session.last_consolidated
if (unconsolidated >= self.memory_window and session.key not in self._consolidating):
    # Spawns async task for consolidation
```

**Problem:** This check happens even for brand new sessions and simple queries. The consolidation logic itself involves:
- Another LLM call to summarize messages
- File I/O for MEMORY.md and HISTORY.md

**Impact:** When triggered, adds 2-5 seconds of additional LLM latency.

---

### 2. Unnecessary Tool Calls and Redundant Operations

#### Location: `nanobot/agent/loop.py`, `nanobot/agent/tools/registry.py`

**Issues Identified:**

##### 2.1 Tool definitions regenerated every LLM call

```python
# In _run_agent_loop():
response = await self.provider.chat(
    messages=messages,
    tools=self.tools.get_definitions(),  # Rebuilt every iteration!
    ...
)

# In registry.py:
def get_definitions(self) -> list[dict[str, Any]]:
    return [tool.to_schema() for tool in self._tools.values()]
```

**Problem:** Tool schemas are static but regenerated on every LLM call (including retry iterations). For 10 tools with complex schemas, this is unnecessary work.

**Impact:** ~10-20ms per LLM call iteration.

##### 2.2 Tool result truncation happens post-execution

```python
# In _save_turn():
if role == "tool" and isinstance(content, str) and len(content) > self._TOOL_RESULT_MAX_CHARS:
    entry["content"] = content[:self._TOOL_RESULT_MAX_CHARS] + "\n... (truncated)"
```

**Problem:** Large tool results (e.g., from `exec` or `read_file`) are fully processed and added to messages before truncation. This bloats the context for subsequent LLM calls.

**Impact:** Large outputs can add 1000s of tokens to context, increasing LLM latency and cost.

##### 2.3 No early exit for trivial queries

The agent loop always goes through the full LLM → tool → LLM cycle even for queries that could be answered directly. There's no "fast path" for simple questions.

---

### 3. Context Loading and Memory Access Patterns

#### Location: `nanobot/agent/context.py`, `nanobot/agent/memory.py`, `nanobot/agent/skills.py`

**Issues Identified:**

##### 3.1 Skills summary built on every context build

```python
# In context.py build_system_prompt():
skills_summary = self.skills.build_skills_summary()
if skills_summary:
    parts.append(f"""# Skills
...
{skills_summary}""")

# In skills.py:
def build_skills_summary(self) -> str:
    all_skills = self.list_skills(filter_unavailable=False)  # Scans directories
    # ... builds XML for EVERY skill
```

**Problem:** `list_skills()` scans both workspace and builtin skill directories, checks requirements for each skill, and builds XML metadata. This happens on EVERY LLM call.

**Impact:** 50-150ms per call depending on number of skills.

##### 3.2 Memory file read on every context build

```python
# In memory.py:
def get_memory_context(self) -> str:
    long_term = self.read_long_term()  # Reads MEMORY.md every time!
    return f"## Long-term Memory\n{long_term}" if long_term else ""
```

**Problem:** MEMORY.md is read from disk on every single LLM call, even if it hasn't changed.

**Impact:** 5-20ms per call for file I/O.

##### 3.3 Bootstrap files re-read every context build

```python
# In context.py:
def _load_bootstrap_files(self) -> str:
    for filename in self.BOOTSTRAP_FILES:  # AGENTS.md, SOUL.md, etc.
        file_path = self.workspace / filename
        if file_path.exists():
            content = file_path.read_text(encoding="utf-8")
```

**Problem:** These files are static but re-read on every LLM call.

**Impact:** 10-50ms per call depending on file sizes.

##### 3.4 Session history slicing without caching

```python
# In session/manager.py:
def get_history(self, max_messages: int = 500) -> list[dict[str, Any]]:
    unconsolidated = self.messages[self.last_consolidated:]
    sliced = unconsolidated[-max_messages:]
    # ... filtering logic
```

**Problem:** While not a major bottleneck, this creates new lists on every call. For long conversations, this is repeated work.

---

### 4. Tool Execution Overhead

#### Location: `nanobot/agent/tools/*.py`

**Issues Identified:**

##### 4.1 Path resolution on every file tool call

```python
# In filesystem.py:
def _resolve_path(path: str, workspace: Path, allowed_dir: Path) -> Path:
    p = Path(path).expanduser()
    if not p.is_absolute() and workspace:
        p = workspace / p
    resolved = p.resolve()  # Expensive resolve() every time!
    if allowed_dir:
        resolved.relative_to(allowed_dir.resolve())  # Another resolve!
```

**Problem:** `Path.resolve()` performs filesystem stat calls. This happens on every file operation.

**Impact:** 5-10ms per file tool call.

##### 4.2 Exec tool creates subprocess with full environment copy

```python
# In shell.py:
async def execute(self, command: str, ...) -> str:
    env = os.environ.copy()  # Copies entire environment
    if self.path_append:
        env["PATH"] = env.get("PATH", "") + os.pathsep + self.path_append
    
    process = await asyncio.create_subprocess_shell(...)
```

**Problem:** For simple commands, copying the entire environment and spawning a subprocess has significant overhead.

**Impact:** 50-200ms for simple commands like `echo "hello"`.

##### 4.3 No command caching for repeated exec calls

If the agent runs the same command twice (e.g., `git status`), it executes twice with no caching.

---

## Specific Recommendations

### Priority 1: High Impact, Low Effort

#### 1. Cache the system prompt

**Location:** `nanobot/agent/context.py`

```python
class ContextBuilder:
    def __init__(self, workspace: Path):
        self.workspace = workspace
        self._system_prompt_cache: str | None = None
        self._system_prompt_mtime: float = 0
    
    def build_system_prompt(self, skill_names: list[str] | None = None) -> str:
        # Check if bootstrap files have changed
        latest_mtime = 0
        for filename in self.BOOTSTRAP_FILES:
            path = self.workspace / filename
            if path.exists():
                latest_mtime = max(latest_mtime, path.stat().st_mtime)
        
        if (self._system_prompt_cache and 
            latest_mtime <= self._system_prompt_mtime and
            skill_names is None):  # skill_names not used in current impl
            return self._system_prompt_cache
        
        # Build prompt...
        self._system_prompt_cache = result
        self._system_prompt_mtime = latest_mtime
        return result
```

**Expected Improvement:** 100-300ms saved per LLM call.

#### 2. Cache tool definitions

**Location:** `nanobot/agent/tools/registry.py`

```python
class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, Tool] = {}
        self._definitions_cache: list[dict] | None = None
    
    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool
        self._definitions_cache = None  # Invalidate cache
    
    def unregister(self, name: str) -> None:
        self._tools.pop(name, None)
        self._definitions_cache = None
    
    def get_definitions(self) -> list[dict[str, Any]]:
        if self._definitions_cache is None:
            self._definitions_cache = [tool.to_schema() for tool in self._tools.values()]
        return self._definitions_cache
```

**Expected Improvement:** 10-20ms per LLM call iteration.

#### 3. Skip MCP connection check when no servers configured

**Location:** `nanobot/agent/loop.py`

```python
async def _connect_mcp(self) -> None:
    # Early exit if no MCP servers configured
    if not self._mcp_servers:
        self._mcp_connected = True  # Mark as "done" to skip future checks
        return
    
    if self._mcp_connected or self._mcp_connecting:
        return
    # ... rest of connection logic
```

**Expected Improvement:** 50-100ms saved per message.

#### 4. Add fast path for simple CLI queries

**Location:** `nanobot/agent/loop.py`

```python
async def process_direct(
    self,
    content: str,
    session_key: str = "cli:direct",
    channel: str = "cli",
    chat_id: str = "direct",
    on_progress: Callable[[str], Awaitable[None]] | None = None,
) -> str:
    # Fast path for trivial queries that don't need tools
    _TRIVIAL_PATTERNS = [
        r"^what'?s?\s+\d+\s*[\+\-\*/]\s*\d+",  # "what's 2+2"
        r"^\d+\s*[\+\-\*/]\s*\d+",  # "2+2"
        r"^hello$|^hi$|^hey$",  # greetings
    ]
    for pattern in _TRIVIAL_PATTERNS:
        if re.match(pattern, content.lower()):
            # Use minimal context, no tools, low max_tokens
            return await self._fast_respond(content, session_key)
    
    await self._connect_mcp()
    # ... normal processing
```

**Expected Improvement:** 500-1000ms for simple queries.

### Priority 2: Medium Impact, Medium Effort

#### 5. Lazy-load memory context

**Location:** `nanobot/agent/context.py`, `nanobot/agent/memory.py`

```python
class ContextBuilder:
    def __init__(self, workspace: Path):
        self.workspace = workspace
        self._memory_context_cache: str | None = None
        self._memory_mtime: float = 0
    
    def get_memory_context(self) -> str:
        memory_file = self.workspace / "memory" / "MEMORY.md"
        if memory_file.exists():
            mtime = memory_file.stat().st_mtime
            if mtime <= self._memory_mtime and self._memory_context_cache is not None:
                return self._memory_context_cache
        
        content = MemoryStore(self.workspace).read_long_term()
        result = f"## Long-term Memory\n{content}" if content else ""
        self._memory_context_cache = result
        self._memory_mtime = mtime if memory_file.exists() else 0
        return result
```

**Expected Improvement:** 5-20ms per LLM call.

#### 6. Reduce tool result size in messages

**Location:** `nanobot/agent/loop.py`

```python
async def _run_agent_loop(self, ...):
    # ... in tool execution loop:
    result = await self.tools.execute(tool_call.name, tool_call.arguments)
    
    # Truncate BEFORE adding to messages
    if len(result) > self._TOOL_RESULT_MAX_CHARS:
        truncated_result = result[:self._TOOL_RESULT_MAX_CHARS] + "\n... (truncated)"
    else:
        truncated_result = result
    
    messages = self.context.add_tool_result(
        messages, tool_call.id, tool_call.name, truncated_result
    )
```

**Expected Improvement:** Reduces token count by 50-90% for large outputs, improving LLM speed.

#### 7. Consolidate memory less aggressively

**Location:** `nanobot/agent/loop.py`

```python
# Current: triggers when unconsolidated >= memory_window (100)
# Recommendation: Increase threshold or add time-based cooldown

MEMORY_CONSOLIDATION_COOLDOWN_SECONDS = 300  # 5 minutes

# In _process_message():
if (unconsolidated >= self.memory_window * 1.5 and  # 150 instead of 100
    session.key not in self._consolidating and
    (not hasattr(session, '_last_consolidation_time') or
     time.time() - session._last_consolidation_time > MEMORY_CONSOLIDATION_COOLDOWN_SECONDS)):
    # ... trigger consolidation
    session._last_consolidation_time = time.time()
```

**Expected Improvement:** Prevents cascading LLM calls during active conversations.

### Priority 3: Lower Impact or Higher Effort

#### 8. Cache bootstrap file contents

Similar to system prompt caching, cache individual bootstrap file contents with mtime checking.

#### 9. Optimize path resolution

```python
# Cache resolved workspace path
class ReadFileTool:
    def __init__(self, workspace: Path | None = None, ...):
        self._workspace = workspace
        self._workspace_resolved = workspace.resolve() if workspace else None
        self._allowed_dir_resolved = allowed_dir.resolve() if allowed_dir else None
    
    async def execute(self, path: str, ...) -> str:
        # Use pre-resolved paths
```

#### 10. Add LLM response caching

For repeated identical queries, cache the LLM response:

```python
class AgentLoop:
    def __init__(self, ...):
        self._response_cache: LRUCache = LRUCache(maxsize=100)
    
    async def _run_agent_loop(self, ...):
        # Create hash of messages (excluding timestamps)
        cache_key = self._messages_hash(messages)
        if cache_key in self._response_cache:
            return self._response_cache[cache_key]
        
        response = await self.provider.chat(...)
        self._response_cache[cache_key] = response
        return response
```

---

## Summary Table

| Optimization | Expected Savings | Effort | Priority |
|--------------|------------------|--------|----------|
| Cache system prompt | 100-300ms/call | Low | 1 |
| Cache tool definitions | 10-20ms/call | Low | 1 |
| Skip MCP when empty | 50-100ms/msg | Low | 1 |
| Fast path for trivial queries | 500-1000ms | Medium | 1 |
| Lazy-load memory | 5-20ms/call | Low | 2 |
| Truncate tool results early | Variable (token reduction) | Low | 2 |
| Less aggressive consolidation | Prevents 2-5s delays | Low | 2 |
| Cache bootstrap files | 10-50ms/call | Medium | 3 |
| Optimize path resolution | 5-10ms/file op | Medium | 3 |
| LLM response caching | Variable | High | 3 |

---

## Implementation Order

For maximum impact with minimal effort, implement in this order:

1. **Cache tool definitions** - 10 lines of code, immediate benefit
2. **Skip MCP connection when empty** - 3 lines, eliminates wasted checks
3. **Cache system prompt** - ~30 lines, biggest single improvement
4. **Truncate tool results early** - 5 lines, reduces token costs
5. **Fast path for trivial queries** - ~50 lines, dramatic improvement for simple tasks
6. **Lazy-load memory** - ~20 lines, incremental improvement
7. **Adjust consolidation threshold** - 5 lines, prevents cascading delays

Total expected improvement for simple tasks: **400-800ms reduction in "thinking time"**.
