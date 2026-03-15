from __future__ import annotations

import json
import re
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import httpx

from llmbench.models import GenerationConfig


@dataclass(slots=True)
class BackendResult:
    output_text: str
    output_tokens: int
    output_tokens_estimated: bool
    ttft_ms: float | None
    status_code: int


class BackendConnectionError(RuntimeError):
    """Raised when connectivity or model validation checks fail."""


class BackendFeatureNotSupportedError(RuntimeError):
    """Raised when a requested benchmark feature is not supported."""


class BackendResponseParseError(RuntimeError):
    """Raised when a backend response cannot be parsed."""


class BaseBackendAdapter(ABC):
    engine_name = "base"

    def __init__(
        self,
        base_url: str,
        model: str,
        api_key: str | None = None,
        endpoint: str = "/v1/chat/completions",
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.endpoint = endpoint
        self.api_key = api_key
        self.extra_headers = extra_headers or {}

    @property
    def headers(self) -> dict[str, str]:
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        headers.update(self.extra_headers)
        return headers

    async def check_connection(self, client: httpx.AsyncClient) -> None:
        models_path = "/v1/models"
        try:
            response = await client.get(models_path, headers=self.headers, timeout=10)
            response.raise_for_status()
        except Exception as exc:  # noqa: BLE001
            msg = f"Could not connect to {self.engine_name} at {self.base_url}. Is the server running?"
            raise BackendConnectionError(msg) from exc

        payload = response.json()
        model_ids = _extract_model_ids(payload)
        if model_ids and self.model not in model_ids:
            msg = (
                f"Model '{self.model}' not returned by {models_path}. "
                f"Available models: {', '.join(model_ids)}"
            )
            raise BackendConnectionError(msg)

    async def generate(
        self,
        client: httpx.AsyncClient,
        prompt: str,
        generation: GenerationConfig,
    ) -> BackendResult:
        if generation.stream:
            return await self._stream_request(client=client, prompt=prompt, generation=generation)
        return await self._non_stream_request(client=client, prompt=prompt, generation=generation)

    async def _non_stream_request(
        self,
        client: httpx.AsyncClient,
        prompt: str,
        generation: GenerationConfig,
    ) -> BackendResult:
        response = await client.post(
            self.endpoint,
            json=self.build_payload(prompt=prompt, generation=generation),
            headers=self.headers,
            timeout=generation.request_timeout_s,
        )
        response.raise_for_status()

        try:
            payload = response.json()
        except json.JSONDecodeError as exc:
            msg = f"{self.engine_name} returned a non-JSON response"
            raise BackendResponseParseError(msg) from exc

        text, output_tokens = self.parse_non_stream_response(payload)
        estimated = output_tokens is None
        final_tokens = output_tokens if output_tokens is not None else self.estimate_output_tokens(text)

        return BackendResult(
            output_text=text,
            output_tokens=final_tokens,
            output_tokens_estimated=estimated,
            ttft_ms=None,
            status_code=response.status_code,
        )

    async def _stream_request(
        self,
        client: httpx.AsyncClient,
        prompt: str,
        generation: GenerationConfig,
    ) -> BackendResult:
        start = time.perf_counter()
        first_token_at: float | None = None
        output_tokens: int | None = None
        chunks: list[str] = []

        async with client.stream(
            "POST",
            self.endpoint,
            json=self.build_payload(prompt=prompt, generation=generation),
            headers=self.headers,
            timeout=generation.request_timeout_s,
        ) as response:
            response.raise_for_status()

            async for line in response.aiter_lines():
                data_line = _extract_sse_payload(line)
                if data_line is None:
                    continue
                if data_line == "[DONE]":
                    break

                try:
                    payload = json.loads(data_line)
                except json.JSONDecodeError:
                    continue

                text_piece, chunk_tokens, finished = self.parse_stream_chunk(payload)
                if text_piece:
                    chunks.append(text_piece)
                    if first_token_at is None:
                        first_token_at = time.perf_counter()
                if chunk_tokens is not None:
                    output_tokens = chunk_tokens
                if finished:
                    break

            status_code = response.status_code

        output_text = "".join(chunks)
        if output_tokens is None:
            output_tokens = self.estimate_output_tokens(output_text)
            estimated = True
        else:
            estimated = False

        ttft_ms = (first_token_at - start) * 1000.0 if first_token_at is not None else None

        return BackendResult(
            output_text=output_text,
            output_tokens=output_tokens,
            output_tokens_estimated=estimated,
            ttft_ms=ttft_ms,
            status_code=status_code,
        )

    @staticmethod
    def estimate_output_tokens(text: str) -> int:
        tokens = re.findall(r"\S+", text)
        return len(tokens)

    @abstractmethod
    def build_payload(self, prompt: str, generation: GenerationConfig) -> dict[str, Any]:
        """Build request payload."""

    @abstractmethod
    def parse_non_stream_response(self, payload: dict[str, Any]) -> tuple[str, int | None]:
        """Return completion text and optional output token count."""

    @abstractmethod
    def parse_stream_chunk(self, payload: dict[str, Any]) -> tuple[str, int | None, bool]:
        """Return delta text, optional output token count, and done flag."""


def _extract_sse_payload(line: str) -> str | None:
    stripped = line.strip()
    if not stripped:
        return None
    if stripped.startswith("data:"):
        return stripped.split("data:", 1)[1].strip()
    if stripped.startswith("{"):
        return stripped
    return None


def _extract_model_ids(payload: dict[str, Any]) -> list[str]:
    data = payload.get("data")
    if not isinstance(data, list):
        return []

    model_ids: list[str] = []
    for item in data:
        if isinstance(item, dict) and isinstance(item.get("id"), str):
            model_ids.append(item["id"])
    return model_ids
