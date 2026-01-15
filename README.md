# Space: Local AI Coding Assistant

Space is a powerful, fully local CLI coding assistant powered by Ollama. It is designed to be a private, secure, and capable alternative to cloud-based coding assistants, offering a rich terminal user interface and a wide range of file and system operations.

## 🚀 Features

-   **100% Local Inference**: Runs entirely on your machine using Ollama models (e.g., Qwen, Llama 3). No data leaves your system.
-   **Plan-Execute Workflow**: For complex tasks, Space creates detailed implementation plans and requests user approval before making changes.
-   **Rich Terminal UI**:
    -   **Live Spinners**: Visual feedback during AI processing.
    -   **Streaming Output**: Real-time response generation.
    -   **Markdown Rendering**: Beautifully formatted text and code in the terminal.
    -   **Panel Layouts**: Organized output for tools and messages.
-   **Comprehensive Toolset**:
    -   **File Operations**: Read, write, edit, delete, copy, move, and append to files.
    -   **Search**: Regex search within files, grep across directories, and file finding.
    -   **Git Integration**: Check status, view diffs, log history, stage files, and commit changes.
    -   **Code Quality**: Syntax checking, linting (Ruff), and auto-formatting.
    -   **System**: Run shell commands and manage Python packages.
    -   **Sandbox**: Execute Python code in a safe, isolated environment.

---

## 🛡️ Agent Reliability Features

Space implements multiple reliability mechanisms to ensure robust, predictable behavior even with smaller local models:

### 1. LLM Hallucination Correction

Local models sometimes wrap tool arguments incorrectly. Space automatically detects and fixes nested argument structures:

```python
# Handles malformed tool calls like:
# {"arguments": {"arguments": {"code": "..."}, "function_name": "python_repl"}}
# Automatically unwrapped to:
# {"code": "..."}
```

This ensures tool execution succeeds even when the model produces slightly malformed outputs.

### 2. Plan-Execute Workflow with Human Approval

For complex tasks, the agent follows a structured workflow:

1. **Analyze** the request and gather context
2. **Generate** a detailed step-by-step implementation plan
3. **Request approval** from the user before proceeding
4. **Execute** only after explicit confirmation

This prevents unintended file modifications and gives users full control over changes.

### 3. Sandboxed Code Execution

The `python_repl` tool executes code in a fully isolated environment:

- **Process Isolation**: Uses `multiprocessing` to run code in a separate process
- **Timeout Enforcement**: 5-second hard limit prevents infinite loops
- **Output Capture**: Captures both stdout and stderr cleanly
- **Graceful Termination**: Processes are terminated if they exceed the timeout

```python
# Safe execution with automatic cleanup
process.join(timeout=5)
if process.is_alive():
    process.terminate()  # Force stop runaway code
```

### 4. Command Execution Safeguards

Shell commands are executed with multiple safety measures:

- **60-second timeout** to prevent hanging operations
- **Working directory validation** before execution
- **Bash shell explicitly used** for consistent behavior
- **Stdout/stderr separation** for clear error reporting

### 5. Code Quality Pipeline

After writing or editing Python code, the agent follows a quality assurance workflow:

```
write_file → check_syntax → lint_file → format_file
```

| Step | Tool | Purpose |
|------|------|---------|
| 1 | `check_syntax` | Fast AST-based syntax validation |
| 2 | `lint_file` | Ruff checks for bugs, style issues (auto-fix available) |
| 3 | `format_file` | PEP 8 compliant formatting |

### 6. Robust Error Handling

Every tool operation is wrapped with comprehensive error handling:

- **File existence checks** before editing
- **Permission validation** before read/write
- **Graceful fallbacks** with descriptive error messages
- **Tool not found** handling for unknown function calls

### 7. Streaming with Live Feedback

The agent uses streaming responses with real-time UI updates:

- Users see the AI's thinking process as it streams
- Tool executions display progress spinners
- Output panels show truncated results (max 500 chars) to prevent terminal flooding

---

## 📋 Prerequisites

