"""
Tests for AnthropicService — Claude API client for the grant automation platform.

Tests cover:
- Service initialization and configuration
- Model routing by pipeline stage
- Cost calculation accuracy
- Cost tracking and summary
- Rate limit logic
- JSON completion parsing
- Content extraction
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.core.anthropic_service import (
    AnthropicService,
    ClaudeCompletionResponse,
    ClaudeModel,
    PipelineStage,
    MODEL_ROUTING,
    get_anthropic_service,
    reset_anthropic_service,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset global singleton between tests."""
    reset_anthropic_service()
    yield
    reset_anthropic_service()


@pytest.fixture
def service_no_key():
    """Service initialized without API key."""
    with patch.dict("os.environ", {}, clear=True):
        return AnthropicService(api_key=None)


@pytest.fixture
def service_with_key():
    """Service initialized with a test API key (bypasses SDK requirement)."""
    import asyncio
    svc = AnthropicService.__new__(AnthropicService)
    svc.api_key = "sk-ant-test-key"
    svc.client = MagicMock()  # Mock client directly
    svc.cost_tracking = {}
    svc._request_history = []
    svc._rate_limit_lock = asyncio.Lock()
    return svc


def _make_mock_response(
    text: str = "Hello",
    input_tokens: int = 100,
    output_tokens: int = 50,
    stop_reason: str = "end_turn",
):
    """Create a mock Claude API response."""
    block = MagicMock()
    block.text = text

    usage = MagicMock()
    usage.input_tokens = input_tokens
    usage.output_tokens = output_tokens

    response = MagicMock()
    response.content = [block]
    response.usage = usage
    response.stop_reason = stop_reason
    return response


# ---------------------------------------------------------------------------
# Initialization Tests
# ---------------------------------------------------------------------------

class TestInitialization:

    def test_no_key_not_available(self, service_no_key):
        assert not service_no_key.is_available

    def test_with_key_is_available(self, service_with_key):
        assert service_with_key.is_available

    def test_singleton_pattern(self):
        with patch("src.core.anthropic_service.AnthropicService") as mock_cls:
            mock_cls.return_value = MagicMock(spec=AnthropicService)
            svc1 = get_anthropic_service()
            svc2 = get_anthropic_service()
            # Same instance returned
            assert svc1 is svc2


# ---------------------------------------------------------------------------
# Model Routing Tests
# ---------------------------------------------------------------------------

class TestModelRouting:

    def test_discovery_uses_haiku(self, service_with_key):
        model = service_with_key.get_model_for_stage(PipelineStage.DISCOVERY)
        assert model == ClaudeModel.HAIKU.value

    def test_fast_screening_uses_haiku(self, service_with_key):
        model = service_with_key.get_model_for_stage(PipelineStage.FAST_SCREENING)
        assert model == ClaudeModel.HAIKU.value

    def test_thorough_screening_uses_sonnet(self, service_with_key):
        model = service_with_key.get_model_for_stage(PipelineStage.THOROUGH_SCREENING)
        assert model == ClaudeModel.SONNET.value

    def test_deep_intelligence_uses_sonnet(self, service_with_key):
        model = service_with_key.get_model_for_stage(PipelineStage.DEEP_INTELLIGENCE)
        assert model == ClaudeModel.SONNET.value

    def test_premium_uses_opus(self, service_with_key):
        model = service_with_key.get_model_for_stage(PipelineStage.PREMIUM_INTELLIGENCE)
        assert model == ClaudeModel.OPUS.value

    def test_all_stages_have_routing(self):
        for stage in PipelineStage:
            assert stage in MODEL_ROUTING


# ---------------------------------------------------------------------------
# Cost Calculation Tests
# ---------------------------------------------------------------------------

