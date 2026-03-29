# Notion Spec-to-Ship Pipeline - Setup Guide

This guide explains how to set up and test the pipeline with Notion MCP and Kiro.

## Architecture Overview

```
┌─────────────────┐
│  Notion Pages   │ ← User writes ideas here
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Notion MCP     │ ← MCP server provides Notion API access
│    Server       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Orchestrator   │ ← This Python pipeline
│   (main.py)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Kiro Agent     │ ← Executes implementation tasks
└─────────────────┘
```

## Prerequisites

1. **Python 3.11+** installed
2. **Notion account** with API access
3. **Notion MCP server** configured in Kiro
4. **Kiro** installed and configured
5. **LLM API key** (Anthropic Claude or OpenAI)

## Step 1: Install Dependencies

```bash
# Install Python dependencies
pip install -e .

# Or with dev dependencies
pip install -e ".[dev]"
```

## Step 2: Configure Notion MCP in Kiro

The Notion MCP server needs to be configured in Kiro's MCP settings.

### Option A: Using Kiro's MCP Configuration UI

1. Open Kiro
2. Open Command Palette (Cmd/Ctrl + Shift + P)
3. Search for "MCP: Configure Servers"
4. Add the Notion MCP server configuration

### Option B: Manual Configuration

Create or edit `.kiro/settings/mcp.json`:

```json
{
  "mcpServers": {
    "notion": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-notion"],
      "env": {
        "NOTION_API_KEY": "your-notion-integration-token-here"
      }
    }
  }
}
```

**Getting your Notion API key:**
1. Go to https://www.notion.so/my-integrations
2. Create a new integration
3. Copy the "Internal Integration Token"
4. Share your Notion pages with the integration

## Step 3: Set Up Environment Variables

Create a `.env` file in the project root:

```bash
# Notion MCP (if not using Kiro's MCP config)
NOTION_MCP_URL=http://localhost:3000

# LLM API Key (choose one)
ANTHROPIC_API_KEY=your-anthropic-key-here
# OR
OPENAI_API_KEY=your-openai-key-here

# Optional: Custom state file location
STATE_FILE=state.json
```

## Step 4: Connect the MCP Client

The orchestrator needs to communicate with Notion via MCP. There are two approaches:

### Approach A: Direct MCP Tool Calls (Recommended for Kiro Integration)

If running inside Kiro, the orchestrator can call MCP tools directly through Kiro's MCP interface.

Update `orchestrator/main.py` to use Kiro's MCP client:

```python
def _default_notion_client() -> Any:
    """Return a Notion MCP client."""
    from orchestrator.notion_mcp_client import NotionMCPClient
    return NotionMCPClient()
```

### Approach B: Standalone MCP Server

If running standalone, you need to start the Notion MCP server separately:

```bash
# Start Notion MCP server
npx -y @modelcontextprotocol/server-notion
```

Then implement the actual MCP calls in `orchestrator/notion_mcp_client.py`.

## Step 5: Test the Pipeline

### Test 1: Unit Tests

```bash
# Run all unit tests
python3 -m pytest tests/ -v

# Expected output: 47 tests passing
```

### Test 2: Manual Pipeline Test

Create a test Notion page:

1. Create a new page in Notion
2. Add the title: `[SHIP] Test Idea`
3. Add some content (at least 10 characters):
   ```
   Build a simple calculator app that can add, subtract, multiply, and divide two numbers.
   ```

Run the pipeline manually:

```python
from orchestrator.main import run_pipeline
from orchestrator.notion_mcp_client import NotionMCPClient

# Initialize clients
notion_client = NotionMCPClient()

# Mock LLM client for testing
class MockLLMClient:
    def complete(self, system_prompt, user_prompt, temperature, timeout):
        return '''
        {
          "introduction": "A simple calculator application",
          "requirements": [
            {
              "id": "R1",
              "title": "Basic arithmetic operations",
              "user_story": "As a user, I want to perform basic math operations",
              "acceptance_criteria": [
                "WHEN the user enters two numbers and selects add, THE SYSTEM SHALL return the sum",
                "WHEN the user enters two numbers and selects subtract, THE SYSTEM SHALL return the difference"
              ]
            }
          ],
          "tasks": [
            {
              "order": 1,
              "title": "Create calculator function",
              "description": "Implement add, subtract, multiply, divide functions",
              "acceptance_criteria": "WHEN called with two numbers, THE SYSTEM SHALL return the correct result"
            }
          ]
        }
        '''

llm_client = MockLLMClient()

# Run pipeline
run = run_pipeline(
    "your-notion-page-id-here",
    notion_client=notion_client,
    llm_client=llm_client
)

print(f"Pipeline run completed: {run.run_id}")
print(f"Status: {run.status}")
```

