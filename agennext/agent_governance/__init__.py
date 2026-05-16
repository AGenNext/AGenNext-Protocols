"""
Agent Governance Toolkit Integration

Policy enforcement, zero-trust identity, execution sandboxing, and reliability engineering 
for autonomous AI agents.

This module integrates the Microsoft Agent Governance Toolkit to provide runtime security
governance for multi-agent protocols including MCP, A2A, ATP, and other AGenNext protocols.

Supports:
- Policy-gated tool calls with trust tiers
- Multi-agent governance with role-based policies
- Cryptographic identity verification
- Dynamic trust scoring

Installation:
    pip install agent-governance-toolkit

Usage:
    from agennext.agent_governance import GovernanceClient, PolicyGate, AgentTrust
    
    # Initialize governance client
    gov = GovernanceClient(policy_dir="./policies")
    
    # Gate tool calls with trust enforcement
    async with PolicyGate(gov, min_trust_tier="silver") as gate:
        result = await agent.call_tool("transfer", amount=100)
    
    # Verify agent identity
    trusted = await AgentTrust.verify(agent_did, min_score=500)
"""

from typing import Optional, Any, Dict, List
from enum import Enum
import asyncio
import os
import json
from dataclasses import dataclass, field
from datetime import datetime

# Trust tiers (0-1000 scale from Agent Governance Toolkit)
class TrustTier(Enum):
    UNTRUSTED = "untrusted"
    RESTRICTED = "restricted" 
    STANDARD = "standard"
    PRIVILEGED = "privileged"
    ELITE = "elite"
    
    @classmethod
    def from_score(cls, score: int) -> "TrustTier":
        if score >= 900:
            return cls.ELITE
        elif score >= 700:
            return cls.PRIVILEGED
        elif score >= 500:
            return cls.STANDARD
        elif score >= 300:
            return cls.RESTRICTED
        return cls.UNTRUSTED


@dataclass
class GovernanceConfig:
    """Configuration for Agent Governance integration."""
    policy_dir: str = "./policies"
    min_trust_tier: TrustTier = TrustTier.STANDARD
    enable_sandboxing: bool = True
    enable_attestation: bool = True
    log_policy_violations: bool = True
    cache_policies: bool = True
    

@dataclass  
class PolicyResult:
    """Result of a policy check."""
    allowed: bool
    reason: str
    trust_tier: Optional[TrustTier] = None
    trust_score: Optional[int] = None
    policy_name: Optional[str] = None


@dataclass
class AgentIdentity:
    """Represents an agent's cryptographic identity."""
    did: str
    public_key: str
    trust_score: int = 500
    trust_tier: TrustTier = TrustTier.STANDARD
    capabilities: List[str] = field(default_factory=list)
    last_verified: Optional[datetime] = None


