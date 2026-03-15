from __future__ import annotations

from pathlib import Path

import pytest

from llmbench.config import ConfigError, load_run_config


def test_load_run_config_resolves_relative_paths(tmp_path: Path) -> None:
    prompts_path = tmp_path / "prompts.json"
    prompts_path.write_text('[{"prompt": "hello"}]', encoding="utf-8")

    config_dir = tmp_path / "configs"
    config_dir.mkdir()
    config_path = config_dir / "run.yaml"
    config_path.write_text(
        "\n".join(
            [
                "name: test-run",
                "backend:",
                "  engine: vllm",
                "  base_url: http://localhost:8000",
                "  model: test-model",
                "generation:",
                "  max_tokens: 16",
                "  stream: false",
                "workload:",
                "  label: unit",
                "  prompts_file: ../prompts.json",
                "  prompt_field: prompt",
                "  num_requests: 3",
                "concurrency_sweep: [1, 2, 2]",
                "repetitions: 1",
                "output_dir: ../outputs",
            ]
        ),
        encoding="utf-8",
    )

    config = load_run_config(config_path)

    assert config.workload.prompts_file == prompts_path.resolve()
    assert config.output_dir == (tmp_path / "outputs").resolve()
    assert config.concurrency_sweep == [1, 2]


def test_load_run_config_raises_when_workload_source_missing(tmp_path: Path) -> None:
    config_path = tmp_path / "bad.yaml"
    config_path.write_text(
        "\n".join(
            [
                "name: bad-run",
                "backend:",
                "  engine: vllm",
                "  base_url: http://localhost:8000",
                "  model: test-model",
                "workload:",
                "  label: empty",
                "  num_requests: 4",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ConfigError):
        load_run_config(config_path)
