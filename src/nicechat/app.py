"""NiceChat application module - contains the main chat UI implementation."""

import argparse
from datetime import datetime

from nicegui import ui

from . import markdown_ext
from .llm import LLMClient

# https://github.com/trentm/python-markdown2/wiki/Extras
MARKDOWN_EXTRAS = [
    "latex2",
    "fenced-code-blocks",
    "tables",
    "wavedrom",
    "cuddled-lists",
    "footnotes",
    "pyshell",
    "smarty-pants",
    "strike",
    "spoiler",
    "task_list",
    "target-blank-links",
]


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


def chat_ui(llm_client: LLMClient, native: bool = False, dark_mode: bool = False):
    """Create a simple LLM chat interface.

    Args:
        llm_client: LLMClient instance for handling API requests.
        native: Run in native desktop window mode (default: False)
    """

    ui.dark_mode(dark_mode)
    with ui.column().classes("w-full max-w-4xl mx-auto"):
        chat_container = ui.column().classes("w-full")
        with ui.row().classes("w-full"):
            input = (
                ui.input(placeholder="Message...")
                .classes("flex-grow")
                .on("keydown.enter", lambda: send_message())
            )
            send_btn = (
                ui.button(icon="send")
                .props("flat dense")
                .on("click", lambda: send_message())
            )
            stop_btn = (
                ui.button(icon="stop")
                .props("flat dense")
                .on("click", lambda: cancel_stream())
                .bind_visibility_from(send_btn, "visible", value=False)
            )

    def render_message(
        role: str, content: str, timestamp: str = None, show_spinner: bool = False
    ):
        """Render a message in the chat UI."""
        spinner = None
        with chat_container:
            alignment = "justify-end" if role == "user" else "justify-start"
            bg_color = "bg-blue-100" if role == "user" else "bg-gray-100"
            sender = "You" if role == "user" else "AI"
            width = "max-w-[80%]" if role == "user" else "w-full"

            with ui.row().classes(f"w-full {alignment} mb-2"):
                with ui.column().classes(f"{bg_color} rounded-lg p-3 {width} gap-0"):
                    with ui.row().classes("items-center justify-between gap-4"):
                        ui.label(sender).classes("text-xs text-gray-500")
                        if timestamp:
                            dt = datetime.fromisoformat(timestamp)
                            ui.label(dt.strftime("%H:%M")).classes(
                                "text-xs text-gray-500"
                            )
                    if role == "assistant" and not content:
                        spinner = ui.spinner(size="sm")
                    response_text = ui.markdown(
                        content,
                        extras=MARKDOWN_EXTRAS,
                    ).classes("text-wrap w-full")

        return response_text, spinner

    # Load and display existing chat history
    for message in llm_client.messages:
        render_message(message["role"], message["content"], message.get("timestamp"))

    async def cancel_stream():
        await llm_client.stop_streaming()

    async def send_message():
        if not input.value.strip():
            return

        send_btn.visible = False
        user_message = input.value
        input.value = ""

        with chat_container:
            # Show user message
            render_message("user", user_message, datetime.now().isoformat())

            # Show loading indicator with custom styling
            response_text, spinner = render_message(
                "assistant", "", datetime.now().isoformat(), show_spinner=True
            )

            # Define callback for streaming chunks
            def update_response(chunk):
                nonlocal spinner
                if spinner is not None:
                    # Clean up loading indicator
                    spinner.delete()
                    spinner = None
                response_text.content += chunk
                fix_scroll()

            # Get AI response
            try:
                reply = await llm_client.send_message(
                    user_message, callback=update_response
                )
            finally:
                send_btn.visible = True

            response_text.content = reply

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
    parser.add_argument("--dark", action="store_true", help="Enable dark mode")
    args = parser.parse_args()

    llm_client = LLMClient(
        api_key=args.api_key,
        model=args.model,
        history_file=args.history_file,
    )
    chat_ui(llm_client, args.native, args.dark)


if __name__ in {"__main__", "__mp_main__"}:
    main()
