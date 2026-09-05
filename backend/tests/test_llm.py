from unittest.mock import AsyncMock, MagicMock
import httpx
import pytest
from app.core.config import Settings
from app.llm.client import OmniRouteClient
from app.llm.exceptions import (
    LLMAuthenticationError,
    LLMConfigurationError,
    LLMConnectionError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMUpstreamError,
    sanitize_error_message,
)
from app.llm.models import (
    LLMCompletionRequest,
    LLMMessage,
    LLMRole,
)
from app.llm.service import LLMService


@pytest.fixture
def mock_config():
    return Settings(
        LLM_PROVIDER="omniroute",
        OMNIROUTE_API_KEY="test-key-secret-123",
        OMNIROUTE_BASE_URL="http://localhost:20128/v1",
        OMNIROUTE_DEFAULT_MODEL="test-model-v1",
        OMNIROUTE_TIMEOUT_SECONDS=10,
        OMNIROUTE_MAX_RETRIES=2,
    )


@pytest.fixture
def placeholder_config():
    return Settings(
        LLM_PROVIDER="omniroute",
        OMNIROUTE_API_KEY="YOUR_OMNIROUTE_API_KEY",
        OMNIROUTE_BASE_URL="YOUR_OMNIROUTE_BASE_URL",
        OMNIROUTE_DEFAULT_MODEL="YOUR_OMNIROUTE_MODEL",
    )


@pytest.mark.asyncio
async def test_config_placeholder_detection(placeholder_config):
    assert placeholder_config.is_omniroute_configured() is False

    service = LLMService(config=placeholder_config)
    request = LLMCompletionRequest(
        messages=[LLMMessage(role=LLMRole.USER, content="Hello")]
    )
    with pytest.raises(LLMConfigurationError):
        await service.generate(request)


