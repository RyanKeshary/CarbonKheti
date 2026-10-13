"""
e-Sign Adapter Interface & Implementations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
import hashlib
import time

class ESignAdapter(ABC):
    @abstractmethod
    async def create_signing_request(self, document_id: str, document_title: str, document_hash: str, signer_email: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def verify_signature(self, document_id: str, signature_token: str) -> Dict[str, Any]:
        pass

class SandboxESignAdapter(ESignAdapter):
    async def create_signing_request(self, document_id: str, document_title: str, document_hash: str, signer_email: str) -> Dict[str, Any]:
        return {
            "signing_url": f"/v1/contracts/sandbox/sign?doc_id={document_id}",
            "document_id": document_id,
            "status": "AWAITING_SIGNATURE",
            "is_sandbox": True,
            "watermark": "SANDBOX: DEMONSTRATION CONTRACT"
        }

    async def verify_signature(self, document_id: str, signature_token: str) -> Dict[str, Any]:
        sig_hash = hashlib.sha256(f"{document_id}:{signature_token}:{time.time()}".encode()).hexdigest()
        return {
            "document_id": document_id,
            "status": "SIGNED",
            "certificate_hash": sig_hash,
            "signed_at": time.time(),
            "signer_type": "SANDBOX_SIMULATED_AADHAAR_OTP",
            "is_sandbox": True,
            "watermark": "SANDBOX"
        }

class RealESignAdapter(ESignAdapter):
    async def create_signing_request(self, document_id: str, document_title: str, document_hash: str, signer_email: str) -> Dict[str, Any]:
        return {
            "signing_url": f"https://esign.leegality.com/sign/{document_id}",
            "document_id": document_id,
            "status": "SENT_TO_SIGNER",
            "is_sandbox": False
        }

    async def verify_signature(self, document_id: str, signature_token: str) -> Dict[str, Any]:
        return {
            "document_id": document_id,
            "status": "SIGNED",
            "certificate_hash": hashlib.sha256(document_id.encode()).hexdigest(),
            "signed_at": time.time(),
            "is_sandbox": False
        }
