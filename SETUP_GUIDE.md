# Notion Spec-to-Ship Pipeline - Setup Guide

Transform your Notion ideas into structured specs and implementation tasks automatically using AI.

## What This Does

1. You create a page in Notion with `[SHIP]` in the title
2. Write your project idea/requirements in the page
3. The pipeline automatically:
   - Detects the new page (polls every 30 seconds)
   - Extracts your idea
   - Uses AI (Groq) to generate a detailed spec
   - Creates a task database in Notion
   - Populates it with implementation tasks
   - Links everything back to your original page

---

## Prerequisites

- Python 3.11 or higher
- A Notion account
- A Groq API account (free)
- Git

---

## Step 1: Clone the Repository

```bash
git clone https://github.com/Shakiran-Nannyombi/NotionMCP-Challenge.git
cd NotionMCP-Challenge
```

---

## Step 2: Install Dependencies

### Option A: Using Virtual Environment (Recommended)

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # On Linux/Mac
# OR
venv\Scripts\activate  # On Windows

# Install dependencies
pip install groq notion-client python-dotenv pytest hypothesis
```

### Option B: Using UV (Faster)

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv pip install groq notion-client python-dotenv pytest hypothesis
```

---

## Step 3: Get Your API Keys

### 3.1 Notion API Key

1. Go to https://www.notion.so/my-integrations
2. Click **"New integration"**
3. Give it a name (e.g., "Spec-to-Ship Pipeline")
4. Select the workspace you want to use
5. Click **"Submit"**
6. Copy the **"Internal Integration Token"** (starts with `ntn_`)
7. **Important:** Share pages with your integration:
   - Open any Notion page you want the pipeline to access
   - Click "..." menu → "Connections"
   - Find and enable your integration

### 3.2 Groq API Key

1. Go to https://console.groq.com/
2. Sign up or log in
3. Go to **API Keys** section
4. Click **"Create API Key"**
5. Copy the key (starts with `gsk_`)

---

## Step 4: Configure Environment

Create a `.env` file in the project root:

```bash
cp .env.example .env
nano .env  # or use your preferred editor
```

Add your keys:

```env
# Notion API Key
NOTION_API_KEY=ntn_your_notion_api_key_here

# Groq API Key
GROQ_API_KEY=gsk_your_groq_api_key_here

# State file location (optional)
STATE_FILE=state.json
```

**Save and close the file.**

---

## Step 5: Test the Connection

### Test Notion Connection

```bash
python3 test_notion_connection.py
```

Expected output:
```
✓ Connection successful!
✓ Found X page(s) with [SHIP] in title
```

If you get errors:
- Check your `NOTION_API_KEY` is correct
- Make sure you shared pages with your integration
- Verify you're using the right workspace

### Test Groq Connection

```bash
python3 test_groq_quick.py
```

Expected output:
```
✓ Groq API connection successful!
Response: [AI generated text]
```

---

## Step 6: Create Your First Idea Page

1. **Open Notion** (the workspace where your integration is installed)

2. **Create a new page** with this format:
   - **Title:** `[SHIP] Calculator App`
   - **Content:**
     ```
     Build a simple calculator application with the following features:
     
     - Basic operations: add, subtract, multiply, divide
     - Input validation for numbers
     - Handle division by zero gracefully
     - Clear button to reset
     - Display calculation history
     - Responsive design for mobile and desktop
     ```

3. **Share the page with your integration:**
   - Click "..." menu → "Connections"
   - Enable your integration

---

## Step 7: Run the Pipeline

### Option A: Manual Run (Test Single Page)

Edit `test_manual_run.py` and add your page ID:

```python
page_id = "your-page-id-here"  # Get from Notion URL
```

Run it:
```bash
python3 test_manual_run.py
```

### Option B: Automatic Poller (Recommended)

Start the poller to automatically detect new `[SHIP]` pages:

```bash
python3 -m orchestrator run
```

You should see:
```
Polling Notion every 30 seconds...
Press Ctrl+C to stop
```

**Leave it running!** It will automatically:
- Check for new `[SHIP]` pages every 30 seconds
- Process each page
- Generate specs and tasks
- Update Notion

---

## Step 8: Check the Results

After the pipeline runs (takes ~10-15 seconds per page):

1. **Go back to Notion**
2. **You should see:**
   - A new database: `Spec_DB for [SHIP] Calculator App`
   - Tasks populated in the database with:
     - Task Title
     - Status (Todo/In Progress/Done)
     - Order
     - Description
   - Your original page updated with:
     - Link to the Spec_DB
     - Spec details (requirements, approach, etc.)

---

## How to Use

### Daily Workflow

1. **Create idea pages in Notion:**
   - Title must start with `[SHIP]`
   - Write your requirements/description
   - Share with your integration

2. **Let the pipeline run:**
   - Keep `python3 -m orchestrator run` running
   - Or run it manually when needed

3. **Check Notion for results:**
   - Spec_DB database created
   - Tasks ready to implement
   - Everything linked together

### Tips

- **Be specific in your descriptions:** The more detail you provide, the better the generated spec
- **Use bullet points:** Makes it easier for AI to parse requirements
- **Include technical details:** Mention frameworks, databases, APIs you want to use
- **One idea per page:** Don't mix multiple projects in one page

### Example Ideas to Try

**Simple:**
```
[SHIP] Todo App

Build a todo list application with:
- Add, edit, delete tasks
- Mark tasks as complete
- Filter by status
- Local storage persistence
```

