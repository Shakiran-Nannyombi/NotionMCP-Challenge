"""Notion MCP client wrapper for the orchestrator.

This module provides a thin wrapper around the Notion API that the
orchestrator components expect. It uses the official Notion SDK directly
since we're running as a standalone Python application.
"""

from __future__ import annotations

import os
from typing import Any

from orchestrator.errors import MCPConnectionError


class NotionMCPClient:
    """Wrapper around Notion API for the orchestrator.
    
    This class provides the interface that orchestrator components expect:
    - search(query, filter) for Poller
    - get_block_children(block_id, start_cursor=None) for IdeaExtractor
    - create_database(payload) for NotionWriter
    - create_page(payload) for NotionWriter
    - append_block_children(page_id, children) for NotionWriter
    - update_page(page_id, properties) for NotionWriter
    - ping() for connection check
    
    Uses the official Notion Python SDK (@notionhq/client equivalent).
    """
    
    def __init__(self, api_key: str | None = None):
        """Initialize the Notion client.
        
        Args:
            api_key: Notion API key. If None, reads from NOTION_API_KEY env var.
        """
        self.api_key = api_key or self._get_api_key_from_env()
        self._client = None
    
    def _get_api_key_from_env(self) -> str:
        """Get API key from environment."""
        api_key = os.environ.get("NOTION_API_KEY")
        if not api_key:
            raise MCPConnectionError(
                "NOTION_API_KEY environment variable not set. "
                "Please set your Notion API key."
            )
        return api_key
    
    def _ensure_client(self):
        """Lazy-load the Notion client."""
        if self._client is None:
            try:
                from notion_client import Client
                self._client = Client(auth=self.api_key)
            except ImportError:
                raise ImportError(
                    "notion-client package not installed. "
                    "Install with: pip install notion-client"
                )
    
    def ping(self) -> None:
        """Check if the Notion API is reachable.
        
        Raises:
            MCPConnectionError: If the API is unreachable.
        """
        self._ensure_client()
        try:
            # Try to list users as a health check
            self._client.users.me()
        except Exception as exc:
            raise MCPConnectionError(f"Failed to connect to Notion API: {exc}") from exc
    
    # ------------------------------------------------------------------
    # Poller interface
    # ------------------------------------------------------------------
    
    def search(self, query: str, filter: dict) -> dict:
        """Search Notion pages.
        
        Args:
            query: Search query string.
            filter: Filter dict with 'value' and 'property' keys.
        
        Returns:
            Dict with 'results' key containing list of page objects.
        """
        self._ensure_client()
        try:
            # Notion API search with filter
            response = self._client.search(
                query=query,
                filter=filter
            )
            return response
        except Exception as exc:
            raise MCPConnectionError(f"Notion search failed: {exc}") from exc
    
    # ------------------------------------------------------------------
    # IdeaExtractor interface
    # ------------------------------------------------------------------
    
    def get_block_children(
        self,
        block_id: str,
        start_cursor: str | None = None
    ) -> dict:
        """Retrieve block children from Notion.
        
        Args:
            block_id: Notion block/page ID.
            start_cursor: Pagination cursor (optional).
        
        Returns:
            Dict with 'results', 'has_more', and 'next_cursor' keys.
        """
        self._ensure_client()
        try:
            kwargs = {"block_id": block_id}
            if start_cursor:
                kwargs["start_cursor"] = start_cursor
            
            response = self._client.blocks.children.list(**kwargs)
            return response
        except Exception as exc:
            raise MCPConnectionError(f"Failed to get block children: {exc}") from exc
    
    # ------------------------------------------------------------------
    # NotionWriter interface
    # ------------------------------------------------------------------
    
    def create_database(self, payload: dict) -> dict:
        """Create a Notion database.
        
        Args:
            payload: Database creation payload with parent, title, and properties.
        
        Returns:
            Dict with 'id' key containing the new database ID.
        """
        self._ensure_client()
        try:
            response = self._client.databases.create(**payload)
            return response
        except Exception as exc:
            raise MCPConnectionError(f"Failed to create database: {exc}") from exc
    
    def create_page(self, payload: dict) -> dict:
        """Create a Notion page.
        
        Args:
            payload: Page creation payload with parent and properties.
        
        Returns:
            Dict with 'id' key containing the new page ID.
        """
        self._ensure_client()
        try:
            response = self._client.pages.create(**payload)
            return response
        except Exception as exc:
            raise MCPConnectionError(f"Failed to create page: {exc}") from exc
    
    def append_block_children(self, page_id: str, children: list[dict]) -> dict:
        """Append block children to a Notion page.
        
        Args:
            page_id: Notion page ID.
            children: List of block objects to append.
        
        Returns:
            Dict with 'results' key containing the created blocks.
        """
        self._ensure_client()
        try:
            response = self._client.blocks.children.append(
                block_id=page_id,
                children=children
            )
            return response
        except Exception as exc:
            raise MCPConnectionError(f"Failed to append blocks: {exc}") from exc
    
    def update_page(self, page_id: str, properties: dict) -> dict:
        """Update a Notion page's properties.
        
        Args:
            page_id: Notion page ID.
            properties: Dict of properties to update.
        
        Returns:
            Dict with updated page object.
        """
        self._ensure_client()
        try:
            response = self._client.pages.update(
                page_id=page_id,
                properties=properties
            )
            return response
        except Exception as exc:
            raise MCPConnectionError(f"Failed to update page: {exc}") from exc
