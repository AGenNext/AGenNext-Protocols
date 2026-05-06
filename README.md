# AGenNext Protocols

A comprehensive collection of AI agent protocols for multi-agent systems.

## Protocols

| # | Protocol | Module | Description |
|---|---------|--------|-------------|
| 1 | **MCP** | `agennext.mcp` | Model Context Protocol - Connect agents to tools & data |
| 2 | **A2A** | `agennext.a2a` | Agent2Agent Protocol - Agent-to-agent communication |
| 3 | **UCP** | `agennext.ucp` | Universal Commerce Protocol - E-commerce flows |
| 4 | **AP2** | `agennext.ap2` | Agent Payments Protocol - Payment authorization |
| 5 | **AG-UI** | `agennext.agui` | Agent-User Interaction - Streaming events |
| 6 | **ACP** | `agennext.acp` | Agentic Commerce Protocol - OpenAI/Stripe |
| 7 | **ATP** | `agennext.atp` | Agent Trade Protocol - Payment-gated API |
| 8 | **ACP2** | `agennext.acp2` | Agent Client Protocol - Editor-agent communication |
| 9 | **AuthZen** | `agennext.authzen` | Authorization - OpenID Foundation |
| 10 | **Agent ID** | `agennext.agentid` | OIDC Identity - Token-based auth |
| 11 | **Entra ID** | `agennext.entraid` | Azure AD - Microsoft Entra ID |
| 12 | **Agent DID** | `agennext.agentdid` | Decentralized Identity - W3C DID |
| 13 | **Registry** | `agennext.registry` | Agent Discovery - A2A discovery |

## Installation

```bash
pip install agennext-protocols
```

## Quick Start

```python
from agennext import (
    MCPClient, A2AClient, UCPClient, PaymentClient,
    AGUIStream, ACPClient, ATPClient, AuthZClient,
    IdentityClient, EntraClient, AgentDID, AgentRegistry
)

# MCP - Connect to tools
async with MCPClient("server.py") as client:
    tools = await client.list_tools()

# A2A - Connect to agents
client = await A2AClient.connect("http://agent:8000")

# UCP - E-commerce
async with UCPClient("http://shop:8182") as client:
    checkout = await client.create_checkout(cart)

# AP2 - Payments
client = PaymentClient(private_key)
mandate = await client.authorize(intent, items)

# AG-UI - Streaming
async with AGUIStream("http://agent:8000") as stream:
    async for event in stream.events():
        print(event)

# ACP - Agentic Commerce
client = ACPClient(merchant_id="...")
cart = Cart(items=[LineItem(id="SKU", quantity=2)])
session = await client.create_checkout(cart)

# ATP - Agent Trade
client = ATPClient(api_key="...", recipient_pubkey="...")
result = await client.request("https://api.example.com/agent", {...})

# AuthZen - Authorization
authz = AuthZClient(base_url="https://auth.example.com")
decision = await authz.check(request)

# Agent Identity - OIDC
identity = IdentityClient(base_url="https://identity.example.com")
token = await identity.authenticate(agent)

# Entra ID - Azure AD
entra = EntraClient(tenant_id="...", client_id="...", client_secret="...")
principal = await entra.register_agent("assistant")

# Agent DID - Decentralized ID
agent = AgentDID.new(agent_id="assistant-001")
client = DIDClient()
doc = await client.resolve(agent.did)

# Registry - Agent Discovery
registry = AgentRegistry()
entry = await registry.register(name="Assistant", endpoint="https://...")
agents = await registry.discover(capability="tools")
```

## Protocol Categories

### Communication
- **MCP** - Tool/data access
- **A2A** - Agent-to-agent
- **AG-UI** - User interaction streaming

### Commerce & Payments
- **UCP** - Universal Commerce
- **ACP** - Agentic Commerce (OpenAI/Stripe)
- **AP2** - Agent Payments
- **ATP** - Agent Trade (Solana)

### Identity & Security
- **AuthZen** - Authorization (OpenID)
- **Agent ID** - OIDC tokens
- **Entra ID** - Azure AD
- **Agent DID** - Decentralized ID
- **ACP2** - Editor-agent (Zed)

### Discovery
- **Registry** - Agent registry

## Docker

```bash
docker build -t agennext/protocols .
docker run agennext/protocols
```

## License

MIT License - see [LICENSE](LICENSE)
