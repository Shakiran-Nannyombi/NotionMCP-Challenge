# Quick Start Guide

Your Notion Spec-to-Ship Pipeline is ready! Follow these steps to test it.

## What's Already Done

- ✅ Groq API integration (tested and working)
- ✅ Notion API client (tested and working)
- ✅ Kiro MCP configuration created
- ✅ All dependencies installed
- ✅ Environment configured

## 🚀 Next Steps

### Step 1: Authenticate Notion MCP in Kiro

1. **Open Kiro** (this IDE)
2. **Run the MCP command:**
   - Open Command Palette (Ctrl+Shift+P / Cmd+Shift+P)
   - Type: `/mcp`
   - Or just type `/mcp` in the chat
3. **Follow the OAuth flow** to connect your Notion workspace
4. **Verify connection:**
   - You should see "notion" listed as connected
   - The MCP server will have access to your Notion workspace

### Step 2: Create a Test Page in Notion

1. **Go to Notion** (https://notion.so)
2. **Create a new page:**
   - Title: `[SHIP] Test Calculator`
   - Content:
     ```
     Build a simple calculator app that can add, subtract, multiply, and divide two numbers.
     
     Requirements:
     - Input validation for numbers
     - Handle division by zero gracefully
     - Display results clearly
     - Support decimal numbers
     ```
3. **Share with your integration:**
   - Click "..." menu in top right
   - Go to "Connections"
   - Enable your integration (if using direct API)
   - OR just make sure the page is in your workspace (if using MCP)

### Step 3: Test the Connection

```bash
# Test Notion API connection
python3 test_notion_connection.py
```

Expected output:
```
✓ Connection successful!
✓ Found 1 page(s) with [SHIP] in title
Pages found:
  - [SHIP] Test Calculator (ID: abc123...)
```

### Step 4: Run the Pipeline Manually

Get your page ID from the Notion URL:
- URL: `https://notion.so/Test-Calculator-abc123def456...`
- Page ID: `abc123def456...` (the part after the last dash)

Create a test script:

```bash
cat > test_manual_run.py << 'EOF'
#!/usr/bin/env python3
from dotenv import load_dotenv
load_dotenv()

from orchestrator.main import run_pipeline

# Replace with your actual page ID
page_id = "YOUR_PAGE_ID_HERE"

print(f"Running pipeline for page: {page_id}")
run = run_pipeline(page_id)

print(f"\nStatus: {run.status}")
print(f"Tasks generated: {len(run.tasks)}")
for task in run.tasks:
    print(f"  {task.order}. {task.title}")
EOF

chmod +x test_manual_run.py
```

Edit the page ID and run:
```bash
python3 test_manual_run.py
```

This will:
1. ✅ Extract content from your Notion page
2. ✅ Generate a spec using Groq (takes ~7 seconds)
3. ✅ Create a Spec_DB in your Notion workspace
4. ✅ Write tasks to the database
5. ✅ Update the original page with a link to the Spec_DB

### Step 5: Start the Automatic Poller

```bash
python3 -m orchestrator run
```

This will:
- Poll Notion every 30 seconds
- Detect new pages with `[SHIP]` in the title
- Automatically run the pipeline for each new page
- Keep running until you press Ctrl+C

### Step 6: Watch It Work!

1. **Create another [SHIP] page in Notion**
2. **Wait 30 seconds** (or less)
3. **Watch the terminal** - you'll see:
   ```
   {"run_id": "...", "stage": "detected", ...}
   {"run_id": "...", "stage": "extracted", ...}
   {"run_id": "...", "stage": "spec_generated", ...}
   {"run_id": "...", "stage": "db_created", ...}
   {"run_id": "...", "stage": "tasks_written", ...}
   ```
4. **Check Notion** - you'll see:
   - A new Spec_DB database
   - Tasks populated in the database
   - Your original page updated with a link

## 🎯 What You Should See

### In Terminal:
```
============================================================
Notion Spec-to-Ship Pipeline - Running
============================================================

Polling Notion every 30 seconds...
Press Ctrl+C to stop

[2026-03-29 12:00:00] Detected new page: abc123...
[2026-03-29 12:00:01] Extracted idea text
[2026-03-29 12:00:08] Generated spec with 5 tasks
[2026-03-29 12:00:09] Created Spec_DB: xyz789...
[2026-03-29 12:00:10] Wrote 5 tasks to database
[2026-03-29 12:00:11] Pipeline completed successfully!
```

### In Notion:
1. **Original [SHIP] page:**
   - Updated with "✅ Spec Generated"
   - Link to Spec_DB

2. **New Spec_DB database:**
   - Title: "Spec_DB for [SHIP] Test Calculator"
   - Columns: Task Title, Status, Order, Description
   - 5 task rows (or however many were generated)

3. **Spec blocks on original page:**
   - Requirements section
   - Tasks list
   - Implementation notes

## 🐛 Troubleshooting

### "No [SHIP] pages found"
- Make sure your page title starts with `[SHIP]`
- Share the page with your integration (if using direct API)
- Wait 30 seconds for the poller to detect it

### "Failed to connect to Notion API"
- Check your `.env` file has `NOTION_API_KEY`
- Verify the API key is valid at https://www.notion.so/my-integrations
- Make sure you shared pages with your integration

### "Groq API call failed"
- Check your `.env` file has `GROQ_API_KEY`
- Verify the API key is valid at https://console.groq.com/
- Check you haven't hit rate limits (30 requests/minute)

### Kiro MCP not working
- Run `/mcp` in Kiro to authenticate
- Check `.kiro/settings/mcp.json` exists
- Restart Kiro
- Check Kiro logs for errors

## 📚 Documentation

- [NOTION_SETUP.md](docs/NOTION_SETUP.md) - Detailed Notion setup
- [SETUP.md](docs/SETUP.md) - General setup guide
- [TESTING.md](docs/TESTING.md) - Testing guide
- [README.md](README.md) - Project overview

## 🎉 Success Criteria

You'll know it's working when:
1. ✅ `test_notion_connection.py` finds your [SHIP] pages
2. ✅ Manual pipeline run creates a Spec_DB in Notion
3. ✅ Poller detects new [SHIP] pages automatically
4. ✅ Groq generates specs in ~7 seconds
5. ✅ Tasks appear in Notion database

## 🚀 Ready to Ship!

Your pipeline is fully configured and ready to use. Just:
1. Authenticate Notion MCP in Kiro (`/mcp`)
2. Create a [SHIP] page
3. Run the poller or manual test
4. Watch the magic happen! ✨
