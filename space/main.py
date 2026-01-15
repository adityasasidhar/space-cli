"""
Space CLI - Main entry point.
Claude Code-inspired interface.
"""
import typer
from rich.console import Console
from .agent import Agent
from .ui import (
    print_banner, startup_animation, format_help_panel, 
    format_models_table, format_sessions_table, format_stats,
    print_success, print_warning, print_info, THEME
)

app = typer.Typer()
console = Console()


@app.callback()
def callback():
    """Space CLI - Local AI Assistant"""


@app.command()
def start(model: str = "qwen3:4b", session: str = None):
    """Start the Space assistant."""
    print_banner()
    startup_animation()

    print_info(f"Model: {model}")
    if session:
        print_info(f"Resuming session: {session}")
    console.print()
    
    agent = Agent(model_name=model, session_id=session)

    from prompt_toolkit import PromptSession
    from prompt_toolkit.history import InMemoryHistory
    from prompt_toolkit.styles import Style

    prompt_session = PromptSession(history=InMemoryHistory())

    style = Style.from_dict({
        "prompt": "#7c3aed bold",  # Purple prompt
    })

    while True:
        try:
            user_input = prompt_session.prompt([("class:prompt", "❯ ")], style=style)

            if not user_input.strip():
                continue

            if user_input.lower() in ["exit", "quit"]:
                break

            # Handle slash commands
            if user_input.strip().startswith("/"):
                command_parts = user_input.strip().split(maxsplit=1)
                command = command_parts[0].lower()

                if command == "/models":
                    models = agent.list_available_models()
                    if models:
                        console.print(format_models_table(models, agent.get_current_model()))
                    else:
                        print_warning("No models found")
                    continue

                elif command == "/model":
                    if len(command_parts) < 2:
                        print_warning("Usage: /model <name>")
                    else:
                        new_model = command_parts[1].strip()
                        if agent.switch_model(new_model):
                            print_success(f"Switched to {new_model}")
                    continue

                elif command == "/current":
                    print_info(f"Model: {agent.get_current_model()}")
                    continue

                elif command == "/help":
                    console.print(format_help_panel())
                    continue
                
                elif command == "/save":
                    path = agent.save_session()
                    print_success(f"Session saved")
                    continue
                
                elif command == "/sessions":
                    sessions = agent.list_sessions()
                    if sessions:
                        console.print(format_sessions_table(sessions, agent.get_session_id()))
                        print_info("Resume with: --session <id>")
                    else:
                        print_warning("No saved sessions")
                    continue
                
                elif command == "/stats":
                    stats = agent.get_token_stats()
                    console.print(format_stats(stats, agent.get_session_id()))
                    continue
                
                elif command == "/mcp_config":
                    from pathlib import Path
                    import os
                    import subprocess
                    
                    config_path = Path.home() / ".space" / "mcp_config.json"
                    
                    if not config_path.exists():
                        config_path.parent.mkdir(parents=True, exist_ok=True)
                        config_path.write_text('{"servers": {}}')
                    
                    import platform
                    
                    try:
                        system = platform.system()
                        if system == 'Windows':
                            os.startfile(str(config_path))
                        elif system == 'Darwin':  # macOS
                            subprocess.call(('open', str(config_path)))
                        else:  # Linux/Unix
                            editor = os.environ.get("EDITOR")
                            if editor:
                                subprocess.run([editor, str(config_path)])
                            else:
                                # Try common editors
                                for ed in ["xdg-open", "nano", "vi"]:
                                    try:
                                        subprocess.run([ed, str(config_path)])
                                        break
                                    except FileNotFoundError:
                                        continue
                        
                        console.print("[dim]Opening config file...[/dim]")
                        
                        agent.mcp_manager._load_config()
                        agent.mcp_manager.connect_all()
                        print_success("Reloaded MCP configuration")
                    except Exception as e:
                        print_warning(f"Error opening editor: {e}")
                    continue
                
                else:
                    print_warning(f"Unknown command: {command}")
                    continue

            # Chat with agent
            agent.chat(user_input)

        except KeyboardInterrupt:
            agent.save_session()
            console.print(f"\n[{THEME['muted']}]Session saved. Goodbye.[/]")
            break
        except Exception as e:
            console.print(f"[{THEME['error']}]Error: {e}[/]")


if __name__ == "__main__":
    app()