1.  **Ollama**: Install Ollama from [ollama.com](https://ollama.com).
2.  **Python 3.10+**: Ensure you have a recent version of Python installed.
3.  **Models**: Pull a coding-capable model. `qwen2.5-coder` or `qwen3` are recommended.
    ```bash
    ollama pull qwen2.5-coder:7b
    ```

## 🛠️ Installation

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd space-cli
    ```

2.  **Create a virtual environment**:
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -e .
    ```

## 💻 Usage

Start the assistant using the CLI entry point:

```bash
python -m space.main start
```

### Command Line Options

-   `--model`: Specify the Ollama model to use (default: `qwen3:4b`).
    ```bash
    python -m space.main start --model llama3
    ```

### Special Slash Commands

-   `/models`: List all available Ollama models on your system.
-   `/model <name>`: Switch to a different model instantly.
-   `/current`: Show the currently active model.
-   `/help`: Display the help menu.
-   `exit` or `quit`: Close the application.

## 🧠 Workflows

### 1. Planning Mode (Complex Tasks)
When you ask for a complex change (e.g., "Refactor the database module" or "Create a new web app"), Space enters **Planning Mode**:
1.  **Analyzes** the request.
2.  **Generates** a step-by-step implementation plan.
3.  **Asks** for your approval.
4.  **Executes** the plan only after you say "yes".

### 2. Direct Mode (Simple Tasks)
For straightforward requests, Space acts immediately:
-   "Read main.py" -> Displays content.
-   "Run ls -la" -> Shows directory listing.

## 🧰 Available Tools

| Category | Tool Name | Description |
| :--- | :--- | :--- |
| **File Ops** | `list_files` | List directory contents. |
| | `read_file` | Read file content. |
| | `write_file` | Write content to a file (creates dirs). |
| | `edit_file` | Replace exact text block in a file. |
| | `append_to_file` | Append text to a file. |
| | `delete_file` | Remove a file. |
| | `copy_file` | Copy a file. |
| | `move_file` | Move or rename a file. |
| | `create_directory` | Create a new directory. |
| | `get_file_info` | Get size and modification time. |
| **Advanced Editing** | `diff_preview` | Preview changes before applying them. |
| | `undo_edit` | Revert the last edit to a file. |
| | `batch_edit` | Apply the same edit to multiple files. |
| **Search & Nav** | `search_file` | Search text/regex in a single file. |
| | `grep_search` | Search pattern across a directory. |
| | `find_files` | Find files by filename pattern. |
| **Code Intelligence** | `check_syntax` | Fast Python syntax validation. |
| | `lint_file` | Lint with Ruff (supports auto-fix). |
| | `format_file` | Format code with Ruff. |
| | `analyze_project` | Analyze project structure and dependencies. |
| | `find_definition` | Find symbol definition. |
| | `find_references` | Find all references to a symbol. |
| **Git Integration** | `git_status` | Show working tree status. |
| | `git_diff` | Show changes. |
| | `git_log` | View commit history. |
| | `git_add` | Stage files. |
| | `git_commit` | Commit changes. |
| **System** | `run_command` | Execute shell commands (bash). |
| | `install_package` | Install pip packages. |
| | `list_installed_packages` | List pip packages. |
| | `wait` | Pause execution for a specified duration. |
| **Testing** | `run_tests` | Run tests (supporting various runners). |
| | `discover_tests` | Discover available tests. |
| **Web & MCP** | `fetch_url` | Fetch URL content as markdown. |
| | `search_web` | Search the web (DuckDuckGo). |
| | `add_mcp_server` | Connect to an MCP server. |
| | `remove_mcp_server` | Disconnect an MCP server. |
| **Sandbox** | `python_repl` | Execute Python code in a safe sandbox. |

## 📝 Examples

**Create a new project:**
> "Create a directory called 'my-app', add a main.py that prints hello world, and a requirements.txt."

**Refactor code:**
> "Search for all print statements in src/ and replace them with logging calls. Then format the files."

**Git workflow:**
> "Check git status, add all changes, and commit with message 'Initial feature implementation'."

**Data Analysis:**
> "Read data.csv and use python code to calculate the average of the 'score' column."

---

## 🏗️ Architecture

```
space/
├── main.py      # CLI entry point (Typer), slash commands, REPL loop
├── agent.py     # Core Agent class, tool registry, chat loop with streaming
├── llm.py       # Ollama client wrapper with streaming support
├── prompts.py   # System prompt with workflow instructions
├── tools.py     # All 20+ tool implementations
└── ui.py        # Rich terminal UI (banners, animations, panels)
```

## 📄 License

MIT License
