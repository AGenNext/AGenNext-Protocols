# AGenNext Protocols

[![CI](https://github.com/AGenNext/AGenNext-Protocols/actions/workflows/ci.yml/badge.svg)](https://github.com/AGenNext/AGenNext-Protocols/actions/workflows/ci.yml)
[![Release](https://github.com/AGenNext/AGenNext-Protocols/actions/workflows/release.yml/badge.svg)](https://github.com/AGenNext/AGenNext-Protocols/actions/workflows/release.yml)
[![PyPI](https://img.shields.io/pypi/v/agennext-protocols.svg)](https://pypi.org/project/agennext-protocols/)
[![Python](https://img.shields.io/pypi/pyversions/agennext-protocols.svg)](https://pypi.org/project/agennext-protocols/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A vendor-agnostic Python SDK for the AI agent protocol stack.

AGenNext Protocols helps teams build interoperable multi-agent systems across communication, commerce, identity, security, and discovery protocols.

## Links

- **Marketing site:** [docs/index.html](docs/index.html)
- **Package:** [PyPI](https://pypi.org/project/agennext-protocols/)
- **Security policy:** [SECURITY.md](SECURITY.md)
- **Contributing guide:** [CONTRIBUTING.md](CONTRIBUTING.md)

## Protocols

| Protocol | Category | Description | Module |
|----------|----------|-------------|--------|
| **MCP** | Communication | Model Context Protocol - Connect agents to tools & data | `agennext.mcp` |
| **A2A** | Communication | Agent2Agent Protocol - Agent-to-agent communication | `agennext.a2a` |
| **AG-UI** | Communication | Agent-User Interaction Protocol - Streaming | `agennext.agui` |
| **UCP** | Commerce | Universal Commerce Protocol - E-commerce flows | `agennext.ucp` |
| **ACP** | Commerce | Agentic Commerce Protocol - OpenAI/Stripe style checkout | `agennext.acp` |
| **AP2** | Commerce | Agent Payments Protocol - Payment authorization | `agennext.ap2` |
| **ATP** | Commerce | Agent Trade Protocol - Payment-gated APIs | `agennext.atp` |
| **AuthZen** | Identity & Security | Authorization checks using OpenID Foundation patterns | `agennext.authzen` |
| **Agent ID** | Identity & Security | OIDC identity and token-based auth | `agennext.agentid` |
| **Entra ID** | Identity & Security | Microsoft Entra ID integration patterns | `agennext.entraid` |
| **Agent DID** | Identity & Security | Decentralized identity using W3C DID patterns | `agennext.agentdid` |
| **ACP2** | Identity & Security | Editor-agent communication | `agennext.acp2` |
| **Registry** | Discovery | Agent registry and capability discovery | `agennext.registry` |

## Installation

```bash
pip install agennext-protocols
```

For local development:

```bash
git clone https://github.com/AGenNext/AGenNext-Protocols.git
cd AGenNext-Protocols
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
```

## Quick Start

### MCP (Model Context Protocol)

```python
from agennext import MCPClient

async with MCPClient("npx -y @notionhq/notion-mcp-server") as client:
    tools = await client.list_tools()
    result = await client.call_tool("search", {"query": "..."})
```

### A2A (Agent2Agent Protocol)

```python
from agennext import A2AClient

client = await A2AClient.connect("http://agent:8000")
card = await client.get_agent_card()
async for response in client.send_message("Hello"):
    print(response)
```

### UCP (Universal Commerce Protocol)

```python
from agennext import UCPClient, CheckoutRequest, LineItem

async with UCPClient("http://shop:8182") as client:
    cart = CheckoutRequest(items=[
        LineItem(id="SKU123", quantity=2)
    ])
    checkout = await client.create_checkout(cart)
    order = await client.complete_checkout(checkout.id)
```

### AP2 (Agent Payments Protocol)

```python
from agennext import PaymentClient, IntentMandate, PaymentItem
from decimal import Decimal

client = PaymentClient(private_key="...")
intent = IntentMandate(
    merchants=["shop.com"],
    limit=Decimal("1000.00"),
    description="Order #12345"
)
items = [PaymentItem(label="Items", amount=Decimal("42.00"))]
mandate = await client.authorize(intent, items)
```

### AG-UI (Agent-User Interaction Protocol)

```python
from agennext import AGUIStream

async with AGUIStream("http://agent:8000") as stream:
    async for event in stream.events():
        print(event.type, event.data)
```

## Quality & Security

This repository includes CI, formatting, linting, dependency auditing, static security analysis, and secret scanning. See `.github/workflows/ci.yml` and `.github/dependabot.yml`.

## Releasing

Releases are automated through GitHub Actions and PyPI Trusted Publishing. Create a GitHub release or push a version tag such as `v1.0.1` to publish.

## License

MIT License - see [LICENSE](LICENSE) for details.
