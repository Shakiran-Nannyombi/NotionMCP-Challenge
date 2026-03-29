```text
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║     N O T I O N   →   S P E C   →   S H I P                                ║
║                                                                              ║
║     Transform rough ideas into structured specs and working code            ║
║     automatically. Write in Notion, ship with AI.                           ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

# Notion Spec-to-Ship Pipeline

An AI-powered automation that turns your Notion ideas into production-ready specs and implementation tasks. Write your project vision in plain English, and watch it transform into a structured development plan.

---

## What It Does

```
Your Idea (Notion)  →  AI Processing (Groq)  →  Structured Output (Notion)
     ↓                        ↓                          ↓
  [SHIP] Page          Extract & Analyze           Spec Database
  Requirements         Generate Tasks              Implementation Plan
  Plain English        Smart Breakdown             Ready to Code
```

**The Flow:**
1. Create a page in Notion with `[SHIP]` in the title
2. Write your project idea in plain English
3. Pipeline detects it automatically (polls every 30s)
4. AI generates a detailed spec with implementation tasks
5. Creates a task database in Notion with everything organized
6. Links it all back to your original page

---

## Live Demo

See it in action:
- Example Input: A simple calculator app idea
- Generated Output: 5-10 structured implementation tasks
- Time: ~10 seconds from idea to spec

---

## Quick Start

### Prerequisites

- Python 3.11+
- Notion account
- Groq API key (free at https://console.groq.com/)

### Installation

```bash
# Clone the repository
git clone https://github.com/Shakiran-Nannyombi/NotionMCP-Challenge.git
cd NotionMCP-Challenge

# Install dependencies
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install groq notion-client python-dotenv

# Configure your API keys
cp .env.example .env
nano .env  # Add your NOTION_API_KEY and GROQ_API_KEY
```

### First Run

```bash
# Test the connection
python3 test_notion_connection.py

# Start the pipeline
python3 -m orchestrator run
```

**Detailed setup:** See [SETUP_GUIDE.md](SETUP_GUIDE.md) for step-by-step instructions.

---

## How to Use

### 1. Create Your Idea Page

In Notion, create a page like this:

**Title:** `[SHIP] Weather Dashboard`

**Content:**
```
Build a weather dashboard application with:

- Display current weather for user's location
- Show 5-day forecast with icons
- Search for weather in any city
- Display temperature, humidity, wind speed
- Responsive design for mobile and desktop
- Use OpenWeather API for data
```

### 2. Share with Integration

- Click "..." menu → "Connections"
- Enable your integration

### 3. Let the Pipeline Work

The pipeline automatically:
- Detects your new page
- Extracts the requirements
- Generates a detailed spec
- Creates implementation tasks
- Organizes everything in a database

### 4. Check the Results

In Notion, you'll see:
- New database: `Spec_DB for Weather Dashboard`
- 5-10 implementation tasks with descriptions
- Your original page updated with spec details
- Everything linked together

---

## Features

**Automatic Detection**
- Polls Notion every 30 seconds
- Finds pages with `[SHIP]` prefix
- No manual triggering needed

**AI-Powered Spec Generation**
- Uses Groq (free, fast LLM)
- Generates detailed requirements
- Breaks down into implementation tasks
- Smart task ordering

**Notion Integration**
- Creates structured databases
- Populates with tasks automatically
- Links everything together
- Updates status in real-time

**Robust & Reliable**
- Retry logic with exponential backoff
- Failure isolation (one task failure doesn't stop others)
- Structured JSON logging
- State persistence

---

## Architecture

```
┌─────────────┐
│   Notion    │  You write your idea here
│   [SHIP]    │
└──────┬──────┘
       │
       ↓
┌─────────────┐
│   Poller    │  Detects new pages every 30s
└──────┬──────┘
       │
       ↓
┌─────────────┐
│  Extractor  │  Reads page content
└──────┬──────┘
       │
       ↓
┌─────────────┐
│  Groq AI    │  Generates spec + tasks
└──────┬──────┘
       │
       ↓
┌─────────────┐
│   Writer    │  Creates database in Notion
└──────┬──────┘
       │
       ↓
┌─────────────┐
│   Notion    │  Spec_DB with tasks ready!
│  Database   │
└─────────────┘
```

---

## Project Structure

```
orchestrator/
├── main.py              # Pipeline orchestrator & entry point
├── poller.py            # Detects new [SHIP] pages
├── extractor.py         # Extracts content from pages
├── spec_generator.py    # AI-powered spec generation
├── notion_writer.py     # Writes back to Notion
├── groq_client.py       # Groq LLM integration
├── notion_mcp_client.py # Notion API wrapper
├── models.py            # Data models
├── errors.py            # Custom exceptions
├── logger.py            # Structured logging
└── retry.py             # Retry decorator