class TestCostCalculation:

    def test_haiku_cost(self, service_with_key):
        usage = {"input_tokens": 1000, "output_tokens": 500}
        cost = service_with_key._calculate_cost(ClaudeModel.HAIKU.value, usage)
        # April 2026 rates
        expected = (1000 * 1.00 / 1e6) + (500 * 5.00 / 1e6)
        assert abs(cost - expected) < 1e-9

    def test_sonnet_cost(self, service_with_key):
        usage = {"input_tokens": 1000, "output_tokens": 500}
        cost = service_with_key._calculate_cost(ClaudeModel.SONNET.value, usage)
        expected = (1000 * 3.00 / 1e6) + (500 * 15.00 / 1e6)
        assert abs(cost - expected) < 1e-9

    def test_opus_cost(self, service_with_key):
        usage = {"input_tokens": 1000, "output_tokens": 500}
        cost = service_with_key._calculate_cost(ClaudeModel.OPUS.value, usage)
        expected = (1000 * 15.00 / 1e6) + (500 * 75.00 / 1e6)
        assert abs(cost - expected) < 1e-9

    def test_unknown_model_falls_back_to_sonnet(self, service_with_key):
        usage = {"input_tokens": 1000, "output_tokens": 500}
        cost = service_with_key._calculate_cost("unknown-model", usage)
        sonnet_cost = service_with_key._calculate_cost(ClaudeModel.SONNET.value, usage)
        assert cost == sonnet_cost

    def test_cost_includes_cache_tokens(self, service_with_key):
        """Cache-read and cache-write tokens must be priced separately."""
        usage = {
            "input_tokens": 1000,
            "output_tokens": 500,
            "cache_creation_input_tokens": 2000,
            "cache_read_input_tokens": 5000,
        }
        cost = service_with_key._calculate_cost(ClaudeModel.SONNET.value, usage)
        expected = (
            1000 * 3.00 / 1e6
            + 500 * 15.00 / 1e6
            + 2000 * 3.75 / 1e6
            + 5000 * 0.30 / 1e6
        )
        assert abs(cost - expected) < 1e-9

    def test_opus_model_id_is_47(self):
        """Guard: Opus must be the current model ID, not the stale 4-6."""
        assert ClaudeModel.OPUS.value == "claude-opus-4-7"


# ---------------------------------------------------------------------------
# Cost Tracking Tests
# ---------------------------------------------------------------------------

class TestCostTracking:

    def test_tracking_empty(self, service_with_key):
        summary = service_with_key.get_cost_summary()
        assert summary["total_requests"] == 0
        assert summary["total_cost"] == 0

    def test_tracking_after_request(self, service_with_key):
        usage = {"input_tokens": 1000, "output_tokens": 500}
        cost = service_with_key._calculate_cost(ClaudeModel.HAIKU.value, usage)
        service_with_key._track_request(ClaudeModel.HAIKU.value, usage, cost, 150.0)

        summary = service_with_key.get_cost_summary()
        assert summary["total_requests"] == 1
        assert summary["total_cost"] > 0
        assert ClaudeModel.HAIKU.value in summary["cost_by_model"]

    def test_reset_tracking(self, service_with_key):
        usage = {"input_tokens": 100, "output_tokens": 50}
        service_with_key._track_request(ClaudeModel.HAIKU.value, usage, 0.01, 100.0)
        service_with_key.reset_cost_tracking()

        summary = service_with_key.get_cost_summary()
        assert summary["total_requests"] == 0


# ---------------------------------------------------------------------------
# API Call Tests (mocked)
# ---------------------------------------------------------------------------

class TestAPICall:

    @pytest.mark.asyncio
    async def test_completion_returns_response(self, service_with_key):
        mock_response = _make_mock_response("Test output", 200, 100)
        service_with_key.client.messages.create = AsyncMock(return_value=mock_response)

        result = await service_with_key.create_completion(
            messages=[{"role": "user", "content": "Hello"}],
            model=ClaudeModel.HAIKU.value,
        )

        assert isinstance(result, ClaudeCompletionResponse)
        assert result.content == "Test output"
        assert result.usage["input_tokens"] == 200
        assert result.usage["output_tokens"] == 100
        assert result.cost_estimate > 0

    @pytest.mark.asyncio
    async def test_completion_uses_stage_routing(self, service_with_key):
        mock_response = _make_mock_response()
        service_with_key.client.messages.create = AsyncMock(return_value=mock_response)

        await service_with_key.create_completion(
            messages=[{"role": "user", "content": "Test"}],
            stage=PipelineStage.FAST_SCREENING,
        )

        call_kwargs = service_with_key.client.messages.create.call_args.kwargs
        assert call_kwargs["model"] == ClaudeModel.HAIKU.value

    @pytest.mark.asyncio
    async def test_completion_no_client_raises(self, service_no_key):
        with pytest.raises(RuntimeError, match="not initialized"):
            await service_no_key.create_completion(
                messages=[{"role": "user", "content": "Hello"}],
            )

    @pytest.mark.asyncio
    async def test_json_completion_parses(self, service_with_key):
        json_output = json.dumps({"score": 0.85, "reasoning": "Good fit"})
        mock_response = _make_mock_response(json_output, 300, 80)
        service_with_key.client.messages.create = AsyncMock(return_value=mock_response)

        result = await service_with_key.create_json_completion(
            messages=[{"role": "user", "content": "Score this"}],
            stage=PipelineStage.FAST_SCREENING,
        )

        assert result["score"] == 0.85
        assert result["reasoning"] == "Good fit"

    @pytest.mark.asyncio
    async def test_json_completion_strips_code_fence(self, service_with_key):
        json_output = '```json\n{"score": 0.9}\n```'
        mock_response = _make_mock_response(json_output, 300, 80)
        service_with_key.client.messages.create = AsyncMock(return_value=mock_response)

        result = await service_with_key.create_json_completion(
            messages=[{"role": "user", "content": "Score"}],
        )

        assert result["score"] == 0.9


