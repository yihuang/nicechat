# NiceChat

A rich featured LLM chat UI using [NiceGUI](https://nicegui.io/) and pure python.

## Installation

```bash
uv pip install nicechat
```

## Features

- Minimal NiceGUI based web interface
- Markdown rendering with rich format support:
  - LaTeX math
  - tables
  - wavedrom
  - mermaid

- Small code base, easy to customize
- MCP support (TODO)
- Persistent chat history in plain text file
- Streaming responses

## Usage

### Web Interface
```bash
# Web interface (default)
nicechat --api-key YOUR_API_KEY --model deepseek-chat

# Native desktop window
nicechat --api-key YOUR_API_KEY --model deepseek-chat --native
```

## Development

```bash
# Setup environment
uv venv
uv pip install -e .[dev]

# Run tests
pytest

# Run development server
uvicorn nicechat.app:main --reload
```
