import json
import time
from typing import List, Dict, Any
import ollama
from .llm import ChatModel
from .tools import (
    list_files, read_file, write_file, edit_file, run_command,
    search_file, grep_search, find_files,
    delete_file, create_directory, move_file, copy_file, append_to_file, get_file_info,
    git_status, git_diff, git_log, git_commit, git_add,
    install_package, list_installed_packages,
    check_syntax, lint_file, format_file,
    python_repl,
    diff_preview, undo_edit, batch_edit,
    wait
)
from .project import (
    analyze_project, run_tests, discover_tests, find_definition, find_references
)
from .prompts import SYSTEM_PROMPT
from .memory import SessionManager, ContextWindow, RetryHandler
from .mcp import McpManager
from .web import fetch_url, search_web
from rich.console import Console

console = Console()

class Agent:
    def __init__(self, model_name: str = "qwen3:4b", session_id: str = None):
        self.model_name = model_name
        self.llm = ChatModel(model=model_name)
        
        # Build system prompt with custom instructions if space.md exists
        system_prompt = self._build_system_prompt()
        self.messages: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}]
        
        # Session and context management
        self.session_manager = SessionManager()
        self.context_window = ContextWindow(max_tokens=8192)
        self.retry_handler = RetryHandler(max_retries=3)
        self.mcp_manager = McpManager()
        self.mcp_manager.connect_all()
        
        # Load existing session or start new one
        if session_id:
            try:
                self.messages = self.session_manager.load_session(session_id)
                console.print(f"[dim]Resumed session: {session_id}[/dim]")
            except FileNotFoundError:
                console.print(f"[yellow]Session '{session_id}' not found, starting new session[/yellow]")
                self.session_manager.new_session()
        else:
            self.session_manager.new_session()
            
        self._init_tools()
    
    def _build_system_prompt(self) -> str:
        """Build system prompt with optional custom instructions from space.md"""
        import os
        from pathlib import Path
        
        prompt = SYSTEM_PROMPT
        
        # Look for space.md in current directory
        space_md_path = Path(os.getcwd()) / "space.md"
        
        if space_md_path.exists():
            try:
                custom_instructions = space_md_path.read_text().strip()
                if custom_instructions:
                    prompt += f"\n\n<custom_instructions>\n{custom_instructions}\n</custom_instructions>"
                    console.print(f"[dim]✓ Loaded custom instructions from space.md[/dim]")
            except Exception as e:
                console.print(f"[yellow]Warning: Could not read space.md: {e}[/yellow]")
        
        return prompt
    
    def _init_tools(self):
        """Initialize tool definitions - called after _build_system_prompt"""
        self.tools = {
            "list_files": list_files,
            "read_file": read_file,
            "write_file": write_file,
            "edit_file": edit_file,
            "run_command": run_command,
            "search_file": search_file,
            "grep_search": grep_search,
            "find_files": find_files,
            "delete_file": delete_file,
            "create_directory": create_directory,
            "move_file": move_file,
            "copy_file": copy_file,
            "append_to_file": append_to_file,
            "get_file_info": get_file_info,
            "git_status": git_status,
            "git_diff": git_diff,
            "git_log": git_log,
            "git_commit": git_commit,
            "git_add": git_add,
            "install_package": install_package,
            "list_installed_packages": list_installed_packages,
            "check_syntax": check_syntax,
            "lint_file": lint_file,
            "format_file": format_file,
            "python_repl": python_repl,
            "diff_preview": diff_preview,
            "undo_edit": undo_edit,
            "batch_edit": batch_edit,
            "analyze_project": analyze_project,
            "run_tests": run_tests,
            "discover_tests": discover_tests,
            "find_definition": find_definition,
            "find_references": find_references,
            "add_mcp_server": self.mcp_manager.add_server,
            "remove_mcp_server": self.mcp_manager.remove_server,
            "wait": wait,
            "fetch_url": fetch_url,
            "search_web": search_web,
        }
        self.tool_definitions = [
            {
                "type": "function",
                "function": {
                    "name": "list_files",
                    "description": "List files in a directory",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "The directory path (default: current directory)"}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Read the content of a file",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "The file path"}
                        },
                        "required": ["path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "write_file",
                    "description": "Write content to a file. Creates parent directories automatically if they don't exist.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "The file path (can be nested, e.g., 'dir/subdir/file.txt')"},
                            "content": {"type": "string", "description": "The content to write"}
                        },
                        "required": ["path", "content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "edit_file",
                    "description": "Replace text in a file. The old_text must match exactly (including whitespace).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "The file path"},
                            "old_text": {"type": "string", "description": "The exact text to replace (must match precisely)"},
                            "new_text": {"type": "string", "description": "The new text"}
                        },
                        "required": ["path", "old_text", "new_text"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "run_command",
                    "description": "Run a shell command using bash. Supports advanced features like 'source', pipes, and redirects.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {"type": "string", "description": "The bash command to run"},
                            "cwd": {"type": "string", "description": "Optional working directory for the command (default: current directory)"}
                        },
                        "required": ["command"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_file",
                    "description": "Search for a pattern in a file",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "The file path"},
                            "pattern": {"type": "string", "description": "The pattern to search for"},
                            "use_regex": {"type": "boolean", "description": "Whether to use regex"}
                        },
                        "required": ["path", "pattern"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "grep_search",
                    "description": "Search for a pattern across multiple files in a directory",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "directory": {"type": "string", "description": "The directory to search"},
                            "pattern": {"type": "string", "description": "The pattern to search for"},
                            "file_pattern": {"type": "string", "description": "File pattern to match (e.g., '*.py')"}
                        },
                        "required": ["directory", "pattern"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "find_files",
                    "description": "Find files by name pattern",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "directory": {"type": "string", "description": "The directory to search"},
                            "name_pattern": {"type": "string", "description": "File name pattern (e.g., '*.py')"}
                        },
                        "required": ["directory", "name_pattern"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "delete_file",
                    "description": "Delete a file",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "The file path to delete"}
                        },
                        "required": ["path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_directory",
                    "description": "Create a new directory",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "The directory path to create"}
                        },
                        "required": ["path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "move_file",
                    "description": "Move or rename a file",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "source": {"type": "string", "description": "Source file path"},
                            "destination": {"type": "string", "description": "Destination file path"}
                        },
                        "required": ["source", "destination"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "copy_file",
                    "description": "Copy a file",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "source": {"type": "string", "description": "Source file path"},
                            "destination": {"type": "string", "description": "Destination file path"}
                        },
                        "required": ["source", "destination"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "append_to_file",
                    "description": "Append content to a file",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "The file path"},
                            "content": {"type": "string", "description": "The content to append"}
                        },
                        "required": ["path", "content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_file_info",
                    "description": "Get file metadata (size, modified time, etc.)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "The file path"}
                        },
                        "required": ["path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "git_status",
                    "description": "Get git status of the repository",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "git_diff",
                    "description": "Show git diff for uncommitted changes",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string", "description": "Optional file path to diff"}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "git_log",
                    "description": "View git commit history",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "num_commits": {"type": "integer", "description": "Number of commits to show"}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "git_commit",
                    "description": "Commit staged changes with a message",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "message": {"type": "string", "description": "Commit message"}
                        },
                        "required": ["message"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "git_add",
                    "description": "Stage a file for commit",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string", "description": "File path to stage"}
                        },
                        "required": ["file_path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "install_package",
                    "description": "Install a Python package using pip",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "package_name": {"type": "string", "description": "Package name to install"}
                        },
                        "required": ["package_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_installed_packages",
                    "description": "List all installed Python packages",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "check_syntax",
                    "description": "Check a Python file for syntax errors using ast.parse(). Fast validation.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Path to the Python file to check"}
                        },
                        "required": ["path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "lint_file",
                    "description": "Lint a Python file using ruff. Checks for style issues, bugs, and errors. Can auto-fix issues.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Path to the Python file to lint"},
                            "fix": {"type": "boolean", "description": "If true, automatically fix issues where possible"}
                        },
                        "required": ["path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "format_file",
                    "description": "Format a Python file using ruff. Applies PEP 8 and best practice formatting.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Path to the Python file to format"}
                        },
                        "required": ["path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "python_repl",
                    "description": "Execute Python code in a safe sandbox. Use this for calculations, data processing, or verifying logic. Captures stdout/stderr. Timeout: 5s.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "code": {"type": "string", "description": "The Python code to execute"}
                        },
                        "required": ["code"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "diff_preview",
                    "description": "Preview changes before applying them. Shows a unified diff of what edit_file would do.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Path to the file"},
                            "old_text": {"type": "string", "description": "Text to find"},
                            "new_text": {"type": "string", "description": "Replacement text"}
                        },
                        "required": ["path", "old_text", "new_text"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "undo_edit",
                    "description": "Undo the last edit to a file by restoring from backup.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Path to the file to undo"}
                        },
                        "required": ["path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "batch_edit",
                    "description": "Apply the same text replacement to multiple files matching a pattern.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_pattern": {"type": "string", "description": "Glob pattern for files (e.g., '*.py')"},
                            "old_text": {"type": "string", "description": "Text to find and replace"},
                            "new_text": {"type": "string", "description": "Replacement text"},
                            "directory": {"type": "string", "description": "Directory to search in (default: current)"}
                        },
                        "required": ["file_pattern", "old_text", "new_text"]
                    }
                }
            },
            # Phase 3: Code Intelligence
            {
                "type": "function",
                "function": {
                    "name": "analyze_project",
                    "description": "Analyze project type, dependencies, and structure. Detects Python, Node, Go, Rust projects.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "directory": {"type": "string", "description": "Directory to analyze (default: current)"}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "run_tests",
                    "description": "Run project tests (auto-detects pytest, npm test, go test, cargo test).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "test_path": {"type": "string", "description": "Specific test file/directory (optional)"},
                            "directory": {"type": "string", "description": "Project directory (default: current)"}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "discover_tests",
                    "description": "Discover test files in the project without running them.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "directory": {"type": "string", "description": "Directory to search (default: current)"}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "find_definition",
                    "description": "Find where a function/class is defined using grep patterns.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "symbol": {"type": "string", "description": "Function or class name to find"},
                            "directory": {"type": "string", "description": "Directory to search (default: current)"}
                        },
                        "required": ["symbol"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "find_references",
                    "description": "Find all references to a symbol in the codebase.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "symbol": {"type": "string", "description": "Symbol to find references of"},
                            "directory": {"type": "string", "description": "Directory to search (default: current)"}
                        },
                        "required": ["symbol"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "add_mcp_server",
                    "description": "Add a new MCP server configuration",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Unique name for the server"},
                            "command": {"type": "string", "description": "Command to run the server"},
                            "args": {"type": "array", "items": {"type": "string"}, "description": "Arguments for the command"},
                            "env": {"type": "object", "additionalProperties": {"type": "string"}, "description": "Environment variables"}
                        },
                        "required": ["name", "command"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "remove_mcp_server",
                    "description": "Remove an MCP server configuration",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Name of the server to remove"}
                        },
                        "required": ["name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "wait",
                    "description": "Wait for a specified duration in seconds.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "seconds": {"type": "integer", "description": "Number of seconds to wait"},
                            "message": {"type": "string", "description": "Optional message to display"}
                        },
                        "required": ["seconds"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "fetch_url",
                    "description": "Fetch and convert web page content to markdown using a headless browser (handles JS).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {"type": "string", "description": "URL to fetch"}
                        },
                        "required": ["url"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_web",
                    "description": "Search the web for information using DuckDuckGo.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "The search query"},
                            "max_results": {"type": "integer", "description": "Maximum number of results (default: 5)"},
                            "deep_search": {"type": "boolean", "description": "If true, fetches full content of top 3 results"}
                        },
                        "required": ["query"]
                    }
                }
            }
        ]

    def chat(self, user_input: str):
        from .ui import format_tool_call, format_tool_output, format_assistant_message, ThinkingSpinner, print_session_info
        
        self.messages.append({"role": "user", "content": user_input})
        self.messages = self.context_window.prune_context(self.messages)
        
        from rich.markdown import Markdown
        
        # Track input tokens
        input_tokens = self.context_window.count_message_tokens(self.messages)
        
        while True:
            full_content = ""
            thinking_content = ""
            tool_calls = []
            
            # Add space after user input
            console.print()
            
            # Real-time streaming
            in_thinking = True
            thinking_started = False
            response_started = False
            spinner = None
            live_display = None

            # Start spinner
            spinner = ThinkingSpinner("Working")
            spinner.__enter__()

            # Merge native tools with dynamic MCP tools
            all_tools = self.tool_definitions + self.mcp_manager.get_tool_definitions()
            stream = self.llm.generate_stream(self.messages, tools=all_tools)

            for chunk in stream:
                if "error" in chunk:
                    if spinner:
                        spinner.__exit__(None, None, None)
                        spinner = None
                    if live_display:
                        live_display.stop()
                    console.print(f"[red]✗ Error:[/red] {chunk['error']}")
                    return

                if "message" in chunk:
                    msg = chunk["message"]

                    # Handle thinking (from think=True) - stream in real time
                    think_chunk = None
                    if hasattr(msg, 'thinking') and msg.thinking:
                        think_chunk = msg.thinking
                    elif isinstance(msg, dict) and msg.get("thinking"):
                        think_chunk = msg["thinking"]

                    if think_chunk:
                        # Stop spinner when we start outputting
                        if spinner:
                            spinner.__exit__(None, None, None)
                            spinner = None
                        if not thinking_started:
                            console.print("[dim]", end="", markup=True)
                            thinking_started = True
                        # Print thinking without markup to avoid tag issues
                        console.print(think_chunk, end="", style="dim")
                        thinking_content += think_chunk

                    # Handle content - stream in real time
                    content_chunk = None
                    if hasattr(msg, 'content') and msg.content:
                        content_chunk = msg.content
                    elif isinstance(msg, dict) and msg.get("content"):
                        content_chunk = msg["content"]

                    if content_chunk:
                        # Stop spinner when we start outputting
                        if spinner:
                            spinner.__exit__(None, None, None)
                            spinner = None
                        if in_thinking and thinking_started:
                            console.print()
                            console.print()
                            in_thinking = False
                        
                        full_content += content_chunk
                        
                        if not live_display:
                            from rich.live import Live
                            # Initialize Live display for Markdown rendering
                            live_display = Live(Markdown(full_content), console=console, refresh_per_second=10)
                            live_display.start()
                        else:
                            # Update existing Live display
                            live_display.update(Markdown(full_content))

                    # Handle tool calls
                    if hasattr(msg, 'tool_calls') and msg.tool_calls:
                        tool_calls.extend(msg.tool_calls)
                    elif isinstance(msg, dict) and msg.get("tool_calls"):
                        tool_calls.extend(msg["tool_calls"])

            # Clean up spinner if still active
            if spinner:
                spinner.__exit__(None, None, None)
            
            # Stop live display if active
            if live_display:
                live_display.stop()
            
            # End line after streaming if anything was output
            if full_content.strip() or thinking_content.strip():
                console.print()  # Space after response

            # Append assistant message to history
            assistant_msg = {"role": "assistant", "content": full_content}
            if tool_calls:
                assistant_msg["tool_calls"] = tool_calls
            self.messages.append(assistant_msg)

            # If no tool calls, we are done
            if not tool_calls:
                # Track output tokens
                output_tokens = self.context_window.estimate_tokens(full_content)
                self.context_window.track_usage(input_tokens, output_tokens)
                
                # Show minimal session info
                stats = self.context_window.get_usage_stats()
                print_session_info(self.session_manager.current_session_id, stats['total_tokens'])
                
                # Auto-save if needed
                if self.session_manager.should_auto_save():
                    self.session_manager.save_session(self.messages)
                break
            
            # Execute tools
            for tool_call in tool_calls:
                function_name = tool_call["function"]["name"]
                arguments = tool_call["function"]["arguments"]
                
                # Fix common LLM hallucination where arguments are wrapped
                if isinstance(arguments, dict) and "arguments" in arguments and isinstance(arguments["arguments"], dict):
                    if "code" in arguments["arguments"] and function_name == "python_repl":
                         arguments = arguments["arguments"]
                    elif len(arguments) <= 2 and "function_name" in arguments: 
                         arguments = arguments["arguments"]

                # Show tool call - Claude Code style
                console.print(format_tool_call(function_name, arguments))
                
                # Execute with spinner
                with console.status(f"[dim]Running...[/dim]", spinner="dots"):
                    content = ""
                    success = False
                    
                    if function_name in self.tools:
                        try:
                            result = self.retry_handler.execute_with_retry(
                                self.tools[function_name], **arguments
                            )
                            content = str(result)
                            success = "Error" not in content
                        except Exception as e:
                            content = f"Error: {str(e)}"
                            success = False
                    elif function_name in [t["function"]["name"] for t in self.mcp_manager.get_tool_definitions()]:
                        # Try to execute as MCP tool
                        try:
                            content = self.mcp_manager.call_tool(function_name, arguments)
                            success = "Error" not in str(content)
                        except Exception as e:
                            content = f"Error executing MCP tool: {str(e)}"
                            success = False
                    else:
                        content = f"Error: Tool {function_name} not found"
                        success = False

                # Show output - compact style
                console.print(format_tool_output(function_name, content, success))

                self.messages.append({
                    "role": "tool",
                    "content": content,
                    "name": function_name
                })

    def get_current_model(self) -> str:
        """Get the name of the currently active model."""
        return self.model_name
    
    def switch_model(self, model_name: str) -> bool:
        """
        Switch to a different model.
        
        Args:
            model_name: Name of the model to switch to
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Test if the model exists by trying to use it
            self.llm = ChatModel(model=model_name)
            self.model_name = model_name
            console.print(f"[bold green]✓ Switched to model: {model_name}[/bold green]")
            return True
        except Exception as e:
            console.print(f"[bold red]✗ Failed to switch model:[/bold red] {str(e)}")
            return False
    
    def list_available_models(self) -> List[Dict[str, Any]]:
        """
        List all available Ollama models.
        
        Returns:
            List of model information dictionaries
        """
        try:
            response = ollama.list()
            # Convert Model objects to dicts with proper field names
            models = []
            for model in response.models:
                models.append({
                    'name': model.model,
                    'size': model.size,
                    'modified_at': model.modified_at
                })
            return models
        except Exception as e:
            console.print(f"[bold red]Error listing models:[/bold red] {str(e)}")
            return []
    
    def save_session(self) -> str:
        """Save the current session."""
        return self.session_manager.save_session(self.messages)
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all available sessions."""
        return self.session_manager.list_sessions()
    
    def get_token_stats(self) -> Dict[str, Any]:
        """Get current token usage statistics."""
        return self.context_window.get_usage_stats()
    
    def get_session_id(self) -> str:
        """Get current session ID."""
        return self.session_manager.current_session_id or "none"
