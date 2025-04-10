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
nicechat

# Native desktop window
nicechat --native

# Specify a different file to start a new thread
nicechat --history-file history.json
```

## Development

```bash
# Setup environment
uv venv
uv pip install -e .
```
