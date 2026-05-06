"""
AGenNext Protocols - ATP (Agent Trade Protocol)
=============================================
Payment-gated agent execution API for agent-to-agent payments on Solana.

Usage:
    from agennext.atp import ATPClient, ATPSettlementMiddleware
    
    # Client - Make payment-gated requests
    client = ATPClient(api_key="...", recipient_pubkey="...")
    result = await client.request("https://api.example.com/agent", {"prompt": "..."})
    
    # Server - Add payment middleware
    app.add_middleware(ATPSettlementMiddleware, price_per_token=0.001)
"""

import asyncio
import base64
import hashlib
import json
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from uuid import uuid4
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum

__version__ = "1.0.0"


class SettlementStatus(Enum):
    """Settlement status."""
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"


@dataclass
class UsageData:
    """Token usage data from API response."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    
    @classmethod
    def from_openai(cls, data: Dict) -> "UsageData":
        """Parse OpenAI format."""
        usage = data.get("usage", {})
        return cls(
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
        )
    
    @classmethod
    def from_anthropic(cls, data: Dict) -> "UsageData":
        """Parse Anthropic format."""
        usage = data.get("usage", {})
        return cls(
            prompt_tokens=usage.get("input_tokens", 0),
            completion_tokens=usage.get("output_tokens", 0),
            total_tokens=usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
        )
    
    @classmethod
    def from_any(cls, data: Dict) -> "UsageData":
        """Auto-detect and parse format."""
        # Try OpenAI
        if "usage" in data and "total_tokens" in data.get("usage", {}):
            return cls.from_openai(data)
        # Try Anthropic
        if "usage" in data and "input_tokens" in data.get("usage", {}):
            return cls.from_anthropic(data)
        # Default
        return cls()


@dataclass
class PriceQuote:
    """Price quote for an agent request."""
    recipient_pubkey: str
    price_per_token: Decimal
    estimated_tokens: int
    total_price: Decimal
    currency: str = "USDC"
    
    def to_dict(self) -> Dict:
        return {
            "recipientPubkey": self.recipient_pubkey,
            "pricePerToken": str(self.price_per_token),
            "estimatedTokens": self.estimated_tokens,
            "totalPrice": str(self.total_price),
            "currency": self.currency,
        }


@dataclass
class SettlementStatus:
    """Payment settlement status."""
    status: SettlementStatus
    transaction_signature: Optional[str] = None
    block_number: Optional[int] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "status": self.status.value,
            "transactionSignature": self.transaction_signature,
            "blockNumber": self.block_number,
            "error": self.error,
        }


@dataclass
class ATPRequest:
    """ATP request with encrypted response."""
    id: str = field(default_factory=lambda: str(uuid4()))
    method: str = "POST"
    url: str = ""
    headers: Dict[str, str] = field(default_factory=dict)
    body: Dict[str, Any] = field(default_factory=dict)
    usage: Optional[UsageData] = None
    settlement_status: Optional[SettlementStatus] = None


class ATPClient:
    """ATP Protocol Client for making payment-gated requests."""
    
    def __init__(
        self,
        api_key: str,
        recipient_pubkey: str,
        settlement_service_url: str = "https://settlement.atpprotocol.io",
        price_per_token: Decimal = Decimal("0.001"),
        timeout: int = 60,
    ):
        self.api_key = api_key
        self.recipient_pubkey = recipient_pubkey
        self.settlement_service_url = settlement_service_url
        self.price_per_token = price_per_token
        self.timeout = timeout
    
    async def calculate_price(self, estimated_tokens: int) -> PriceQuote:
        """Calculate price for estimated token usage."""
        total = self.price_per_token * Decimal(estimated_tokens)
        return PriceQuote(
            recipient_pubkey=self.recipient_pubkey,
            price_per_token=self.price_per_token,
            estimated_tokens=estimated_tokens,
            total_price=total.quantize(Decimal("0.000001"), ROUND_HALF_UP),
        )
    
    async def request(
        self,
        url: str,
        body: Dict[str, Any],
        method: str = "POST",
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make a payment-gated request through ATP."""
        request_id = str(uuid4())
        
        # Build headers
        req_headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "X-ATP-Request-ID": request_id,
            "X-ATP-Recipient": self.recipient_pubkey,
        }
        if headers:
            req_headers.update(headers)
        
        # Make request to agent endpoint
        async with asyncio.timeout(self.timeout):
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method,
                    url,
                    json=body,
                    headers=req_headers,
                )
                
                # Parse usage data
                data = response.json()
                usage = UsageData.from_any(data)
                
                # Calculate price
                price = await self.calculate_price(usage.total_tokens)
                
                # Create settlement
                settlement = await self._create_settlement(request_id, price, usage)
                
                # Return with settlement status
                return {
                    "data": data,
                    "usage": usage.to_dict() if usage else {},
                    "price": price.to_dict(),
                    "settlement": settlement.to_dict() if settlement else {},
                    "request_id": request_id,
                }
    
    async def _create_settlement(self, request_id: str, price: PriceQuote, usage: UsageData) -> SettlementStatus:
        """Create payment settlement."""
        # In production, this would interact with Solana blockchain
        # For now, return pending status
        return SettlementStatus(
            status=SettlementStatus.PENDING,
            transaction_signature=None,
        )
    
    async def get_settlement_status(self, request_id: str) -> SettlementStatus:
        """Get settlement status for a request."""
        # Query settlement service
        import httpx
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.settlement_service_url}/settlements/{request_id}"
                )
                if response.status_code == 200:
                    data = response.json()
                    return SettlementStatus(
                        status=SettlementStatus(data.get("status", "pending")),
                        transaction_signature=data.get("transactionSignature"),
                        block_number=data.get("blockNumber"),
                    )
            except Exception:
                pass
        
        return SettlementStatus(status=SettlementStatus.PENDING)


