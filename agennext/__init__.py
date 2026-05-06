"""
AGenNext Protocols
================
A collection of AI agent protocols for multi-agent systems.

Quick Start:
    from agennext import MCPClient, A2AClient, UCPClient, PaymentClient, AGUIStream, ACPClient
    
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
"""

__version__ = "1.0.0"
__author__ = "AGenNext"

# Protocol exports
from .mcp import MCPClient, MCPProtocol, Tool
from .a2a import A2AClient, A2AServer, AgentCard
from .ucp import UCPClient, CheckoutRequest, CheckoutResponse, LineItem as UcpLineItem
from .ap2 import (
    IntentMandate,
    PaymentMandate,
    PaymentReceipt,
    PaymentCurrencyAmount,
    PaymentItem,
    PaymentClient,
    PaymentStatus,
)
from .agui import (
    AGUIStream,
    AGUIServer,
    AGUIEvent,
    EventType,
    TextMessage,
    ToolCall,
    ToolCallResult,
    RunStarted,
    RunFinished,
    InputRequired,
    Error,
)
from .acp import (
    ACPClient,
    Cart,
    LineItem,
    Money,
    Quantity,
    CheckoutSession,
    Order,
    CheckoutStatus,
    LineItemStatus,
)

__all__ = [
    # MCP
    "MCPClient",
    "MCPProtocol",
    "Tool",
    # A2A
    "A2AClient",
    "A2AServer",
    "AgentCard",
    # UCP
    "UCPClient",
    "CheckoutRequest",
    "CheckoutResponse",
    "LineItem",
    # AP2
    "IntentMandate",
    "PaymentMandate",
    "PaymentReceipt",
    "PaymentCurrencyAmount",
    "PaymentItem",
    "PaymentClient",
    "PaymentStatus",
    # AG-UI
    "AGUIStream",
    "AGUIServer",
    "AGUIEvent",
    "EventType",
    "TextMessage",
    "ToolCall",
    "ToolCallResult",
    "RunStarted",
    "RunFinished",
    "InputRequired",
    "Error",
    # ACP
    "ACPClient",
    "Cart",
    "LineItem",
    "Money",
    "Quantity",
    "CheckoutSession",
    "Order",
    "CheckoutStatus",
    "LineItemStatus",
    # Version
    "__version__",
]