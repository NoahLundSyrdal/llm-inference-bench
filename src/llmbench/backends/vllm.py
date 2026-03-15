from __future__ import annotations

from typing import Any

from llmbench.backends.base import BackendResponseParseError, BaseBackendAdapter
from llmbench.models import GenerationConfig


class VLLMBackendAdapter(BaseBackendAdapter):
    engine_name = "vllm"

    def build_payload(self, prompt: str, generation: GenerationConfig) -> dict[str, Any]:
        return {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": generation.max_tokens,
            "temperature": generation.temperature,
            "top_p": generation.top_p,
            "stream": generation.stream,
        }

    def parse_non_stream_response(self, payload: dict[str, Any]) -> tuple[str, int | None]:
        choices = payload.get("choices")
        if not isinstance(choices, list) or not choices:
            msg = "Response missing choices"
            raise BackendResponseParseError(msg)

        first = choices[0]
        content = ""
        if isinstance(first, dict):
            message = first.get("message")
            if isinstance(message, dict) and isinstance(message.get("content"), str):
                content = message["content"]

        usage = payload.get("usage")
        output_tokens = None
        if isinstance(usage, dict) and isinstance(usage.get("completion_tokens"), int):
            output_tokens = usage["completion_tokens"]

        return content, output_tokens

    def parse_stream_chunk(self, payload: dict[str, Any]) -> tuple[str, int | None, bool]:
        choices = payload.get("choices")
        text_piece = ""
        finished = False

        if isinstance(choices, list) and choices:
            first = choices[0]
            if isinstance(first, dict):
                delta = first.get("delta")
                if isinstance(delta, dict) and isinstance(delta.get("content"), str):
                    text_piece = delta["content"]
                if first.get("finish_reason") is not None:
                    finished = True

        usage = payload.get("usage")
        output_tokens = None
        if isinstance(usage, dict) and isinstance(usage.get("completion_tokens"), int):
            output_tokens = usage["completion_tokens"]

        return text_piece, output_tokens, finished
