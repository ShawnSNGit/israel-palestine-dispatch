import os
import json
import time
import hashlib
import logging
from typing import Any, Dict, Optional

import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from diskcache import Cache
from pydantic import BaseModel, ValidationError

# Configuration / environment
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_API_URL = os.getenv("ANTHROPIC_API_URL", "https://api.anthropic.com/v1/complete")
DEFAULT_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-2.1")
CACHE_DIR = os.getenv("SYNTH_CACHE_DIR", "/tmp/synth_cache")
CACHE_TTL = int(os.getenv("SYNTH_CACHE_TTL", "3600"))  # seconds

# Initialize cache & logger
cache = Cache(CACHE_DIR)
logger = logging.getLogger("anthropic_client")
logging.basicConfig(level=logging.INFO)

# Example schema for expected structured response (adjust to your needs)
class SummarySchema(BaseModel):
    summary: str
    confidence: Optional[float] = None
    citations: Optional[Dict[str, str]] = None


def _cache_key(model: str, prompt: str, params: Dict[str, Any]) -> str:
    h = hashlib.sha256()
    h.update(model.encode())
    h.update(b"\n")
    h.update(prompt.encode())
    h.update(b"\n")
    h.update(json.dumps(params, sort_keys=True).encode())
    return h.hexdigest()


# Retry policy: retry on network errors and 5xx up to 4 attempts with exponential backoff
@retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=1, min=1, max=10),
       retry=retry_if_exception_type(requests.exceptions.RequestException))
def _post_json(payload: Dict[str, Any], timeout: int = 60) -> Dict[str, Any]:
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "Content-Type": "application/json",
    }
    resp = requests.post(ANTHROPIC_API_URL, headers=headers, json=payload, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


class AnthropicClient:
    def __init__(self, model: str = DEFAULT_MODEL, temperature: float = 0.0, max_tokens: int = 512):
        if not ANTHROPIC_API_KEY:
            raise RuntimeError("Set ANTHROPIC_API_KEY in environment")
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def complete(self, prompt: str, stop: Optional[list] = None, use_cache: bool = True,
                 cache_ttl: int = CACHE_TTL, extra: Dict[str, Any] = None) -> Dict[str, Any]:
        params = {"temperature": self.temperature, "max_tokens_to_sample": self.max_tokens}
        if extra:
            params.update(extra)
        key = _cache_key(self.model, prompt, params)

        if use_cache:
            cached = cache.get(key)
            if cached:
                logger.info("cache hit")
                return cached

        payload = {
            "model": self.model,
            "prompt": prompt,
            "max_tokens_to_sample": params["max_tokens_to_sample"],
            "temperature": params["temperature"],
        }
        if stop:
            payload["stop"] = stop

        t0 = time.time()
        result = _post_json(payload)
        latency = time.time() - t0

        # Audit log: minimal info (don't log secrets)
        audit = {
            "timestamp": time.time(),
            "model": self.model,
            "params": params,
            "prompt_hash": hashlib.sha256(prompt.encode()).hexdigest(),
            "latency_s": latency,
            "response_keys": list(result.keys()),
        }
        # write a small audit file for traceability (swap for DB or S3 in prod)
        audit_path = f"/tmp/anthropic_audit_{hashlib.sha256(json.dumps(audit).encode()).hexdigest()}.json"
        try:
            with open(audit_path, "w") as f:
                json.dump(audit, f)
        except Exception:
            logger.exception("Failed to write audit file")

        if use_cache:
            cache.set(key, result, expire=cache_ttl)

        return result

    def structured_summary(self, prompt: str, schema=SummarySchema, **kwargs) -> BaseModel:
        """
        Ask model for a JSON object matching schema. Validate and return model output as Pydantic object.
        """
        instruct = (
            "You are a careful, evidence-first summarizer. Return only a JSON object matching the schema exactly. "
            "Do NOT provide chain-of-thought or internal reasoning. If you cannot, return an empty JSON object {}.\n\n"
            f"Schema: {schema.schema_json(indent=2)}\n\n"
            "Now produce the requested output."
        )
        full_prompt = instruct + "\n\n" + prompt
        raw = self.complete(full_prompt, **kwargs)
        # model-specific: extract text field (adjust if API returns different structure)
        text = None
        if isinstance(raw, dict):
            # Anthropic API may return a 'completion' or 'completion_text' or 'text' field
            for k in ("completion", "completion_text", "text", "response", "output"):
                if k in raw:
                    text = raw[k]
                    break
            # fallback: if 'completion' nested
            if text is None and "completion" in raw:
                text = raw["completion"]
        if text is None:
            text = json.dumps(raw)

        # Try to locate first JSON substring
        try:
            start = text.index("{")
            obj = json.loads(text[start:])
        except Exception:
            # fallback: try entire text parse
            try:
                obj = json.loads(text)
            except Exception:
                raise ValueError("Model did not return valid JSON")

        # Validate schema
        try:
            validated = schema.parse_obj(obj)
        except ValidationError as e:
            logger.error("Response did not validate schema: %s", e)
            raise
        return validated
