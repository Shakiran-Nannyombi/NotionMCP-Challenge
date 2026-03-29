#!/usr/bin/env python3
"""Test the full pipeline with real Groq LLM but mock Notion."""

import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from orchestrator.main import run_pipeline
from orchestrator.groq_client import GroqClient
from orchestrator.models import Task, TaskResult


class MockNotionClient:
    """Mock Notion MCP client for testing."""
    
    def ping(self):
        print("✓ Mock Notion MCP connection OK")
    
    def search(self, query, filter):
        return {"results": []}
    
    def get_block_children(self, block_id, start_cursor=None):
        if start_cursor:
            return {"results": [], "has_more": False, "next_cursor": None}
        
        return {
            "results": [
                {
                    "id": "block-1",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {"plain_text": "Build a simple calculator app that can add, subtract, multiply, and divide two numbers. It should have input validation and handle division by zero gracefully."}
                        ]
                    },
                    "has_children": False
                }
            ],
            "has_more": False,
            "next_cursor": None
        }
    
    def create_database(self, payload):
        print(f"✓ Mock: Created Spec_DB")
        return {"id": "mock-db-id"}
    
    def create_page(self, payload):
        title = payload.get("properties", {}).get("Task Title", {}).get("title", [{}])[0].get("text", {}).get("content", "Unknown")
        print(f"✓ Mock: Created task page: {title}")
        return {"id": f"mock-page-{title}"}
    
    def append_block_children(self, page_id, children):
        print(f"✓ Mock: Appended {len(children)} blocks to {page_id}")
        return {"results": children}
    
    def update_page(self, page_id, properties):
        status = properties.get("Status", {}).get("select", {}).get("name", "Unknown")
        print(f"✓ Mock: Updated {page_id} status to {status}")
        return {"id": page_id}


class MockAgentDriver:
    """Mock agent driver for testing."""
    
    def execute_task(self, task: Task):
        print(f"✓ Mock: Executed task {task.order}: {task.title}")
        return TaskResult(
            success=True,
            output=f"Successfully completed: {task.title}",
            error=None
        )


def main():
    print("=" * 60)
    print("Notion Spec-to-Ship Pipeline - Test with Real Groq")
    print("=" * 60)
    print()
    
    # Create clients
    notion_client = MockNotionClient()
    llm_client = GroqClient()  # Real Groq client!
    agent_driver = MockAgentDriver()
    
    print("Starting pipeline...")
    print("- Notion: Mock")
    print("- LLM: Real Groq API")
    print("- Agent: Mock")
    print()
    
    try:
        run = run_pipeline(
            "test-page-id",
            notion_client=notion_client,
            llm_client=llm_client,
            agent_driver=agent_driver,
            state_file="test_state.json"
        )
        
        print()
        print("=" * 60)
        print("Pipeline completed successfully!")
        print("=" * 60)
        print(f"Run ID: {run.run_id}")
        print(f"Status: {run.status.value}")
        print(f"Tasks: {len(run.tasks)}")
        print(f"Completed: {sum(1 for t in run.tasks if t.status.value == 'Done')}")
        print(f"Failed: {sum(1 for t in run.tasks if t.status.value == 'Failed')}")
        print()
        
        if run.tasks:
            print("Generated Tasks:")
            for task in run.tasks:
                print(f"  {task.order}. {task.title}")
        
        return 0
        
    except Exception as e:
        print()
        print("=" * 60)
        print(f"Pipeline failed: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
