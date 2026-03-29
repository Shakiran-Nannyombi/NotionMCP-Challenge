# Groq Integration Setup

Your pipeline is now configured to use Groq API! Here's what was set up:

## What's Configured

✅ **Groq Client** (`orchestrator/groq_client.py`)
- Implements the LLMClient protocol
- Uses `llama-3.3-70b-versatile` model by default
- Supports other models: `mixtral-8x7b-32768`, `llama-3.1-70b-versatile`

✅ **Auto-Detection** (`orchestrator/main.py`)
- Automatically creates Groq client if `GROQ_API_KEY` is set
- Falls back to None if not configured (for testing with mocks)

✅ **Environment** (`.env`)
- Your Groq API key is configured
- Your Notion API key is configured

## Next Steps

### 1. Install Groq Package

Since you're on an externally-managed Python environment, you have two options:

**Option A: Use a virtual environment (recommended)**
```bash
python3 -m venv venv
source venv/bin/activate
pip install groq python-dotenv pytest hypothesis
```

**Option B: Use the install script**
```bash
./scripts/install_dependencies.sh
```

**Option C: Install with --break-system-packages (not recommended)**
```bash
pip install --break-system-packages groq python-dotenv pytest hypothesis
```

### 2. Test Groq Integration

Create a test script to verify Groq works:

```python
# test_groq.py
from orchestrator.groq_client import GroqClient

client = GroqClient()
response = client.complete(
    system_prompt="You are a helpful assistant.",
    user_prompt="Say hello in one sentence.",
    temperature=0.2,
    timeout=30.0
)
print(response)
```

Run it:
```bash
python3 test_groq.py
```

Expected output: A friendly greeting from the LLM.

### 3. Test Full Pipeline with Groq

```bash
# This will use your real Groq API key
python3 scripts/test_pipeline.py
```

But first, update `test_pipeline.py` to use the real Groq client instead of mock:

```python
# In scripts/test_pipeline.py, replace MockLLMClient with:
from orchestrator.groq_client import GroqClient
llm_client = GroqClient()
```

### 4. Configure Notion MCP

To complete the integration, you need to set up Notion MCP in Kiro:

1. Open Kiro
2. Command Palette → "MCP: Configure Servers"
3. Add Notion MCP configuration:

```json
{
  "mcpServers": {
    "notion": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-notion"],
      "env": {
        "NOTION_API_KEY": "ntn_YOUR_NOTION_API_KEY_HERE"
      }
    }
  }
}
```

### 5. Create Test Page in Notion

1. Go to Notion
2. Create a new page
3. Title: `[SHIP] Test Calculator`
4. Content:
   ```
   Build a simple calculator that can add, subtract, multiply, and divide two numbers.
   It should validate inputs and handle division by zero.
   ```
5. Share the page with your integration

### 6. Run the Pipeline

```bash
# Start the poller
python3 -m orchestrator run
```

The pipeline will:
1. Detect your `[SHIP]` page
2. Extract the content
3. Call Groq to generate a spec
4. Create a Spec_DB in Notion
5. Execute tasks via Kiro

## Groq API Details

### Models Available

- `llama-3.3-70b-versatile` (default) - Best balance of speed and quality
- `mixtral-8x7b-32768` - Fast, good for simple tasks
- `llama-3.1-70b-versatile` - High quality, slightly slower

### Rate Limits

Groq free tier:
- 30 requests per minute
- 14,400 tokens per minute

This is more than enough for the pipeline (typically 1-2 requests per spec generation).

### Cost

Groq is **free** for the models we're using! 🎉

### Changing Models

Edit `orchestrator/groq_client.py`:

```python
def __init__(
    self,
    api_key: str | None = None,
    model: str = "mixtral-8x7b-32768",  # Change this
):
```

Or pass it when creating the client:

```python
from orchestrator.groq_client import GroqClient
client = GroqClient(model="llama-3.1-70b-versatile")
```

## Troubleshooting

### "groq package not installed"

Install it:
```bash
pip install groq
```

### "GROQ_API_KEY environment variable not set"

Check your `.env` file:
```bash
cat .env | grep GROQ_API_KEY
```

Make sure it's loaded:
```bash
export $(cat .env | xargs)
```

### "Groq API call failed: 401 Unauthorized"

Your API key is invalid. Get a new one from https://console.groq.com/

### "Groq API call failed: 429 Too Many Requests"

You've hit the rate limit. Wait a minute and try again.

### Spec generation returns malformed JSON

Try a different model or increase temperature slightly:
```python
client = GroqClient(model="llama-3.3-70b-versatile")
```

## What's Next?

1. ✅ Groq integration complete
2. ⏳ Install Groq package
3. ⏳ Test Groq client
4. ⏳ Configure Notion MCP in Kiro
5. ⏳ Implement real MCP calls in `NotionMCPClient`
6. ⏳ Test end-to-end pipeline
7. ⏳ Demo!

## Files Modified

- `orchestrator/groq_client.py` - New Groq client
- `orchestrator/main.py` - Auto-detect Groq from env
- `pyproject.toml` - Added groq dependency
- `.env.example` - Groq as primary option
- `README.md` - Updated with Groq instructions
- `scripts/install_dependencies.sh` - Install script

Your pipeline is ready to use Groq! 🚀
