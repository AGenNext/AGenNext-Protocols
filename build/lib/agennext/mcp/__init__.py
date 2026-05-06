"""
AGenNext Protocols - MCP (Model Context Protocol)
==========================================
A standardized connection pattern for AI agents to connect to data sources and tools.

Installation:
    pip install mcp

Usage:
    from agennext.mcp import MCPClient
    
    async with MCPClient("server.py") as client:
        tools = await client.list_tools()
        result = await client.call_tool("tool_name", {"arg": "value"})
"""

import asyncio
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass
from mcp import ClientStarter
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource

__version__ = "1.0.0"

@dataclass
class MCPProtocol:
    """MCP Protocol implementation."""
    
    def __init__(self, command: str, args: Optional[List[str]] = None, env: Optional[Dict] = None):
        self.command = command
        self.args = args or []
        self.env = env or {}
        self._client = None
    
    async def __aenter__(self):
        self._client = ClientStarter(
            command=self.command,
            args=self.args,
            env=self.env
        )
        await self._client.__aenter__()
        return self
    
    async def __aexit__(self, *args):
        if self._client:
            await self._client.__aexit__(*args)
    
    async def list_tools(self) -> List[Tool]:
        """List available tools from MCP server."""
        if not self._client:
            raise RuntimeError("Not connected. Use 'async with' context manager.")
        return await self._client.list_tools()
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Call a tool on the MCP server."""
        if not self._client:
            raise RuntimeError("Not connected. Use 'async with' context manager.")
        result = await self._client.call_tool(name, arguments)
        return result


class MCPClient:
    """MCP Client wrapper."""
    
    def __init__(self, command: str, args: Optional[List[str]] = None, env: Optional[Dict] = None):
        self.command = command
        self.args = args or []
        self.env = env or {}
    
    async def __aenter__(self):
        self._protocol = MCPProtocol(self.command, self.args, self.env)
        return await self._protocol.__aenter__()
    
    async def __aexit__(self, *args):
        return await self._protocol.__aexit__(*args)


__all__ = ["MCPClient", "MCPProtocol", "Tool", "TextContent", "__version__"]