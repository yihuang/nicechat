"""LLM interaction module - handles all OpenAI API communication."""

import json
import os
from pathlib import Path

from openai import AsyncOpenAI, AuthenticationError


class LLMClient:
    """Handles LLM interactions and maintains conversation state."""

    def __init__(
        self,
        api_key: str = None,
        model: str = "deepseek-chat",
        history_file: str = "chat_history.json",
    ):
        """Initialize the LLM client.

        Args:
            api_key: DeepSeek API key (optional, falls back to DEEPSEEK_API_KEY env var)
            model: Model to use (default: deepseek-chat)
            history_file: File to store chat history (default: chat_history.json)
        """
        api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        self.history_file = Path(history_file)
        self.client = (
            AsyncOpenAI(api_key=api_key, base_url="https://api.deepseek.com/v1")
            if api_key
            else None
        )
        self.model = model
        self.messages = self._load_history()

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

        self.messages.append(
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
            # Use async for streaming
            stream = await self.client.chat.completions.create(
                model=self.model, messages=self.messages, stream=True
            )

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    chunk_content = chunk.choices[0].delta.content
                    full_reply += chunk_content
                    if callback:
                        callback(chunk_content)

            msg = {
                "role": "assistant",
                "content": full_reply,
                "timestamp": datetime.now().isoformat(),
            }
            self.messages.append(msg)
            self._save_message(msg)
            return full_reply
        except AuthenticationError:
            return "⚠️ Invalid API key"
        except Exception as e:
            return f"⚠️ Error: {str(e)}"

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
