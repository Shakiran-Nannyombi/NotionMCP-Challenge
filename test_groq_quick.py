#!/usr/bin/env python3
"""Quick test to verify Groq integration works."""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 60)
print("Testing Groq Integration")
print("=" * 60)
print()

# Check API key
api_key = os.environ.get("GROQ_API_KEY")
if not api_key:
    print("❌ GROQ_API_KEY not found in environment")
    exit(1)

print(f"✓ GROQ_API_KEY found: {api_key[:20]}...")
print()

# Test Groq client
print("Testing Groq client...")
try:
    from orchestrator.groq_client import GroqClient
    
    client = GroqClient()
    print("✓ GroqClient created successfully")
    print()
    
    # Test completion
    print("Sending test request to Groq...")
    response = client.complete(
        system_prompt="You are a helpful assistant. Respond in one short sentence.",
        user_prompt="Say hello and confirm you're working.",
        temperature=0.2,
        timeout=30.0
    )
    
    print("✓ Groq API call successful!")
    print()
    print("Response:")
    print("-" * 60)
    print(response)
    print("-" * 60)
    print()
    print("✅ Groq integration is working!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
