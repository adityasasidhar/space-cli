#  SPACE CLI

![Python](https://img.shields.io/badge/Python-3.12%2B-blue?style=for-the-badge&logo=python)
![Ollama](https://img.shields.io/badge/Powered%20By-Ollama-white?style=for-the-badge&logo=ollama)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Beta-orange?style=for-the-badge)

**The Private, Agentic Coding Assistant for your Terminal.**

Space is a next-generation CLI tool that turns your local LLMs (via Ollama) into autonomous coding agents. It doesn't just autocomplete—it **plans**, **searches**, **edits**, and **executes**.

> "Like GitHub Copilot Workspace or Claude Code, but running 100% locally on your machine."

---

## Why Space?

*   **🔒 100% Privacy**: Your code never leaves your machine. Powered by local models like `qwen2.5-coder` or `llama3`.
*   **🧠 Agentic Workflow**: Space doesn't guess; it creates an implementation plan, asks for your approval, and then executes complex multi-file changes.
*   **🕸️ IRL-Level Research**: Built-in **Deep Search** capabilities allow the agent to search the web and read documentation pages concurrently to solve problems.
*   **🔌 Unlimited Extensibility**: First-class support for **MCP (Model Context Protocol)**. Connect your agent to databases, Slack, GitHub, or any other API via MCP servers.
*   **🛡️ Safety First**: Sandboxed execution, syntax checking, linting, and "undo" capabilities ensure your codebase stays healthy.

---

## Key Features

### Powerful Toolset
*   **File Mastery**: Read, write, edit, delete, and organize files with safety checks.
*   **Git Integration**: `git status`, `diff`, `log`, `add`, and `commit` directly from the agent.
*   **System Control**: Run bash commands and manage packages.
*   **Code Intelligence**: AST-based syntax checking, `ruff` linting/formatting, and symbol navigation.

### 🌐 Web & Connectivity
*   **`search_web`**: Search DuckDuckGo for answers.
*   **Deep Search**: Auto-crawls top results to read full documentation and tutorials.
*   **`fetch_url`**: Read any URL (including JS-heavy sites) as clean Markdown.
*   **MCP Support**: Add/remove MCP servers on the fly to give the agent new superpowers.

### 💻 User Experience
*   **Rich UI**: Beautiful terminal output with live spinners, markdown rendering, and syntax highlighting.
*   **Streaming**: Watch the agent "think" and generating responses in real-time.
*   **Interactive REPL**: A safe Python sandbox for the agent to test logic before writing code.

---

## Installation

Prerequisites: **Python 3.12+** and **[Ollama](https://ollama.com)**.

1.  **Clone the repo**
    ```bash
    git clone https://github.com/adityasasidhar/space-cli.git
    cd space-cli
    ```

2.  **Install** (using `uv` is recommended, but `pip` works too)
    ```bash
    pip install -e .
    ```

3.  **Pull a Model**
    ```bash
    ollama pull qwen2.5-coder:7b
    ```

4.  **Launch**
    ```bash
    python -m space.main start --model qwen2.5-coder:7b
    ```

---

##  Usage Examples

### 1. The "Research & Fix" Flow
Space can go online to find solutions.
> "I'm getting a 'ConnectionRefused' error with my Redis setup. **Search the web** for common causes and fixes, then check my `config.py` to see if I made a mistake."

### 2. The "Refactor" Flow
Space treats code quality seriously.
> "Analyze the `src/` directory. Find all functions longer than 50 lines, refactor them into smaller helpers, and run the linter to ensure everything is PEP 8 compliant."

### 3. The "New Feature" Flow
Space plans before it acts.
> "I want to add a new `/stats` endpoint to my FastAPI app. Create a plan to add the route, the service logic, and a unit test. Ask me for approval before writing code."

### 4. The "MCP" Flow
Connect external tools.
> "Add the **Postgres MCP server**. Then, inspect my database schema and suggest indices for the `users` table."

---

##  Slash Commands

*   `/models`: List available Ollama models.
*   `/model <name>`: Switch models instantly (e.g., `/model deepseek-r1`).
*   `/mcp_config`: Open the MCP configuration file in your editor.
*   `/help`: Show available commands and tools.
*   `/clear`: Clear the conversation history.

---

##  Architecture

Space is built on a modular "Brain" architecture:

*   **`Agent`**: The core orchestrator. Manages memory, context window, and tool dispatch.
*   **`McpManager`**: Handles connections to external MCP servers via stdio.
*   **`Web`**: Powers `fetch_url` (Crawl4AI) and `search_web` (DuckDuckGo).
*   **`Tools`**: A registry of 30+ native capabilities (File, Git, System).
*   **`UI`**: A stunning interface powered by `rich` and `prompt_toolkit`.

---

## Contributing

We love contributions!
1.  Fork the repo.
2.  Create a feature branch.
3.  Submit a PR.

**License**: MIT
