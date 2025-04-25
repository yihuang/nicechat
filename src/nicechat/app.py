"""NiceChat application module - contains the main chat UI implementation."""

import argparse
from datetime import datetime

from nicegui import ui

from . import markdown_ext
from .llm import LLMClient

# https://github.com/trentm/python-markdown2/wiki/Extras
MARKDOWN_EXTRAS = [
    "latex2",
    "fenced-code-blocks2",
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
const scrollThreshold = 200; // pixels from bottom
const nearBottom = window.innerHeight + window.scrollY >= document.body.offsetHeight - scrollThreshold;
if (nearBottom) {
    // scroll to bottom with smooth behavior
    window.scrollTo(0, document.body.scrollHeight);
}
                """
    )


def global_style():
    ui.add_head_html(
        """
    <style>
    .markdown-body {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        line-height: 1.6;
    }
    .markdown-body p {
        margin: 0.5em 0;
    }
    .markdown-body pre {
        background-color: rgba(0,0,0,0.05);
        border-radius: 6px;
        padding: 1em;
        overflow-x: auto;
        margin-bottom: 0;
    }
    .code-block-container {
        position: relative;
    }
    .copy-button {
        position: absolute;
        top: 0.5em;
        right: 0.5em;
        // background: rgba(0,0,0,0.1);
        border: none;
        border-radius: 4px;
        padding: 0.25em;
        cursor: pointer;
        opacity: 0;
        transition: opacity 0.2s;
    }
    .code-block-container:hover .copy-button {
        opacity: 1;
    }
    .dark .copy-button {
        background: rgba(255,255,255,0.1);
    }
    .markdown-body code {
        font-family: ui-monospace, SFMono-Regular, SF Mono, Menlo, Consolas, Liberation Mono, monospace;
        border-radius: 3px;
        font-size: 0.9em;
    }
    .dark .markdown-body pre {
        background-color: rgba(255,255,255,0.05);
    }
    .markdown-body blockquote {
        border-left: 4px solid #ddd;
        padding-left: 1em;
        margin-left: 0;
        color: #777;
    }
    .dark .markdown-body blockquote {
        border-left-color: #444;
        color: #aaa;
    }
    </style>
    """
    )


def chat_ui(llm_client: LLMClient):
    """Create a simple LLM chat interface.

    Args:
        llm_client: LLMClient instance for handling API requests.
    """
    # Add markdown styling
    global_style()
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
            bg_color = "bg-blue-500/10" if role == "user" else "bg-gray-500/10"
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
                    if role == "assistant" and show_spinner:
                        spinner = ui.spinner(size="sm")
                    response_text = ui.markdown(
                        content,
                        extras=MARKDOWN_EXTRAS,
                    ).classes("text-wrap w-full markdown-body")

        return response_text, spinner

    # Load and display existing chat history
    for message in llm_client.messages:
        render_message(message["role"], message["content"], message.get("timestamp"))

    stream_stopped = False

    async def cancel_stream():
        nonlocal stream_stopped
        stream_stopped = True

    async def send_message():
        nonlocal stream_stopped
        if not input.value.strip():
            return

        send_btn.visible = False
        user_message = input.value
        input.value = ""
        stream_stopped = False

        with chat_container:
            # Show user message
            render_message("user", user_message, datetime.now().isoformat())
            fix_scroll()  # Scroll to bottom after user message

            # Show loading indicator with custom styling
            response_text, spinner = render_message(
                "assistant", "", datetime.now().isoformat(), show_spinner=True
            )
            fix_scroll()  # Scroll to bottom after showing spinner

            # Define callback for streaming chunks
            def update_response(chunk):
                nonlocal spinner
                if spinner is not None:
                    # Clean up loading indicator
                    spinner.delete()
                    spinner = None
                response_text.content += chunk
                fix_scroll()

                return stream_stopped

            # Get AI response
            try:
                await llm_client.send_message(user_message, callback=update_response)
            finally:
                send_btn.visible = True
                update_response("")


def main():
    """Command line interface for NiceChat."""
    parser = argparse.ArgumentParser(description="NiceChat - Simple LLM Chat UI")
    parser.add_argument(
        "--model",
        default="deepseek/deepseek-chat",
        help='Model to use, in litellm format, "provider/model_name", (default: deepseek/deepseek-chat)',
    )
    parser.add_argument(
        "--history-file", default="chat_history.json", help="File to store chat history"
    )
    parser.add_argument(
        "--native", action="store_true", help="Run in native desktop window mode"
    )
    parser.add_argument("--dark", action="store_true", help="Enable dark mode")
    args = parser.parse_args()

    llm_client = LLMClient(args.model, args.history_file)
    ui.dark_mode(args.dark)
    chat_ui(llm_client)
    ui.run(title=f"NiceChat - {llm_client.model}", native=args.native)


main()
