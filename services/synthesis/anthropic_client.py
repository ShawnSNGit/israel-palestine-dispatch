"""Small, defensive Anthropic Messages API client.

The API key is read only from ANTHROPIC_API_KEY. The client never logs the key
or the full prompt. Set ANTHROPIC_MODEL explicitly in production.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from typing import Any, Dict, Optional, Type, TypeVar

import requests
from diskcache import Cache
from pydantic import BaseModel, ValidationError
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

API_URL = os.getenv("ANTHROPIC_API_URL", "https://api.anthropic.com/v1/messages")
API_VERSION = os.getenv("ANTHROPIC_VERSION", "2023-06-01")
DEFAULT_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
CACHE_TTL = int(os.getenv("SYNTH_CACHE_TTL", "3600"))
CACHE_DIR = os.getenv("SYNTH_CACHE_DIR", "/tmp/synth_cache")
T = TypeVar("T", bound=BaseModel)


class SummarySchema(BaseModel):
    summary: str
    confidence: Optional[float] = None
    citations: Optional[Dict[str, str]] = None


def _retryable(exc: BaseException) -> bool:
    if not isinstance(exc, requests.RequestException):
        return False
    response = getattr(exc, "response", None)
    return response is None or response.status_code == 429 or response.status_code >= 500


@retry(
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=1, min=1, max=20),
    retry=retry_if_exception(_retryable),
    reraise=True,
)
def _post(payload: Dict[str, Any], key: str, timeout: int = 60) -> Dict[str, Any]:
    response = requests.post(
        API_URL,
        headers={
            "x-api-key": key,
            "anthropic-version": API_VERSION,
            "content-type": "application/json",
        },
        json=payload,
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()


def _json_object(text: str) -> Dict[str, Any]:
    """Parse a JSON object, allowing harmless Markdown code fences."""
    cleaned = text.strip().replace("```json", "").replace("```", "").strip()
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start < 0 or end < start:
        raise ValueError("Anthropic response did not contain a JSON object")
    value = json.loads(cleaned[start : end + 1])
    if not isinstance(value, dict):
        raise ValueError("Anthropic response JSON was not an object")
    return value


class AnthropicClient:
    def __init__(self, model: str = DEFAULT_MODEL, max_tokens: int = 512, temperature: float = 0.0):
        self.key = os.getenv("ANTHROPIC_API_KEY")
        if not self.key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set")
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.cache = Cache(CACHE_DIR)

    def complete(self, prompt: str, *, system: Optional[str] = None, use_cache: bool = True) -> Dict[str, Any]:
        if not prompt.strip():
            raise ValueError("prompt must not be empty")
        payload: Dict[str, Any] = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            payload["system"] = system
        cache_key = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        if use_cache:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached
        started = time.monotonic()
        result = _post(payload, self.key)
        logger.info("Anthropic request completed model=%s latency_ms=%d", self.model, int((time.monotonic() - started) * 1000))
        if use_cache:
            self.cache.set(cache_key, result, expire=CACHE_TTL)
        return result

    def structured_summary(self, prompt: str, schema: Type[T] = SummarySchema) -> T:
        system = (
            "You are an evidence-first summarizer. Return only valid JSON matching the requested schema. "
            "Do not reveal private reasoning. Use only the supplied evidence and cite source IDs."
        )
        result = self.complete(prompt, system=system)
        content = result.get("content", [])
        text = "".join(block.get("text", "") for block in content if block.get("type") == "text")
        if not text:
            raise ValueError("Anthropic returned no text content")
        try:
            return schema.parse_obj(_json_object(text))
        except (ValueError, json.JSONDecodeError, ValidationError) as exc:
            raise ValueError(f"Anthropic response failed schema validation: {exc}") from exc
