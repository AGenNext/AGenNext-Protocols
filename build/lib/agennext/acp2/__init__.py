"""
AGenNext Protocols - Agent Client Protocol (ACP)
=============================================
A protocol for connecting any editor to any agent.
Used by Zed, Gemini CLI, and other AI-powered editors.

Usage:
    from agennext.acp2 import ACPClient, Agent
    
    client = ACPClient()
    agent = await client.spawn_agent("echo")
    result = await agent.complete("Hello!")
"""

import asyncio
import json
import subprocess
from typing import Optional, Dict, Any, List, AsyncIterator
from dataclasses import dataclass, field
from uuid import uuid4
from enum import Enum

__version__ = "1.0.0"


class MessageRole(Enum):
    """Message role in ACP conversation."""
    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"


@dataclass
class Message:
    """A message in ACP protocol."""
    role: MessageRole
    content: str
    timestamp: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {"role": self.role.value, "content": self.content, "timestamp": self.timestamp}


@dataclass
class Tool:
    """A tool provided by the agent."""
    name: str
    description: str
    input_schema: Dict = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Tool":
        return cls(name=data.get("name", ""), description=data.get("description", ""), input_schema=data.get("input_schema", {}))


@dataclass
class ToolCall:
    """A tool call request."""
    id: str
    name: str
    arguments: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        return {"id": self.id, "name": self.name, "arguments": self.arguments}


@dataclass
class ToolResult:
    """Result from a tool call."""
    call_id: str
    result: str
    is_error: bool = False
    
    @classmethod
    def from_dict(cls, data: Dict) -> "ToolResult":
        return cls(call_id=data.get("call_id", ""), result=data.get("result", ""), is_error=data.get("is_error", False))


@dataclass
class Agent:
    """An ACP agent instance."""
    id: str
    name: str
    description: str
    tools: List[Tool] = field(default_factory=list)
    client: Optional["ACPClient"] = None
    
    @classmethod
    def from_dict(cls, data: Dict, client: Optional["ACPClient"] = None) -> "Agent":
        tools = [Tool.from_dict(t) for t in data.get("tools", [])]
        return cls(id=data.get("id", ""), name=data.get("name", ""), description=data.get("description", ""), tools=tools, client=client)
    
    async def complete(self, prompt: str) -> str:
        if not self.client:
            raise RuntimeError("Agent not connected")
        return await self.client._send_message(self.id, prompt)


class ACPClient:
    """Agent Client Protocol Client."""
    
    def __init__(self, command: Optional[str] = None):
        self.command = command
        self.agents: Dict[str, Agent] = {}
        self._process: Optional[subprocess.Process] = None
    
    async def __aenter__(self):
        await self.connect()
        return self
    
    async def __aexit__(self, *args):
        await self.disconnect()
    
    async def connect(self):
        if self.command:
            self._process = await asyncio.create_subprocess_exec(
                *self.command.split(),
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
    
    async def disconnect(self):
        if self._process:
            self._process.terminate()
            await self._process.wait()
    
    async def list_agents(self) -> List[Agent]:
        request = {"jsonrpc": "2.0", "id": str(uuid4()), "method": "agents/list", "params": {}}
        response = await self._send_request(request)
        agents_data = response.get("result", {}).get("agents", [])
        return [Agent.from_dict(a, self) for a in agents_data]
    
    async def spawn_agent(self, name: str) -> Agent:
        request = {"jsonrpc": "2.0", "id": str(uuid4()), "method": "agents/spawn", "params": {"name": name}}
        response = await self._send_request(request)
        agent = Agent.from_dict(response.get("result", {}), self)
        self.agents[agent.id] = agent
        return agent
    
    async def kill_agent(self, agent_id: str):
        request = {"jsonrpc": "2.0", "id": str(uuid4()), "method": "agents/kill", "params": {"agent_id": agent_id}}
        await self._send_request(request)
        self.agents.pop(agent_id, None)
    
    async def _send_message(self, agent_id: str, content: str) -> str:
        request = {"jsonrpc": "2.0", "id": str(uuid4()), "method": "agents/complete", "params": {"agent_id": agent_id, "message": {"role": "user", "content": content}}}
        response = await self._send_request(request)
        return response.get("result", {}).get("content", "")
    
    async def _send_request(self, request: Dict) -> Dict:
        if not self._process:
            raise RuntimeError("Not connected")
        request_json = json.dumps(request) + "\n"
        self._process.stdin.write(request_json.encode())
        await self._process.stdin.drain()
        response_line = await self._process.stdout.readline()
        return json.loads(response_line.decode())


__all__ = ["ACPClient", "Agent", "Message", "MessageRole", "Tool", "ToolCall", "ToolResult", "__version__"]
