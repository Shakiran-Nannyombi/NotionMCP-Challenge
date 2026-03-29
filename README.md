# Notion Spec-to-Ship Pipeline

AI-powered pipeline that transforms rough ideas in Notion into structured specs and working code.

## Quick Start

### 1. Install Dependencies

```bash
# Option A: Using the install script
./scripts/install_dependencies.sh

# Option B: Manual installation (recommended: use a virtual environment)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install groq python-dotenv pytest hypothesis
```

### 2. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your API keys
nano .env  # or your preferred editor
```

Required:
- `GROQ_API_KEY` - Get from https://console.groq.com/
- `NOTION_API_KEY` - Get from https://www.notion.so/my-integrations

See [NOTION_SETUP.md](docs/NOTION_SETUP.md) for detailed Notion integration setup.

### 3. Test the Pipeline

```bash
# Run unit tests
python3 -m pytest tests/ -v

# Test with mock clients (no API keys needed)
python3 scripts/test_pipeline.py
```

## Architecture

```
Notion Page → Notion MCP → Orchestrator → Kiro Agent
     ↓            ↓             ↓             ↓
  [SHIP]      Extract       Generate      Execute
   Idea        Text          Spec          Tasks
```

## Features

- ✅ Automatic idea detection in Notion (polling every 30s)
- ✅ LLM-powered spec generation (requirements + tasks)
- ✅ Structured database creation in Notion
- ✅ Automated task execution via Kiro
- ✅ Real-time status syncing
- ✅ Structured JSON logging
- ✅ Retry logic with exponential backoff
- ✅ Failure isolation (one task failure doesn't halt pipeline)

## Documentation

- [NOTION_SETUP.md](docs/NOTION_SETUP.md) - Notion integration setup
- [GROQ_SETUP.md](docs/GROQ_SETUP.md) - Groq API setup
- [SETUP.md](docs/SETUP.md) - Detailed setup guide
- [TESTING.md](docs/TESTING.md) - Testing guide and troubleshooting
- [.env.example](.env.example) - Configuration options

## Usage

### Start the Poller

```bash
python3 -m orchestrator run
```

This will:
1. Poll Notion every 30 seconds
2. Detect pages with `[SHIP]` prefix
3. Generate specs and execute tasks automatically

### Check Pipeline Status

```bash
python3 -m orchestrator status <run-id>
```

### Manual Pipeline Run

```python
from orchestrator.main import run_pipeline

run = run_pipeline("your-notion-page-id")
print(f"Status: {run.status}")
print(f"Tasks completed: {len([t for t in run.tasks if t.status == 'Done'])}")
```

## Project Structure

```
orchestrator/
├── main.py              # Pipeline orchestrator
├── poller.py            # Notion page detection
├── extractor.py         # Content extraction
├── spec_generator.py    # LLM-based spec generation
├── notion_writer.py     # Write back to Notion
├── agent_driver.py      # Kiro task execution
├── status_syncer.py     # Status synchronization
├── groq_client.py       # Groq LLM client
├── notion_mcp_client.py # Notion MCP wrapper
├── models.py            # Data models
├── errors.py            # Custom exceptions
├── logger.py            # Structured logging
└── retry.py             # Retry decorator

tests/
├── unit/                # Unit tests (47 tests)
└── property/            # Property-based tests (optional)

scripts/
├── test_pipeline.py     # End-to-end test with mocks
└── install_dependencies.sh  # Dependency installer
```

## Development

### Run Tests

```bash
# All tests
python3 -m pytest tests/ -v

# Specific test file
python3 -m pytest tests/unit/test_poller.py -v

# With coverage
python3 -m pytest tests/ --cov=orchestrator
```

### View Logs

```bash
# Run with logging
python3 -m orchestrator run 2>&1 | tee pipeline.log

# Parse JSON logs
cat pipeline.log | grep '{"run_id"' | jq .

# Filter by stage
cat pipeline.log | jq 'select(.stage == "task_completed")'
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest tests/`
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- Check [TESTING.md](TESTING.md) for troubleshooting
- Review [SETUP.md](SETUP.md) for configuration help
- Open an issue on GitHub
