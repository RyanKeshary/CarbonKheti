"""
SandboxPay: In-Platform Demonstration Payment Adapter.
Section 5 Mandate:
- SBX- prefix on all transaction IDs
- Watermarked SANDBOX outputs
- Selectable outcomes for testing:
  success | pending | failure | upi_timeout | duplicate_webhook | insufficient_funds | penny_drop_mismatch
"""

import hmac
import hashlib
import time
from typing import Dict, Any
from .base import PaymentAdapter

class SandboxPaymentAdapter(PaymentAdapter):
    def __init__(self, failure_mode: str = "success"):
        # Selectable failure modes
        self.failure_mode = failure_mode  # success, pending, failure, upi_timeout, duplicate_webhook, insufficient_funds, penny_drop_mismatch
        self.webhook_secret = "sandbox_webhook_secret_key_2026"

    def set_failure_mode(self, mode: str):
        self.failure_mode = mode

    async def create_order(self, order_id: str, amount_paise: int, description: str, customer_info: Dict[str, Any]) -> Dict[str, Any]:
        sbx_order_id = f"SBX-ORD-{order_id}-{int(time.time())}"
        
        if self.failure_mode == "failure":
            return {
                "status": "FAILED",
                "order_id": sbx_order_id,
                "amount_paise": amount_paise,
                "error": "Payment order rejected by sandbox gateway policy",
                "is_sandbox": True,
                "watermark": "SANDBOX"
            }

        return {
            "status": "CREATED",
            "order_id": sbx_order_id,
            "amount_paise": amount_paise,
            "checkout_url": f"/v1/payments/sandbox/checkout?order_id={sbx_order_id}",
            "payment_methods_supported": ["UPI", "NEFT_RTGS", "CORPORATE_NETBANKING"],
            "is_sandbox": True,
            "watermark": "SANDBOX: NO REAL MONEY MOVES"
        }

    def verify_webhook(self, payload: bytes, signature: str) -> bool:
        if self.failure_mode == "invalid_signature":
            return False
        # Validates HMAC SHA256 or accepts sandbox token
        computed = hmac.new(self.webhook_secret.encode(), payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(computed, signature) or signature.startswith("sbx_sig_")

    async def verify_penny_drop(self, bank_account: str, ifsc: str, expected_name: str) -> Dict[str, Any]:
        if self.failure_mode == "penny_drop_mismatch":
            return {
                "verified": False,
                "status": "NAME_MISMATCH",
                "name_match_score": 0.32,
                "registered_name": "UNKNOWN BENF",
                "reference_id": f"SBX-PND-{int(time.time())}",
                "is_sandbox": True,
                "watermark": "SANDBOX"
            }

        return {
            "verified": True,
            "status": "VERIFIED_ACTIVE",
            "name_match_score": 0.98,
            "registered_name": expected_name.upper(),
            "reference_id": f"SBX-PND-{int(time.time())}",
            "is_sandbox": True,
            "watermark": "SANDBOX"
        }

    async def execute_payout(self, payout_id: str, amount_paise: int, beneficiary: Dict[str, Any], idempotency_key: str) -> Dict[str, Any]:
        if self.failure_mode == "insufficient_funds":
            return {
                "status": "FAILED",
                "failure_reason": "Escrow balance insufficient for staged payout batch",
                "payout_id": f"SBX-PO-{payout_id}",
                "utr": None,
                "is_sandbox": True,
                "watermark": "SANDBOX"
            }

        if self.failure_mode == "failure":
            return {
                "status": "FAILED",
                "failure_reason": "Simulated beneficiary bank account frozen/dormant",
                "payout_id": f"SBX-PO-{payout_id}",
                "utr": None,
                "is_sandbox": True,
                "watermark": "SANDBOX"
            }

        sbx_utr = f"SBX-UTR-{int(time.time())}-{payout_id[:8]}"
        return {
            "status": "PAID",
            "payout_id": f"SBX-PO-{payout_id}",
            "amount_paise": amount_paise,
            "utr": sbx_utr,
            "idempotency_key": idempotency_key,
            "beneficiary_account": beneficiary.get("bank_account", "SBX-ACC-XXXX"),
            "transferred_at": time.time(),
            "is_sandbox": True,
            "watermark": "SANDBOX: SIMULATED SETTLEMENT"
        }
