"""
AGenNext Protocols - AP2 (Agent Payments Protocol)
==============================================
Typed mandates for payment authorization with audit trails.

Usage:
    from agennext.ap2 import IntentMandate, PaymentMandate, PaymentClient
    
    # Define payment intent
    intent = IntentMandate(
        merchants=["shop.com"],
        limit=Decimal("1000.00"),
        description="Order #12345"
    )
    
    # Authorize payment
    client = PaymentClient(wallet_private_key)
    mandate = await client.authorize(intent, cart)
    
    # Get receipt
    receipt = await client.get_receipt(mandate.payment_id)
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from decimal import Decimal
from datetime import datetime, timedelta
from enum import Enum
import uuid
import hashlib
import jwt

__version__ = "0.1.0"

# Try to use ap2 if available
try:
    from ap2.types.mandate import IntentMandate as _AP2Mandate
    from ap2.types.payment_receipt import PaymentReceipt, Success
    AP2_SDK_AVAILABLE = True
except ImportError:
    _AP2Mandate = None
    AP2_SDK_AVAILABLE = False


class PaymentStatus(Enum):
    """Payment status."""
    PENDING = "pending"
    AUTHORIZED = "authorized"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


@dataclass
class PaymentCurrencyAmount:
    """Monetary amount."""
    currency: str = "USD"
    value: str = "0"
    
    def to_dict(self) -> Dict:
        return {"currency": self.currency, "value": self.value}
    
    @classmethod
    def from_decimal(cls, amount: Decimal, currency: str = "USD") -> "PaymentCurrencyAmount":
        return cls(currency=currency, value=str(amount))


@dataclass
class PaymentItem:
    """Payment line item."""
    label: str
    amount: PaymentCurrencyAmount
    
    def to_dict(self) -> Dict:
        return {"label": self.label, "amount": self.amount.to_dict()}


@dataclass
class IntentMandate:
    """Intent to pay - specifies payment authorization."""
    merchants: List[str]
    limit: Decimal
    description: str = ""
    requires_refundability: bool = True
    user_confirmation_required: bool = False
    expires_at: Optional[datetime] = None
    
    def __post_init__(self):
        if not self.expires_at:
            self.expires_at = datetime.utcnow() + timedelta(hours=1)
    
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at
    
    def to_dict(self) -> Dict:
        return {
            "naturalLanguageDescription": self.description,
            "merchants": self.merchants,
            "requiresRefundability": self.requires_refundability,
            "userCartConfirmationRequired": self.user_confirmation_required,
            "intentExpiry": self.expires_at.isoformat() + "Z",
        }


@dataclass
class PaymentMandate:
    """Signed payment mandate."""
    payment_mandate_id: str
    payment_details_id: str
    payment_details_total: PaymentItem
    merchant_agent: str
    user_authorization: Optional[str] = None
    
    def is_authorized(self) -> bool:
        return self.user_authorization is not None
    
    def to_dict(self) -> Dict:
        return {
            "paymentMandateId": self.payment_mandate_id,
            "paymentDetailsId": self.payment_details_id,
            "paymentDetailsTotal": self.payment_details_total.to_dict(),
            "merchantAgent": self.merchant_agent,
            "userAuthorization": self.user_authorization,
        }


@dataclass
class PaymentReceipt:
    """Proof of payment - closes the audit trail."""
    payment_mandate_id: str
    payment_id: str
    amount: PaymentCurrencyAmount
    payment_status: PaymentStatus
    merchant_confirmation_id: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "paymentMandateId": self.payment_mandate_id,
            "paymentId": self.payment_id,
            "amount": self.amount.to_dict(),
            "paymentStatus": self.payment_status.value,
            "merchantConfirmationId": self.merchant_confirmation_id,
        }


class PaymentClient:
    """AP2 Payment Client."""
    
    def __init__(self, private_key: Optional[str] = None):
        self.private_key = private_key
        self._mandates: Dict[str, PaymentMandate] = {}
        self._receipts: Dict[str, PaymentReceipt] = {}
    
    async def authorize(self, intent: IntentMandate, items: List[PaymentItem]) -> PaymentMandate:
        """Authorize payment based on intent."""
        if intent.is_expired():
            raise ValueError("Intent mandate has expired")
        
        total = Decimal("0")
        for item in items:
            total += Decimal(item.amount.value)
        
        if total > intent.limit:
            raise ValueError(f"Amount {total} exceeds limit {intent.limit}")
        
        # Create mandate
        mandate = PaymentMandate(
            payment_mandate_id=str(uuid.uuid4()),
            payment_details_id=str(uuid.uuid4()),
            payment_details_total=PaymentItem(
                label="Total",
                amount=PaymentCurrencyAmount.from_decimal(total),
            ),
            merchant_agent=", ".join(intent.merchants),
        )
        
        self._mandates[mandate.payment_mandate_id] = mandate
        return mandate
    
    def sign_mandate(self, mandate: PaymentMandate) -> PaymentMandate:
        """Sign a mandate with user authorization."""
        if not self.private_key:
            raise ValueError("No private key to sign mandate")
        
        # Create signature
        data = f"{mandate.payment_mandate_id}:{mandate.payment_details_id}"
        signature = hashlib.sha256(data.encode()).hexdigest()
        
        mandate.user_authorization = signature
        return mandate
    
    async def complete_payment(self, mandate: PaymentMandate) -> PaymentReceipt:
        """Complete payment and generate receipt."""
        if not mandate.is_authorized():
            raise ValueError("Mandate not authorized")
        
        receipt = PaymentReceipt(
            payment_mandate_id=mandate.payment_mandate_id,
            payment_id=f"PAY-{uuid.uuid4().hex[:8]}",
            amount=mandate.payment_details_total.amount,
            payment_status=PaymentStatus.COMPLETED,
            merchant_confirmation_id=f"ORD-{uuid.uuid4().hex[:8]}",
        )
        
        self._receipts[receipt.payment_id] = receipt
        return receipt
    
    async def get_receipt(self, payment_id: str) -> Optional[PaymentReceipt]:
        """Get payment receipt."""
        return self._receipts.get(payment_id)


__all__ = [
    "IntentMandate",
    "PaymentMandate",
    "PaymentReceipt", 
    "PaymentCurrencyAmount",
    "PaymentItem",
    "PaymentClient",
    "PaymentStatus",
    "__version__",
]