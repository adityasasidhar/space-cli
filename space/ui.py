"""
UI components for Space CLI - Claude Code inspired design.
Clean, minimal, professional terminal interface.
"""
import time
import os
from rich.console import Console, Group
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.align import Align
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.markdown import Markdown
from rich.rule import Rule

console = Console()

# Theme colors
THEME = {
    "primary": "#7c3aed",      # Purple
    "secondary": "#06b6d4",    # Cyan
    "success": "#10b981",      # Green
    "warning": "#f59e0b",      # Amber
    "error": "#ef4444",        # Red
    "muted": "#6b7280",        # Gray
    "text": "#f3f4f6",         # Light gray
}


def print_banner():
    """Print SPACE CODE ASCII art banner - Claude Code inspired."""
    logo = r"""
[#7c3aed]  ██████  ██████   █████   ██████ ███████      ██████  ██████  ██████  ███████ [/]
[#8b5cf6] ██      ██   ██ ██   ██ ██      ██          ██      ██    ██ ██   ██ ██      [/]
[#a855f7] ███████ ██████  ███████ ██      █████       ██      ██    ██ ██   ██ █████   [/]
[#c084fc]      ██ ██      ██   ██ ██      ██          ██      ██    ██ ██   ██ ██      [/]
[#d8b4fe] ██████  ██      ██   ██  ██████ ███████      ██████  ██████  ██████  ███████ [/]
"""
    
    console.print(logo)
    console.print(Align.center(Text("Local AI Coding Assistant", style=THEME['muted'])))
    console.print()


def print_banner_minimal():
    """Print ultra-minimal one-line banner."""
    banner = Text()
    banner.append("◆ ", style=f"bold {THEME['primary']}")
    banner.append("Space", style=f"bold {THEME['text']}")
    banner.append(" v1.0", style=f"{THEME['muted']}")
    
    console.print()
    console.print(Panel(
        banner,
        border_style=THEME['primary'],
        padding=(0, 1),
    ))
    console.print()


def startup_animation():
    """Quick, professional startup sequence."""
    steps = [
        "Initializing agent",
        "Loading tools",
        "Ready",
    ]
    
    with Progress(
        SpinnerColumn(style=THEME['primary']),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task(steps[0], total=len(steps))
        for i, step in enumerate(steps):
            progress.update(task, description=f"[{THEME['muted']}]{step}[/]")
            time.sleep(0.15)
            progress.advance(task)
    
    console.print(f"[{THEME['success']}]✓[/] Ready\n")


def print_thinking():
    """Return a thinking indicator text."""
    return f"[{THEME['muted']}]Thinking...[/]"


def format_tool_call(name: str, args: dict) -> Panel:
    """Format a tool call for display - Claude Code style."""
    import json
    
    # Tool icon based on category
    icons = {
        "read": "📖",
        "write": "✏️",
        "edit": "📝",
        "list": "📁",
        "run": "▶️",
        "git": "🔀",
        "search": "🔍",
        "find": "🔍",
        "grep": "🔍",
        "check": "✅",
        "lint": "🔧",
        "format": "🎨",
        "python": "🐍",
        "install": "📦",
        "delete": "🗑️",
        "copy": "📋",
        "move": "📦",
        "diff": "📊",
        "undo": "↩️",
        "batch": "📚",
        "analyze": "📊",
        "test": "🧪",
        "discover": "🔎",
    }
    
    icon = "⚡"
    for key, val in icons.items():
        if key in name.lower():
            icon = val
            break
    
    # Compact args display
    args_display = ""
    if args:
        if "path" in args:
            args_display = args["path"]
        elif "command" in args:
            cmd = args["command"]
            if len(cmd) > 50:
                cmd = cmd[:47] + "..."
            args_display = cmd
        elif "directory" in args:
            args_display = args["directory"]
        elif "symbol" in args:
            args_display = args["symbol"]
        else:
            # Show first arg value
            first_val = str(list(args.values())[0])
            if len(first_val) > 40:
                first_val = first_val[:37] + "..."
            args_display = first_val
    
    content = Text()
    content.append(f"{icon} ", style="")
    content.append(name, style=f"bold {THEME['secondary']}")
    if args_display:
        content.append(f" {args_display}", style=THEME['muted'])
    
    return Panel(
        content,
        border_style=THEME['muted'],
        padding=(0, 1),
        title="[dim]tool[/dim]",
        title_align="left",
    )


def format_tool_output(name: str, output: str, success: bool = True) -> Panel:
    """Format tool output - compact and clean."""
    # Truncate long output
    max_lines = 15
    lines = output.split('\n')
    if len(lines) > max_lines:
        output = '\n'.join(lines[:max_lines]) + f"\n[{THEME['muted']}]... ({len(lines) - max_lines} more lines)[/]"
    
    if len(output) > 800:
        output = output[:800] + f"\n[{THEME['muted']}]... (truncated)[/]"
    
    border_color = THEME['success'] if success else THEME['error']
    status_icon = "✓" if success else "✗"
    
    return Panel(
        output,
        border_style=border_color,
        padding=(0, 1),
        title=f"[{border_color}]{status_icon}[/]",
        title_align="left",
    )


def format_assistant_message(content: str) -> None:
    """Display assistant response with markdown formatting."""
    if content.strip():
        console.print(Markdown(content))


def format_user_prompt() -> list:
    """Return the styled user prompt."""
    return [("class:prompt", "❯ ")]


def print_session_info(session_id: str, token_count: int):
    """Print minimal session info."""
    console.print(
        f"[{THEME['muted']}]Session: {session_id} │ Tokens: {token_count}[/]"
    )


def print_divider(title: str = None):
    """Print a subtle divider."""
    if title:
        console.print(Rule(title, style=THEME['muted']))
    else:
        console.print(Rule(style=THEME['muted']))


def print_error(message: str):
    """Print an error message."""
    console.print(f"[{THEME['error']}]✗ Error:[/] {message}")


def print_success(message: str):
    """Print a success message."""
    console.print(f"[{THEME['success']}]✓[/] {message}")


def print_warning(message: str):
    """Print a warning message."""
    console.print(f"[{THEME['warning']}]⚠[/] {message}")


def print_info(message: str):
    """Print an info message."""
    console.print(f"[{THEME['muted']}]ℹ[/] {message}")


def format_help_panel() -> Panel:
    """Format the help panel - Claude Code style."""
    commands = [
        ("/help", "Show this help"),
        ("/models", "List available models"),
        ("/model <name>", "Switch model"),
        ("/current", "Show current model"),
        ("/save", "Save session"),
        ("/sessions", "List sessions"),
        ("/stats", "Token statistics"),
        ("exit", "Exit Space"),
    ]
    
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style=THEME['secondary'])
    table.add_column(style=THEME['muted'])
    
    for cmd, desc in commands:
        table.add_row(cmd, desc)
    
    return Panel(
        table,
        title="[bold]Commands[/bold]",
        border_style=THEME['primary'],
        padding=(1, 2),
    )