# ---------------------------------------------------------------------------
# Content Extraction Tests
# ---------------------------------------------------------------------------

class TestContentExtraction:

    def test_extract_single_block(self, service_with_key):
        response = _make_mock_response("Hello world")
        content = service_with_key._extract_content(response)
        assert content == "Hello world"

    def test_extract_multiple_blocks(self, service_with_key):
        block1 = MagicMock()
        block1.text = "Part 1"
        block2 = MagicMock()
        block2.text = "Part 2"

        response = MagicMock()
        response.content = [block1, block2]

        content = service_with_key._extract_content(response)
        assert content == "Part 1\nPart 2"

    def test_extract_empty_response(self, service_with_key):
        response = MagicMock()
        response.content = []
        content = service_with_key._extract_content(response)
        assert content == ""


# ---------------------------------------------------------------------------
# Rate limit concurrency tests
# ---------------------------------------------------------------------------

class TestRateLimitConcurrency:

    @pytest.mark.asyncio
    async def test_concurrent_checks_do_not_overshoot_rpm(self, service_with_key):
        """Many coroutines racing through _check_rate_limits must not exceed RPM.

        Reproduces the bug described in the April 2026 review: without a lock,
        multiple coroutines could pass the threshold check simultaneously and
        trigger Anthropic's 429. With the lock, each reservation is atomic, so
        the post-run count matches the number of calls that fit under the cap.
        """
        import asyncio

        # threshold = int(20 * 0.9) = 18 — well above 10 parallel callers
        service_with_key.RATE_LIMIT_RPM = 20

        async def one():
            await service_with_key._check_rate_limits(estimated_tokens=100)

        await asyncio.gather(*(one() for _ in range(10)))

        # Exactly 10 reservations landed, none lost to races
        assert len(service_with_key._request_history) == 10

    @pytest.mark.asyncio
    async def test_stop_reason_none_is_normalized(self, service_with_key):
        """When the SDK returns stop_reason=None, the response must carry 'unknown'."""
        mock_response = _make_mock_response("out", 100, 50, stop_reason=None)
        service_with_key.client.messages.create = AsyncMock(return_value=mock_response)

        response = await service_with_key.create_completion(
            messages=[{"role": "user", "content": "x"}],
            stage=PipelineStage.FAST_SCREENING,
        )
        assert response.stop_reason == "unknown"

    @pytest.mark.asyncio
    async def test_cache_system_prompt_adds_cache_control(self, service_with_key):
        """cache_system_prompt=True must emit structured system block with cache_control."""
        mock_response = _make_mock_response("ok", 100, 50)
        service_with_key.client.messages.create = AsyncMock(return_value=mock_response)

        await service_with_key.create_completion(
            messages=[{"role": "user", "content": "x"}],
            stage=PipelineStage.FAST_SCREENING,
            system="You are a helpful assistant.",
            cache_system_prompt=True,
        )

        call_kwargs = service_with_key.client.messages.create.call_args.kwargs
        assert isinstance(call_kwargs["system"], list)
        assert call_kwargs["system"][0]["cache_control"] == {"type": "ephemeral"}
