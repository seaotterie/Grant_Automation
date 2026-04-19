"""
Anthropic Service - Centralized Claude API management for grant automation platform

This service provides a unified interface for Claude API calls across all AI tools,
handling authentication, rate limiting, error handling, cost tracking, and model routing.

Model Routing:
  - claude-haiku-4-5:  Fast screening (~$0.001/call) - discovery, fast screening
  - claude-sonnet-4-6: Thorough analysis (~$0.01/call) - thorough screening, deep intelligence
  - claude-opus-4-7:   Premium analysis (~$0.20/call) - premium tier deep intelligence
"""

import asyncio
import logging
import os
import re
import time
import json
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

# Strip leading/trailing markdown fences (```json ... ``` or ``` ... ```)
_FENCE_RE = re.compile(
    r"\A\s*```(?:json|JSON)?\s*\n?|\n?```\s*\Z",
    re.MULTILINE,
)

# Try to import the anthropic SDK; allow graceful degradation if not installed
try:
    import anthropic
    from anthropic import AsyncAnthropic
    ANTHROPIC_SDK_AVAILABLE = True
except ImportError:
    ANTHROPIC_SDK_AVAILABLE = False
    logger.warning("anthropic SDK not installed. Run: pip install anthropic")


class ClaudeModel(Enum):
    """Available Claude models with their intended use cases."""
    HAIKU = "claude-haiku-4-5-20251001"
    SONNET = "claude-sonnet-4-6"
    OPUS = "claude-opus-4-7"


class PipelineStage(Enum):
    """Pipeline stages mapped to recommended models."""
    DISCOVERY = "discovery"
    FAST_SCREENING = "fast_screening"
    THOROUGH_SCREENING = "thorough_screening"
    DEEP_INTELLIGENCE = "deep_intelligence"
    PREMIUM_INTELLIGENCE = "premium_intelligence"


# Model routing: which model to use for each pipeline stage
MODEL_ROUTING = {
    PipelineStage.DISCOVERY: ClaudeModel.HAIKU,
    PipelineStage.FAST_SCREENING: ClaudeModel.HAIKU,
    PipelineStage.THOROUGH_SCREENING: ClaudeModel.SONNET,
    PipelineStage.DEEP_INTELLIGENCE: ClaudeModel.SONNET,
    PipelineStage.PREMIUM_INTELLIGENCE: ClaudeModel.OPUS,
}


@dataclass
class ClaudeCompletionRequest:
    """Structured request for Claude completion."""
    model: str
    messages: List[Dict[str, str]]
    system: Optional[str] = None
    max_tokens: int = 4096
    temperature: Optional[float] = None
    stop_sequences: Optional[List[str]] = None
    metadata: Optional[Dict[str, str]] = None


@dataclass
class ClaudeCompletionResponse:
    """Structured response from Claude completion."""
    content: str
    model: str
    usage: Dict[str, int]
    stop_reason: str
    cost_estimate: float
    latency_ms: float = 0.0


@dataclass
class ModelCostTracker:
    """Per-model cost tracking."""
    requests: int = 0
    total_cost: float = 0.0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_latency_ms: float = 0.0

    @property
    def avg_cost_per_request(self) -> float:
        return self.total_cost / max(self.requests, 1)

    @property
    def avg_latency_ms(self) -> float:
        return self.total_latency_ms / max(self.requests, 1)


