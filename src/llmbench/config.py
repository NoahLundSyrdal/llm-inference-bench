from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from llmbench.models import RunConfig, WorkloadConfig


class ConfigError(ValueError):
    """Raised when benchmark config is invalid or cannot be loaded."""


def load_run_config(config_path: str | Path) -> RunConfig:
    path = Path(config_path).expanduser()
    if not path.exists():
        msg = f"Config file not found: {path}"
        raise ConfigError(msg)

    try:
        raw: dict[str, Any] | None = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        msg = f"Invalid YAML in config file: {path}"
        raise ConfigError(msg) from exc

    if raw is None:
        msg = f"Config file is empty: {path}"
        raise ConfigError(msg)

    try:
        config = RunConfig.model_validate(raw)
    except ValidationError as exc:
        msg = f"Config validation failed for: {path}"
        raise ConfigError(msg) from exc

    return resolve_config_paths(config, base_dir=path.parent)


def resolve_config_paths(config: RunConfig, base_dir: Path) -> RunConfig:
    workload: WorkloadConfig = config.workload

    if workload.prompts_file is not None:
        prompts_file = workload.prompts_file
        if not prompts_file.is_absolute():
            prompts_file = (base_dir / prompts_file).resolve()
        workload = workload.model_copy(update={"prompts_file": prompts_file})

    output_dir = config.output_dir
    if not output_dir.is_absolute():
        output_dir = (base_dir / output_dir).resolve()

    return config.model_copy(update={"workload": workload, "output_dir": output_dir})


def save_config_snapshot(config: RunConfig, output_path: str | Path) -> None:
    path = Path(output_path)
    path.write_text(
        yaml.safe_dump(config.model_dump(mode="json"), sort_keys=False),
        encoding="utf-8",
    )
