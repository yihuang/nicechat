"""NiceChat package - a simple LLM chat UI using NiceGUI."""

__version__ = "0.1.0"

from nicegui import ui
from openai import OpenAI

def chat_ui(api_key: str = None, model: str = "gpt-3.5-turbo"):
    """Create a simple LLM chat interface."""
    
    client = OpenAI(api_key=api_key) if api_key else None
    messages = []
    
    async def send_message():
        if not input.value.strip():
            return
            
        messages.append({'role': 'user', 'content': input.value})
        chat_messages.add_message('You', input.value)
        input.value = ''
        
        if client:
            response = client.chat.completions.create(
                model=model,
                messages=messages
            )
            reply = response.choices[0].message.content
            messages.append({'role': 'assistant', 'content': reply})
            chat_messages.add_message('AI', reply)
        else:
            chat_messages.add_message('AI', 'Please provide an OpenAI API key')
    
    with ui.column().classes('w-full max-w-2xl mx-auto'):
        chat_messages = ui.chat_message().classes('w-full')
        with ui.row().classes('w-full'):
            input = ui.input(placeholder='Message...').classes('flex-grow')
            ui.button('Send', on_click=send_message)
    
    ui.run()
