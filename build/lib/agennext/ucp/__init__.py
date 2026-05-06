"""
AGenNext Protocols - UCP (Universal Commerce Protocol)
=================================================
Standardizes the shopping lifecycle with modular capabilities.

Usage:
    from agennext.ucp import UCPClient, CheckoutRequest, LineItem
    
    client = await UCPClient.connect("http://shop:8182")
    cart = CheckoutRequest(items=[LineItem(id="SKU123", quantity=2)])
    checkout = await client.create_checkout(cart)
    order = await client.complete_checkout(checkout.id)
"""

import httpx
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from uuid import uuid4
from decimal import Decimal

__version__ = "1.0.0"

# Try to use ucp-sdk if available
try:
    from ucp_sdk.models.schemas.shopping.checkout_create_req import CheckoutCreateRequest as _UCPRequest
    from ucp_sdk.models.discovery.profile_schema import UcpDiscoveryProfile
    UCP_SDK_AVAILABLE = True
except ImportError:
    _UCPRequest = None
    UCP_SDK_AVAILABLE = False


@dataclass
class LineItem:
    """A line item in a checkout."""
    id: str
    quantity: int = 1
    price: Optional[Decimal] = None
    name: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "quantity": self.quantity,
            "price": str(self.price) if self.price else None,
            "name": self.name,
        }


@dataclass
class CheckoutRequest:
    """A checkout request."""
    items: List[LineItem] = field(default_factory=list)
    currency: str = "USD"
    customer_id: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "lineItems": [item.to_dict() for item in self.items],
            "currency": self.currency,
            "customerId": self.customer_id,
        }


@dataclass
class CheckoutResponse:
    """Checkout response."""
    id: str
    status: str
    total: Decimal
    currency: str
    items: List[LineItem]
    
    @classmethod
    def from_dict(cls, data: Dict) -> "CheckoutResponse":
        return cls(
            id=data.get("id", ""),
            status=data.get("status", ""),
            total=Decimal(str(data.get("total", 0))),
            currency=data.get("currency", "USD"),
            items=[LineItem(**item) for item in data.get("lineItems", [])],
        )


class UCPClient:
    """UCP Protocol Client."""
    
    def __init__(self, base_url: str, agent_profile: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.agent_profile = agent_profile or "http://localhost/agent"
        self._http = None
    
    async def __aenter__(self):
        self._http = httpx.AsyncClient(timeout=30.0)
        return self
    
    async def __aexit__(self, *args):
        if self._http:
            await self._http.aclose()
    
    async def discover_profile(self) -> Dict:
        """Discover the UCP profile."""
        resp = await self._http.get(f"{self.base_url}/.well-known/ucp")
        resp.raise_for_status()
        return resp.json()
    
    async def create_checkout(self, request: CheckoutRequest) -> CheckoutResponse:
        """Create a checkout session."""
        headers = {
            "UCP-Agent": self.agent_profile,
            "Idempotency-Key": str(uuid4()),
            "Request-Id": str(uuid4()),
        }
        
        resp = await self._http.post(
            f"{self.base_url}/checkout-sessions",
            json=request.to_dict(),
            headers=headers,
        )
        resp.raise_for_status()
        return CheckoutResponse.from_dict(resp.json())
    
    async def complete_checkout(self, checkout_id: str) -> Dict:
        """Complete a checkout."""
        headers = {
            "UCP-Agent": self.agent_profile,
            "Idempotency-Key": str(uuid4()),
        }
        
        resp = await self._http.post(
            f"{self.base_url}/checkout-sessions/{checkout_id}/complete",
            headers=headers,
        )
        resp.raise_for_status()
        return resp.json()
    
    async def get_checkout(self, checkout_id: str) -> CheckoutResponse:
        """Get checkout status."""
        resp = await self._http.get(f"{self.base_url}/checkout-sessions/{checkout_id}")
        resp.raise_for_status()
        return CheckoutResponse.from_dict(resp.json())


__all__ = ["UCPClient", "CheckoutRequest", "CheckoutResponse", "LineItem", "__version__"]