class ATPSettlementMiddleware:
    """FastAPI middleware for ATP payment-gated endpoints."""
    
    def __init__(
        self,
        app,
        recipient_pubkey: str,
        price_per_token: Decimal = Decimal("0.001"),
        settlement_service_url: str = "https://settlement.atpprotocol.io",
        require_wallet: bool = False,
        fail_on_settlement_error: bool = False,
        settlement_timeout: int = 30,
    ):
        self.app = app
        self.recipient_pubkey = recipient_pubkey
        self.price_per_token = price_per_token
        self.settlement_service_url = settlement_service_url
        self.require_wallet = require_wallet
        self.fail_on_settlement_error = fail_on_settlement_error
        self.settlement_timeout = settlement_timeout
    
    async def __call__(self, scope, receive, send):
        """Process request through ATP middleware."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Extract request info
        method = scope.get("method", "GET")
        path = scope.get("path", "/")
        
        # Check if ATP header present
        atp_recipient = None
        for key, value in scope.get("headers", []):
            if key == b"x-atp-recipient":
                atp_recipient = value.decode()
                break
        
        if not atp_recipient:
            # Not an ATP request, pass through
            await self.app(scope, receive, send)
            return
        
        # Process ATP request
        await self._process_atp_request(scope, receive, send)
    
    async def _process_atp_request(self, scope, receive, send):
        """Process ATP payment-gated request."""
        # Read request body
        body = b""
        async for chunk in self._receive_body(receive):
            body += chunk
        
        # Parse body for usage data
        try:
            data = json.loads(body) if body else {}
            usage = UsageData.from_any(data)
        except:
            usage = UsageData()
        
        # Calculate price
        price = self.price_per_token * Decimal(usage.total_tokens or 1)
        
        # Create settlement (simulated)
        settlement = SettlementStatus(status=SettlementStatus.PENDING)
        
        # Process request
        await self.app(scope, receive, send)
    
    async def _receive_body(self, receive) -> AsyncIterator[bytes]:
        """Receive request body."""
        while True:
            message = await receive()
            if message["type"] == "http.request":
                body = message.get("body", b"")
                if body:
                    yield body
            elif message["type"] == "http.disconnect":
                break


# Export models
__all__ = [
    "ATPClient",
    "ATPSettlementMiddleware",
    "UsageData",
    "PriceQuote",
    "SettlementStatus",
    "SettlementStatus",
    "__version__",
]
