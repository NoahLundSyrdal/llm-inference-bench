from __future__ import annotations

from pathlib import Path

import pandas as pd

from llmbench.backends.base import BackendResult, BaseBackendAdapter
from llmbench.io_utils import read_jsonl
from llmbench.models import BackendConfig, GenerationConfig, RunConfig, WorkloadConfig
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
        return BackendResult(
            output_text=f"response to: {prompt}",
            output_tokens=4,
            output_tokens_estimated=False,
            ttft_ms=5.0 if generation.stream else None,
            status_code=200,
        )


def test_runner_writes_expected_artifacts(tmp_path: Path) -> None:
    config = RunConfig(
        name="unit-runner",
        backend=BackendConfig(
            engine="vllm",
            base_url="http://localhost:9999",
            model="dummy-model",
        ),
        generation=GenerationConfig(max_tokens=8, stream=True, request_timeout_s=5),
        workload=WorkloadConfig(label="synthetic", synthetic_count=2, num_requests=6),
        concurrency_sweep=[1, 3],
        repetitions=2,
        output_dir=tmp_path,
    )

    runner = BenchmarkRunner(backend_override=DummyBackendAdapter(base_url="http://x", model="m"))
    run_dir = runner.run(config)

    assert (run_dir / "raw_requests.jsonl").exists()
    assert (run_dir / "raw_requests.csv").exists()
    assert (run_dir / "aggregated.csv").exists()
    assert (run_dir / "summary.md").exists()
    assert (run_dir / "run_metadata.json").exists()
    assert (run_dir / "latency_vs_concurrency.png").exists()

    rows = read_jsonl(run_dir / "raw_requests.jsonl")
    expected_requests = config.workload.num_requests * len(config.concurrency_sweep) * config.repetitions
    assert len(rows) == expected_requests

    summary = pd.read_csv(run_dir / "aggregated.csv")
    assert set(summary["concurrency"].tolist()) == {1, 3}
