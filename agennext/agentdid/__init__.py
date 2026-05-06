"""
AGenNext Protocols - Agent DID (Decentralized Identity)
=================================================
Decentralized Identity for AI agents using DID (Decentralized Identifiers).
Based on W3C DID Core specification and Agent Identity Protocol.

Usage:
    from agennext.agentdid import AgentDID, DIDClient, VerificationMethod
    
    # Create agent identity
    agent = AgentDID.new(agent_id="assistant-001")
    
    # Resolve DID
    client = DIDClient()
    doc = await client.resolve("did:web:agent.example:assistant")
    
    # Verify agent
    if await client.verify(agent):
        print("Verified!")
"""

import hashlib
import json
import time
import uuid
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum
import base58
import codecs

__version__ = "1.0.0"


class DIDMethod(Enum):
    """DID method."""
    WEB = "web"
    KEY = "key"
    AGENT = "agent"
    ION = "ion"


@dataclass
class VerificationMethod:
    """DID Verification Method."""
    id: str
    type: str
    controller: str
    public_key_jwk: Optional[Dict] = None
    public_key_multibase: Optional[str] = None
    
    def to_dict(self) -> Dict:
        result = {
            "id": self.id,
            "type": self.type,
            "controller": self.controller,
        }
        if self.public_key_jwk:
            result["publicKeyJwk"] = self.public_key_jwk
        if self.public_key_multibase:
            result["publicKeyMultibase"] = self.public_key_multibase
        return result


@dataclass
class Service:
    """DID Service endpoint."""
    id: str
    type: str
    service_endpoint: str
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "type": self.type,
            "serviceEndpoint": self.service_endpoint,
        }


@dataclass
class DIDDocument:
    """W3C DID Document."""
    context: List[str] = field(default_factory=lambda: ["https://www.w3.org/ns/did/v1"])
    id: str
    also_known_as: Optional[List[str]] = None
    controller: Optional[List[str]] = None
    verification_method: List[VerificationMethod] = field(default_factory=list)
    authentication: List[str] = field(default_factory=list)
    assertion_method: List[str] = field(default_factory=list)
    service: List[Service] = field(default_factory=list)
    created: Optional[str] = None
    updated: Optional[str] = None
    
    def to_dict(self) -> Dict:
        result = {
            "@context": self.context,
            "id": self.id,
        }
        if self.also_known_as:
            result["alsoKnownAs"] = self.also_known_as
        if self.controller:
            result["controller"] = self.controller
        if self.verification_method:
            result["verificationMethod"] = [vm.to_dict() for vm in self.verification_method]
        if self.authentication:
            result["authentication"] = self.authentication
        if self.assertion_method:
            result["assertionMethod"] = self.assertion_method
        if self.service:
            result["service"] = [s.to_dict() for s in self.service]
        if self.created:
            result["created"] = self.created
        if self.updated:
            result["updated"] = self.updated
        return result
    
    @classmethod
    def from_dict(cls, data: Dict) -> "DIDDocument":
        vms = [
            VerificationMethod(**vm)
            for vm in data.get("verificationMethod", [])
        ]
        services = [Service(**s) for s in data.get("service", [])]
        
        return cls(
            context=data.get("@context", ["https://www.w3.org/ns/did/v1"]),
            id=data.get("id", ""),
            also_known_as=data.get("alsoKnownAs"),
            controller=data.get("controller"),
            verification_method=vms,
            authentication=data.get("authentication", []),
            assertion_method=data.get("assertionMethod", []),
            service=services,
            created=data.get("created"),
            updated=data.get("updated"),
        )


@dataclass
class AgentDID:
    """Agent Decentralized Identity."""
    did: str
    private_key: Optional[str] = None
    document: Optional[DIDDocument] = None
    
    @classmethod
    def new(
        cls,
        agent_id: str,
        method: DIDMethod = DIDMethod.AGENT,
        domain: Optional[str] = None,
    ) -> "AgentDID":
        """Create a new Agent DID."""
        # Generate keypair (simplified)
        key_id = uuid.uuid4().hex[:16]
        
        if method == DIDMethod.WEB and domain:
            did = f"did:web:{domain}:{agent_id}"
        elif method == DIDMethod.KEY:
            key_bytes = hashlib.sha256(agent_id.encode()).digest()
            did = f"did:key:{base58.b58encode(key_bytes).decode()}"
        else:
            did = f"did:agent:{agent_id}"
        
        # Create document
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        vm_id = f"{did}#keys-1"
        vm = VerificationMethod(
            id=vm_id,
            type="Ed25519VerificationKey2020",
            controller=did,
            public_key_multibase=base58.b58encode(hashlib.sha256(did.encode()).digest()).decode(),
        )
        
        doc = DIDDocument(
            id=did,
            verification_method=[vm],
            authentication=[vm_id],
            assertion_method=[vm_id],
            created=now,
            updated=now,
        )
        
        return cls(did=did, document=doc)
    
    def add_service(self, service_type: str, endpoint: str):
        """Add a service endpoint to the DID."""
        service = Service(
            id=f"{self.did}#{service_type}",
            type=service_type,
            service_endpoint=endpoint,
        )
        self.document.service.append(service)
        self.document.updated = time.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    def sign(self, data: str) -> str:
        """Sign data with agent's private key (simplified)."""
        if self.private_key:
            return hashlib.sha256(f"{data}{self.private_key}".encode()).hexdigest()
        return hashlib.sha256(f"{data}{self.did}".encode()).hexdigest()
    
    def verify(self, data: str, signature: str) -> bool:
        """Verify a signature."""
        expected = self.sign(data)
        return expected == signature
    
    def to_dict(self) -> Dict:
        """Export as dict."""
        return {
            "did": self.did,
            "document": self.document.to_dict() if self.document else None,
        }


