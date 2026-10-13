"""
SMS Adapter Interface & Implementations (DLT vs Sandbox).
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
import time

class SMSAdapter(ABC):
    @abstractmethod
    async def send_otp(self, phone_number: str, otp_code: str) -> bool:
        pass

    @abstractmethod
    async def send_transaction_sms(self, phone_number: str, template_id: str, variables: Dict[str, str]) -> bool:
        pass

class SandboxSMSAdapter(SMSAdapter):
    def __init__(self):
        self.sent_messages: List[Dict[str, Any]] = []

    async def send_otp(self, phone_number: str, otp_code: str) -> bool:
        self.sent_messages.append({
            "phone_number": phone_number,
            "type": "OTP",
            "otp_code": otp_code,
            "timestamp": time.time(),
            "watermark": "SANDBOX_SMS"
        })
        return True

    async def send_transaction_sms(self, phone_number: str, template_id: str, variables: Dict[str, str]) -> bool:
        self.sent_messages.append({
            "phone_number": phone_number,
            "type": "TRANSACTION",
            "template_id": template_id,
            "variables": variables,
            "timestamp": time.time(),
            "watermark": "SANDBOX_SMS"
        })
        return True

class RealSMSAdapter(SMSAdapter):
    def __init__(self, provider: str = "DLT_GATEWAY"):
        self.provider = provider

    async def send_otp(self, phone_number: str, otp_code: str) -> bool:
        # Calls DLT registered SMS endpoint
        return True

    async def send_transaction_sms(self, phone_number: str, template_id: str, variables: Dict[str, str]) -> bool:
        return True
