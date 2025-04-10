"""NiceChat application module - contains the main chat UI implementation."""

import argparse

from nicegui import ui

from .llm import LLMClient


def chat_ui(api_key: str = None, model: str = "deepseek-chat"):
    """Create a simple LLM chat interface.

    Args:
        api_key: OpenAI API key (optional)
        model: OpenAI model to use (default: gpt-3.5-turbo)
    """
    llm_client = LLMClient(api_key=api_key, model=model)

    async def send_message():
        if not input.value.strip():
            return

        user_message = input.value
        input.value = ""

        with chat_container:
            # Show user message with custom styling
            with ui.row().classes("w-full justify-end mb-2"):
                with ui.column().classes("bg-blue-100 rounded-lg p-3 max-w-[80%]"):
                    ui.label("You").classes("text-xs text-gray-500")
                    ui.label(user_message).classes("text-wrap")
            
            # Show loading indicator with custom styling
            with ui.row().classes("w-full justify-start mb-2"):
                with ui.column().classes("bg-gray-100 rounded-lg p-3 max-w-[80%]"):
                    with ui.row().classes("items-center gap-2"):
                        loading = ui.spinner(size="sm")
                        ui.label("Thinking...").classes("text-gray-500")
            # Create response container with markdown support
            response_text = ui.markdown("").classes("text-wrap")

            # Define callback for streaming chunks
            def update_response(chunk):
                nonlocal loading
                if loading is not None:
                    # Clean up loading indicator
                    loading.delete()
                    text = None
                if loading is not None:
                    # First chunk - create AI message container
                    loading.delete()
                    loading = None
                    with ui.row().classes("w-full justify-start mb-2"):
                        with ui.column().classes("bg-gray-100 rounded-lg p-3 max-w-[80%]"):
                            ui.label("AI").classes("text-xs text-gray-500")
                            response_text = ui.markdown("").classes("text-wrap")
                response_text.content += chunk
                ui.update(response_text)

            # Get AI response
            reply = await llm_client.send_message(
                user_message, callback=update_response
            )

    with ui.column().classes("w-full max-w-2xl mx-auto"):
        chat_container = ui.column().classes("w-full")
        with ui.row().classes("w-full"):
            input = (
                ui.input(placeholder="Message...")
                .classes("flex-grow")
                .on("keydown.enter", lambda: send_message())
            )
            ui.button("Send", on_click=lambda: send_message())

    ui.run(title=f"NiceChat - {model}")


def main():
    """Command line interface for NiceChat."""
    parser = argparse.ArgumentParser(description="NiceChat - Simple LLM Chat UI")
    parser.add_argument(
        "--api-key", help="DeepSeek API key (defaults to DEEPSEEK_API_KEY env var)"
    )
    parser.add_argument("--model", default="deepseek-chat", help="OpenAI model to use")
    args = parser.parse_args()

    chat_ui(api_key=args.api_key, model=args.model)


if __name__ in {"__main__", "__mp_main__"}:
    main()
