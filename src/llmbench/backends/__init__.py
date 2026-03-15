from llmbench.backends.base import (
    BackendConnectionError,
    BackendFeatureNotSupportedError,
    BackendResponseParseError,
    BackendResult,
    BaseBackendAdapter,
)
from llmbench.backends.vllm import VLLMBackendAdapter
from llmbench.models import BackendConfig


def build_backend(config: BackendConfig) -> BaseBackendAdapter:
    return VLLMBackendAdapter(
        base_url=config.base_url,
        model=config.model,
        api_key=config.api_key,
        endpoint=config.endpoint,
        extra_headers=config.extra_headers,
    )


__all__ = [
    "BackendConnectionError",
    "BackendFeatureNotSupportedError",
    "BackendResponseParseError",
    "BackendResult",
    "BaseBackendAdapter",
    "VLLMBackendAdapter",
    "build_backend",
]
