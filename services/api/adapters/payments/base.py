"""
Abstract Base Payment Adapter Interface for CarbonKheti.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any

class PaymentAdapter(ABC):
    @abstractmethod
    async def create_order(self, order_id: str, amount_paise: int, description: str, customer_info: Dict[str, Any]) -> Dict[str, Any]:
        """Creates an inbound payment order / checkout session."""
        pass

    @abstractmethod
    def verify_webhook(self, payload: bytes, signature: str) -> bool:
        """Verifies HMAC SHA-256 signature on incoming payment gateway webhooks."""
        pass

    @abstractmethod
    async def verify_penny_drop(self, bank_account: str, ifsc: str, expected_name: str) -> Dict[str, Any]:
        """Performs penny-drop account verification and returns name-match score."""
        pass

    @abstractmethod
    async def execute_payout(self, payout_id: str, amount_paise: int, beneficiary: Dict[str, Any], idempotency_key: str) -> Dict[str, Any]:
        """Executes an outbound disbursement to farmer/cooperative."""
        pass
