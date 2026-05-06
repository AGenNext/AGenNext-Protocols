# AGenNext Protocols

A collection of AI agent protocols for multi-agent systems.

## Protocols

| Protocol | Description | Package |
|----------|-------------|---------|
| **MCP** | Model Context Protocol - Connect agents to tools & data | `mcp` |
| **A2A** | Agent2Agent Protocol - Agent-to-agent communication | `a2a-sdk` |
| **UCP** | Universal Commerce Protocol - E-commerce flows | `ucp-sdk` |
| **AP2** | Agent Payments Protocol - Payment authorization | `ap2` |
| **AG-UI** | Agent-User Interaction Protocol - Streaming | `ag-ui-protocol` |

## Installation

```bash
pip install agennext-protocols
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
from agennext import A2AClient, AgentCard

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
items = [PaymentItem(label="Items", amount=...)]
mandate = await client.authorize(intent, items)
```

### AG-UI (Agent-User Interaction Protocol)

```python
from agennext import AGUIStream

async with AGUIStream("http://agent:8000") as stream:
    async for event in stream.events():
        print(event.type, event.data)
```

## API Reference

See [docs/](docs/) for detailed API documentation.

## License

MIT License - see [LICENSE](LICENSE) for details.