# Notion Integration Setup

Your pipeline is now configured to connect to Notion! Here's how to set it up and test it.

## What's Configured

✅ **Notion API Client** (`orchestrator/notion_mcp_client.py`)
- Uses official Notion Python SDK (`notion-client`)
- Implements all required methods for the pipeline
- Automatic connection testing

✅ **Kiro MCP Configuration** (`.kiro/settings/mcp.json`)
- Configured to use Notion's hosted MCP server
- URL: `https://mcp.notion.com/mcp`
- OAuth authentication through Kiro

✅ **Environment** (`.env`)
- Your Notion API key is configured
- Ready for standalone Python testing

## Two Ways to Use Notion

### Option 1: Through Kiro (Recommended for Task Execution)

This uses Notion's hosted MCP server through Kiro's MCP integration.

**Setup:**

1. **Authenticate with Notion MCP in Kiro:**
   - Open Kiro
   - Run command: `/mcp` 
   - Follow the OAuth flow to connect your Notion workspace
   - This gives Kiro access to read/write your Notion pages

2. **Verify Connection:**
   - In Kiro, you should see "notion" listed as a connected MCP server
   - The MCP server will have access to your entire Notion workspace

**When to use:**
- When running the full pipeline with Kiro task execution
- When you want Kiro to execute tasks and update Notion automatically

### Option 2: Direct API (For Testing & Development)

This uses the Notion API directly through Python for testing the pipeline.

**Setup:**

1. **Create a Notion Integration:**
   - Go to https://www.notion.so/my-integrations
   - Click "New integration"
   - Name it (e.g., "Spec-to-Ship Pipeline")
   - Copy the API key (starts with `ntn_`)
   - Already configured in your `.env` file

2. **Share Pages with Integration:**
   - Open any Notion page you want the pipeline to access
   - Click "..." menu → "Connections"
   - Find and enable your integration

3. **Test Connection:**
   ```bash
   python3 test_notion_connection.py
   ```

**When to use:**
- Testing the pipeline without Kiro
- Development and debugging
- Running the poller standalone

## Creating a Test Page

1. **In Notion, create a new page:**
   - Title: `[SHIP] Test Calculator`
   - Content:
     ```
     Build a simple calculator app that can add, subtract, multiply, and divide two numbers.
     
     Requirements:
     - Input validation for numbers
     - Handle division by zero gracefully
     - Display results clearly
     ```

2. **Share with your integration:**
   - Click "..." → "Connections"
   - Enable your integration

3. **Get the page ID:**
   - Copy the page URL: `https://notion.so/Test-Calculator-abc123...`
   - The page ID is the last part: `abc123...`

## Testing the Pipeline

### Test 1: Connection Test

```bash
python3 test_notion_connection.py
```

Expected output:
- ✓ Connection successful
- ✓ Found X page(s) with [SHIP] in title
- Lists your [SHIP] pages

### Test 2: Full Pipeline with Real Notion

Create a test script:

```python
#!/usr/bin/env python3
from dotenv import load_dotenv
load_dotenv()

from orchestrator.main import run_pipeline

# Replace with your actual page ID
page_id = "your-page-id-here"

run = run_pipeline(page_id)
print(f"Status: {run.status}")
print(f"Tasks: {len(run.tasks)}")
```

Run it:
```bash
python3 test_real_notion.py
```

This will:
1. Extract content from your Notion page
2. Generate a spec using Groq
3. Create a Spec_DB in Notion
4. Write tasks to the database
5. Execute tasks (mock for now)

### Test 3: Start the Poller

```bash
python3 -m orchestrator run
```

This will:
- Poll Notion every 30 seconds
- Detect new [SHIP] pages
- Automatically run the pipeline for each page

## Notion API Permissions

Your integration needs these permissions (already configured):
- ✅ Read content
- ✅ Update content
- ✅ Insert content
- ✅ Read comments (optional)
- ✅ Create comments (optional)

## Troubleshooting

### "NOTION_API_KEY environment variable not set"

Check your `.env` file:
```bash
cat .env | grep NOTION_API_KEY
```

Make sure it's loaded:
```bash
export $(cat .env | xargs)
```

### "Failed to connect to Notion API: 401 Unauthorized"

Your API key is invalid or expired:
1. Go to https://www.notion.so/my-integrations
2. Find your integration
3. Copy the "Internal Integration Token"
4. Update `.env` with the new key

### "Failed to connect to Notion API: 404 Not Found"

The page doesn't exist or your integration doesn't have access:
1. Open the page in Notion
2. Click "..." → "Connections"
3. Enable your integration

### "No [SHIP] pages found"

Create a test page:
1. Title must start with `[SHIP]`
2. Share it with your integration
3. Wait 30 seconds for the poller to detect it

### Kiro MCP Connection Issues

If Kiro can't connect to Notion MCP:
1. Check `.kiro/settings/mcp.json` exists
2. Restart Kiro
3. Run `/mcp` command to authenticate
4. Check Kiro logs for errors

## What's Next?

1. ✅ Notion API client implemented
2. ✅ Connection tested successfully
3. ✅ Kiro MCP configured
4. ⏳ Authenticate Notion MCP in Kiro (run `/mcp`)
5. ⏳ Create a [SHIP] page in Notion
6. ⏳ Test full pipeline end-to-end
7. ⏳ Start the poller and watch it work!

## Architecture

```
Standalone Mode (Testing):
Notion API → NotionMCPClient → Orchestrator → Groq → Notion API

Full Pipeline Mode (Production):
Notion Page → Poller → Orchestrator → Groq → Notion API
                                    ↓
                              Kiro Agent (via MCP)
                                    ↓
                              Task Execution
                                    ↓
                              Notion Status Updates
```

## Files Modified

- `orchestrator/notion_mcp_client.py` - Real Notion API client
- `orchestrator/main.py` - Auto-detect Notion client from env
- `.kiro/settings/mcp.json` - Kiro MCP configuration
- `pyproject.toml` - Added notion-client dependency
- `test_notion_connection.py` - Connection test script

Your pipeline is ready to connect to Notion! 🚀
