"""
AGenNext Protocols - A2A (Agent2Agent Protocol)
============================================
Enables communication and collaboration between AI agents.

Usage:
    from agennext.a2a import A2AClient, AgentCard
    
    client = await A2AClient.connect("http://agent:8000")
    card = await client.get_agent_card()
    async for response in client.send_message(msg):
        print(response)
"""

import asyncio
import httpx
from typing import Any, Dict, List, Optional, AsyncIterator
from dataclasses import dataclass
from uuid import uuid4

# Use a2a-sdk if available, otherwise define our own
try:
    from a2a.client import A2AClient as _BaseClient
    from a2a.types import AgentCard, SendMessageRequest, MessageSendParams, TextPart
    A2A_SDK_AVAILABLE = True
except ImportError:
    _BaseClient = None
    A2A_SDK_AVAILABLE = False
    AgentCard = None
    SendMessageRequest = None
    TextPart = None

__version__ = "1.0.0"

@dataclass
class AgentCard:
    """A2A Agent Card model."""
    name: str
    description: str
    url: str
    version: str = "1.0.0"
    skills: List[Dict] = None
    default_input_modes: List[str] = None
    default_output_modes: List[str] = None
    
    def __post_init__(self):
        if self.skills is None:
            self.skills = []
        if self.default_input_modes is None:
            self.default_input_modes = ["text"]
        if self.default_output_modes is None:
            self.default_output_modes = ["text"]


class A2AClient:
    """A2A Protocol Client."""
    
    def __init__(self, url: str, auth: Optional[Dict] = None):
        self.url = url.rstrip("/")
        self.auth = auth or {}
        self._client = None
    
    @classmethod
    async def connect(cls, url: str, auth: Optional[Dict] = None) -> "A2AClient":
        """Create and connect to an A2A agent."""
        client = cls(url, auth)
        await client.connect()
        return client
    
    async def connect(self):
        """Establish connection."""
        self._http = httpx.AsyncClient(timeout=30.0)
        # Verify connection
        card_url = f"{self.url}/.well-known/agent-card.json"
        resp = await self._http.get(card_url)
        resp.raise_for_status()
        self._agent_card = resp.json()
    
    async def disconnect(self):
        """Close connection."""
        if self._http:
            await self._http.aclose()
    
    async def get_agent_card(self) -> AgentCard:
        """Get the agent's capability card."""
        if not hasattr(self, '_agent_card'):
            await self.connect()
        data = self._agent_card
        return AgentCard(
            name=data.get("name", ""),
            description=data.get("description", ""),
            url=data.get("url", self.url),
            version=data.get("version", "1.0.0"),
            skills=data.get("skills", []),
        )
    
    async def send_message(self, message: str, task_id: Optional[str] = None) -> AsyncIterator[Dict]:
        """Send a message to the agent and receive responses."""
        if not task_id:
            task_id = str(uuid4())
        
        payload = {
            "jsonrpc": "2.0",
            "id": task_id,
            "method": "message/send",
            "params": {
                "messageId": task_id,
                "role": "user",
                "parts": [{"type": "text", "text": message}],
            }
        }
        
        async with self._http.stream("POST", f"{self.url}/", json=payload) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if line.strip():
                    yield line
    
    async def __aenter__(self):
        await self.connect()
        return self
    
    async def __aexit__(self, *args):
        await self.disconnect()


class A2AServer:
    """Simple A2A Protocol Server."""
    
    def __init__(self, name: str, description: str, skills: List[Dict], handler):
        self.name = name
        self.description = description
        self.skills = skills
        self.handler = handler
    
    def get_agent_card(self) -> Dict:
        """Generate the agent card."""
        return {
            "name": self.name,
            "description": self.description,
            "url": "http://localhost:8000",
            "version": "1.0.0",
            "skills": self.skills,
            "defaultInputModes": ["text"],
            "defaultOutputModes": ["text"],
        }
    
    async def handle_message(self, message: Dict) -> Dict:
        """Handle incoming message."""
        return await self.handler(message)


__all__ = ["A2AClient", "A2AServer", "AgentCard", "__version__"]