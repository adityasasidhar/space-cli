import json
import os
import asyncio
import threading
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from rich.console import Console
from contextlib import AsyncExitStack

# MCP Imports
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

console = Console()

@dataclass
class McpServerConfig:
    name: str
    command: str
    args: List[str]
    env: Dict[str, str] = None

class McpManager:
    def __init__(self):
        self.config_path = Path.home() / ".space" / "mcp_config.json"
        self.server_configs: Dict[str, McpServerConfig] = {}
        
        self.tools: List[Dict[str, Any]] = []
        
        # Asyncio loop management
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        
        # internal state managed on the loop
        self._sessions: Dict[str, ClientSession] = {}
        self._exit_stack = AsyncExitStack()

        self._load_config()

    def _run_loop(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def _run_async(self, coro):
        """Run a coroutine on the background loop and wait for the result."""
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result()

    def _load_config(self):
        """Load server configurations from JSON file."""
        if not self.config_path.exists():
            return

        try:
            data = json.loads(self.config_path.read_text())
            for name, config in data.get("servers", {}).items():
                self.server_configs[name] = McpServerConfig(
                    name=name,
                    command=config["command"],
                    args=config.get("args", []),
                    env=config.get("env")
                )
        except Exception as e:
            console.print(f"[red]Error loading MCP config: {e}[/red]")

    def _save_config(self):
        """Save server configurations to JSON file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {"servers": {}}
        for name, config in self.server_configs.items():
            data["servers"][name] = {
                "command": config.command,
                "args": config.args,
                "env": config.env
            }
            
        self.config_path.write_text(json.dumps(data, indent=2))

    async def _connect_server_async(self, name: str) -> bool:
        """Async implementation of connect."""
        config = self.server_configs.get(name)
        if not config:
            return False

        try:
            env = os.environ.copy()
            if config.env:
                env.update(config.env)

            server_params = StdioServerParameters(
                command=config.command,
                args=config.args,
                env=env
            )

            # Create the context manager
            client_ctx = stdio_client(server_params)
            read, write = await self._exit_stack.enter_async_context(client_ctx)
            
            session_ctx = ClientSession(read, write)
            session = await self._exit_stack.enter_async_context(session_ctx)
            
            await session.initialize()
            self._sessions[name] = session
            console.print(f"[green]✓ Connected to MCP server: {name}[/green]")
            return True
        except Exception as e:
            console.print(f"[red]Failed to connect to MCP server '{name}': {e}[/red]")
            return False

    async def _refresh_tools_async(self):
        """Async implementation of refresh tools."""
        self.tools = [] # Clear existing
        for name, session in self._sessions.items():
            try:
                result = await session.list_tools()
                for tool in result.tools:
                    # Convert inputSchema to parameters
                    schema = tool.inputSchema
                    if not schema:
                        schema = {"type": "object", "properties": {}}
                        
                    tool_def = {
                        "type": "function",
                        "function": {
                            "name": tool.name,
                            "description": tool.description,
                            "parameters": schema
                        }
                    }
                    self.tools.append((name, tool_def))
            except Exception as e:
                console.print(f"[yellow]Failed to list tools for {name}: {e}[/yellow]")

    async def _call_tool_async(self, tool_name: str, arguments: dict) -> Any:
        # Find which server has this tool
        target_server = None
        for server_name, tool_def in self.tools:
            if tool_def["function"]["name"] == tool_name:
                target_server = server_name
                break
                
        if not target_server:
            raise ValueError(f"Tool {tool_name} not found in any connected MCP server")
            
        session = self._sessions.get(target_server)
        if not session:
            raise ValueError(f"Server {target_server} is not connected")
            
        result = await session.call_tool(tool_name, arguments)
        return result

    # --- Sync Public API ---

    def connect_all(self):
        """Connect to all configured servers."""
        for name in self.server_configs:
            self._run_async(self._connect_server_async(name))
        
        # Refresh tools after connecting
        self._run_async(self._refresh_tools_async())

    def add_server(self, name: str, command: str, args: List[str] = [], env: Dict[str, str] = None):
        """Add a new server to the configuration."""
        self.server_configs[name] = McpServerConfig(name, command, args, env)
        self._save_config()
        console.print(f"[green]Added MCP server '{name}' to config[/green]")
        # Try to connect immediately
        success = self._run_async(self._connect_server_async(name))
        if success:
            self._run_async(self._refresh_tools_async())

    def remove_server(self, name: str):
        """Remove a server from the configuration."""
        if name in self.server_configs:
            # We should probably disconnect first but for now just remove config
            del self.server_configs[name]
            self._save_config()
            console.print(f"[green]Removed MCP server '{name}'[/green]")
        else:
            console.print(f"[yellow]Server '{name}' not found[/yellow]")
            
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Return list of tool definitions for the LLM."""
        return [t[1] for t in self.tools]
        
    def call_tool(self, tool_name: str, arguments: dict) -> Any:
        """Execute a tool on the appropriate server."""
        result = self._run_async(self._call_tool_async(tool_name, arguments))
        
        # Format result to string (Mcp result object to text)
        content = []
        if hasattr(result, 'content'):
            for item in result.content:
                if hasattr(item, 'text'):
                    content.append(item.text)
                else:
                    content.append(str(item))
        return "\n".join(content)
