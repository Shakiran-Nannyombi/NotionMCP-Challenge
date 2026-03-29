# Testing the Notion Spec-to-Ship Pipeline

## Quick Test (No MCP Required)

The easiest way to test the pipeline is with the provided mock clients:

```bash
python3 scripts/test_pipeline.py
```

This runs the entire pipeline with mock Notion MCP and LLM clients, demonstrating:
- ✓ Idea extraction from Notion
- ✓ Spec generation via LLM
- ✓ Spec_DB creation in Notion
- ✓ Task execution via coding agent
- ✓ Status syncing back to Notion
- ✓ Structured JSON logging
- ✓ Run summary output

**Expected output:** All stages complete successfully with 3 tasks done, 0 failed.

## Unit Tests

Run the full test suite:

```bash
python3 -m pytest tests/ -v
```

**Expected:** 47 tests passing in ~0.1s

## Integration with Real Notion MCP

To test with actual Notion:

### 1. Configure Notion MCP in Kiro

Add to `.kiro/settings/mcp.json`:

```json
{
  "mcpServers": {
    "notion": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-notion"],
      "env": {
        "NOTION_API_KEY": "secret_your_key_here"
      }
    }
  }
}
```

### 2. Get Notion API Key

1. Go to https://www.notion.so/my-integrations
2. Click "New integration"
3. Name it "Spec-to-Ship Pipeline"
4. Copy the "Internal Integration Token"
5. Share your test pages with this integration

### 3. Create Test Page

In Notion:
1. Create a new page
2. Title: `[SHIP] Calculator App`
3. Content:
   ```
   Build a simple calculator that can add, subtract, multiply, and divide two numbers.
   It should have a command-line interface and validate inputs.
   ```
4. Share the page with your integration

### 4. Implement Real MCP Client

Update `orchestrator/notion_mcp_client.py` to call actual MCP tools.

**Example using Kiro's MCP interface:**

```python
def search(self, query: str, filter: dict) -> dict:
    # Call Notion MCP tool through Kiro
    result = kiro_mcp_client.call_tool("notion", "search", {
        "query": query,
        "filter": filter
    })
    return result
```

### 5. Run Pipeline

```python
from orchestrator.main import run_pipeline
from orchestrator.notion_mcp_client import NotionMCPClient

notion_client = NotionMCPClient()
run = run_pipeline("your-page-id-here", notion_client=notion_client)
```

## Testing with Kiro

The pipeline invokes Kiro to execute tasks. To test this:

### 1. Verify Kiro is Accessible

```bash
which kiro
# Should output: /path/to/kiro

kiro --version
# Should output version info
```

### 2. Test Task Execution

```python
from orchestrator.agent_driver import CodingAgentDriver
from orchestrator.models import Task

driver = CodingAgentDriver()
task = Task(
    order=1,
    title="Create hello.py",
    description="Create a Python file that prints 'Hello, World!'",
    acceptance_criteria="WHEN executed, THE SYSTEM SHALL print 'Hello, World!'"
)

result = driver.execute_task(task)
print(f"Success: {result.success}")
print(f"Output: {result.output}")
```

## Testing the Poller

Test the background polling loop:

```bash
# Start poller (Ctrl+C to stop)
python3 -m orchestrator run
```

The poller will:
1. Check Notion every 30 seconds
2. Detect pages with `[SHIP]` prefix
3. Spawn pipeline runs in background threads
4. Log all activity to stdout

## Monitoring Pipeline Runs

### Check Run Status

```bash
# Get status of a specific run
python3 -m orchestrator status <run-id>
```

### View State File

```bash
# Pretty-print state
cat test_state.json | python3 -m json.tool

# Or with jq
cat test_state.json | jq .
```

### Parse Structured Logs

```bash
# Filter logs by stage
cat pipeline.log | grep '"stage": "task_completed"' | jq .

# Count events by stage
cat pipeline.log | jq -r .stage | sort | uniq -c

# Find failed tasks
cat pipeline.log | grep '"outcome": "failure"' | jq .
```

## Common Issues

### "NOTION_MCP_URL environment variable not set"

Set the environment variable:
```bash
export NOTION_MCP_URL=http://localhost:3000
```

Or configure Notion MCP in Kiro's settings.

### "EmptyIdeaError: content is too short"

Ensure your Notion page has at least 10 characters of content.

### "SpecGenerationError: failed after 3 attempts"

Check:
- LLM API key is valid
- You have API credits/quota
- Network connectivity

### "TaskExecutionError: Failed to launch coding agent"

Check:
- Kiro is installed: `which kiro`
- Kiro is in PATH
- Kiro can be invoked: `kiro --version`

## Performance Benchmarks

With mock clients:
- Full pipeline: ~0.7s
- Idea extraction: ~0.001s
- Spec generation: ~0.001s (mock)
- Notion writes: ~0.7s (350ms delay × 3 tasks)
- Task execution: ~0.001s (mock)

With real clients (estimated):
- Full pipeline: ~30-60s
- Idea extraction: ~1-2s
- Spec generation: ~10-20s (LLM)
- Notion writes: ~5-10s
- Task execution: ~10-30s per task

## Next Steps

1. **Implement Real MCP Calls**: Replace mock methods in `NotionMCPClient`
2. **Add LLM Client**: Implement Anthropic or OpenAI client
3. **Test End-to-End**: Run full pipeline with real Notion page
4. **Add Error Scenarios**: Test with invalid inputs, API failures, etc.
5. **Load Testing**: Test with multiple concurrent pipeline runs
6. **Property Tests**: Implement optional property-based tests from spec

## Demo Preparation

For the hackathon demo, test this flow:

1. ✓ Unit tests pass
2. ✓ Mock pipeline runs successfully
3. ✓ Notion MCP configured in Kiro
4. ✓ Test page created with `[SHIP]` prefix
5. ✓ Poller detects and processes page
6. ✓ Spec_DB created in Notion
7. ✓ Tasks written to database
8. ✓ Kiro executes tasks
9. ✓ Status syncs back to Notion
10. ✓ Completion summary appears

**Pro tip:** Run through the entire flow at least once before the demo to catch any issues!
