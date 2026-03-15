from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

from llmbench.models import WorkloadConfig


class WorkloadError(ValueError):
    """Raised when prompts cannot be loaded or interpreted."""


def load_prompts(workload: WorkloadConfig) -> list[str]:
    prompts: list[str] = []

    if workload.prompts_file is not None:
        prompts.extend(_load_prompts_from_file(workload.prompts_file, workload.prompt_field))

    if workload.synthetic_count > 0:
        prompts.extend(_build_synthetic_prompts(workload.synthetic_prompt_template, workload.synthetic_count))

    prompts = [prompt.strip() for prompt in prompts if prompt and prompt.strip()]
    if not prompts:
        msg = "No prompts available after loading workload sources"
        raise WorkloadError(msg)

    return prompts


def materialize_request_prompts(
    source_prompts: list[str],
    num_requests: int,
    shuffle: bool = False,
    seed: int = 1337,
) -> list[str]:
    if not source_prompts:
        msg = "source_prompts cannot be empty"
        raise WorkloadError(msg)
    if num_requests < 1:
        msg = "num_requests must be >= 1"
        raise WorkloadError(msg)

    prompts = source_prompts.copy()
    if shuffle:
        rng = random.Random(seed)
        rng.shuffle(prompts)

    repeated: list[str] = []
    for index in range(num_requests):
        repeated.append(prompts[index % len(prompts)])
    return repeated


def _load_prompts_from_file(path: Path, prompt_field: str) -> list[str]:
    if not path.exists():
        msg = f"Prompts file not found: {path}"
        raise WorkloadError(msg)

    if path.suffix.lower() == ".jsonl":
        return _load_jsonl_prompts(path, prompt_field)

    if path.suffix.lower() == ".json":
        return _load_json_prompts(path, prompt_field)

    msg = f"Unsupported prompts file format: {path.suffix}"
    raise WorkloadError(msg)


def _load_json_prompts(path: Path, prompt_field: str) -> list[str]:
    try:
        payload = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        msg = f"Failed to parse JSON prompts file: {path}"
        raise WorkloadError(msg) from exc

    if not isinstance(payload, list):
        msg = f"JSON prompts file must contain a list: {path}"
        raise WorkloadError(msg)

    prompts: list[str] = []
    for item in payload:
        prompt = _extract_prompt(item, prompt_field)
        if prompt is not None:
            prompts.append(prompt)
    return prompts


def _load_jsonl_prompts(path: Path, prompt_field: str) -> list[str]:
    prompts: list[str] = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            item: Any = json.loads(line)
        except json.JSONDecodeError as exc:
            msg = f"Invalid JSONL line in prompts file: {path}"
            raise WorkloadError(msg) from exc
        prompt = _extract_prompt(item, prompt_field)
        if prompt is not None:
            prompts.append(prompt)
    return prompts


def _extract_prompt(item: Any, prompt_field: str) -> str | None:
    if isinstance(item, str):
        return item

    if isinstance(item, dict):
        prompt_value = item.get(prompt_field)
        if isinstance(prompt_value, str):
            return prompt_value

        messages = item.get("messages")
        if isinstance(messages, list):
            parts: list[str] = []
            for message in messages:
                if isinstance(message, dict) and isinstance(message.get("content"), str):
                    parts.append(message["content"])
            if parts:
                return "\n".join(parts)

    return None


def _build_synthetic_prompts(template: str, count: int) -> list[str]:
    return [template.format(i=index + 1) for index in range(count)]