class AnthropicService:
    """
    Centralized Anthropic/Claude service for the grant automation platform.

    Features:
    - Model routing by pipeline stage
    - Async API calls with rate limiting
    - Cost tracking per model
    - Structured JSON output support
    - Graceful error handling with retries
    """

    # Claude API pricing (per token) — April 2026
    # Includes cache read/write pricing for prompt caching
    COST_PER_TOKEN = {
        ClaudeModel.HAIKU.value: {
            "input": 1.00 / 1_000_000,
            "output": 5.00 / 1_000_000,
            "cache_write": 1.25 / 1_000_000,
            "cache_read": 0.10 / 1_000_000,
        },
        ClaudeModel.SONNET.value: {
            "input": 3.00 / 1_000_000,
            "output": 15.00 / 1_000_000,
            "cache_write": 3.75 / 1_000_000,
            "cache_read": 0.30 / 1_000_000,
        },
        ClaudeModel.OPUS.value: {
            "input": 15.00 / 1_000_000,
            "output": 75.00 / 1_000_000,
            "cache_write": 18.75 / 1_000_000,
            "cache_read": 1.50 / 1_000_000,
        },
    }

    # Rate limits (conservative defaults)
    RATE_LIMIT_RPM = 1000  # requests per minute
    RATE_LIMIT_TPM = 400_000  # tokens per minute

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Anthropic service.

        Args:
            api_key: Anthropic API key. Falls back to ANTHROPIC_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.client: Optional[Any] = None
        self.cost_tracking: Dict[str, ModelCostTracker] = {}
        # (timestamp, input_tokens_est) tuples for sliding-window RPM/TPM enforcement
        self._request_history: List[tuple] = []
        self._rate_limit_lock = asyncio.Lock()

        if not ANTHROPIC_SDK_AVAILABLE:
            logger.error(
                "anthropic SDK not installed. Install with: pip install anthropic"
            )
            return

        if self.api_key:
            self.client = AsyncAnthropic(
                api_key=self.api_key,
                max_retries=3,
                timeout=60.0,
            )
            logger.info("Anthropic service initialized with API key")
        else:
            logger.warning(
                "Anthropic service initialized without API key — "
                "set ANTHROPIC_API_KEY in .env"
            )

    @property
    def is_available(self) -> bool:
        """Whether the service is ready to make API calls."""
        return self.client is not None

    def get_model_for_stage(self, stage: PipelineStage) -> str:
        """
        Get the recommended Claude model for a pipeline stage.

        Args:
            stage: Pipeline stage enum

        Returns:
            Model ID string
        """
        model = MODEL_ROUTING.get(stage, ClaudeModel.SONNET)
        return model.value

    async def create_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        stage: Optional[PipelineStage] = None,
        system: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: Optional[float] = None,
        stop_sequences: Optional[List[str]] = None,
        json_mode: bool = False,
        cache_system_prompt: bool = False,
    ) -> ClaudeCompletionResponse:
        """
        Create a Claude completion with rate limiting and cost tracking.

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Explicit model ID (overrides stage routing)
            stage: Pipeline stage for automatic model selection
            system: System prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-1.0)
            stop_sequences: Stop sequences
            json_mode: If True, instructs Claude to return valid JSON
            cache_system_prompt: If True, emit ephemeral cache_control on the
                system prompt for prompt caching (50-90% input-token savings
                on repeated system prompts, e.g. batch screening).

        Returns:
            ClaudeCompletionResponse with content and metadata

        Raises:
            RuntimeError: If client not initialized
            anthropic.APIError: On API failures after retries
        """
        if not self.client:
            raise RuntimeError(
                "Anthropic client not initialized — "
                "set ANTHROPIC_API_KEY environment variable"
            )

        # Resolve model
        if model is None:
            if stage is not None:
                model = self.get_model_for_stage(stage)
            else:
                model = ClaudeModel.SONNET.value

        # Resolve system prompt (json_mode appends JSON instruction)
        if system and json_mode:
            system = (
                f"{system}\n\nIMPORTANT: Respond with valid JSON only. "
                "Do not include any text outside the JSON object."
            )
        elif not system and json_mode:
            system = (
                "Respond with valid JSON only. "
                "Do not include any text outside the JSON object."
            )

        # Estimate tokens for TPM rate limiting (rough: ~4 chars per token)
        estimated_input_tokens = self._estimate_tokens(messages, system)

        # Rate limiting (concurrency-safe, enforces both RPM and TPM)
        await self._check_rate_limits(estimated_input_tokens + max_tokens)

        # Build API params
        api_params: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
        }

        if system:
            if cache_system_prompt:
                # Emit a structured system block with ephemeral cache_control
                api_params["system"] = [
                    {
                        "type": "text",
                        "text": system,
                        "cache_control": {"type": "ephemeral"},
                    }
                ]
            else:
                api_params["system"] = system

        if temperature is not None:
            api_params["temperature"] = temperature

        if stop_sequences:
            api_params["stop_sequences"] = stop_sequences

        # Make API call
        start_time = time.time()
        try:
            response = await self.client.messages.create(**api_params)
        except Exception as e:
            # Log with classification to help downstream retry decisions
            err_type = type(e).__name__
            logger.error(f"Claude API call failed ({model}, {err_type}): {e}")
            raise

        latency_ms = (time.time() - start_time) * 1000

        # Extract content
        content = self._extract_content(response)

        # Build usage dict (include cache tokens when available)
        usage_obj = response.usage

        def _usage_int(attr: str) -> int:
            val = getattr(usage_obj, attr, None)
            if isinstance(val, int):
                return val
            return 0

        usage = {
            "input_tokens": _usage_int("input_tokens"),
            "output_tokens": _usage_int("output_tokens"),
            "cache_creation_input_tokens": _usage_int("cache_creation_input_tokens"),
            "cache_read_input_tokens": _usage_int("cache_read_input_tokens"),
        }
        usage["total_tokens"] = (
            usage["input_tokens"]
            + usage["output_tokens"]
            + usage["cache_creation_input_tokens"]
            + usage["cache_read_input_tokens"]
        )

        # Calculate cost (includes cache write/read pricing)
        cost = self._calculate_cost(model, usage)

        # Track
        self._track_request(model, usage, cost, latency_ms)

        # Normalize stop_reason (SDK may return None on some interruptions)
        stop_reason = response.stop_reason or "unknown"

        logger.info(
            f"Claude completion: {model}, "
            f"tokens: {usage['total_tokens']} "
            f"(in={usage['input_tokens']}, out={usage['output_tokens']}, "
            f"cache_w={usage['cache_creation_input_tokens']}, "
            f"cache_r={usage['cache_read_input_tokens']}), "
            f"cost: ${cost:.4f}, "
            f"latency: {latency_ms:.0f}ms"
        )

        return ClaudeCompletionResponse(
            content=content,
            model=model,
            usage=usage,
            stop_reason=stop_reason,
            cost_estimate=cost,
            latency_ms=latency_ms,
        )

    async def create_json_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        stage: Optional[PipelineStage] = None,
        system: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
        cache_system_prompt: bool = False,
    ) -> Dict[str, Any]:
        """
        Create a Claude completion that returns parsed JSON.

        Convenience wrapper around create_completion with json_mode=True.
        Parses the response content as JSON and returns the dict.

        Returns:
            Parsed JSON dict

        Raises:
            json.JSONDecodeError: If response is not valid JSON
        """
        response = await self.create_completion(
            messages=messages,
            model=model,
            stage=stage,
            system=system,
            max_tokens=max_tokens,
            temperature=temperature,
            json_mode=True,
            cache_system_prompt=cache_system_prompt,
        )

        # Strip markdown code fences via a single regex (handles ```json, ```, etc.)
        content = _FENCE_RE.sub("", response.content).strip()

        return json.loads(content)

    def _extract_content(self, response: Any) -> str:
        """Extract text content from Claude API response."""
        if not response.content:
            logger.warning("Empty response content from Claude")
            return ""

        # Claude returns a list of content blocks
        text_parts = []
        for block in response.content:
            if hasattr(block, "text"):
                text_parts.append(block.text)

        if not text_parts:
            logger.warning("No text blocks found in Claude response")
            return ""

        return "\n".join(text_parts)

    def _calculate_cost(self, model: str, usage: Dict[str, int]) -> float:
        """Calculate cost estimate for an API call (includes cache pricing)."""
        rates = self.COST_PER_TOKEN.get(model)
        if not rates:
            # Fall back to Sonnet pricing for unknown models
            rates = self.COST_PER_TOKEN[ClaudeModel.SONNET.value]

        input_cost = usage.get("input_tokens", 0) * rates["input"]
        output_cost = usage.get("output_tokens", 0) * rates["output"]
        cache_write_cost = (
            usage.get("cache_creation_input_tokens", 0) * rates.get("cache_write", rates["input"])
        )
        cache_read_cost = (
            usage.get("cache_read_input_tokens", 0) * rates.get("cache_read", rates["input"])
        )

        return input_cost + output_cost + cache_write_cost + cache_read_cost

    def _estimate_tokens(
        self,
        messages: List[Dict[str, Any]],
        system: Optional[str] = None,
    ) -> int:
        """Rough token estimate for TPM rate limiting (~4 chars/token)."""
        total_chars = 0
        if system:
            total_chars += len(system)
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, str):
                total_chars += len(content)
            elif isinstance(content, list):
                # Handle structured content blocks
                for block in content:
                    if isinstance(block, dict):
                        total_chars += len(str(block.get("text", "")))
        return max(1, total_chars // 4)

    def _track_request(
        self,
        model: str,
        usage: Dict[str, int],
        cost: float,
        latency_ms: float,
    ) -> None:
        """Track request for cost and performance monitoring."""
        if model not in self.cost_tracking:
            self.cost_tracking[model] = ModelCostTracker()

        tracker = self.cost_tracking[model]
        tracker.requests += 1
        tracker.total_cost += cost
        tracker.total_input_tokens += (
            usage.get("input_tokens", 0)
            + usage.get("cache_creation_input_tokens", 0)
            + usage.get("cache_read_input_tokens", 0)
        )
        tracker.total_output_tokens += usage.get("output_tokens", 0)
        tracker.total_latency_ms += latency_ms

    async def _check_rate_limits(self, estimated_tokens: int = 0) -> None:
        """Enforce RPM + TPM rate limits with backpressure.

        Concurrency-safe via asyncio.Lock: prevents the overshoot that occurs
        when many coroutines (e.g. 200-opportunity screening) pass the check
        simultaneously and trigger Anthropic's 429 response.
        """
        async with self._rate_limit_lock:
            while True:
                now = time.time()
                # Slide the window: drop entries older than 60s
                self._request_history = [
                    (t, tokens) for (t, tokens) in self._request_history
                    if now - t < 60
                ]

                current_rpm = len(self._request_history)
                current_tpm = sum(tokens for (_, tokens) in self._request_history)

                rpm_threshold = int(self.RATE_LIMIT_RPM * 0.9)
                tpm_threshold = int(self.RATE_LIMIT_TPM * 0.9)

                rpm_hit = current_rpm >= rpm_threshold
                tpm_hit = current_tpm + estimated_tokens >= tpm_threshold

                if not (rpm_hit or tpm_hit):
                    # Reserve our slot now, while still holding the lock, so the
                    # next coroutine sees our reservation when it computes limits.
                    self._request_history.append((now, estimated_tokens))
                    return

                # Figure out how long to wait for the oldest entry to age out
                oldest_ts = self._request_history[0][0] if self._request_history else now
                wait_time = max(0.1, 60 - (now - oldest_ts))
                reason = "RPM" if rpm_hit else "TPM"
                logger.info(
                    f"Rate limit approaching ({reason}: rpm={current_rpm}, "
                    f"tpm={current_tpm}), waiting {wait_time:.1f}s"
                )
                await asyncio.sleep(wait_time)
                # Loop and re-check — other coroutines may still push us back over

    def get_cost_summary(self) -> Dict[str, Any]:
        """Get comprehensive cost tracking summary."""
        total_cost = sum(t.total_cost for t in self.cost_tracking.values())
        total_requests = sum(t.requests for t in self.cost_tracking.values())
        total_input = sum(t.total_input_tokens for t in self.cost_tracking.values())
        total_output = sum(t.total_output_tokens for t in self.cost_tracking.values())

        return {
            "total_requests": total_requests,
            "total_cost": round(total_cost, 6),
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "avg_cost_per_request": round(total_cost / max(total_requests, 1), 6),
            "cost_by_model": {
                model: {
                    "requests": tracker.requests,
                    "total_cost": round(tracker.total_cost, 6),
                    "avg_cost": round(tracker.avg_cost_per_request, 6),
                    "avg_latency_ms": round(tracker.avg_latency_ms, 1),
                    "input_tokens": tracker.total_input_tokens,
                    "output_tokens": tracker.total_output_tokens,
                }
                for model, tracker in self.cost_tracking.items()
            },
        }

    def reset_cost_tracking(self) -> None:
        """Reset all cost tracking data."""
        self.cost_tracking.clear()
        self._request_history.clear()
        logger.info("Anthropic cost tracking reset")

    @property
    def request_count(self) -> int:
        """Total requests tracked across all models (read-only)."""
        return sum(t.requests for t in self.cost_tracking.values())


# ---------------------------------------------------------------------------
# Global singleton
# ---------------------------------------------------------------------------

_anthropic_service: Optional[AnthropicService] = None


def get_anthropic_service() -> AnthropicService:
    """Get the global Anthropic service instance (singleton)."""
    global _anthropic_service
    if _anthropic_service is None:
        _anthropic_service = AnthropicService()
    return _anthropic_service


def configure_anthropic_service(api_key: str) -> AnthropicService:
    """Configure the global Anthropic service with an explicit API key."""
    global _anthropic_service
    _anthropic_service = AnthropicService(api_key=api_key)
    return _anthropic_service


def reset_anthropic_service() -> None:
    """Reset the global instance (useful for testing)."""
    global _anthropic_service
    _anthropic_service = None


__all__ = [
    "AnthropicService",
    "ClaudeCompletionRequest",
    "ClaudeCompletionResponse",
    "ClaudeModel",
    "PipelineStage",
    "MODEL_ROUTING",
    "get_anthropic_service",
    "configure_anthropic_service",
    "reset_anthropic_service",
]
