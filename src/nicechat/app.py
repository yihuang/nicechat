"""NiceChat application module - contains the main chat UI implementation."""

import argparse
from datetime import datetime

from nicegui import ui

from . import markdown_ext
from .llm import LLMClient


def fix_scroll():
    ui.run_javascript(
        """
const scrollThreshold = 100; // pixels from bottom
const nearBottom = window.innerHeight + window.scrollY >= document.body.offsetHeight - scrollThreshold;
if (nearBottom) {
    window.scrollTo(0, document.body.scrollHeight);
}
                """
    )


def chat_ui(llm_client: LLMClient, native: bool = False):
    """Create a simple LLM chat interface.

    Args:
        llm_client: LLMClient instance for handling API requests.
        native: Run in native desktop window mode (default: False)
    """

    with ui.column().classes("w-full max-w-2xl mx-auto"):
        chat_container = ui.column().classes("w-full")
        with ui.row().classes("w-full"):
            input = (
                ui.input(placeholder="Message...")
                .classes("flex-grow")
                .on("keydown.enter", lambda: send_message())
            )
            ui.button("Send", on_click=lambda: send_message())

    def render_message(role: str, content: str, timestamp: str = None):
        """Render a message in the chat UI."""
        nonlocal chat_container
        with chat_container:
            alignment = "justify-end" if role == "user" else "justify-start"
            bg_color = "bg-blue-100" if role == "user" else "bg-gray-100"
            sender = "You" if role == "user" else "AI"

            with ui.row().classes(f"w-full {alignment} mb-2"):
                with ui.column().classes(f"{bg_color} rounded-lg p-3 max-w-[80%]"):
                    with ui.row().classes("items-center justify-between gap-4"):
                        ui.label(sender).classes("text-xs text-gray-500")
                        if timestamp:
                            from datetime import datetime

                            dt = datetime.fromisoformat(timestamp)
                            ui.label(dt.strftime("%H:%M")).classes(
                                "text-xs text-gray-500"
                            )
                    ui.markdown(
                        content,
                        extras=[
                            "latex2",
                            "fenced-code-blocks",
                            "tables",
                            "wavedrom",
                        ],
                    ).classes("text-wrap")

    # Load and display existing chat history
    for message in llm_client.messages:
        render_message(message["role"], message["content"], message.get("timestamp"))

    async def send_message():
        if not input.value.strip():
            return

        user_message = input.value
        input.value = ""

        with chat_container:
            # Show user message
            render_message("user", user_message, datetime.now().isoformat())

            # Show loading indicator with custom styling
            with ui.row().classes("w-full justify-start mb-2"):
                with ui.column().classes("bg-gray-100 rounded-lg p-3 max-w-[80%]"):
                    ui.label("AI").classes("text-xs text-gray-500")
                    with ui.row().classes("items-center gap-2"):
                        loading = ui.spinner(size="sm")
                        # Create response container with markdown support
                        response_text = ui.markdown(
                            "",
                            extras=[
                                "latex2",
                                "fenced-code-blocks",
                                "tables",
                                "wavedrom",
                            ],
                        ).classes("text-wrap")

            # Define callback for streaming chunks
            def update_response(chunk):
                nonlocal loading
                if loading is not None:
                    # Clean up loading indicator
                    loading.delete()
                    loading = None
                response_text.content += chunk
                ui.update(response_text)
                fix_scroll()

            # Get AI response
            reply = await llm_client.send_message(
                user_message, callback=update_response
            )

    ui.run(title=f"NiceChat - {llm_client.model}", native=native)


def main():
    """Command line interface for NiceChat."""
    parser = argparse.ArgumentParser(description="NiceChat - Simple LLM Chat UI")
    parser.add_argument(
        "--api-key", help="DeepSeek API key (defaults to DEEPSEEK_API_KEY env var)"
    )
    parser.add_argument("--model", default="deepseek-chat", help="OpenAI model to use")
    parser.add_argument(
        "--history-file", default="chat_history.json", help="File to store chat history"
    )
    parser.add_argument(
        "--native", action="store_true", help="Run in native desktop window mode"
    )
    args = parser.parse_args()

    llm_client = LLMClient(
        api_key=args.api_key, model=args.model, history_file=args.history_file
    )
    chat_ui(llm_client, args.native)


if __name__ in {"__main__", "__mp_main__"}:
    main()
