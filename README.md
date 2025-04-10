# NiceChat

A simple LLM chat UI using NiceGUI.

## Installation

```bash
uv pip install nicechat
```

## Features

- NiceGUI based interface
- OpenAI API integration
- Simple and clean design

## Usage

```python
from nicechat import chat_ui

# Run with your OpenAI API key
chat_ui(api_key="your-api-key-here")

# Or run without API key (will show placeholder responses)
chat_ui()
```

## Development

```bash
uv venv
uv pip install -e .
```
