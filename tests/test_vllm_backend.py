from __future__ import annotations

import httpx
import pytest

from llmbench.backends.base import BackendConnectionError
from llmbench.backends.vllm import VLLMBackendAdapter
from llmbench.models import GenerationConfig


@pytest.mark.asyncio
async def test_check_connection_passes_when_model_visible() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v1/models":
            return httpx.Response(200, json={"data": [{"id": "test-model"}]})
        return httpx.Response(404)

    backend = VLLMBackendAdapter(base_url="http://testserver", model="test-model")

    async with httpx.AsyncClient(base_url="http://testserver", transport=httpx.MockTransport(handler)) as client:
        await backend.check_connection(client)


@pytest.mark.asyncio
async def test_check_connection_raises_if_model_missing() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"data": [{"id": "different-model"}]})

    backend = VLLMBackendAdapter(base_url="http://testserver", model="test-model")

    async with httpx.AsyncClient(base_url="http://testserver", transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(BackendConnectionError):
            await backend.check_connection(client)


@pytest.mark.asyncio
async def test_vllm_non_stream_parses_usage_tokens() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "hello world"}}],
                "usage": {"completion_tokens": 2},
            },
        )

    backend = VLLMBackendAdapter(base_url="http://testserver", model="test-model")
    generation = GenerationConfig(max_tokens=16, stream=False)

    async with httpx.AsyncClient(base_url="http://testserver", transport=httpx.MockTransport(handler)) as client:
        result = await backend.generate(client=client, prompt="hello", generation=generation)

    assert result.output_text == "hello world"
    assert result.output_tokens == 2
    assert result.output_tokens_estimated is False
    assert result.ttft_ms is None
