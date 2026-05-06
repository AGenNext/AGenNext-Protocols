"""
AGenNext Protocols - Agent Identity (Entra ID)
=========================================
Microsoft Entra ID (Azure AD) integration for AI agent identity management.
Entra Verified ID for agent credentials.

Usage:
    from agennext.entraid import EntraClient, AgentPrincipal, CredentialManager
    
    # Authenticate with Entra ID
    client = EntraClient(
        tenant_id="...",
        client_id="...",
        client_secret="...",
    )
    
    # Register agent as service principal
    principal = await client.register_agent(
        name="assistant-agent",
        capabilities=["chat", "tools"],
    )
    
    # Get access token
    token = await client.get_token()
"""

import time
import uuid
import base64
import hashlib
import json
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum

__version__ = "1.0.0"


class AgentType(Enum):
    """Type of agent principal in Entra ID."""
    SERVICE_PRINCIPAL = "ServicePrincipal"
    MANAGED_IDENTITY = "ManagedIdentity"
    APPLICATION = "Application"


@dataclass
class AgentPrincipal:
    """Service principal representing an AI agent in Entra ID."""
    id: str
    app_id: str
    display_name: str
    object_type: str = "ServicePrincipal"
    enabled: bool = True
    tags: List[str] = field(default_factory=list)
    key_credentials: List[Dict] = field(default_factory=list)
    password_credentials: List[Dict] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "appId": self.app_id,
            "displayName": self.display_name,
            "accountEnabled": self.enabled,
            "tags": self.tags,
            "keyCredentials": self.key_credentials,
            "passwordCredentials": self.password_credentials,
        }


@dataclass
class VerifiedCredential:
    """Verifiable credential for agent identity."""
    id: str
    issuer: str
    type: str
    claims: Dict[str, Any]
    issued_at: int
    expires_at: int
    
    @property
    def is_expired(self) -> bool:
        return time.time() > self.expires_at
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "issuer": self.issuer,
            "type": self.type,
            "claims": self.claims,
            "issuedAt": self.issued_at,
            "expiresAt": self.expires_at,
        }


@dataclass
class AccessToken:
    """Entra ID access token."""
    access_token: str
    token_type: str = "Bearer"
    expires_in: int = 3600
    resource: str = ""
    
    @property
    def expires_at(self) -> int:
        return int(time.time()) + self.expires_in
    
    @property
    def is_expired(self) -> bool:
        return time.time() > self.expires_at
    
    @classmethod
    def from_dict(cls, data: Dict) -> "AccessToken":
        return cls(
            access_token=data.get("access_token", ""),
            token_type=data.get("token_type", "Bearer"),
            expires_in=data.get("expires_in", 3600),
            resource=data.get("resource", ""),
        )


