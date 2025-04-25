"""LLM interaction module - handles communication with multiple LLM providers."""

import json
from enum import Enum, auto
from pathlib import Path

import httpx
from litellm import AuthenticationError, acompletion


class Provider(Enum):
    """Supported LLM providers."""

    LITELLM = auto()
    OPENAI = auto()
    ANTHROPIC = auto()


class LLMClient:
    """Handles LLM interactions and maintains conversation state."""

    def __init__(self, model: str, history_file: str = "chat_history.json"):
        """Initialize the LLM client.

        Args:
            model: Model to use, in litellm format, "provider/model_name"
            history_file: File to store chat history (default: chat_history.json)
        """
        self.history_file = Path(history_file)
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

        self._append_message(
            {
                "role": "user",
                "content": user_message,
                "timestamp": datetime.now().isoformat(),
            }
        )

        try:
            full_reply = ""

            response = await acompletion(
                model=self.model,
                messages=self.messages,
                stream=True,
            )

            async for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    chunk_content = chunk.choices[0].delta.content
                    full_reply += chunk_content
                    if callback and callback(chunk_content):
                        break
        except httpx.ReadError:
            # could be cancelled by user, or network error,
            # just keep the partial response
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
