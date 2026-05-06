"""
AGenNext Protocols
================
A collection of AI agent protocols for multi-agent systems.

Quick Start:
    from agennext import MCPClient, A2AClient, UCPClient, PaymentClient, AGUIStream, ACPClient, ATPClient
    
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
    
    # ATP - Agent Trade Protocol
    client = ATPClient(api_key="...", recipient_pubkey="...")
    result = await client.request("https://api.example.com/agent", {"prompt": "..."})
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
from .atp import (
    ATPClient,
    ATPSettlementMiddleware,
    UsageData,
    PriceQuote,
    SettlementStatus,
)
from .agentdid import (
    AgentDID,
    DIDClient,
    DIDDocument,
    DIDMethod,
    VerificationMethod,
    Service,
)
from .registry import (
    AgentRegistry,
    RegistryClient,
    AgentEntry,
    AgentCapability,
    AgentStatus,
    SearchQuery,
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
    # ATP
    "ATPClient",
    "ATPSettlementMiddleware",
    "UsageData",
    "PriceQuote",
    "SettlementStatus",
    # Agent Client Protocol
    "AgentClient",
    "Agent",
    "Message",
    "MessageRole",
    "Tool",
    "ToolCall",
    "ToolResult",
    # AuthZen
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
    # Agent Identity
    "AgentIdentity",
    "AgentCredential",
    "IdentityClient",
    "Token",
    "TokenRequest",
    "AgentRegistry",
    "AgentCapability",
    # Entra ID
    "EntraClient",
    "VerifiedCredentialManager",
    "AgentPrincipal",
    "VerifiedCredential",
    "AccessToken",
    "AgentType",
    # Agent DID
    "AgentDID",
    "DIDClient",
    "DIDDocument",
    "DIDMethod",
    "VerificationMethod",
    "Service",
    # Registry
    "RegistryClient",
    "AgentEntry",
    "SearchQuery",
    "RegistryStats",
    # Version
    "__version__",
]