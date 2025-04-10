"""LLM interaction module - handles all OpenAI API communication."""

from openai import OpenAI, AuthenticationError

class LLMClient:
    """Handles LLM interactions and maintains conversation state."""
    
    def __init__(self, api_key: str = None, model: str = "deepseek-chat"):
        """Initialize the LLM client.
        
        Args:
            api_key: DeepSeek API key (optional, falls back to DEEPSEEK_API_KEY env var)
            model: Model to use (default: deepseek-chat)
        """
        import os
        api_key = api_key or os.getenv('DEEPSEEK_API_KEY')
        self.client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com/v1") if api_key else None
        self.model = model
        self.messages = []
    
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
            
        self.messages.append({'role': 'user', 'content': user_message})
        
        if not self.client:
            return '⚠️ Please provide an OpenAI API key'
            
        try:
            full_reply = ""
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    chunk_content = chunk.choices[0].delta.content
                    full_reply += chunk_content
                    if callback:
                        callback(chunk_content)
            
            self.messages.append({'role': 'assistant', 'content': full_reply})
            return full_reply
        except AuthenticationError:
            return '⚠️ Invalid API key'
        except Exception as e:
            return f'⚠️ Error: {str(e)}'
