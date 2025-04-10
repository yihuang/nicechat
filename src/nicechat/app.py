"""NiceChat application module - contains the main chat UI implementation."""

import argparse
from nicegui import ui
from openai import OpenAI, AuthenticationError

def chat_ui(api_key: str = None, model: str = "gpt-3.5-turbo"):
    """Create a simple LLM chat interface.
    
    Args:
        api_key: OpenAI API key (optional)
        model: OpenAI model to use (default: gpt-3.5-turbo)
    """
    
    client = OpenAI(api_key=api_key) if api_key else None
    messages = []
    
    async def send_message():
        if not input.value.strip():
            return
            
        messages.append({'role': 'user', 'content': input.value})
        chat_messages.add_message('You', input.value)
        input.value = ''
        
        if not client:
            chat_messages.add_message('AI', '⚠️ Please provide an OpenAI API key')
            return
            
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages
            )
            reply = response.choices[0].message.content
            messages.append({'role': 'assistant', 'content': reply})
            chat_messages.add_message('AI', reply)
        except AuthenticationError:
            chat_messages.add_message('AI', '⚠️ Invalid API key')
        except Exception as e:
            chat_messages.add_message('AI', f'⚠️ Error: {str(e)}')
    
    with ui.column().classes('w-full max-w-2xl mx-auto'):
        chat_messages = ui.chat_message().classes('w-full')
        with ui.row().classes('w-full'):
            input = ui.input(placeholder='Message...').classes('flex-grow')
            ui.button('Send', on_click=send_message)
    
    ui.run(title=f"NiceChat - {model}")

def main():
    """Command line interface for NiceChat."""
    parser = argparse.ArgumentParser(description='NiceChat - Simple LLM Chat UI')
    parser.add_argument('--api-key', help='OpenAI API key')
    parser.add_argument('--model', default='gpt-3.5-turbo',
                       help='OpenAI model to use')
    args = parser.parse_args()
    
    chat_ui(api_key=args.api_key, model=args.model)

if __name__ in {"__main__", "__mp_main__"}:
    main()
