"""
AGenNext Protocols - ACP (Agentic Commerce Protocol)
==============================================
The Agentic Commerce Protocol (ACP) is an interaction model and open standard 
for connecting buyers, their AI agents, and businesses to complete purchases seamlessly.

Maintained by: OpenAI and Stripe

Usage:
    from agennext.acp import ACPClient, Cart, CheckoutSession
    
    client = ACPClient(merchant_id="...")
    cart = Cart(items=[LineItem(id="SKU123", quantity=2)])
    session = await client.create_checkout(cart)
    await client.complete_checkout(session.id)
"""

import httpx
import time
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from uuid import uuid4
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum

__version__ = "1.0.0"


class CheckoutStatus(Enum):
    """Checkout session status."""
    CREATED = "created"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class LineItemStatus(Enum):
    """Line item status."""
    PROCESSING = "processing"
    PARTIAL = "partial"
    FULFILLED = "fulfilled"
    REMOVED = "removed"


@dataclass
class Money:
    """Monetary amount in specified currency."""
    currency: str = "USD"
    value: str = "0"
    
    @classmethod
    def from_decimal(cls, amount: Decimal, currency: str = "USD") -> "Money":
        return cls(currency=currency, value=str(amount.quantize(Decimal("0.01"), ROUND_HALF_UP)))
    
    def to_dict(self) -> Dict:
        return {"currency": self.currency, "value": self.value}
    
    @property
    def decimal(self) -> Decimal:
        return Decimal(self.value)


@dataclass
class Quantity:
    """Line item quantity breakdown."""
    ordered: int
    current: int = 0
    fulfilled: int = 0
    
    def __post_init__(self):
        if self.current == 0:
            self.current = self.ordered
    
    def to_dict(self) -> Dict:
        return {"ordered": self.ordered, "current": self.current, "fulfilled": self.fulfilled}
    
    @property
    def status(self) -> LineItemStatus:
        if self.current == 0:
            return LineItemStatus.REMOVED
        elif self.fulfilled >= self.current:
            return LineItemStatus.FULFILLED
        elif self.fulfilled > 0:
            return LineItemStatus.PARTIAL
        return LineItemStatus.PROCESSING


@dataclass
class LineItem:
    """A line item in cart/checkout."""
    id: str
    quantity: int = 1
    price: Money = field(default_factory=lambda: Money())
    name: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "quantity": self.quantity,
            "price": self.price.to_dict(),
            "name": self.name,
            "description": self.description,
            "imageUrl": self.image_url,
        }
    
    @property
    def total(self) -> Money:
        total = self.price.decimal * Decimal(self.quantity)
        return Money.from_decimal(total, self.price.currency)


@dataclass
class Cart:
    """Shopping cart."""
    items: List[LineItem] = field(default_factory=list)
    currency: str = "USD"
    
    def to_dict(self) -> Dict:
        return {"lineItems": [item.to_dict() for item in self.items], "currency": self.currency}
    
    @property
    def total(self) -> Money:
        total = Decimal("0")
        for item in self.items:
            total += item.total.decimal
        return Money.from_decimal(total, self.currency)


@dataclass
class CheckoutSession:
    """Checkout session response."""
    id: str
    status: CheckoutStatus
    cart: Cart
    total: Money
    url: Optional[str] = None
    payment_intent_client_secret: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict) -> "CheckoutSession":
        cart_data = data.get("cart", {})
        items = [
            LineItem(
                id=item.get("id", ""),
                quantity=item.get("quantity", 1),
                price=Money(
                    currency=item.get("price", {}).get("currency", "USD"),
                    value=item.get("price", {}).get("value", "0"),
                ),
                name=item.get("name"),
            )
            for item in cart_data.get("lineItems", [])
        ]
        cart = Cart(items=items, currency=cart_data.get("currency", "USD"))
        total_data = data.get("total", {})
        total = Money(currency=total_data.get("currency", "USD"), value=total_data.get("value", "0"))
        
        return cls(
            id=data.get("id", ""),
            status=CheckoutStatus(data.get("status", "created")),
            cart=cart,
            total=total,
            url=data.get("url"),
            payment_intent_client_secret=data.get("paymentIntentClientSecret"),
        )


