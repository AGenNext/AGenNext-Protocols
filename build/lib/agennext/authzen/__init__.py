"""
AGenNext Protocols - AuthZen (Authorization Protocol)
=============================================
Proposed standard for Authorization API by OpenID Foundation.
Fine-grained authorization for AI agents.

Usage:
    from agennext.authzen import AuthZClient, AccessRequest, Decision
    
    client = AuthZClient(base_url="https://auth.example.com")
    request = AccessRequest(
        subject="user:123",
        action="read",
        resource="doc:456",
    )
    decision = await client.check(request)
    if decision.allowed:
        print("Access granted!")
"""

import httpx
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from uuid import uuid4
from enum import Enum
from datetime import datetime

__version__ = "1.0.0"


class DecisionEffect(Enum):
    """Authorization decision effect."""
    PERMIT = "PERMIT"
    DENY = "DENY"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    INDETERMINATE = "INDETERMINATE"


@dataclass
class Subject:
    """Subject (who is making the request)."""
    id: str
    type: str = "user"
    attributes: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {"id": self.id, "type": self.type, "attributes": self.attributes}


@dataclass
class Resource:
    """Resource being accessed."""
    id: str
    type: str
    attributes: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {"id": self.id, "type": self.type, "attributes": self.attributes}


@dataclass
class Action:
    """Action being performed."""
    name: str
    attributes: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {"name": self.name, "attributes": self.attributes}


@dataclass
class Context:
    """Additional context for authorization."""
    time: Optional[str] = None
    ip_address: Optional[str] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        result = {}
        if self.time:
            result["time"] = self.time
        if self.ip_address:
            result["ip_address"] = self.ip_address
        result["attributes"] = self.attributes
        return result


@dataclass
class AccessRequest:
    """Authorization access request."""
    subject: Subject
    action: Action
    resource: Resource
    context: Optional[Context] = None
    
    def to_dict(self) -> Dict:
        return {
            "subject": self.subject.to_dict(),
            "action": self.action.to_dict(),
            "resource": self.resource.to_dict(),
            "context": self.context.to_dict() if self.context else {},
        }


@dataclass
class Decision:
    """Authorization decision."""
    effect: DecisionEffect
    obligations: List[Dict] = field(default_factory=list)
    advice: List[Dict] = field(default_factory=list)
    
    @property
    def allowed(self) -> bool:
        return self.effect == DecisionEffect.PERMIT
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Decision":
        return cls(
            effect=DecisionEffect(data.get("effect", "DENY")),
            obligations=data.get("obligations", []),
            advice=data.get("advice", []),
        )


@dataclass
class Policy:
    """Authorization policy."""
    id: str
    name: str
    description: str
    effect: DecisionEffect
    subject_match: Dict[str, Any] = field(default_factory=dict)
    resource_match: Dict[str, Any] = field(default_factory=dict)
    action_match: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "effect": self.effect.value,
            "subjectMatch": self.subject_match,
            "resourceMatch": self.resource_match,
            "actionMatch": self.action_match,
        }


class AuthZClient:
    """AuthZen Authorization Client."""
    
    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        client_id: Optional[str] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.client_id = client_id
        self._http = None
    
    async def __aenter__(self):
        self._http = httpx.AsyncClient(timeout=30.0)
        return self
    
    async def __aexit__(self, *args):
        if self._http:
            await self._http.aclose()
    
    def _get_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        if self.client_id:
            headers["X-Client-ID"] = self.client_id
        return headers
    
    async def check(self, request: AccessRequest) -> Decision:
        """Check authorization for an access request."""
        resp = await self._http.post(
            f"{self.base_url}/v1/authorize",
            json=request.to_dict(),
            headers=self._get_headers(),
        )
        resp.raise_for_status()
        return Decision.from_dict(resp.json())
    
    async def batch_check(self, requests: List[AccessRequest]) -> List[Decision]:
        """Batch check authorization for multiple requests."""
        resp = await self._http.post(
            f"{self.base_url}/v1/authorize/batch",
            json={"requests": [r.to_dict() for r in requests]},
            headers=self._get_headers(),
        )
        resp.raise_for_status()
        data = resp.json()
        return [Decision.from_dict(d) for d in data.get("decisions", [])]
    
    async def list_policies(self) -> List[Policy]:
        """List authorization policies."""
        resp = await self._http.get(
            f"{self.base_url}/v1/policies",
            headers=self._get_headers(),
        )
        resp.raise_for_status()
        data = resp.json()
        return [Policy(**p) for p in data.get("policies", [])]
    
    async def create_policy(self, policy: Policy) -> Policy:
        """Create a new authorization policy."""
        resp = await self._http.post(
            f"{self.base_url}/v1/policies",
            json=policy.to_dict(),
            headers=self._get_headers(),
        )
        resp.raise_for_status()
        return Policy(**resp.json())
    
    async def delete_policy(self, policy_id: str):
        """Delete an authorization policy."""
        resp = await self._http.delete(
            f"{self.base_url}/v1/policies/{policy_id}",
            headers=self._get_headers(),
        )
        resp.raise_for_status()


class AuthZServer:
    """Simple AuthZen Authorization Server."""
    
    def __init__(self):
        self.policies: Dict[str, Policy] = {}
    
    def add_policy(self, policy: Policy):
        """Add a policy."""
        self.policies[policy.id] = policy
    
    async def check(self, request: AccessRequest) -> Decision:
        """Check authorization against policies."""
        for policy in self.policies.values():
            # Simple matching - in production use proper PEP/PDP
            if self._matches(request.subject, policy.subject_match) and \
               self._matches(request.resource, policy.resource_match) and \
               self._matches_action(request.action, policy.action_match):
                return Decision(effect=policy.effect)
        
        return Decision(effect=DecisionEffect.DENY)
    
    def _matches(self, entity: Any, match_criteria: Dict) -> bool:
        if not match_criteria:
            return True
        # Simple attribute matching
        return True
    
    def _matches_action(self, action: Action, match_criteria: Dict) -> bool:
        if not match_criteria:
            return True
        if "name" in match_criteria:
            return action.name == match_criteria["name"]
        return True


__all__ = [
    "AuthZClient",
    "AuthZServer",
    "AccessRequest",
    "Decision",
    "DecisionEffect",
    "Subject",
    "Resource",
    "Action",
    "Context",
    "Policy",
    "__version__",
]
