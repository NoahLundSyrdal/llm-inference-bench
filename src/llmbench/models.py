from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class BackendConfig(BaseModel):
    engine: Literal["vllm"] = "vllm"
    base_url: str = "http://localhost:8000"
    model: str
    api_key: str | None = None
    endpoint: str = "/v1/chat/completions"
    extra_headers: dict[str, str] = Field(default_factory=dict)

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, value: str) -> str:
        if not value.startswith(("http://", "https://")):
            msg = "backend.base_url must start with http:// or https://"
            raise ValueError(msg)
        return value.rstrip("/")

    @field_validator("model")
    @classmethod
    def validate_model(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            msg = "backend.model must be non-empty"
            raise ValueError(msg)
        return cleaned

    @field_validator("endpoint")
    @classmethod
    def validate_endpoint(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned.startswith("/"):
            msg = "backend.endpoint must start with '/'"
            raise ValueError(msg)
        return cleaned


class GenerationConfig(BaseModel):
    max_tokens: int = Field(default=128, ge=1)
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    top_p: float = Field(default=1.0, gt=0.0, le=1.0)
    stream: bool = False
    request_timeout_s: float = Field(default=45.0, gt=0.0)


class WorkloadConfig(BaseModel):
    label: str = "quickstart"
    prompts_file: Path | None = None
    prompt_field: str = "prompt"
    num_requests: int = Field(default=32, ge=1)
    synthetic_count: int = Field(default=0, ge=0)
    synthetic_prompt_template: str = (
        "Summarize a practical tip for reducing LLM inference latency. (sample={i})"
    )
    shuffle: bool = True
    seed: int = 42

    @model_validator(mode="after")
    def validate_prompt_source(self) -> WorkloadConfig:
        if self.prompts_file is None and self.synthetic_count == 0:
            msg = "workload requires prompts_file or synthetic_count > 0"
            raise ValueError(msg)
        return self


class RunConfig(BaseModel):
    name: str = "local-vllm"
    backend: BackendConfig
    generation: GenerationConfig = Field(default_factory=GenerationConfig)
    workload: WorkloadConfig
    concurrency_sweep: list[int] = Field(default_factory=lambda: [1, 4, 8])
    repetitions: int = Field(default=1, ge=1)
    output_dir: Path = Path("outputs")
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            msg = "name must be non-empty"
            raise ValueError(msg)
        return cleaned

    @field_validator("concurrency_sweep")
    @classmethod
    def validate_concurrency_sweep(cls, values: list[int]) -> list[int]:
        if not values:
            msg = "concurrency_sweep cannot be empty"
            raise ValueError(msg)

        deduped: list[int] = []
        for value in values:
            if value < 1:
                msg = "concurrency values must be >= 1"
                raise ValueError(msg)
            if value not in deduped:
                deduped.append(value)
        return deduped


class RequestRecord(BaseModel):
    request_id: str
    run_id: str
    run_name: str
    workload_label: str
    repetition: int
    concurrency: int
    prompt_index: int
    prompt: str
    engine: str
    model: str
    stream: bool
    started_at: datetime
    ended_at: datetime
    latency_ms: float = Field(ge=0.0)
    ttft_ms: float | None = Field(default=None, ge=0.0)
    completion_time_ms: float = Field(ge=0.0)
    output_tokens: int = Field(ge=0)
    output_tokens_estimated: bool
    tokens_per_sec: float | None = Field(default=None, ge=0.0)
    success: bool
    status_code: int | None = None
    error_type: str | None = None
    error_message: str | None = None


class RunMetadata(BaseModel):
    run_id: str
    run_name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    engine: str
    model: str
    python_version: str
    platform: str
    config: dict[str, Any]
    git_commit: str | None = None