@pytest.mark.asyncio
async def test_successful_generation_default_model(mock_config):
    mock_http_client = AsyncMock()
    mock_http_client.post.return_value = MagicMock(
        status_code=200,
        json=lambda: {
            "model": "test-model-v1",
            "choices": [
                {
                    "message": {"role": "assistant", "content": "Hello there!"},
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15,
            },
        },
    )

    client = OmniRouteClient(
        base_url=mock_config.omniroute_base_url,
        api_key=mock_config.omniroute_api_key,
        timeout_seconds=mock_config.omniroute_timeout_seconds,
        max_retries=mock_config.omniroute_max_retries,
        http_client=mock_http_client,
    )

    mock_ai_gen_service = AsyncMock()
    service = LLMService(client=client, config=mock_config, ai_generation_service=mock_ai_gen_service)

    request = LLMCompletionRequest(
        messages=[LLMMessage(role=LLMRole.USER, content="Say hello")],
        task_type="unit_test",
    )
    response = await service.generate(request)

    assert response.content == "Hello there!"
    assert response.model == "test-model-v1"
    assert response.finish_reason == "stop"
    assert response.usage.prompt_tokens == 10
    assert response.usage.completion_tokens == 5
    assert response.usage.total_tokens == 15

    mock_ai_gen_service.create_generation.assert_called_once()
    saved_gen = mock_ai_gen_service.create_generation.call_args[0][0]
    assert saved_gen.task_type == "unit_test"
    assert saved_gen.model == "test-model-v1"
    assert saved_gen.output_text == "Hello there!"
    assert saved_gen.tokens_input == 10
    assert saved_gen.tokens_output == 5


@pytest.mark.asyncio
async def test_model_override(mock_config):
    mock_http_client = AsyncMock()
    mock_http_client.post.return_value = MagicMock(
        status_code=200,
        json=lambda: {
            "model": "override-model-v2",
            "choices": [
                {
                    "message": {"role": "assistant", "content": "Overridden model response"},
                    "finish_reason": "stop",
                }
            ],
            "usage": None,
        },
    )

    client = OmniRouteClient(
        base_url=mock_config.omniroute_base_url,
        api_key=mock_config.omniroute_api_key,
        http_client=mock_http_client,
    )
    service = LLMService(client=client, config=mock_config)

    request = LLMCompletionRequest(
        messages=[LLMMessage(role=LLMRole.USER, content="Test override")],
        model="override-model-v2",
    )
    response = await service.generate(request)

    assert response.model == "override-model-v2"
    assert response.usage is None

    called_payload = mock_http_client.post.call_args[1]["json"]
    assert called_payload["model"] == "override-model-v2"


@pytest.mark.asyncio
async def test_timeout_handling(mock_config):
    mock_http_client = AsyncMock()
    mock_http_client.post.side_effect = httpx.TimeoutException("Timeout")

    client = OmniRouteClient(
        base_url=mock_config.omniroute_base_url,
        api_key=mock_config.omniroute_api_key,
        timeout_seconds=5,
        max_retries=1,
        http_client=mock_http_client,
    )
    service = LLMService(client=client, config=mock_config)

    request = LLMCompletionRequest(
        messages=[LLMMessage(role=LLMRole.USER, content="Timeout test")]
    )

    with pytest.raises(LLMTimeoutError):
        await service.generate(request)

    assert mock_http_client.post.call_count == 2


@pytest.mark.asyncio
async def test_connection_failure(mock_config):
    mock_http_client = AsyncMock()
    mock_http_client.post.side_effect = httpx.ConnectError("Connection refused")

    client = OmniRouteClient(
        base_url=mock_config.omniroute_base_url,
        api_key=mock_config.omniroute_api_key,
        max_retries=1,
        http_client=mock_http_client,
    )
    service = LLMService(client=client, config=mock_config)

    request = LLMCompletionRequest(
        messages=[LLMMessage(role=LLMRole.USER, content="Connection error test")]
    )

    with pytest.raises(LLMConnectionError):
        await service.generate(request)


@pytest.mark.asyncio
async def test_401_authentication_failure_no_retry(mock_config):
    mock_http_client = AsyncMock()
    mock_http_client.post.return_value = MagicMock(status_code=401)

    client = OmniRouteClient(
        base_url=mock_config.omniroute_base_url,
        api_key="invalid-key-secret",
        max_retries=2,
        http_client=mock_http_client,
    )
    service = LLMService(client=client, config=mock_config)

    request = LLMCompletionRequest(
        messages=[LLMMessage(role=LLMRole.USER, content="Auth test")]
    )

    with pytest.raises(LLMAuthenticationError):
        await service.generate(request)

    assert mock_http_client.post.call_count == 1


@pytest.mark.asyncio
async def test_429_rate_limit_error(mock_config):
    mock_http_client = AsyncMock()
    mock_http_client.post.return_value = MagicMock(status_code=429)

    client = OmniRouteClient(
        base_url=mock_config.omniroute_base_url,
        api_key=mock_config.omniroute_api_key,
        max_retries=2,
        http_client=mock_http_client,
    )
    service = LLMService(client=client, config=mock_config)

    request = LLMCompletionRequest(
        messages=[LLMMessage(role=LLMRole.USER, content="Rate limit test")]
    )

    with pytest.raises(LLMRateLimitError):
        await service.generate(request)


@pytest.mark.asyncio
async def test_5xx_upstream_error_with_retry(mock_config):
    mock_http_client = AsyncMock()
    mock_http_client.post.return_value = MagicMock(status_code=502)

    client = OmniRouteClient(
        base_url=mock_config.omniroute_base_url,
        api_key=mock_config.omniroute_api_key,
        max_retries=2,
        http_client=mock_http_client,
    )
    service = LLMService(client=client, config=mock_config)

    request = LLMCompletionRequest(
        messages=[LLMMessage(role=LLMRole.USER, content="Upstream 502 test")]
    )

    with pytest.raises(LLMUpstreamError):
        await service.generate(request)

    assert mock_http_client.post.call_count == 3


def test_secret_redaction():
    secret_key = "sk-proj-super-secret-key-12345"
    raw_message = f"Error connecting with Authorization: Bearer {secret_key} and api_key={secret_key}"
    sanitized = sanitize_error_message(raw_message)

    assert secret_key not in sanitized
    assert "Bearer [REDACTED]" in sanitized
    assert "api_key=[REDACTED]" in sanitized


@pytest.mark.asyncio
async def test_health_check(mock_config, placeholder_config):
    unconfig_service = LLMService(config=placeholder_config)
    unconfig_health = await unconfig_service.health_check()
    assert unconfig_health["status"] == "degraded"

    service = LLMService(config=mock_config)
    health = await service.health_check()
    assert health["provider"] == "omniroute"
    assert "test-key-secret-123" not in str(health)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_omniroute_integration():
    config = Settings(
        OMNIROUTE_BASE_URL="http://localhost:20128/v1",
        OMNIROUTE_API_KEY="test_key",
        OMNIROUTE_DEFAULT_MODEL="test_model",
    )
    service = LLMService(config=config)
    res = await service.health_check()
    assert "status" in res