tests/
├── unit/                # 47 unit tests
└── property/            # Property-based tests

docs/
├── SETUP_GUIDE.md       # Detailed setup instructions
├── NOTION_SETUP.md      # Notion integration guide
├── SETUP.md             # General setup
└── TESTING.md           # Testing & troubleshooting
```

---

## Example Ideas to Try

**Simple:**
```
[SHIP] Todo App

Build a todo list with add, edit, delete, and mark complete features.
Use local storage for persistence.
```

**Medium:**
```
[SHIP] Blog Platform

Create a blog platform with:
- User authentication
- Create, edit, delete posts
- Comments system
- Categories and tags
- Markdown support
- Responsive design
```

**Complex:**
```
[SHIP] E-commerce Platform

Full e-commerce solution with:

Backend:
- User auth (JWT)
- Product catalog
- Shopping cart
- Order management
- Payment integration (Stripe)
- Admin dashboard
- PostgreSQL database

Frontend:
- React + TypeScript
- Product listing & search
- Cart & checkout
- User profile
- Order history
```

---

## Advanced Usage

### Manual Pipeline Run

```python
from orchestrator.main import run_pipeline

# Run for a specific page
run = run_pipeline("your-notion-page-id")

# Check results
print(f"Status: {run.status}")
print(f"Tasks: {len(run.tasks)}")
for task in run.tasks:
    print(f"  {task.order}. {task.title}")
```

### Check Pipeline Status

```bash
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
# All tests
python3 -m pytest tests/ -v

# Specific test
python3 -m pytest tests/unit/test_poller.py -v

# With coverage
python3 -m pytest tests/ --cov=orchestrator
```

---

## Configuration

Edit `.env` to customize:

```env
# Required
NOTION_API_KEY=ntn_your_key_here
GROQ_API_KEY=gsk_your_key_here

# Optional
STATE_FILE=state.json           # Where to store pipeline state
POLL_INTERVAL=30                # How often to check Notion (seconds)
LLM_TEMPERATURE=0.2             # AI creativity (0.0-1.0)
```

---

## Deployment

### Run Locally

```bash
# Foreground
python3 -m orchestrator run

# Background (Linux/Mac)
nohup python3 -m orchestrator run > pipeline.log 2>&1 &
```

### Deploy to Server

See [SETUP_GUIDE.md](SETUP_GUIDE.md) for:
- DigitalOcean VPS setup
- systemd service configuration
- Docker deployment
- Railway/Heroku deployment

---

## Troubleshooting

**"No [SHIP] pages found"**
- Ensure page title starts with `[SHIP]`
- Share page with your integration
- Wait 30 seconds for poller

**"Failed to connect to Notion API"**
- Check `NOTION_API_KEY` in `.env`
- Verify key at https://www.notion.so/my-integrations
- Ensure pages are shared with integration

**"Groq API call failed"**
- Check `GROQ_API_KEY` in `.env`
- Verify key at https://console.groq.com/
- Check rate limits (30 requests/minute)

**More help:** See [TESTING.md](docs/TESTING.md)

---

## Documentation

- [SETUP_GUIDE.md](SETUP_GUIDE.md) - Complete setup walkthrough
- [NOTION_SETUP.md](docs/NOTION_SETUP.md) - Notion integration details
- [QUICKSTART.md](QUICKSTART.md) - Get started in 5 minutes
- [TESTING.md](docs/TESTING.md) - Testing & troubleshooting

---

## Tech Stack

- **Python 3.11+** - Core language
- **Notion API** - Workspace integration
- **Groq** - Fast, free LLM (llama-3.3-70b)
- **notion-client** - Official Notion SDK
- **pytest** - Testing framework

---

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest tests/`
5. Submit a pull request

---

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

## Support

- Issues: https://github.com/Shakiran-Nannyombi/NotionMCP-Challenge/issues
- Discussions: https://github.com/Shakiran-Nannyombi/NotionMCP-Challenge/discussions
- Documentation: Check the `docs/` folder

---

## Acknowledgments

Built for the Notion MCP Challenge. Powered by Groq's lightning-fast LLM inference.

---

```text
Made with code and coffee
Transform ideas → Ship products
```
