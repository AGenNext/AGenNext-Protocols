"""
AGenNext Protocols - Agent Registry
==============================
Registry for discovering and managing AI agents.
Based on A2A Agent Discovery patterns.

Usage:
    from agennext.registry import AgentRegistry, RegistryClient, AgentEntry
    
    # Register an agent
    registry = AgentRegistry()
    entry = await registry.register(
        name="Assistant",
        endpoint="https://agent.example.com",
        capabilities=["chat", "tools"],
    )
    
    # Discover agents
    agents = await registry.discover(capability="tools")
    for agent in agents:
        print(f"Found: {agent.name}")
"""

import time
import uuid
import hashlib
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum

__version__ = "1.0.0"


class AgentStatus(Enum):
    """Agent status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    BUSY = "busy"
    OFFLINE = "offline"


@dataclass
class AgentCapability:
    """Agent capability."""
    id: str
    name: str
    description: str
    input_modes: List[str] = field(default_factory=lambda: ["text"])
    output_modes: List[str] = field(default_factory=lambda: ["text"])
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "inputModes": self.input_modes,
            "outputModes": self.output_modes,
        }


@dataclass
class AgentEntry:
    """Registry entry for an agent."""
    id: str
    name: str
    description: str
    url: str
    version: str = "1.0.0"
    status: AgentStatus = AgentStatus.ACTIVE
    capabilities: List[AgentCapability] = field(default_factory=list)
    skills: List[Dict] = field(default_factory=list)
    provider: Optional[Dict] = None
    documentation_url: Optional[str] = None
    api_version: str = "1.0.0"
    created_at: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ"))
    updated_at: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ"))
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "url": self.url,
            "version": self.version,
            "status": self.status.value,
            "capabilities": [c.to_dict() for c in self.capabilities],
            "skills": self.skills,
            "provider": self.provider,
            "documentationUrl": self.documentation_url,
            "apiVersion": self.api_version,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "AgentEntry":
        caps = [AgentCapability(**c) for c in data.get("capabilities", [])]
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            url=data.get("url", ""),
            version=data.get("version", "1.0.0"),
            status=AgentStatus(data.get("status", "active")),
            capabilities=caps,
            skills=data.get("skills", []),
            provider=data.get("provider"),
            documentation_url=data.get("documentationUrl"),
            api_version=data.get("apiVersion", "1.0.0"),
            created_at=data.get("createdAt", ""),
            updated_at=data.get("updatedAt", ""),
        )


@dataclass
class SearchQuery:
    """Search query for agent discovery."""
    query: Optional[str] = None
    capabilities: Optional[List[str]] = None
    status: AgentStatus = AgentStatus.ACTIVE
    limit: int = 10
    offset: int = 0


@dataclass
class RegistryStats:
    """Registry statistics."""
    total_agents: int = 0
    active_agents: int = 0
    by_capability: Dict[str, int] = field(default_factory=dict)


class AgentRegistry:
    """Local agent registry."""
    
    def __init__(self):
        self.agents: Dict[str, AgentEntry] = {}
    
    async def register(
        self,
        name: str,
        endpoint: str,
        capabilities: Optional[List[str]] = None,
        description: str = "",
        version: str = "1.0.0",
    ) -> AgentEntry:
        """Register a new agent."""
        agent_id = str(uuid.uuid4())
        
        # Convert capability names to objects
        cap_objs = []
        if capabilities:
            for cap in capabilities:
                cap_objs.append(AgentCapability(
                    id=cap.lower().replace(" ", "-"),
                    name=cap,
                    description=f"Agent capability: {cap}",
                ))
        
        entry = AgentEntry(
            id=agent_id,
            name=name,
            description=description,
            url=endpoint,
            version=version,
            capabilities=cap_objs,
        )
        
        self.agents[agent_id] = entry
        return entry
    
    async def update(self, agent_id: str, **kwargs) -> Optional[AgentEntry]:
        """Update an agent entry."""
        if agent_id not in self.agents:
            return None
        
        entry = self.agents[agent_id]
        
        for key, value in kwargs.items():
            if hasattr(entry, key):
                setattr(entry, key, value)
        
        entry.updated_at = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        return entry
    
    async def unregister(self, agent_id: str) -> bool:
        """Unregister an agent."""
        if agent_id in self.agents:
            del self.agents[agent_id]
            return True
        return False
    
    async def get(self, agent_id: str) -> Optional[AgentEntry]:
        """Get an agent by ID."""
        return self.agents.get(agent_id)
    
    async def discover(
        self,
        query: Optional[SearchQuery] = None,
    ) -> List[AgentEntry]:
        """Discover agents matching query."""
        results = []
        
        for agent in self.agents.values():
            # Filter by status
            if query and query.status:
                if agent.status != query.status:
                    continue
            
            # Filter by capabilities
            if query and query.capabilities:
                agent_caps = [c.id for c in agent.capabilities]
                if not any(c in agent_caps for c in query.capabilities):
                    continue
            
            # Filter by query string
            if query and query.query:
                q = query.query.lower()
                if q not in agent.name.lower() and q not in agent.description.lower():
                    continue
            
            results.append(agent)
        
        # Apply pagination
        if query:
            results = results[query.offset:query.offset + query.limit]
        
        return results
    
    async def get_agent_card(self, agent_id: str) -> Optional[Dict]:
        """Get agent card (A2A format)."""
        agent = await self.get(agent_id)
        if not agent:
            return None
        
        return {
            "name": agent.name,
            "description": agent.description,
            "url": agent.url,
            "version": agent.version,
            "capabilities": {"streaming": True, "pushNotifications": False},
            "skills": agent.skills,
            "defaultInputModes": ["text"],
            "defaultOutputModes": ["text"],
        }
    
    async def stats(self) -> RegistryStats:
        """Get registry statistics."""
        stats = RegistryStats()
        stats.total_agents = len(self.agents)
        
        for agent in self.agents.values():
            if agent.status == AgentStatus.ACTIVE:
                stats.active_agents += 1
            
            for cap in agent.capabilities:
                cap_id = cap.id
                stats.by_capability[cap_id] = stats.by_capability.get(cap_id, 0) + 1
        
        return stats


class RegistryClient:
    """Registry HTTP Client for remote registry."""
    
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
    
    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers
    
    async def register(self, entry: AgentEntry) -> AgentEntry:
        """Register an agent."""
        import httpx
        
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/agents",
                json=entry.to_dict(),
                headers=self._headers(),
            )
            resp.raise_for_status()
            return AgentEntry.from_dict(resp.json())
    
    async def get(self, agent_id: str) -> Optional[AgentEntry]:
        """Get an agent."""
        import httpx
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/agents/{agent_id}",
                headers=self._headers(),
            )
            if resp.status_code == 200:
                return AgentEntry.from_dict(resp.json())
            return None
    
    async def discover(
        self,
        query: Optional[str] = None,
        capabilities: Optional[List[str]] = None,
        limit: int = 10,
    ) -> List[AgentEntry]:
        """Discover agents."""
        import httpx
        
        params = {"limit": limit}
        if query:
            params["query"] = query
        if capabilities:
            params["capabilities"] = ",".join(capabilities)
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/agents",
                params=params,
                headers=self._headers(),
            )
            resp.raise_for_status()
            data = resp.json()
            return [AgentEntry.from_dict(a) for a in data.get("agents", [])]
    
    async def update_status(self, agent_id: str, status: AgentStatus) -> bool:
        """Update agent status."""
        import httpx
        
        async with httpx.AsyncClient() as client:
            resp = await client.patch(
                f"{self.base_url}/agents/{agent_id}/status",
                json={"status": status.value},
                headers=self._headers(),
            )
            return resp.status_code == 200
    
    async def unregister(self, agent_id: str) -> bool:
        """Unregister an agent."""
        import httpx
        
        async with httpx.AsyncClient() as client:
            resp = await client.delete(
                f"{self.base_url}/agents/{agent_id}",
                headers=self._headers(),
            )
            return resp.status_code == 200


__all__ = [
    "AgentRegistry",
    "RegistryClient",
    "AgentEntry",
    "AgentCapability",
    "AgentStatus",
    "SearchQuery",
    "RegistryStats",
    "__version__",
]
