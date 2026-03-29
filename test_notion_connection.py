#!/usr/bin/env python3
"""Test Notion API connection."""

import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from orchestrator.notion_mcp_client import NotionMCPClient


def main():
    print("=" * 60)
    print("Testing Notion API Connection")
    print("=" * 60)
    print()
    
    try:
        # Create client
        print("Creating Notion client...")
        client = NotionMCPClient()
        
        # Test connection
        print("Testing connection (ping)...")
        client.ping()
        print("✓ Connection successful!")
        print()
        
        # Test search
        print("Testing search for [CALCULATOR] pages...")
        results = client.search(
            query="[CALCULATOR]",
            filter={"property": "object", "value": "page"}
        )
        
        pages = results.get("results", [])
        print(f"✓ Found {len(pages)} page(s) with [CALCULATOR] in title")
        print()
        
        if pages:
            print("Pages found:")
            for page in pages[:5]:  # Show first 5
                title = "Untitled"
                if "properties" in page:
                    title_prop = page["properties"].get("title", {})
                    if "title" in title_prop and title_prop["title"]:
                        title = title_prop["title"][0]["plain_text"]
                print(f"  - {title} (ID: {page['id']})")
        else:
            print("No [SHIP] pages found. Create a page with [SHIP] in the title to test!")
        
        print()
        print("=" * 60)
        print("Notion API connection test completed successfully!")
        print("=" * 60)
        return 0
        
    except Exception as e:
        print()
        print("=" * 60)
        print(f"Connection test failed: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
