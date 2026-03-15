from __future__ import annotations

import asyncio
import platform
import sys
import time
import uuid
from pathlib import Path

import httpx

from llmbench.backends import BackendConnectionError, BaseBackendAdapter, build_backend
from llmbench.config import save_config_snapshot
from llmbench.io_utils import (
    append_jsonl,
    create_run_directory,
    detect_git_commit,
    timestamp_slug,
    utc_now,
    write_json,
)
from llmbench.metrics import aggregate_metrics, records_to_dataframe, top_failure_modes
from llmbench.models import RequestRecord, RunConfig, RunMetadata
from llmbench.plotting import generate_plots
from llmbench.reporting import generate_summary_markdown
from llmbench.workloads import load_prompts, materialize_request_prompts


async def check_backend(config: RunConfig) -> None:
    backend = build_backend(config.backend)
    async with httpx.AsyncClient(base_url=config.backend.base_url, timeout=None, follow_redirects=True) as client:
        await backend.check_connection(client)


class BenchmarkRunner:
    def __init__(self, backend_override: BaseBackendAdapter | None = None) -> None:
        self.backend_override = backend_override

    def run(self, config: RunConfig) -> Path:
        return asyncio.run(self.run_async(config))

    async def run_async(self, config: RunConfig) -> Path:
        run_id = timestamp_slug()
        run_dir = create_run_directory(config.output_dir, config.name, run_id)
        raw_jsonl_path = run_dir / "raw_requests.jsonl"

        backend = self.backend_override or build_backend(config.backend)
        metadata = RunMetadata(
            run_id=run_id,
            run_name=config.name,
            engine=backend.engine_name,
            model=config.backend.model,
            python_version=sys.version.split()[0],
            platform=platform.platform(),
            config=config.model_dump(mode="json"),
            git_commit=detect_git_commit(Path.cwd()),
        )
        write_json(run_dir / "run_metadata.json", metadata.model_dump(mode="json"))
        save_config_snapshot(config, run_dir / "config_snapshot.yaml")

        source_prompts = load_prompts(config.workload)
        all_records: list[RequestRecord] = []

        async with httpx.AsyncClient(base_url=config.backend.base_url, timeout=None, follow_redirects=True) as client:
            try:
                await backend.check_connection(client)
            except BackendConnectionError:
                raise

            for repetition in range(1, config.repetitions + 1):
                for concurrency in config.concurrency_sweep:
                    prompts = materialize_request_prompts(
                        source_prompts=source_prompts,
                        num_requests=config.workload.num_requests,
                        shuffle=config.workload.shuffle,
                        seed=config.workload.seed + repetition + concurrency,
                    )
                    records = await self._run_scenario(
                        config=config,
                        client=client,
                        backend=backend,
                        prompts=prompts,
                        run_id=run_id,
                        repetition=repetition,
                        concurrency=concurrency,
                        raw_jsonl_path=raw_jsonl_path,
                    )
                    all_records.extend(records)

        records_df = records_to_dataframe(all_records)
        records_df.to_csv(run_dir / "raw_requests.csv", index=False)

        summary_df = aggregate_metrics(records_df)
        summary_df.to_csv(run_dir / "aggregated.csv", index=False)

        failures_df = top_failure_modes(records_df)
        failures_df.to_csv(run_dir / "failures.csv", index=False)

        plot_paths = generate_plots(summary_df, run_dir)
        report = generate_summary_markdown(
            metadata=metadata.model_dump(mode="json"),
            summary_df=summary_df,
            failure_df=failures_df,
            plot_paths=plot_paths,
        )
        (run_dir / "summary.md").write_text(report, encoding="utf-8")

        return run_dir

    async def _run_scenario(
        self,
        config: RunConfig,
        client: httpx.AsyncClient,
        backend: BaseBackendAdapter,
        prompts: list[str],
        run_id: str,
        repetition: int,
        concurrency: int,
        raw_jsonl_path: Path,
    ) -> list[RequestRecord]:
        sem = asyncio.Semaphore(concurrency)
        write_lock = asyncio.Lock()

        tasks = [
            self._execute_request(
                config=config,
                client=client,
                backend=backend,
                sem=sem,
                write_lock=write_lock,
                raw_jsonl_path=raw_jsonl_path,
                run_id=run_id,
                repetition=repetition,
                concurrency=concurrency,
                prompt_index=i,
                prompt=prompt,
            )
            for i, prompt in enumerate(prompts)
        ]
        return await asyncio.gather(*tasks)

    async def _execute_request(
        self,
        config: RunConfig,
        client: httpx.AsyncClient,
        backend: BaseBackendAdapter,
        sem: asyncio.Semaphore,
        write_lock: asyncio.Lock,
        raw_jsonl_path: Path,
        run_id: str,
        repetition: int,
        concurrency: int,
        prompt_index: int,
        prompt: str,
    ) -> RequestRecord:
        async with sem:
            request_id = str(uuid.uuid4())
            started_at = utc_now()
            start = time.perf_counter()

            try:
                result = await backend.generate(client=client, prompt=prompt, generation=config.generation)
                ended_at = utc_now()
                total_ms = (time.perf_counter() - start) * 1000.0
                tokens_per_sec = (
                    result.output_tokens / (total_ms / 1000.0)
                    if result.output_tokens > 0 and total_ms > 0
                    else 0.0
                )

                record = RequestRecord(
                    request_id=request_id,
                    run_id=run_id,
                    run_name=config.name,
                    workload_label=config.workload.label,
                    repetition=repetition,
                    concurrency=concurrency,
                    prompt_index=prompt_index,
                    prompt=prompt,
                    engine=backend.engine_name,
                    model=config.backend.model,
                    stream=config.generation.stream,
                    started_at=started_at,
                    ended_at=ended_at,
                    latency_ms=total_ms,
                    ttft_ms=result.ttft_ms,
                    completion_time_ms=total_ms,
                    output_tokens=result.output_tokens,
                    output_tokens_estimated=result.output_tokens_estimated,
                    tokens_per_sec=tokens_per_sec,
                    success=True,
                    status_code=result.status_code,
                )
            except Exception as exc:  # noqa: BLE001
                ended_at = utc_now()
                total_ms = (time.perf_counter() - start) * 1000.0
                status_code = exc.response.status_code if isinstance(exc, httpx.HTTPStatusError) else None

                record = RequestRecord(
                    request_id=request_id,
                    run_id=run_id,
                    run_name=config.name,
                    workload_label=config.workload.label,
                    repetition=repetition,
                    concurrency=concurrency,
                    prompt_index=prompt_index,
                    prompt=prompt,
                    engine=backend.engine_name,
                    model=config.backend.model,
                    stream=config.generation.stream,
                    started_at=started_at,
                    ended_at=ended_at,
                    latency_ms=total_ms,
                    ttft_ms=None,
                    completion_time_ms=total_ms,
                    output_tokens=0,
                    output_tokens_estimated=False,
                    tokens_per_sec=0.0,
                    success=False,
                    status_code=status_code,
                    error_type=type(exc).__name__,
                    error_message=str(exc),
                )

            async with write_lock:
                append_jsonl(raw_jsonl_path, record.model_dump(mode="json"))

            return record
