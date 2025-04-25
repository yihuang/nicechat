"""LLM interaction module - handles communication with multiple LLM providers."""

import json
import os
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, Optional

import httpx
from litellm import acompletion, AuthenticationError


class Provider(Enum):
    """Supported LLM providers."""

    LITELLM = auto()
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
        self.api_key = api_key or os.getenv(self._get_api_key_env_var())
        return None  # LiteLLM doesn't need a persistent client

    def _get_api_key_env_var(self) -> str:
        """Get the appropriate API key environment variable name."""
        return {
            Provider.LITELLM: "LITELLM_API_KEY",
            Provider.OPENAI: "OPENAI_API_KEY",
            Provider.ANTHROPIC: "ANTHROPIC_API_KEY",
        }.get(self.provider, "LITELLM_API_KEY")

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

            response = await acompletion(
                model=self.model,
                messages=self.messages,
                stream=True,
                api_key=self.api_key
            )
            
            async for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    chunk_content = chunk.choices[0].delta.content
                    full_reply += chunk_content
                    if callback:
                        callback(chunk_content)
        except httpx.ReadError:
            # could be cancelled by user, or network error, just keep the partial response
            pass
        except AuthenticationError:
            return "⚠️ Invalid API key"
        except Exception as e:
            return f"⚠️ Error: {str(e)}"

        self._append_message(
            {
                "role": "assistant",
                "content": full_reply,
                "timestamp": datetime.now().isoformat(),
            }
        )
        return full_reply

    async def stop_streaming(self):
        """Stop streaming messages from the LLM."""
        # LiteLLM handles streaming cancellation internally
        print("Streaming stopped")

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