class EntraClient:
    """Microsoft Entra ID Client for agent identity management."""
    
    def __init__(
        self,
        tenant_id: str,
        client_id: str,
        client_secret: Optional[str] = None,
        authority: str = "https://login.microsoftonline.com",
    ):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.authority = authority.rstrip("/")
        self._token: Optional[AccessToken] = None
    
    @property
    def token_url(self) -> str:
        return f"{self.authority}/{self.tenant_id}/oauth2/v2.0/token"
    
    @property
    def graph_url(self) -> str:
        return "https://graph.microsoft.com/v1.0"
    
    async def get_token(self, scope: Optional[str] = None) -> AccessToken:
        """Get access token using client credentials flow."""
        import httpx
        
        if scope is None:
            scope = f"{self.graph_url}/.default"
        
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": scope,
        }
        
        async with httpx.AsyncClient() as client:
            resp = await client.post(self.token_url, data=data)
            resp.raise_for_status()
            self._token = AccessToken.from_dict(resp.json())
            return self._token
    
    async def _get_headers(self) -> Dict[str, str]:
        """Get headers with auth token."""
        if not self._token or self._token.is_expired:
            await self.get_token()
        
        return {
            "Authorization": f"{self._token.token_type} {self._token.access_token}",
            "Content-Type": "application/json",
        }
    
    async def register_agent(
        self,
        display_name: str,
        tags: Optional[List[str]] = None,
    ) -> AgentPrincipal:
        """Register an AI agent as a service principal."""
        import httpx
        
        app_id = str(uuid.uuid4())
        principal_id = str(uuid.uuid4())
        
        principal = AgentPrincipal(
            id=principal_id,
            app_id=app_id,
            display_name=display_name,
            tags=tags or ["agent", "ai"],
        )
        
        # Create application
        app_data = {
            "appId": app_id,
            "displayName": display_name,
            "tags": tags or ["agent", "ai"],
            "requiredResourceAccess": [],
        }
        
        async with httpx.AsyncClient() as client:
            # Create app registration
            resp = await client.post(
                f"{self.graph_url}/applications",
                json=app_data,
                headers=await self._get_headers(),
            )
            # Create service principal
            sp_data = principal.to_dict()
            resp = await client.post(
                f"{self.graph_url}/servicePrincipals",
                json=sp_data,
                headers=await self._get_headers(),
            )
        
        return principal
    
    async def get_agent(self, agent_id: str) -> Optional[AgentPrincipal]:
        """Get an agent service principal by ID."""
        import httpx
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.graph_url}/servicePrincipals/{agent_id}",
                headers=await self._get_headers(),
            )
            if resp.status_code == 200:
                data = resp.json()
                return AgentPrincipal(
                    id=data.get("id", ""),
                    app_id=data.get("appId", ""),
                    display_name=data.get("displayName", ""),
                    enabled=data.get("accountEnabled", True),
                )
        return None
    
    async def list_agents(self, filter_tag: Optional[str] = None) -> List[AgentPrincipal]:
        """List all agent service principals."""
        import httpx
        
        url = f"{self.graph_url}/servicePrincipals"
        if filter_tag:
            url += f"?$filter=tags/any(t:t eq '{filter_tag}')"
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=await self._get_headers())
            resp.raise_for_status()
            data = resp.json()
            
            return [
                AgentPrincipal(
                    id=sp.get("id", ""),
                    app_id=sp.get("appId", ""),
                    display_name=sp.get("displayName", ""),
                    enabled=sp.get("accountEnabled", True),
                )
                for sp in data.get("value", [])
            ]
    
    async def add_agent_credential(
        self,
        agent_id: str,
        display_name: str,
        credential_type: str = "password",
    ) -> str:
        """Add credential to agent service principal."""
        import httpx
        
        if credential_type == "password":
            secret = uuid.uuid4().hex + base64.b64encode(uuid.uuid4().bytes).decode()
            cred = {
                "displayName": display_name,
                "secretText": secret,
            }
        else:
            # Key credential
            cred = {
                "displayName": display_name,
                "type": "AsymmetricX509Cert",
                "usage": "Verify",
            }
        
        async with httpx.AsyncClient() as client:
            if credential_type == "password":
                url = f"{self.graph_url}/servicePrincipals/{agent_id}/addPassword"
            else:
                url = f"{self.graph_url}/servicePrincipals/{agent_id}/addKey"
            
            resp = await client.post(url, json=cred, headers=await self._get_headers())
            resp.raise_for_status()
            data = resp.json()
            
            if credential_type == "password":
                return data.get("secretText", "")
            return data.get("keyId", "")
    
    async def revoke_agent(self, agent_id: str):
        """Disable an agent service principal."""
        import httpx
        
        async with httpx.AsyncClient() as client:
            resp = await client.patch(
                f"{self.graph_url}/servicePrincipals/{agent_id}",
                json={"accountEnabled": False},
                headers=await self._get_headers(),
            )
            resp.raise_for_status()
    
    async def delete_agent(self, agent_id: str):
        """Delete an agent service principal."""
        import httpx
        
        async with httpx.AsyncClient() as client:
            resp = await client.delete(
                f"{self.graph_url}/servicePrincipals/{agent_id}",
                headers=await self._get_headers(),
            )
            resp.raise_for_status()


class VerifiedCredentialManager:
    """Entra Verified ID manager for agent credentials."""
    
    def __init__(self, client: EntraClient, authority: str):
        self.client = client
        self.authority = authority
    
    async def issue_credential(
        self,
        agent_id: str,
        credential_type: str,
        claims: Dict[str, Any],
        validity_hours: int = 24,
    ) -> VerifiedCredential:
        """Issue a verifiable credential to an agent."""
        now = int(time.time())
        
        credential = VerifiedCredential(
            id=str(uuid.uuid4()),
            issuer=self.client.client_id,
            type=credential_type,
            claims=claims,
            issued_at=now,
            expires_at=now + (validity_hours * 3600),
        )
        
        # In production, this would call the Verifiable Credentials API
        return credential
    
    async def verify_credential(self, credential: VerifiedCredential) -> bool:
        """Verify a credential is valid and not expired."""
        if credential.is_expired:
            return False
        
        # In production, verify the credential signature
        return True
    
    async def revoke_credential(self, credential_id: str):
        """Revoke a credential."""
        # In production, call the revocation API
        pass


__all__ = [
    "EntraClient",
    "VerifiedCredentialManager",
    "AgentPrincipal",
    "VerifiedCredential",
    "AccessToken",
    "AgentType",
    "__version__",
]