**Medium:**
```
[SHIP] Weather Dashboard

Create a weather dashboard that:
- Shows current weather for user's location
- Displays 5-day forecast
- Search for any city
- Shows temperature, humidity, wind speed
- Uses OpenWeather API
- Responsive design
```

**Complex:**
```
[SHIP] E-commerce Platform

Build a full e-commerce platform with:

Backend:
- User authentication (JWT)
- Product catalog with categories
- Shopping cart
- Order management
- Payment integration (Stripe)
- Admin dashboard
- PostgreSQL database

Frontend:
- React with TypeScript
- Product listing and search
- Cart and checkout flow
- User profile and order history
- Responsive design
```

---

## Troubleshooting

### "No [SHIP] pages found"

- Make sure your page title starts with `[SHIP]`
- Share the page with your integration
- Wait 30 seconds for the poller to detect it

### "Failed to connect to Notion API"

- Check your `NOTION_API_KEY` in `.env`
- Verify the key is valid at https://www.notion.so/my-integrations
- Make sure you shared pages with your integration

### "Groq API call failed"

- Check your `GROQ_API_KEY` in `.env`
- Verify the key at https://console.groq.com/
- Check you haven't hit rate limits (30 requests/minute)

### "Pipeline runs but nothing appears in Notion"

- Check the terminal logs for errors
- Verify your integration has write permissions
- Make sure you're looking at the correct workspace

### Pipeline stops unexpectedly

- Check logs: `python3 -m orchestrator run 2>&1 | tee pipeline.log`
- Look for error messages
- Restart the poller

---

## Running in Background

### Linux/Mac

```bash
# Run in background
nohup python3 -m orchestrator run > pipeline.log 2>&1 &

# Check if running
ps aux | grep orchestrator

# View logs
tail -f pipeline.log

# Stop it
pkill -f "orchestrator run"
```

### Using systemd (Linux)

Create `/etc/systemd/system/notion-pipeline.service`:

```ini
[Unit]
Description=Notion Spec-to-Ship Pipeline
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/NotionMCP-Challenge
Environment="PATH=/path/to/NotionMCP-Challenge/venv/bin"
ExecStart=/path/to/NotionMCP-Challenge/venv/bin/python3 -m orchestrator run
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable notion-pipeline
sudo systemctl start notion-pipeline
sudo systemctl status notion-pipeline
```

---

## Advanced Usage

### Check Pipeline Status

```bash
# Get status of a specific run
python3 -m orchestrator status <run-id>
```

### View Logs

```bash
# Run with logging
python3 -m orchestrator run 2>&1 | tee pipeline.log

# Parse JSON logs
cat pipeline.log | grep '{"run_id"' | jq .

# Filter by stage
cat pipeline.log | jq 'select(.stage == "spec_generated")'
```

### Run Tests

```bash
# Run all tests
python3 -m pytest tests/ -v

# Run specific test
python3 -m pytest tests/unit/test_poller.py -v

# With coverage
python3 -m pytest tests/ --cov=orchestrator
```

---

## Project Structure

```
NotionMCP-Challenge/
├── orchestrator/           # Main pipeline code
│   ├── main.py            # Pipeline orchestrator
│   ├── poller.py          # Notion page detection
│   ├── extractor.py       # Content extraction
│   ├── spec_generator.py # AI spec generation
│   ├── notion_writer.py   # Write back to Notion
│   ├── groq_client.py     # Groq API client
│   └── notion_mcp_client.py # Notion API client
├── tests/                 # Unit tests
├── docs/                  # Documentation
├── .env                   # Your API keys (create this)
├── .env.example          # Example configuration
├── test_notion_connection.py  # Test Notion connection
├── test_groq_quick.py    # Test Groq connection
└── README.md             # Project overview
```

---

## What Gets Created in Notion

For each `[SHIP]` page, the pipeline creates:

1. **Spec_DB Database** with columns:
   - Task Title (title)
   - Status (select: Todo, In Progress, Done)
   - Order (number)
   - Description (text)

2. **Tasks** populated in the database:
   - Typically 5-10 tasks per project
   - Ordered by implementation sequence
   - Detailed descriptions

3. **Original page updated** with:
   - Link to Spec_DB
   - Requirements section
   - Technical approach
   - Implementation notes

---

## FAQ

**Q: How much does this cost?**
A: Groq API is free! Notion is free for personal use. The only cost is if you deploy to a server.

**Q: Can I use a different AI model?**
A: Yes! You can swap Groq for OpenAI, Anthropic, or any other LLM. Just update `orchestrator/main.py`.

**Q: Can I customize the spec format?**
A: Yes! Edit the prompts in `orchestrator/spec_generator.py`.

**Q: Does it work with Notion databases?**
A: Currently it works with pages. Database support coming soon!

**Q: Can I run multiple pipelines?**
A: Yes! Just use different `STATE_FILE` values in `.env`.

**Q: How do I update the code?**
A: `git pull origin main` then restart the pipeline.

---

## Support

- **Issues:** https://github.com/Shakiran-Nannyombi/NotionMCP-Challenge/issues
- **Documentation:** Check the `docs/` folder
- **Examples:** See `QUICKSTART.md`

---

## Next Steps

1. ✅ Set up locally (you're here!)
2. ⏳ Create your first `[SHIP]` page
3. ⏳ Run the pipeline and see results
4. ⏳ Deploy to a server for 24/7 operation
5. ⏳ Customize the spec format for your needs

Happy shipping! 🚀
