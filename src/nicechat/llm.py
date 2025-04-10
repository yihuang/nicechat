"""LLM interaction module - handles all OpenAI API communication."""

from openai import OpenAI, AuthenticationError

class LLMClient:
    """Handles LLM interactions and maintains conversation state."""
    
    def __init__(self, api_key: str = None, model: str = "gpt-3.5-turbo"):
        """Initialize the LLM client.
        
        Args:
            api_key: OpenAI API key (optional)
            model: OpenAI model to use (default: gpt-3.5-turbo)
        """
        self.client = OpenAI(api_key=api_key) if api_key else None
        self.model = model
        self.messages = []
    
    async def send_message(self, user_message: str) -> str:
        """Send a message to the LLM and get the response.
        
        Args:
            user_message: The user's message to send
            
        Returns:
            The AI's response or an error message
        """
        if not user_message.strip():
            return ""
            
        self.messages.append({'role': 'user', 'content': user_message})
        
        if not self.client:
            return '⚠️ Please provide an OpenAI API key'
            
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages
            )
            reply = response.choices[0].message.content
            self.messages.append({'role': 'assistant', 'content': reply})
            return reply
        except AuthenticationError:
            return '⚠️ Invalid API key'
        except Exception as e:
            return f'⚠️ Error: {str(e)}'
