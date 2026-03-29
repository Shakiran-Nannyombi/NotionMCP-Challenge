#!/bin/bash
# Install dependencies for the Notion Spec-to-Ship Pipeline

set -e

echo "Installing Notion Spec-to-Ship Pipeline dependencies..."
echo

# Check if we're in a virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  No virtual environment detected."
    echo "It's recommended to use a virtual environment."
    echo
    echo "To create one:"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
    INSTALL_CMD="pip install --user"
else
    echo "✓ Virtual environment detected: $VIRTUAL_ENV"
    INSTALL_CMD="pip install"
fi

echo
echo "Installing packages..."
$INSTALL_CMD groq notion-client python-dotenv pytest hypothesis

echo
echo "✓ Dependencies installed successfully!"
echo
echo "Next steps:"
echo "1. Copy .env.example to .env and fill in your API keys"
echo "2. Run tests: python3 -m pytest tests/"
echo "3. Test pipeline: python3 scripts/test_pipeline.py"
