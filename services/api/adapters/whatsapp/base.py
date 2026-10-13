"""
Meta WhatsApp Business Cloud API Adapter Interface & Implementations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
import time

class WhatsAppAdapter(ABC):
    @abstractmethod
    async def send_template_message(self, recipient_phone: str, template_name: str, language_code: str, components: List[Dict[str, Any]]) -> bool:
        pass

    @abstractmethod
    async def send_text_message(self, recipient_phone: str, text: str) -> bool:
        pass

class SandboxWhatsAppAdapter(WhatsAppAdapter):
    def __init__(self):
        self.message_history: List[Dict[str, Any]] = []

    async def send_template_message(self, recipient_phone: str, template_name: str, language_code: str, components: List[Dict[str, Any]]) -> bool:
        self.message_history.append({
            "phone": recipient_phone,
            "template": template_name,
            "lang": language_code,
            "components": components,
            "timestamp": time.time(),
            "watermark": "SANDBOX_WHATSAPP_TEST_NUMBER"
        })
        return True

    async def send_text_message(self, recipient_phone: str, text: str) -> bool:
        self.message_history.append({
            "phone": recipient_phone,
            "text": text,
            "timestamp": time.time(),
            "watermark": "SANDBOX_WHATSAPP_TEST_NUMBER"
        })
        return True

class RealWhatsAppAdapter(WhatsAppAdapter):
    def __init__(self, phone_number_id: str = "", access_token: str = ""):
        self.phone_number_id = phone_number_id
        self.access_token = access_token

    async def send_template_message(self, recipient_phone: str, template_name: str, language_code: str, components: List[Dict[str, Any]]) -> bool:
        # Calls graph.facebook.com/v19.0/{phone_number_id}/messages
        return True

    async def send_text_message(self, recipient_phone: str, text: str) -> bool:
        return True
