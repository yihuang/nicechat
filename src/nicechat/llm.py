"""LLM interaction module - handles communication with multiple LLM providers."""

import json
import os
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, Optional

import anthropic
from openai import AsyncOpenAI, AuthenticationError


class Provider(Enum):
    """Supported LLM providers."""

    DEEPSEEK = auto()
    OPENAI = auto()
    ANTHROPIC = auto()


class LLMClient:
    """Handles LLM interactions and maintains conversation state."""

    def __init__(
        self,
        api_key: str = None,
        model: str = "deepseek-chat",
        history_file: str = "chat_history.json",
        provider: Provider = Provider.DEEPSEEK,
    ):
        """Initialize the LLM client.

        Args:
            api_key: API key (optional, falls back to provider-specific env vars)
            model: Model to use (default: deepseek-chat)
            history_file: File to store chat history (default: chat_history.json)
            provider: LLM provider to use (default: DEEPSEEK)
        """
        self.history_file = Path(history_file)
        self.model = model
        self.provider = provider
        self.client = self._init_client(api_key)
        self.messages = self._load_history()

    def _init_client(self, api_key: Optional[str]) -> Any:
        """Initialize the appropriate client based on provider."""
        api_key = api_key or os.getenv(self._get_api_key_env_var())
        if not api_key:
            return None

        if self.provider == Provider.DEEPSEEK:
            return AsyncOpenAI(api_key=api_key, base_url="https://api.deepseek.com/v1")
        elif self.provider == Provider.OPENAI:
            return AsyncOpenAI(api_key=api_key)
        elif self.provider == Provider.ANTHROPIC:
            return anthropic.AsyncAnthropic(api_key=api_key)
        return None

    def _get_api_key_env_var(self) -> str:
        """Get the appropriate API key environment variable name."""
        return {
            Provider.DEEPSEEK: "DEEPSEEK_API_KEY",
            Provider.OPENAI: "OPENAI_API_KEY",
            Provider.ANTHROPIC: "ANTHROPIC_API_KEY",
        }.get(self.provider, "DEEPSEEK_API_KEY")

    async def send_message(self, user_message: str, callback=None) -> str:
        """Send a message to the LLM and get the response.

        Args:
            user_message: The user's message to send
            callback: Optional function to call with each chunk of the response

        Returns:
            The complete AI's response or an error message
        """
        if not user_message.strip():
            return ""

        from datetime import datetime

        self._append_message(
            {
                "role": "user",
                "content": user_message,
                "timestamp": datetime.now().isoformat(),
            }
        )

        if not self.client:
            return "⚠️ Please provide an OpenAI API key"

        try:
            full_reply = ""

            if self.provider in (Provider.DEEPSEEK, Provider.OPENAI):
                stream = await self.client.chat.completions.create(
                    model=self.model, messages=self.messages, stream=True
                )
                async for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        chunk_content = chunk.choices[0].delta.content
                        full_reply += chunk_content
                        if callback:
                            callback(chunk_content)

            elif self.provider == Provider.ANTHROPIC:
                async with self.client.messages.stream(
                    model=self.model,
                    messages=self.messages,
                    max_tokens=4096,
                ) as stream:
                    async for chunk in stream:
                        if chunk.content:
                            chunk_content = chunk.content[0].text
                            full_reply += chunk_content
                            if callback:
                                callback(chunk_content)

            self._append_message(
                {
                    "role": "assistant",
                    "content": full_reply,
                    "timestamp": datetime.now().isoformat(),
                }
            )
            return full_reply
        except AuthenticationError:
            return "⚠️ Invalid API key"
        except Exception as e:
            return f"⚠️ Error: {str(e)}"

    def _append_message(self, message: dict):
        """Append a message to the chat history."""
        self.messages.append(message)
        self._save_message(message)

    def _save_message(self, message: dict):
        """Save chat history to file as JSONL (one message per line)."""
        try:
            with open(self.history_file, "a") as f:
                f.write(json.dumps(message) + "\n")
        except Exception as e:
            print(f"Warning: Failed to save chat history: {e}")

    def _load_history(self):
        """Load chat history from JSONL file."""
        try:
            if self.history_file.exists():
                with open(self.history_file) as f:
                    return [json.loads(line) for line in f if line.strip()]
        except Exception as e:
            print(f"Warning: Failed to load chat history: {e}")
        return []