def format_models_table(models: list, current_model: str) -> Table:
    """Format models list as a clean table."""
    table = Table(
        show_header=True,
        header_style=f"bold {THEME['secondary']}",
        border_style=THEME['muted'],
    )
    table.add_column("Model", style=THEME['text'])
    table.add_column("Size", style=THEME['muted'])
    
    for model in models:
        name = model.get("name", "Unknown")
        size = f"{model.get('size', 0) / (1024**3):.1f}GB"
        
        if name == current_model:
            name = f"● {name}"
            table.add_row(f"[{THEME['success']}]{name}[/]", size)
        else:
            table.add_row(f"  {name}", size)
    
    return table


def format_sessions_table(sessions: list, current_id: str) -> Table:
    """Format sessions list as a clean table."""
    table = Table(
        show_header=True,
        header_style=f"bold {THEME['secondary']}",
        border_style=THEME['muted'],
    )
    table.add_column("Session", style=THEME['text'])
    table.add_column("Messages", style=THEME['muted'])
    table.add_column("Created", style=THEME['muted'])
    
    for sess in sessions[:10]:
        sess_id = sess.get('id', 'Unknown')
        is_current = sess_id == current_id
        
        if is_current:
            table.add_row(
                f"[{THEME['success']}]● {sess_id}[/]",
                str(sess.get('message_count', 0)),
                sess.get('created_at', 'Unknown')[:16]
            )
        else:
            table.add_row(
                f"  {sess_id}",
                str(sess.get('message_count', 0)),
                sess.get('created_at', 'Unknown')[:16]
            )
    
    return table


def format_stats(stats: dict, session_id: str) -> Panel:
    """Format token stats panel."""
    content = f"""Total tokens: {stats.get('total_tokens', 0)}
Requests: {stats.get('request_count', 0)}
Avg/request: {stats.get('avg_tokens_per_request', 0)}
Session: {session_id}"""
    
    return Panel(
        content,
        title="[bold]Statistics[/bold]",
        border_style=THEME['primary'],
        padding=(0, 2),
    )


# Spinner for thinking state
class ThinkingSpinner:
    """Context manager for thinking animation."""
    
    def __init__(self, message: str = "Thinking"):
        self.message = message
        self.progress = None
        self.task = None
    
    def __enter__(self):
        self.progress = Progress(
            SpinnerColumn(style=THEME['primary']),
            TextColumn(f"[{THEME['muted']}]{self.message}[/]"),
            console=console,
            transient=True,
        )
        self.progress.start()
        self.task = self.progress.add_task("", total=None)
        return self
    
    def __exit__(self, *args):
        self.progress.stop()
    
    def update(self, message: str):
        """Update the thinking message."""
        self.progress.update(self.task, description=f"[{THEME['muted']}]{message}[/]")