### Test 3: Poller Loop

Start the background poller:

```bash
python3 -m orchestrator run
```

This will:
1. Poll Notion every 30 seconds
2. Detect pages with `[SHIP]` prefix or `pipeline_trigger = true`
3. Spawn a pipeline run for each new page
4. Execute tasks via Kiro

Press Ctrl+C to stop.

## Step 6: Integration with Kiro

The orchestrator calls Kiro to execute tasks via `CodingAgentDriver`. The current implementation uses subprocess:

```python
# In orchestrator/agent_driver.py
subprocess.run(["kiro", temp_file_path], ...)
```

### Making Kiro Accessible

Ensure Kiro is in your PATH:

```bash
# Check if Kiro is accessible
which kiro

# If not, add Kiro to PATH or use full path
export PATH="/path/to/kiro:$PATH"
```

### Alternative: MCP-based Task Execution

Instead of subprocess, you could invoke Kiro via MCP if Kiro exposes task execution as an MCP tool.

## Troubleshooting

### Issue: "NOTION_MCP_URL environment variable not set"

**Solution:** Set the environment variable or configure Notion MCP in Kiro's settings.

### Issue: "MCP connection failed"

**Solution:** 
1. Verify Notion MCP server is running
2. Check your Notion API key is valid
3. Ensure pages are shared with your integration

### Issue: "EmptyIdeaError"

**Solution:** Ensure your Notion page has at least 10 characters of content.

### Issue: "SpecGenerationError"

**Solution:**
1. Check your LLM API key is valid
2. Verify you have API credits/quota
3. Check network connectivity

### Issue: "TaskExecutionError"

**Solution:**
1. Verify Kiro is installed and in PATH
2. Check Kiro can be invoked: `kiro --version`
3. Review task execution logs

## Monitoring

### View Pipeline Status

```bash
# Get status of a specific run
python3 -m orchestrator status <run-id>
```

### View Structured Logs

All pipeline events are logged as JSON to stdout:

```bash
# Run pipeline and save logs
python3 -m orchestrator run 2>&1 | tee pipeline.log

# Parse logs with jq
cat pipeline.log | grep '{"run_id"' | jq .
```

### Check State File

```bash
# View current state
cat state.json | jq .

# View active runs
cat state.json | jq '.active_runs'

# View seen pages
cat state.json | jq '.seen_pages'
```

## Next Steps

1. **Implement Real MCP Calls**: Replace the stub methods in `NotionMCPClient` with actual MCP tool calls
2. **Add LLM Client**: Implement a real LLM client (Anthropic or OpenAI)
3. **Configure Kiro Integration**: Set up proper Kiro invocation for task execution
4. **Add Property Tests**: Implement the optional property-based tests from the spec
5. **Production Deployment**: Set up proper error monitoring, logging, and alerting

## Demo Checklist

For the hackathon demo:

- [ ] Notion integration created and API key obtained
- [ ] Notion MCP server configured in Kiro
- [ ] Test Notion page created with `[SHIP]` prefix
- [ ] Environment variables set (.env file)
- [ ] Dependencies installed (`pip install -e .`)
- [ ] Unit tests passing (`pytest tests/`)
- [ ] Poller running (`python3 -m orchestrator run`)
- [ ] Kiro accessible and configured
- [ ] LLM API key valid and has quota
- [ ] Demo page ready with a clear, simple idea

## Architecture Notes

### Why MCP?

The Model Context Protocol (MCP) provides a standardized way for AI agents to interact with external tools and data sources. Using MCP for Notion access means:

1. **Standardized Interface**: The orchestrator doesn't need to know Notion API details
2. **Kiro Integration**: Kiro can manage MCP servers and provide them to the orchestrator
3. **Testability**: Easy to mock MCP calls for testing
4. **Extensibility**: Can add other MCP servers (GitHub, Slack, etc.) without changing orchestrator code

### Pipeline Flow

1. **Poller** detects new Notion pages (30s interval)
2. **Extractor** recursively fetches all block content
3. **SpecGenerator** calls LLM to produce structured spec
4. **NotionWriter** creates Spec_DB and writes task rows
5. **AgentDriver** invokes Kiro for each task
6. **StatusSyncer** updates Notion with task status
7. **Logger** emits structured JSON for observability

### Error Handling Strategy

- **Retry with backoff**: All external calls (Notion, LLM) retry 3x with exponential backoff
- **Failure isolation**: Task failures don't halt the pipeline
- **Early returns**: Critical failures (empty idea, spec generation) return early
- **Best-effort writes**: Non-critical Notion writes (spec blocks, completion) don't halt on failure
- **Structured logging**: All errors logged with context for debugging
