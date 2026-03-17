from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pandas as pd

from llmbench.backends.base import BackendResult, BaseBackendAdapter
from llmbench.campaign import CampaignRunner, load_campaign_config
from llmbench.models import GenerationConfig
from llmbench.runner import BenchmarkRunner


class DummyBackendAdapter(BaseBackendAdapter):
    engine_name = "dummy"

    async def check_connection(self, client) -> None:  # type: ignore[override]
        return None

    def build_payload(self, prompt: str, generation: GenerationConfig) -> dict[str, object]:
        return {"prompt": prompt}

    def parse_non_stream_response(self, payload: dict[str, object]) -> tuple[str, int | None]:
        return "ok", 2

    def parse_stream_chunk(self, payload: dict[str, object]) -> tuple[str, int | None, bool]:
        return "ok", 2, True

    async def generate(self, client, prompt, generation):  # type: ignore[override]
        if generation.stream:
            await asyncio.sleep(0.03)
        return BackendResult(
            output_text=f"response to: {prompt}",
            output_tokens=4,
            output_tokens_estimated=False,
            ttft_ms=5.0 if generation.stream else None,
            status_code=200,
        )


def _write_base_run_config(tmp_path: Path) -> Path:
    prompts_path = tmp_path / "prompts.json"
    prompts_path.write_text('[{"prompt": "hello"}]', encoding="utf-8")

    run_config_path = tmp_path / "base_run.yaml"
    run_config_path.write_text(
        "\n".join(
            [
                "name: campaign-unit",
                "backend:",
                "  engine: vllm",
                "  base_url: http://localhost:8000",
                "  model: test-model",
                "generation:",
                "  max_tokens: 16",
                "  stream: false",
                "workload:",
                "  label: unit",
                "  prompts_file: prompts.json",
                "  prompt_field: prompt",
                "  num_requests: 4",
                "concurrency_sweep: [1, 2]",
                "repetitions: 1",
                "output_dir: run_outputs",
            ]
        ),
        encoding="utf-8",
    )
    return run_config_path


def test_load_campaign_config_expands_matrix(tmp_path: Path) -> None:
    run_config_path = _write_base_run_config(tmp_path)
    campaign_path = tmp_path / "campaign.yaml"
    campaign_path.write_text(
        "\n".join(
            [
                "name: matrix-campaign",
                "output_dir: campaign-results",
                "matrix:",
                "  vllm_version: ['0.14', '0.15']",
                "  hardware: ['cpu', 'cuda']",
                "experiment_template:",
                "  name: run-{vllm_version}-{hardware}",
                f"  config_path: {run_config_path.name}",
                "  tags:",
                "    scheduler: default",
            ]
        ),
        encoding="utf-8",
    )

    config = load_campaign_config(campaign_path)

    assert len(config.experiments) == 4
    assert config.output_dir == (tmp_path / "campaign-results").resolve()
    names = {exp.name for exp in config.experiments}
    assert names == {
        "run-0.14-cpu",
        "run-0.14-cuda",
        "run-0.15-cpu",
        "run-0.15-cuda",
    }
    for experiment in config.experiments:
        assert experiment.config_path == run_config_path.resolve()
        assert "vllm_version" in experiment.tags
        assert "hardware" in experiment.tags
        assert experiment.tags["scheduler"] == "default"


def test_campaign_runner_writes_summary_and_metadata_tags(tmp_path: Path) -> None:
    run_config_path = _write_base_run_config(tmp_path)
    campaign_path = tmp_path / "campaign.yaml"
    campaign_path.write_text(
        "\n".join(
            [
                "name: explicit-campaign",
                "output_dir: campaign-results",
                "baseline:",
                "  version: '0.15.0'",
                "throughput_drop_pct_threshold: 1",
                "latency_p95_increase_pct_threshold: 1",
                "experiments:",
                "  - name: v014-cpu",
                f"    config_path: {run_config_path.name}",
                "    tags:",
                "      version: '0.15.0'",
                "      hardware: cpu",
                "  - name: v015-gpu",
                f"    config_path: {run_config_path.name}",
                "    generation_overrides:",
                "      stream: true",
                "    tags:",
                "      version: main",
                "      hardware: cpu",
            ]
        ),
        encoding="utf-8",
    )

    campaign_config = load_campaign_config(campaign_path)
    campaign_runner = CampaignRunner(
        benchmark_runner=BenchmarkRunner(
            backend_override=DummyBackendAdapter(base_url="http://x", model="m")
        )
    )
    campaign_dir = campaign_runner.run(campaign_config, max_workers=2)

    summary_csv = campaign_dir / "campaign_runs.csv"
    report_md = campaign_dir / "campaign_report.md"
    assert summary_csv.exists()
    assert report_md.exists()

    summary = pd.read_csv(summary_csv)
    assert len(summary) == 2
    assert set(summary["status"].tolist()) == {"ok"}
    assert "peak_throughput_tokens_per_s" in summary.columns
    assert set(summary["tag_version"].astype(str).tolist()) == {"0.15.0", "main"}
    assert {"git_sha", "vllm_commit", "torch_version", "cpu_model", "num_threads"}.issubset(
        set(summary.columns)
    )
    assert set(summary["vllm_commit"].astype(str).tolist()) == {"0.15.0", "main"}
    assert summary["num_threads"].astype(int).min() >= 1

    run_dir = Path(summary.iloc[0]["run_dir"])
    metadata_path = run_dir / "run_metadata.json"
    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata = payload["config"]["metadata"]
    assert metadata["campaign_name"] == "explicit-campaign"
    assert metadata["experiment_name"] in {"v014-cpu", "v015-gpu"}
    assert isinstance(metadata["experiment_tags"], dict)

    report = report_md.read_text(encoding="utf-8")
    assert "Regression checks" in report
    assert "Regression detected" in report
