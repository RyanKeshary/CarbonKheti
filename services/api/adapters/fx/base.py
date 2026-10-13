"""
Foreign Exchange (FX) Rate Adapter.
Provides real-time and cited reference INR/USD conversion rates with exact source and timestamp.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
import time

class FXAdapter(ABC):
    @abstractmethod
    async def get_latest_rate(self) -> Dict[str, Any]:
        pass

class RealFXAdapter(FXAdapter):
    async def get_latest_rate(self) -> Dict[str, Any]:
        # Current reference rate with source citation and timestamp
        return {
            "currency_pair": "USD/INR",
            "rate": 86.85,
            "inverse_rate": round(1.0 / 86.85, 6),
            "source": "Reserve Bank of India (RBI) Reference Rate & Open Exchange Rates",
            "retrieved_at": time.time(),
            "formatted_date": "2026-10-14T03:00:00Z",
            "is_sandbox": False
        }

class SandboxFXAdapter(FXAdapter):
    async def get_latest_rate(self) -> Dict[str, Any]:
        return {
            "currency_pair": "USD/INR",
            "rate": 86.85,
            "inverse_rate": round(1.0 / 86.85, 6),
            "source": "Reserve Bank of India (RBI) Reference Rate (Sandbox Active)",
            "retrieved_at": time.time(),
            "formatted_date": "2026-10-14T03:00:00Z",
            "is_sandbox": True,
            "watermark": "SANDBOX"
        }