@dataclass
class Order:
    """Order after checkout completion."""
    id: str
    status: str
    items: List[Dict] = field(default_factory=list)
    total: Money = field(default_factory=Money)
    created_at: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Order":
        return cls(
            id=data.get("id", ""),
            status=data.get("status", ""),
            items=data.get("lineItems", []),
            total=Money(
                currency=data.get("total", {}).get("currency", "USD"),
                value=data.get("total", {}).get("value", "0"),
            ),
            created_at=data.get("createdAt"),
        )


class ACPClient:
    """Agentic Commerce Protocol Client."""
    
    def __init__(
        self,
        merchant_id: str,
        api_key: Optional[str] = None,
        base_url: str = "https://api.agenticcommerce.dev",
    ):
        self.merchant_id = merchant_id
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self._http = None
    
    async def __aenter__(self):
        self._http = httpx.AsyncClient(timeout=30.0)
        return self
    
    async def __aexit__(self, *args):
        if self._http:
            await self._http.aclose()
    
    def _generate_idempotency_key(self) -> str:
        return f"{uuid4()}-{int(time.time() * 1000)}"
    
    async def discover(self) -> Dict:
        """Discover merchant capabilities via well-known URL."""
        resp = await self._http.get(f"{self.base_url}/.well-known/agentic-commerce")
        resp.raise_for_status()
        return resp.json()
    
    async def get_products(self) -> List[Dict]:
        """Get merchant product catalog."""
        headers = {"Idempotency-Key": self._generate_idempotency_key()}
        resp = await self._http.get(f"{self.base_url}/products", headers=headers)
        resp.raise_for_status()
        return resp.json().get("products", [])
    
    async def create_checkout(self, cart: Cart) -> CheckoutSession:
        """Create a checkout session."""
        headers = {
            "Idempotency-Key": self._generate_idempotency_key(),
            "Content-Type": "application/json",
        }
        payload = {"cart": cart.to_dict(), "merchantId": self.merchant_id}
        resp = await self._http.post(f"{self.base_url}/checkouts", json=payload, headers=headers)
        resp.raise_for_status()
        return CheckoutSession.from_dict(resp.json())
    
    async def get_checkout(self, session_id: str) -> CheckoutSession:
        """Get checkout session status."""
        resp = await self._http.get(f"{self.base_url}/checkouts/{session_id}")
        resp.raise_for_status()
        return CheckoutSession.from_dict(resp.json())
    
    async def complete_checkout(self, session_id: str, payment_method_id: str = "pm_card_visa") -> Order:
        """Complete checkout with payment method."""
        headers = {
            "Idempotency-Key": self._generate_idempotency_key(),
            "Content-Type": "application/json",
        }
        payload = {"paymentMethodId": payment_method_id}
        resp = await self._http.post(
            f"{self.base_url}/checkouts/{session_id}/complete",
            json=payload,
            headers=headers,
        )
        resp.raise_for_status()
        return Order.from_dict(resp.json())
    
    async def get_orders(self, status: Optional[str] = None) -> List[Order]:
        """Get orders with optional status filter."""
        params = {}
        if status:
            params["status"] = status
        resp = await self._http.get(f"{self.base_url}/orders", params=params)
        resp.raise_for_status()
        orders = resp.json().get("orders", [])
        return [Order.from_dict(o) for o in orders]


__all__ = [
    "ACPClient",
    "Cart",
    "LineItem",
    "Money",
    "Quantity",
    "CheckoutSession",
    "Order",
    "CheckoutStatus",
    "LineItemStatus",
    "__version__",
]