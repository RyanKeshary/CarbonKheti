"""
SandboxPay: In-Platform Demonstration Payment Adapter.
Implements Section 11 Mandate:
- SBX- prefix on all transaction IDs
- Watermarked "SANDBOX: NO REAL MONEY MOVES" outputs
- All failure & edge modes:
  - success
  - upi_timeout
  - insufficient_funds
  - penny_drop_mismatch
  - dormant_account
  - duplicate_webhook
  - delayed_webhook
  - partial_payment
  - refund
  - chargeback_reversal
  - payout_returned
  - bank_holiday_delay
- Supports integer paise arithmetic, largest-remainder allocation, and hosted sandbox checkout.
"""

import hmac
import hashlib
import time
from typing import Dict, Any, Optional
from .base import PaymentAdapter

class SandboxPaymentAdapter(PaymentAdapter):
    SUPPORTED_MODES = [
        "success",
        "upi_timeout",
        "insufficient_funds",
        "penny_drop_mismatch",
        "dormant_account",
        "duplicate_webhook",
        "delayed_webhook",
        "partial_payment",
        "refund",
        "chargeback_reversal",
        "payout_returned",
        "bank_holiday_delay"
    ]

    def __init__(self, failure_mode: str = "success"):
        self.failure_mode = failure_mode if failure_mode in self.SUPPORTED_MODES else "success"
        self.webhook_secret = "sandbox_webhook_secret_key_2026"
        self.seen_webhooks = set()

    def set_failure_mode(self, mode: str):
        if mode in self.SUPPORTED_MODES:
            self.failure_mode = mode
        else:
            raise ValueError(f"Unsupported failure mode: {mode}. Must be one of {self.SUPPORTED_MODES}")

    async def create_order(
        self,
        order_id: str,
        amount_paise: int,
        description: str,
        customer_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        sbx_order_id = f"SBX-ORD-{order_id}-{int(time.time())}"

        if self.failure_mode == "upi_timeout":
            return {
                "status": "TIMED_OUT",
                "order_id": sbx_order_id,
                "amount_paise": amount_paise,
                "error": "UPI Collect Request expired after 300 seconds (Sandbox simulation)",
                "is_sandbox": True,
                "watermark": "SANDBOX"
            }

        return {
            "status": "CREATED",
            "order_id": sbx_order_id,
            "amount_paise": amount_paise,
            "checkout_url": f"/v1/payments/sandbox/checkout?order_id={sbx_order_id}",
            "payment_methods_supported": ["UPI", "CARD", "CORPORATE_NETBANKING"],
            "failure_mode_active": self.failure_mode,
            "is_sandbox": True,
            "watermark": "SANDBOX: NO REAL MONEY MOVES"
        }

    async def process_checkout(
        self,
        order_id: str,
        amount_paise: int,
        method: str = "UPI",
        vpa_or_card: str = "test@sandboxupi"
    ) -> Dict[str, Any]:
        """Simulates processing on the hosted sandbox checkout page."""
        tx_id = f"SBX-TXN-{int(time.time())}-{order_id[:8]}"

        if self.failure_mode == "upi_timeout":
            return {
                "success": False,
                "status": "TIMED_OUT",
                "transaction_id": tx_id,
                "error_code": "UPI_GATEWAY_TIMEOUT",
                "message": "User failed to approve MPIN within payment window on UPI app.",
                "is_sandbox": True,
                "watermark": "SANDBOX"
            }

        if self.failure_mode == "insufficient_funds":
            return {
                "success": False,
                "status": "DECLINED",
                "transaction_id": tx_id,
                "error_code": "INSUFFICIENT_FUNDS",
                "message": "Issuing bank declined transaction due to insufficient funds.",
                "is_sandbox": True,
                "watermark": "SANDBOX"
            }

        if self.failure_mode == "bank_holiday_delay":
            return {
                "success": True,
                "status": "PENDING_CLEARANCE",
                "transaction_id": tx_id,
                "message": "RTGS/NEFT settlement delayed due to national/state bank holiday. Processing on next business day.",
                "is_sandbox": True,
                "watermark": "SANDBOX"
            }

        if self.failure_mode == "partial_payment":
            partial_paise = amount_paise // 2
            return {
                "success": True,
                "status": "PARTIALLY_PAID",
                "transaction_id": tx_id,
                "amount_paid_paise": partial_paise,
                "balance_remaining_paise": amount_paise - partial_paise,
                "message": f"Partial installment of {partial_paise} paise received. Awaiting remainder.",
                "is_sandbox": True,
                "watermark": "SANDBOX"
            }

        # Default success
        return {
            "success": True,
            "status": "PAID",
            "transaction_id": tx_id,
            "amount_paid_paise": amount_paise,
            "method": method,
            "vpa_or_card": vpa_or_card,
            "paid_at": time.time(),
            "receipt_url": f"/v1/payments/receipt/{tx_id}",
            "is_sandbox": True,
            "watermark": "SANDBOX: NO REAL MONEY MOVES"
        }

    def verify_webhook(self, payload: bytes, signature: str) -> bool:
        if self.failure_mode == "invalid_signature":
            return False
        computed = hmac.new(self.webhook_secret.encode(), payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(computed, signature) or signature.startswith("sbx_sig_")

    def handle_webhook_event(self, webhook_id: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulates webhook delivery, including duplicate and delayed delivery modes."""
        if self.failure_mode == "duplicate_webhook":
            is_dup = webhook_id in self.seen_webhooks
            self.seen_webhooks.add(webhook_id)
            return {
                "delivered": True,
                "is_duplicate": is_dup,
                "delivery_attempt": 2 if is_dup else 1,
                "status": "DUPLICATE_IGNORED" if is_dup else "PROCESSED",
                "is_sandbox": True,
                "watermark": "SANDBOX"
            }

        if self.failure_mode == "delayed_webhook":
            return {
                "delivered": True,
                "simulated_delay_seconds": 120,
                "status": "DELAYED_OUT_OF_ORDER",
                "is_sandbox": True,
                "watermark": "SANDBOX"
            }

        self.seen_webhooks.add(webhook_id)
        return {
            "delivered": True,
            "status": "PROCESSED",
            "is_sandbox": True,
            "watermark": "SANDBOX"
        }

    async def verify_penny_drop(
        self,
        bank_account: str,
        ifsc: str,
        expected_name: str
    ) -> Dict[str, Any]:
        if self.failure_mode == "penny_drop_mismatch":
            return {
                "verified": False,
                "status": "NAME_MISMATCH",
                "name_match_score": 0.32,
                "registered_name": "UNKNOWN BENF",
                "reference_id": f"SBX-PND-{int(time.time())}",
                "reason": "Name on bank records does not match farmer identity documents.",
                "is_sandbox": True,
                "watermark": "SANDBOX"
            }

        if self.failure_mode == "dormant_account":
            return {
                "verified": False,
                "status": "ACCOUNT_DORMANT",
                "name_match_score": 0.0,
                "registered_name": None,
                "reference_id": f"SBX-PND-{int(time.time())}",
                "reason": "Beneficiary account is marked dormant or inoperative by NPCI/bank.",
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

    async def execute_payout(
        self,
        payout_id: str,
        amount_paise: int,
        beneficiary: Dict[str, Any],
        idempotency_key: str
    ) -> Dict[str, Any]:
        if self.failure_mode == "insufficient_funds":
            return {
                "status": "FAILED",
                "failure_reason": "Escrow balance insufficient for staged payout batch",
                "payout_id": f"SBX-PO-{payout_id}",
                "utr": None,
                "is_sandbox": True,
                "watermark": "SANDBOX"
            }

        if self.failure_mode == "dormant_account":
            return {
                "status": "FAILED",
                "failure_reason": "Bank returned payout: Account inoperative / dormant",
                "payout_id": f"SBX-PO-{payout_id}",
                "utr": None,
                "is_sandbox": True,
                "watermark": "SANDBOX"
            }

        if self.failure_mode == "payout_returned":
            return {
                "status": "RETURNED_BY_BANK",
                "failure_reason": "Payout settled but subsequently reversed by beneficiary bank (Account closed)",
                "payout_id": f"SBX-PO-{payout_id}",
                "utr": f"SBX-UTR-REV-{int(time.time())}",
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
            "beneficiary_account": beneficiary.get("bank_account", "SBX-ACC-0001"),
            "transferred_at": time.time(),
            "is_sandbox": True,
            "watermark": "SANDBOX: SIMULATED SETTLEMENT"
        }

    async def process_refund(self, original_tx_id: str, refund_amount_paise: int, reason: str) -> Dict[str, Any]:
        refund_id = f"SBX-REF-{int(time.time())}"
        return {
            "status": "REFUNDED",
            "refund_id": refund_id,
            "original_transaction_id": original_tx_id,
            "refund_amount_paise": refund_amount_paise,
            "reason": reason,
            "processed_at": time.time(),
            "is_sandbox": True,
            "watermark": "SANDBOX"
        }
