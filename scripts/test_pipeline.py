#!/usr/bin/env python3
"""Quick test script for the Notion Spec-to-Ship Pipeline.

This script demonstrates how to run the pipeline with mock clients for testing.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestrator.main import run_pipeline
from orchestrator.models import Task


class MockNotionClient:
    """Mock Notion MCP client for testing."""
    
    def ping(self):
        """Mock ping - always succeeds."""
        print("✓ Mock Notion MCP connection OK")
    
    def search(self, query, filter):
        """Mock search - returns empty results."""
        return {"results": []}
    
    def get_block_children(self, block_id, start_cursor=None):
        """Mock get_block_children - returns sample content."""
        if start_cursor:
            return {"results": [], "has_more": False, "next_cursor": None}
        
        return {
            "results": [
                {
                    "id": "block-1",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {"plain_text": "Build a simple calculator app that can add, subtract, multiply, and divide two numbers."}
                        ]
                    },
                    "has_children": False
                }
            ],
            "has_more": False,
            "next_cursor": None
        }
    
    def create_database(self, payload):
        """Mock create_database."""
        print(f"✓ Mock: Created Spec_DB")
        return {"id": "mock-db-id"}
    
    def create_page(self, payload):
        """Mock create_page."""
        title = payload.get("properties", {}).get("Task Title", {}).get("title", [{}])[0].get("text", {}).get("content", "Unknown")
        print(f"✓ Mock: Created task page: {title}")
        return {"id": f"mock-page-{title}"}
    
    def append_block_children(self, page_id, children):
        """Mock append_block_children."""
        print(f"✓ Mock: Appended {len(children)} blocks to {page_id}")
        return {"results": children}
    
    def update_page(self, page_id, properties):
        """Mock update_page."""
        status = properties.get("Status", {}).get("select", {}).get("name", "Unknown")
        print(f"✓ Mock: Updated {page_id} status to {status}")
        return {"id": page_id}


class MockLLMClient:
    """Mock LLM client for testing."""
    
    def complete(self, system_prompt, user_prompt, temperature, timeout):
        """Mock LLM completion - returns a valid spec."""
        print("✓ Mock: Generated spec via LLM")
        return '''
{
  "introduction": "A simple calculator application that performs basic arithmetic operations on two numbers.",
  "requirements": [
    {
      "id": "R1",
      "title": "Basic arithmetic operations",
      "user_story": "As a user, I want to perform basic math operations so that I can calculate results quickly",
      "acceptance_criteria": [
        "WHEN the user enters two numbers and selects add, THE SYSTEM SHALL return the sum",
        "WHEN the user enters two numbers and selects subtract, THE SYSTEM SHALL return the difference",
        "WHEN the user enters two numbers and selects multiply, THE SYSTEM SHALL return the product",
        "WHEN the user enters two numbers and selects divide, THE SYSTEM SHALL return the quotient"
      ]
    },
    {
      "id": "R2",
      "title": "Input validation",
      "user_story": "As a user, I want the system to validate my inputs so that I get meaningful error messages",
      "acceptance_criteria": [
        "WHEN the user enters non-numeric input, THE SYSTEM SHALL display an error message",
        "WHEN the user attempts to divide by zero, THE SYSTEM SHALL display an error message"
      ]
    }
  ],
  "tasks": [
    {
      "order": 1,
      "title": "Create calculator module",
      "description": "Implement a calculator module with functions for add, subtract, multiply, and divide operations. Each function should accept two numeric parameters and return the result.",
      "acceptance_criteria": "WHEN called with two numbers, THE SYSTEM SHALL return the correct arithmetic result"
    },
    {
      "order": 2,
      "title": "Add input validation",
      "description": "Implement input validation to check for non-numeric inputs and division by zero. Raise appropriate exceptions with clear error messages.",
      "acceptance_criteria": "WHEN invalid input is provided, THE SYSTEM SHALL raise a ValueError with a descriptive message"
    },
    {
      "order": 3,
      "title": "Create CLI interface",
      "description": "Build a command-line interface that prompts the user for two numbers and an operation, then displays the result or error message.",
      "acceptance_criteria": "WHEN the user runs the CLI, THE SYSTEM SHALL prompt for inputs and display results"
    }
  ]
}
'''


class MockAgentDriver:
    """Mock agent driver for testing."""
    
    def execute_task(self, task: Task):
        """Mock task execution - always succeeds."""
        print(f"✓ Mock: Executed task {task.order}: {task.title}")
        from orchestrator.models import TaskResult
        return TaskResult(
            success=True,
            output=f"Successfully completed: {task.title}",
            error=None
        )


def main():
    """Run a test pipeline with mock clients."""
    print("=" * 60)
    print("Notion Spec-to-Ship Pipeline - Test Run")
    print("=" * 60)
    print()
    
    # Create mock clients
    notion_client = MockNotionClient()
    llm_client = MockLLMClient()
    agent_driver = MockAgentDriver()
    
    # Run pipeline
    print("Starting pipeline with mock clients...")
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