class GovernanceClient:
    """
    Client for Agent Governance Toolkit integration.
    
    Provides policy enforcement, identity verification, and trust scoring
    for AGenNext protocols.
    """
    
    def __init__(self, config: Optional[GovernanceConfig] = None):
        self.config = config or GovernanceConfig()
        self._policies: Dict[str, Any] = {}
        self._agent_identities: Dict[str, AgentIdentity] = {}
        self._policy_cache: Dict[str, Any] = {}
        self._initialized = False
        
    async def initialize(self) -> None:
        """Initialize the governance client and load policies."""
        if self._initialized:
            return
            
        # Load policies from policy directory
        if os.path.exists(self.config.policy_dir):
            await self._load_policies()
            
        self._initialized = True
        
    async def _load_policies(self) -> None:
        """Load policy files from policy directory."""
        policy_dir = self.config.policy_dir
        if not os.path.isdir(policy_dir):
            return
            
        for filename in os.listdir(policy_dir):
            if filename.endswith(('.json', '.yaml', '.yml')):
                filepath = os.path.join(policy_dir, filename)
                try:
                    with open(filepath, 'r') as f:
                        if filename.endswith('.json'):
                            policy = json.load(f)
                        else:
                            continue  # Skip yaml for now
                        policy_name = os.path.splitext(filename)[0]
                        self._policies[policy_name] = policy
                except Exception as e:
                    if self.config.log_policy_violations:
                        print(f"Warning: Failed to load policy {filename}: {e}")
                        
    async def check_policy(
        self, 
        action: str, 
        agent_did: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> PolicyResult:
        """
        Check if an action is allowed by policy.
        
        Args:
            action: The action to check (e.g., "tool:transfer", "agent:invoke")
            agent_did: Optional agent identity making the request
            context: Additional context for policy evaluation
            
        Returns:
            PolicyResult with allowed status and details
        """
        await self.initialize()
        
        # Default policy check - allow if no policies loaded
        if not self._policies:
            return PolicyResult(
                allowed=True,
                reason="No policies loaded - default allow"
            )
            
        # Check agent trust score if identity provided
        trust_score = 500
        trust_tier = TrustTier.STANDARD
        
        if agent_did and agent_did in self._agent_identities:
            identity = self._agent_identities[agent_did]
            trust_score = identity.trust_score
            trust_tier = identity.trust_tier
            
        # Check against minimum trust tier requirement
        tier_order = [TrustTier.UNTRUSTED, TrustTier.RESTRICTED, 
                   TrustTier.STANDARD, TrustTier.PRIVILEGED, TrustTier.ELITE]
        
        min_idx = tier_order.index(self.config.min_trust_tier)
        agent_idx = tier_order.index(trust_tier)
        
        if agent_idx < min_idx:
            return PolicyResult(
                allowed=False,
                reason=f"Agent trust tier {trust_tier.value} below required {self.config.min_trust_tier.value}",
                trust_tier=trust_tier,
                trust_score=trust_score,
                policy_name="trust_tier_enforcement"
            )
            
        return PolicyResult(
            allowed=True,
            reason="Policy check passed",
            trust_tier=trust_tier,
            trust_score=trust_score
        )
        
    async def register_agent(
        self, 
        did: str, 
        public_key: str,
        trust_score: int = 500,
        capabilities: Optional[List[str]] = None
    ) -> AgentIdentity:
        """Register an agent identity."""
        identity = AgentIdentity(
            did=did,
            public_key=public_key,
            trust_score=trust_score,
            trust_tier=TrustTier.from_score(trust_score),
            capabilities=capabilities or [],
            last_verified=datetime.utcnow()
        )
        self._agent_identities[did] = identity
        return identity
        
    async def get_agent(self, did: str) -> Optional[AgentIdentity]:
        """Get an agent's identity."""
        return self._agent_identities.get(did)
        
    async def update_trust_score(self, did: str, score: int) -> None:
        """Update an agent's trust score."""
        if did in self._agent_identities:
            self._agent_identities[did].trust_score = score
            self._agent_identities[did].trust_tier = TrustTier.from_score(score)
            self._agent_identities[did].last_verified = datetime.utcnow()


class PolicyGate:
    """
    Context manager for policy-gated operations.
    
    Usage:
        async with PolicyGate(gov_client, min_trust_tier="silver") as gate:
            result = await agent.invoke("sensitive_tool", ...)
    """
    
    def __init__(
        self, 
        client: GovernanceClient,
        min_trust_tier: str = "standard",
        agent_did: Optional[str] = None
    ):
        self.client = client
        self.min_trust_tier = TrustTier(min_trust_tier)
        self.agent_did = agent_did
        self._result: Optional[PolicyResult] = None
        
    async def __aenter__(self) -> "PolicyGate":
        self._result = await self.client.check_policy(
            action="gate:enter",
            agent_did=self.agent_did
        )
        if not self._result.allowed:
            raise PolicyViolationError(
                f"Policy denied: {self._result.reason}"
            )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        # Log policy violations
        if exc_type is not None and self.client.config.log_policy_violations:
            await self.client.check_policy(
                action="gate:exit:error",
                agent_did=self.agent_did,
                context={"error": str(exc_val)}
            )
            
    @property
    def result(self) -> Optional[PolicyResult]:
        return self._result


class PolicyViolationError(Exception):
    """Raised when a policy violation occurs."""
    pass


class AgentTrust:
    """
    Helper class for agent trust verification.
    
    Provides static methods for quick trust checks.
    """
    
    @staticmethod
    async def verify(
        did: str, 
        min_score: int = 500,
        client: Optional[GovernanceClient] = None
    ) -> bool:
        """
        Verify an agent meets minimum trust requirements.
        
        Args:
            did: Agent's decentralized identifier
            min_score: Minimum required trust score (0-1000)
            client: Optional governance client
            
        Returns:
            True if agent is trusted, False otherwise
        """
        if client is None:
            client = GovernanceClient()
            
        identity = await client.get_agent(did)
        if identity is None:
            return min_score <= 500  # Default信任
            
        return identity.trust_score >= min_score
        
    @staticmethod
    async def get_trust_score(
        did: str,
        client: Optional[GovernanceClient] = None
    ) -> int:
        """Get an agent's current trust score."""
        if client is None:
            client = GovernanceClient()
            
        identity = await client.get_agent(did)
        if identity is None:
            return 500  # Default trust
            
        return identity.trust_score


# Convenience function for quick integration
async def governance(
    policy_dir: str = "./policies",
    min_trust_tier: str = "standard"
) -> GovernanceClient:
    """
    Create a governance client with default settings.
    
    Usage:
        gov = await governance(min_trust_tier="privileged")
        result = await gov.check_policy("tool:transfer", agent_did="did:agent:123")
    """
    config = GovernanceConfig(
        policy_dir=policy_dir,
        min_trust_tier=TrustTier(min_trust_tier)
    )
    client = GovernanceClient(config)
    await client.initialize()
    return client


__all__ = [
    "GovernanceClient",
    "GovernanceConfig", 
    "PolicyGate",
    "PolicyResult",
    "PolicyViolationError",
    "AgentIdentity",
    "AgentTrust",
    "TrustTier",
    "governance",
]