class DIDClient:
    """DID Resolution Client."""
    
    def __init__(self):
        self.cache: Dict[str, DIDDocument] = {}
    
    async def resolve(self, did: str) -> Optional[DIDDocument]:
        """Resolve a DID to its document."""
        # Check cache
        if did in self.cache:
            return self.cache[did]
        
        # Parse DID
        if not did.startswith("did:"):
            raise ValueError("Invalid DID format")
        
        parts = did.split(":")
        if len(parts) < 3:
            raise ValueError("Invalid DID format")
        
        method = parts[1]
        
        # Web DID resolution
        if method == "web":
            doc = await self._resolve_web(did)
        # Key DID (self-contained)
        elif method == "key":
            doc = self._resolve_key(did)
        # Agent DID
        elif method == "agent":
            doc = self._resolve_agent(did)
        else:
            raise ValueError(f"Unsupported DID method: {method}")
        
        if doc:
            self.cache[did] = doc
        
        return doc
    
    async def _resolve_web(self, did: str) -> Optional[DIDDocument]:
        """Resolve web DID."""
        import httpx
        
        # Extract domain and path
        parts = did.split(":")
        if len(parts) < 4:
            return None
        
        domain = parts[2]
        path = "/".join(parts[3:])
        
        url = f"https://{domain}/.well-known/did.json"
        if path:
            url = f"https://{domain}/{path}/did.json"
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    return DIDDocument.from_dict(resp.json())
        except:
            pass
        
        return None
    
    def _resolve_key(self, did: str) -> Optional[DIDDocument]:
        """Resolve key DID (self-contained)."""
        # Key DIDs are self-contained
        parts = did.split(":")
        if len(parts) < 3:
            return None
        
        multicodec = parts[2]
        
        # Create document from key
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        vm_id = f"{did}#keys-1"
        
        vm = VerificationMethod(
            id=vm_id,
            type="Ed25519VerificationKey2020",
            controller=did,
            public_key_multibase=multicodec,
        )
        
        return DIDDocument(
            id=did,
            verification_method=[vm],
            authentication=[vm_id],
            assertion_method=[vm_id],
            created=now,
            updated=now,
        )
    
    def _resolve_agent(self, did: str) -> Optional[DIDDocument]:
        """Resolve agent DID."""
        # Agent DIDs use a registry
        parts = did.split(":")
        if len(parts) < 3:
            return None
        
        agent_id = parts[2]
        
        # In production, query an agent registry
        return None
    
    async def verify(
        self,
        agent: AgentDID,
        data: str,
        signature: str,
    ) -> bool:
        """Verify agent identity and signature."""
        doc = await self.resolve(agent.did)
        
        if not doc:
            return False
        
        return agent.verify(data, signature)
    
    async def create_verifiable_credential(
        self,
        agent: AgentDID,
        claims: Dict[str, Any],
        issuer: Optional[str] = None,
    ) -> Dict:
        """Create a Verifiable Credential."""
        credential = {
            "@context": [
                "https://www.w3.org/2018/credentials/v1",
                "https://www.w3.org/ns/credentials/v2",
            ],
            "id": f"urn:uuid:{uuid.uuid4()}",
            "type": ["VerifiableCredential", "AgentCredential"],
            "issuer": issuer or agent.did,
            "issuanceDate": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "credentialSubject": {
                "id": agent.did,
                "claims": claims,
            },
        }
        
        # Sign credential
        data_to_sign = json.dumps(credential, sort_keys=True)
        credential["proof"] = {
            "type": "Ed25519Signature2020",
            "created": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "verificationMethod": f"{agent.did}#keys-1",
            "proofPurpose": "assertionMethod",
            "proofValue": agent.sign(data_to_sign),
        }
        
        return credential


__all__ = [
    "AgentDID",
    "DIDClient",
    "DIDDocument",
    "DIDMethod",
    "VerificationMethod",
    "Service",
    "__version__",
]
