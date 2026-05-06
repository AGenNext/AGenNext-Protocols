"""
AGenNext Protocols - Agent Identity (OIDC)
=====================================
Identity management for AI agents using OpenID Connect.

Usage:
    from agennext.agentid import AgentIdentity, IdentityClient, Token
    
    # Register agent identity
    identity = AgentIdentity(
        agent_id="agent-001",
        name="Assistant Agent",
        capabilities=["text generation", "tool use"],
    )
    
    # Authenticate and get tokens
    client = IdentityClient(base_url="https://identity.example.com")
    token = await client.authenticate(identity)
"""

import time
import uuid
import hashlib
import jwt
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum

__version__ = "1.0.0"


class AgentCapability(Enum):
    """Agent capabilities."""
    TEXT_GENERATION = "text_generation"
    TOOL_USE = "tool_use"
    AGENT_COMMUNICATION = "agent_communication"
    DATA_ACCESS = "data_access"
    PAYMENT = "payment"


@dataclass
class AgentIdentity:
    """Identity of an AI agent."""
    agent_id: str
    name: str
    version: str = "1.0.0"
    capabilities: List[str] = field(default_factory=list)
    publisher: Optional[str] = None
    audience: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "version": self.version,
            "capabilities": self.capabilities,
            "publisher": self.publisher,
            "audience": self.audience,
            "metadata": self.metadata,
        }


@dataclass
class Token:
    """JWT token for agent authentication."""
    access_token: str
    token_type: str = "Bearer"
    expires_in: int = 3600
    refresh_token: Optional[str] = None
    scope: Optional[str] = None
    
    @property
    def expires_at(self) -> int:
        return int(time.time()) + self.expires_in
    
    @property
    def is_expired(self) -> bool:
        return time.time() > self.expires_at
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Token":
        return cls(
            access_token=data.get("access_token", ""),
            token_type=data.get("token_type", "Bearer"),
            expires_in=data.get("expires_in", 3600),
            refresh_token=data.get("refresh_token"),
            scope=data.get("scope"),
        )


@dataclass
class TokenRequest:
    """Token request for agent authentication."""
    grant_type: str = "client_credentials"
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    agent_id: Optional[str] = None
    scope: Optional[str] = None
    
    def to_form(self) -> Dict[str, str]:
        data = {"grant_type": self.grant_type}
        if self.client_id:
            data["client_id"] = self.client_id
        if self.client_secret:
            data["client_secret"] = self.client_secret
        if self.agent_id:
            data["agent_id"] = self.agent_id
        if self.scope:
            data["scope"] = self.scope
        return data


@dataclass
class AgentCredential:
    """Credential for agent authentication."""
    client_id: str
    client_secret: str
    agent_id: str
    
    def to_dict(self) -> Dict:
        return {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "agent_id": self.agent_id,
        }


class IdentityClient:
    """OIDC-based Identity Client for agents."""
    
    def __init__(
        self,
        base_url: str,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.client_id = client_id
        self.client_secret = client_secret
        self._token: Optional[Token] = None
    
    async def authenticate(
        self,
        identity: AgentIdentity,
        scope: Optional[str] = None,
    ) -> Token:
        """Authenticate an agent and get access token."""
        import httpx
        
        request = TokenRequest(
            grant_type="agent_credentials",
            client_id=self.client_id,
            client_secret=self.client_secret,
            agent_id=identity.agent_id,
            scope=scope or " ".join(identity.capabilities),
        )
        
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/oauth/token",
                data=request.to_form(),
            )
            resp.raise_for_status()
            self._token = Token.from_dict(resp.json())
            return self._token
    
    async def register_agent(
        self,
        identity: AgentIdentity,
        credential: Optional[AgentCredential] = None,
    ) -> AgentCredential:
        """Register a new agent identity."""
        import httpx
        
        payload = identity.to_dict()
        if credential:
            payload["credential"] = credential.to_dict()
        
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/agents",
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return AgentCredential(**data.get("credential", {}))
    
    async def get_agent_info(self, agent_id: str) -> AgentIdentity:
        """Get agent identity information."""
        import httpx
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.base_url}/agents/{agent_id}")
            resp.raise_for_status()
            return AgentIdentity(**resp.json())
    
    async def update_agent(
        self,
        agent_id: str,
        identity: AgentIdentity,
    ) -> AgentIdentity:
        """Update agent identity."""
        import httpx
        
        async with httpx.AsyncClient() as client:
            resp = await client.put(
                f"{self.base_url}/agents/{agent_id}",
                json=identity.to_dict(),
            )
            resp.raise_for_status()
            return AgentIdentity(**resp.json())
    
    async def revoke_token(self, token: str):
        """Revoke an access token."""
        import httpx
        
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{self.base_url}/oauth/revoke",
                data={"token": token},
            )
    
    def create_agent_token(
        self,
        identity: AgentIdentity,
        secret_key: str,
        expires_in: int = 3600,
    ) -> Token:
        """Create a signed JWT for an agent (for testing)."""
        now = int(time.time())
        
        payload = {
            "iss": self.base_url,
            "sub": identity.agent_id,
            "aud": identity.audience or "agents",
            "iat": now,
            "exp": now + expires_in,
            "agent": identity.to_dict(),
        }
        
        token = jwt.encode(payload, secret_key, algorithm="HS256")
        
        return Token(
            access_token=token,
            expires_in=expires_in,
            scope=" ".join(identity.capabilities),
        )
    
    def verify_token(self, token: str, secret_key: str) -> Dict:
        """Verify and decode a JWT token."""
        return jwt.decode(token, secret_key, algorithms=["HS256", "RS256"])


class AgentRegistry:
    """Local registry for agent identities."""
    
    def __init__(self):
        self.identities: Dict[str, AgentIdentity] = {}
        self.credentials: Dict[str, AgentCredential] = {}
    
    def register(self, identity: AgentIdentity) -> AgentCredential:
        """Register an agent identity."""
        self.identities[identity.agent_id] = identity
        
        credential = AgentCredential(
            client_id=f"agent-{identity.agent_id}",
            client_secret=uuid.uuid4().hex,
            agent_id=identity.agent_id,
        )
        self.credentials[identity.agent_id] = credential
        return credential
    
    def get(self, agent_id: str) -> Optional[AgentIdentity]:
        """Get agent identity."""
        return self.identities.get(agent_id)
    
    def get_credential(self, agent_id: str) -> Optional[AgentCredential]:
        """Get agent credential."""
        return self.credentials.get(agent_id)
    
    def list_all(self) -> List[AgentIdentity]:
        """List all registered agents."""
        return list(self.identities.values())
    
    def revoke(self, agent_id: str):
        """Revoke an agent identity."""
        self.identities.pop(agent_id, None)
        self.credentials.pop(agent_id, None)


__all__ = [
    "AgentIdentity",
    "AgentCredential",
    "IdentityClient",
    "Token",
    "TokenRequest",
    "AgentRegistry",
    "AgentCapability",
    "__version__",
]
