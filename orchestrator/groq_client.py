"""Groq LLM client for the orchestrator.

This module provides a client that implements the LLMClient protocol expected
by SpecGenerator, using Groq's API.
"""

from __future__ import annotations

import os
from typing import Protocol


class GroqClient:
    """Groq API client for spec generation.
    
    Implements the interface expected by SpecGenerator:
    - complete(system_prompt, user_prompt, temperature, timeout) -> str
    """
    
    def __init__(
        self,
        api_key: str | None = None,
        model: str = "llama-3.3-70b-versatile",
    ):
        """Initialize the Groq client.
        
        Args:
            api_key: Groq API key. If None, reads from GROQ_API_KEY env var.
            model: Model to use. Defaults to llama-3.3-70b-versatile.
                   Other options: mixtral-8x7b-32768, llama-3.1-70b-versatile
        """
        self.api_key = api_key or self._get_api_key_from_env()
        self.model = model
        self._client = None
    
    def _get_api_key_from_env(self) -> str:
        """Get API key from environment."""
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError(
                "GROQ_API_KEY environment variable not set. "
                "Please set your Groq API key."
            )
        return api_key
    
    def _ensure_client(self):
        """Lazy-load the Groq client."""
        if self._client is None:
            try:
                from groq import Groq
                self._client = Groq(api_key=self.api_key)
            except ImportError:
                raise ImportError(
                    "groq package not installed. Install with: pip install groq"
                )
    
    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
        timeout: float = 120.0,
    ) -> str:
        """Generate a completion using Groq API.
        
        Args:
            system_prompt: System prompt to set context.
            user_prompt: User prompt with the actual request.
            temperature: Sampling temperature (0.0 to 2.0).
            timeout: Request timeout in seconds.
        
        Returns:
            The model's text response.
        
        Raises:
            Exception: If the API call fails.
        """
        self._ensure_client()
        
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                max_tokens=8000,  # Groq supports up to 32k for some models
                timeout=timeout,
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            raise Exception(f"Groq API call failed: {e}") from e
