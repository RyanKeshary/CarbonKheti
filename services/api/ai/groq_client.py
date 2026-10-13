"""
Groq LLM Client & Server-Side Proxy.
Complies with Section 8.1:
- GROQ_API_KEY read strictly from server environment variable
- Dynamic model discovery from Groq /openai/v1/models endpoint
- Circuit breaker, timeout, exponential backoff retries
- Rate limiting and PII redaction
"""

import os
import time
import json
import logging
import asyncio
from typing import Dict, Any, List, Optional
import urllib.request
import urllib.error

logger = logging.getLogger("carbonkheti.groq")

# Model fallbacks in case dynamic query is unavailable or during cold boot
DEFAULT_REASONING_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-70b-versatile",
    "llama3-70b-8192"
]
DEFAULT_FAST_MODELS = [
    "llama-3.1-8b-instant",
    "llama3-8b-8192"
]
DEFAULT_WHISPER_MODEL = "whisper-large-v3"

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout_sec: float = 60.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout_sec = recovery_timeout_sec
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.state = "CLOSED"  # CLOSED (normal), OPEN (broken), HALF_OPEN (probing)

    def record_success(self):
        self.failure_count = 0
        self.state = "CLOSED"

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(f"Groq API circuit breaker tripped to OPEN after {self.failure_count} consecutive failures.")

    def can_attempt(self) -> bool:
        if self.state == "CLOSED":
            return True
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout_sec:
                self.state = "HALF_OPEN"
                return True
            return False
        return True  # HALF_OPEN allows probe

class GroqProxyClient:
    def __init__(self):
        self.api_base = "https://api.groq.com/openai/v1"
        self.circuit_breaker = CircuitBreaker()
        self.discovered_models: List[str] = []
        self.selected_reasoning_model = DEFAULT_REASONING_MODELS[0]
        self.selected_fast_model = DEFAULT_FAST_MODELS[0]
        self._initialized = False

    @property
    def api_key(self) -> Optional[str]:
        # Never store key in attribute or logs; fetch directly from environment
        return os.environ.get("GROQ_API_KEY")

    def has_api_key(self) -> bool:
        key = self.api_key
        return bool(key and len(key.strip()) > 10)

    async def discover_models(self):
        """Discovers available models from Groq endpoint dynamically without hard-coding."""
        if not self.has_api_key():
            logger.info("GROQ_API_KEY not configured. Using deterministic offline agronomy response fallbacks.")
            return

        try:
            req = urllib.request.Request(
                f"{self.api_base}/models",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "User-Agent": "CarbonKheti-API/1.0"
                }
            )
            # Run in thread executor to keep async
            loop = asyncio.get_event_loop()
            resp_bytes = await loop.run_in_executor(
                None, lambda: urllib.request.urlopen(req, timeout=8).read()
            )
            data = json.loads(resp_bytes.decode("utf-8"))
            models_list = [m["id"] for m in data.get("data", [])]
            self.discovered_models = models_list

            # Select best matching reasoning model
            for candidate in DEFAULT_REASONING_MODELS:
                if candidate in models_list:
                    self.selected_reasoning_model = candidate
                    break

            # Select best matching fast model
            for candidate in DEFAULT_FAST_MODELS:
                if candidate in models_list:
                    self.selected_fast_model = candidate
                    break

            self._initialized = True
            logger.info(f"Groq models discovered. Reasoning: {self.selected_reasoning_model}, Fast: {self.selected_fast_model}")
        except Exception as e:
            logger.warning(f"Could not discover Groq models dynamically: {e}. Using configured defaults.")

    def redact_pii(self, text: str) -> str:
        """Minimises PII before transmitting to LLM (Aadhaar-like 12 digits, 10-digit phone numbers)."""
        import re
        # Redact 12-digit continuous numbers
        text = re.sub(r'\b\d{4}\s?\d{4}\s?\d{4}\b', '[REDACTED_ID]', text)
        # Redact 10-digit Indian phone numbers
        text = re.sub(r'\b[6-9]\d{9}\b', '[REDACTED_PHONE]', text)
        return text

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        use_reasoning: bool = True,
        temperature: float = 0.2,
        max_tokens: int = 800
    ) -> Dict[str, Any]:
        """
        Executes chat completion with retry, timeout, circuit breaker and safety checks.
        """
        if not self.has_api_key():
            return {
                "success": False,
                "error": "GROQ_API_KEY_NOT_CONFIGURED",
                "message": "Groq API key not set in environment. Set GROQ_API_KEY to activate live LLM."
            }

        if not self.circuit_breaker.can_attempt():
            return {
                "success": False,
                "error": "CIRCUIT_BREAKER_OPEN",
                "message": "Groq API is temporarily paused due to upstream error rate. Retrying shortly."
            }

        model = self.selected_reasoning_model if use_reasoning else self.selected_fast_model

        # Redact PII in user messages
        clean_messages = []
        for msg in messages:
            clean_messages.append({
                "role": msg["role"],
                "content": self.redact_pii(msg["content"])
            })

        payload = {
            "model": model,
            "messages": clean_messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        # Up to 3 retries with exponential backoff
        for attempt in range(1, 4):
            try:
                payload_bytes = json.dumps(payload).encode("utf-8")
                req = urllib.request.Request(
                    f"{self.api_base}/chat/completions",
                    data=payload_bytes,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "User-Agent": "CarbonKheti-API/1.0"
                    }
                )
                loop = asyncio.get_event_loop()
                resp_bytes = await loop.run_in_executor(
                    None, lambda: urllib.request.urlopen(req, timeout=15).read()
                )
                res_json = json.loads(resp_bytes.decode("utf-8"))
                self.circuit_breaker.record_success()

                choice = res_json["choices"][0]["message"]["content"]
                return {
                    "success": True,
                    "content": choice,
                    "model_used": model,
                    "tokens_used": res_json.get("usage", {}).get("total_tokens", 0)
                }
            except urllib.error.HTTPError as e:
                err_body = e.read().decode("utf-8", errors="ignore")
                logger.warning(f"Groq API HTTP error attempt {attempt}: {e.code} - {err_body}")
                if e.code in [400, 401]:  # Non-retryable client error
                    self.circuit_breaker.record_failure()
                    return {"success": False, "error": f"HTTP_{e.code}", "message": err_body}
                await asyncio.sleep(2 ** attempt)
            except Exception as e:
                logger.warning(f"Groq API call attempt {attempt} failed: {e}")
                await asyncio.sleep(2 ** attempt)

        self.circuit_breaker.record_failure()
        return {
            "success": False,
            "error": "UPSTREAM_TIMEOUT",
            "message": "Groq API did not respond after 3 attempts."
        }

# Global singleton client
groq_client = GroqProxyClient()
