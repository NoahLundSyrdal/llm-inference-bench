from __future__ import annotations

import asyncio
import itertools
import json
import os
import shlex
import subprocess
import time
from pathlib import Path
from typing import Any

import pandas as pd
import yaml
from pydantic import BaseModel, Field, ValidationError

from llmbench.config import ConfigError, load_run_config
from llmbench.io_utils import create_run_directory, sanitize_name, timestamp_slug, write_json
from llmbench.runner import BenchmarkRunner, check_backend


class CampaignServerConfig(BaseModel):
    command: str
    cwd: Path | None = None
    startup_grace_s: float = Field(default=1.0, ge=0.0)
    ready_check_retries: int = Field(default=60, ge=1)
    ready_check_interval_s: float = Field(default=2.0, gt=0.0)
    shutdown_grace_s: float = Field(default=5.0, ge=0.0)


class CampaignExperimentConfig(BaseModel):
    name: str
    config_path: Path
    tags: dict[str, str | int | float | bool] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    backend_base_url: str | None = None
    backend_model: str | None = None
    generation_overrides: dict[str, Any] = Field(default_factory=dict)
    concurrency_sweep: list[int] | None = None
    repetitions: int | None = Field(default=None, ge=1)
    output_dir: Path | None = None
    server: CampaignServerConfig | None = None


class CampaignTemplateConfig(BaseModel):
    name: str
    config_path: str
    tags: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    backend_base_url: str | None = None
    backend_model: str | None = None
    generation_overrides: dict[str, Any] = Field(default_factory=dict)
    concurrency_sweep: list[int] | None = None
    repetitions: int | None = Field(default=None, ge=1)
    output_dir: str | None = None
    server: dict[str, Any] | None = None


class CampaignConfig(BaseModel):
    name: str
    output_dir: Path = Path("results/campaigns")
    continue_on_error: bool = False
    baseline: dict[str, str | int | float | bool] | None = None
    throughput_drop_pct_threshold: float = Field(default=10.0, ge=0.0)
    latency_p95_increase_pct_threshold: float = Field(default=15.0, ge=0.0)
    experiments: list[CampaignExperimentConfig] = Field(default_factory=list)


def load_campaign_config(config_path: str | Path) -> CampaignConfig:
    path = Path(config_path).expanduser()
    if not path.exists():
        msg = f"Campaign config file not found: {path}"
        raise ConfigError(msg)

    try:
        raw: dict[str, Any] | None = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        msg = f"Invalid YAML in campaign config file: {path}"
        raise ConfigError(msg) from exc

    if raw is None:
        msg = f"Campaign config file is empty: {path}"
        raise ConfigError(msg)

    experiments: list[dict[str, Any]] = list(raw.get("experiments", []))
    matrix = raw.get("matrix")
    template = raw.get("experiment_template")
    if matrix is not None or template is not None:
        experiments.extend(_expand_matrix_experiments(matrix=matrix, template=template))

    payload = {
        "name": raw.get("name", "campaign"),
        "output_dir": raw.get("output_dir", "results/campaigns"),
        "continue_on_error": raw.get("continue_on_error", False),
        "baseline": raw.get("baseline"),
        "throughput_drop_pct_threshold": raw.get("throughput_drop_pct_threshold", 10.0),
        "latency_p95_increase_pct_threshold": raw.get("latency_p95_increase_pct_threshold", 15.0),
        "experiments": experiments,
    }
    try:
        config = CampaignConfig.model_validate(payload)
    except ValidationError as exc:
        msg = f"Campaign config validation failed for: {path}"
        raise ConfigError(msg) from exc

    if not config.experiments:
        msg = "campaign requires at least one experiment"
        raise ConfigError(msg)

    return _resolve_campaign_paths(config, base_dir=path.parent)


def _expand_matrix_experiments(
    matrix: Any,
    template: Any,
) -> list[dict[str, Any]]:
    if matrix is None or template is None:
        msg = "campaign matrix expansion requires both 'matrix' and 'experiment_template'"
        raise ConfigError(msg)

    if not isinstance(matrix, dict) or not matrix:
        msg = "campaign matrix must be a non-empty map"
        raise ConfigError(msg)

    matrix_keys = list(matrix.keys())
    matrix_values: list[list[Any]] = []
    for key in matrix_keys:
        values = matrix[key]
        if not isinstance(values, list) or not values:
            msg = f"matrix axis '{key}' must be a non-empty list"
            raise ConfigError(msg)
        matrix_values.append(values)

    try:
        parsed_template = CampaignTemplateConfig.model_validate(template)
    except ValidationError as exc:
        msg = "campaign experiment_template validation failed"
        raise ConfigError(msg) from exc

    experiments: list[dict[str, Any]] = []
    for combination in itertools.product(*matrix_values):
        context = dict(zip(matrix_keys, combination, strict=True))
        rendered = _render_value(parsed_template.model_dump(mode="python"), context=context)
        rendered_tags = rendered.get("tags", {})
        if isinstance(rendered_tags, dict):
            rendered["tags"] = {**context, **rendered_tags}
        experiments.append(rendered)
    return experiments


def _render_value(value: Any, context: dict[str, Any]) -> Any:
    if isinstance(value, str):
        try:
            return value.format(**context)
        except KeyError as exc:
            msg = f"Missing matrix variable in template: {exc.args[0]}"
            raise ConfigError(msg) from exc
    if isinstance(value, list):
        return [_render_value(item, context=context) for item in value]
    if isinstance(value, dict):
        return {key: _render_value(item, context=context) for key, item in value.items()}
    return value


def _resolve_campaign_paths(config: CampaignConfig, base_dir: Path) -> CampaignConfig:
    campaign_output_dir = config.output_dir
    if not campaign_output_dir.is_absolute():
        campaign_output_dir = (base_dir / campaign_output_dir).resolve()

    experiments: list[CampaignExperimentConfig] = []
    for experiment in config.experiments:
        config_path = experiment.config_path
        if not config_path.is_absolute():
            config_path = (base_dir / config_path).resolve()

        output_dir = experiment.output_dir
        if output_dir is not None and not output_dir.is_absolute():
            output_dir = (base_dir / output_dir).resolve()

        server = experiment.server
        if server is not None and server.cwd is not None and not server.cwd.is_absolute():
            server = server.model_copy(update={"cwd": (base_dir / server.cwd).resolve()})

        experiments.append(
            experiment.model_copy(
                update={"config_path": config_path, "output_dir": output_dir, "server": server}
            )
        )

    return config.model_copy(update={"output_dir": campaign_output_dir, "experiments": experiments})


class CampaignRunner:
    def __init__(self, benchmark_runner: BenchmarkRunner | None = None) -> None:
        self.benchmark_runner = benchmark_runner or BenchmarkRunner()
        self._runtime_probe_cache: dict[str, dict[str, Any]] = {}

    def run(self, config: CampaignConfig, *, dry_run: bool = False, max_workers: int = 1) -> Path:
        if max_workers < 1:
            msg = "max_workers must be >= 1"
            raise ValueError(msg)
        campaign_run_id = timestamp_slug()
        campaign_dir = create_run_directory(config.output_dir, config.name, campaign_run_id)
        if dry_run:
            self._write_dry_run_plan(config=config, campaign_dir=campaign_dir, max_workers=max_workers)
            return campaign_dir

        records = self._run_experiments(
            campaign=config,
            campaign_run_id=campaign_run_id,
            campaign_dir=campaign_dir,
            max_workers=max_workers,
        )

        self._write_campaign_outputs(campaign=config, campaign_dir=campaign_dir, records=records)
        failures = [record for record in records if record["status"] == "failed"]
        if failures and not config.continue_on_error:
            first_error = failures[0].get("error", "unknown error")
            msg = f"Campaign stopped after failure: {first_error}"
            raise RuntimeError(msg)

        return campaign_dir

    def _run_experiments(
        self,
        *,
        campaign: CampaignConfig,
        campaign_run_id: str,
        campaign_dir: Path,
        max_workers: int,
    ) -> list[dict[str, Any]]:
        if max_workers == 1:
            records: list[dict[str, Any]] = []
            for experiment in campaign.experiments:
                row = self._run_experiment(
                    campaign=campaign,
                    campaign_run_id=campaign_run_id,
                    campaign_dir=campaign_dir,
                    experiment=experiment,
                )
                records.append(row)
                if row["status"] == "failed" and not campaign.continue_on_error:
                    break
            return records

        return asyncio.run(
            self._run_experiments_parallel(
                campaign=campaign,
                campaign_run_id=campaign_run_id,
                campaign_dir=campaign_dir,
                max_workers=max_workers,
            )
        )

    async def _run_experiments_parallel(
        self,
        *,
        campaign: CampaignConfig,
        campaign_run_id: str,
        campaign_dir: Path,
        max_workers: int,
    ) -> list[dict[str, Any]]:
        indexed = list(enumerate(campaign.experiments))
        collected: list[tuple[int, dict[str, Any]]] = []

        for batch_start in range(0, len(indexed), max_workers):
            batch = indexed[batch_start : batch_start + max_workers]
            tasks = [
                asyncio.to_thread(
                    self._run_experiment,
                    campaign=campaign,
                    campaign_run_id=campaign_run_id,
                    campaign_dir=campaign_dir,
                    experiment=experiment,
                )
                for _, experiment in batch
            ]
            rows = await asyncio.gather(*tasks)
            for (index, _), row in zip(batch, rows, strict=True):
                collected.append((index, row))

            if not campaign.continue_on_error and any(row["status"] == "failed" for row in rows):
                break

        collected.sort(key=lambda item: item[0])
        return [row for _, row in collected]

    def _run_experiment(
        self,
        *,
        campaign: CampaignConfig,
        campaign_run_id: str,
        campaign_dir: Path,
        experiment: CampaignExperimentConfig,
    ) -> dict[str, Any]:
        run_output_dir = (
            experiment.output_dir
            if experiment.output_dir is not None
            else campaign_dir / "runs" / sanitize_name(experiment.name)
        )

        merged_tags = dict(experiment.tags)
        base_record = {
            "campaign_name": campaign.name,
            "campaign_run_id": campaign_run_id,
            "experiment_name": experiment.name,
            "status": "failed",
            "run_dir": "",
            "error": "",
            **{f"tag_{key}": value for key, value in merged_tags.items()},
            **self._base_repro_fields(),
        }

        process: subprocess.Popen[str] | None = None
        log_handle = None
        server_log_path: Path | None = None
        try:
            run_config = load_run_config(experiment.config_path)
            backend_updates: dict[str, Any] = {}
            if experiment.backend_base_url is not None:
                backend_updates["base_url"] = experiment.backend_base_url
            if experiment.backend_model is not None:
                backend_updates["model"] = experiment.backend_model

            backend = (
                run_config.backend.model_copy(update=backend_updates)
                if backend_updates
                else run_config.backend
            )
            generation = (
                run_config.generation.model_copy(update=experiment.generation_overrides)
                if experiment.generation_overrides
                else run_config.generation
            )
            metadata = {
                **run_config.metadata,
                **experiment.metadata,
                "campaign_name": campaign.name,
                "campaign_run_id": campaign_run_id,
                "experiment_name": experiment.name,
                "experiment_tags": merged_tags,
            }
            run_name = f"{run_config.name}-{sanitize_name(experiment.name)}"
            run_config = run_config.model_copy(
                update={
                    "name": run_name,
                    "backend": backend,
                    "generation": generation,
                    "metadata": metadata,
                    "output_dir": run_output_dir,
                    "concurrency_sweep": (
                        experiment.concurrency_sweep
                        if experiment.concurrency_sweep is not None
                        else run_config.concurrency_sweep
                    ),
                    "repetitions": (
                        experiment.repetitions
                        if experiment.repetitions is not None
                        else run_config.repetitions
                    ),
                }
            )

            if experiment.server is not None:
                server_log_path = campaign_dir / "logs" / f"{sanitize_name(experiment.name)}.log"
                server_log_path.parent.mkdir(parents=True, exist_ok=True)
                log_handle = server_log_path.open("w", encoding="utf-8")
                process = subprocess.Popen(
                    experiment.server.command,
                    shell=True,
                    cwd=experiment.server.cwd,
                    stdout=log_handle,
                    stderr=subprocess.STDOUT,
                    text=True,
                )
                if experiment.server.startup_grace_s > 0:
                    time.sleep(experiment.server.startup_grace_s)
                self._wait_for_backend_ready(config=run_config, server=experiment.server, process=process)

            run_dir = self.benchmark_runner.run(run_config)
            record = {
                **base_record,
                "status": "ok",
                "run_dir": str(run_dir),
                "error": "",
            }
            record.update(self._extract_rollup_metrics(run_dir))
            record.update(
                self._collect_repro_metadata(
                    run_dir=run_dir,
                    experiment=experiment,
                    fallback_tags=merged_tags,
                )
            )
            if server_log_path is not None:
                record["server_log"] = str(server_log_path)
            return record
        except Exception as exc:  # noqa: BLE001
            record = {
                **base_record,
                "error": str(exc),
            }
            if server_log_path is not None:
                record["server_log"] = str(server_log_path)
            return record
        finally:
            if process is not None:
                process.terminate()
                try:
                    process.wait(
                        timeout=experiment.server.shutdown_grace_s if experiment.server is not None else 5.0
                    )
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            if log_handle is not None:
                log_handle.close()

    def _base_repro_fields(self) -> dict[str, Any]:
        return {
            "git_sha": "",
            "vllm_commit": "",
            "torch_version": "",
            "cpu_model": _detect_cpu_model(),
            "num_threads": os.cpu_count() or 0,
        }

    def _collect_repro_metadata(
        self,
        *,
        run_dir: Path,
        experiment: CampaignExperimentConfig,
        fallback_tags: dict[str, str | int | float | bool],
    ) -> dict[str, Any]:
        metadata = self._base_repro_fields()

        run_metadata_path = run_dir / "run_metadata.json"
        if run_metadata_path.exists():
            try:
                payload = json.loads(run_metadata_path.read_text(encoding="utf-8"))
                commit = payload.get("git_commit")
                if isinstance(commit, str):
                    metadata["git_sha"] = commit
            except json.JSONDecodeError:
                pass

        runtime_info = self._probe_runtime_metadata(
            server_command=experiment.server.command if experiment.server is not None else None
        )
        if runtime_info.get("torch_version"):
            metadata["torch_version"] = runtime_info["torch_version"]
        if runtime_info.get("vllm_commit"):
            metadata["vllm_commit"] = runtime_info["vllm_commit"]

        if not metadata["vllm_commit"]:
            version_value = fallback_tags.get("version", fallback_tags.get("vllm_version", ""))
            metadata["vllm_commit"] = str(version_value)

        return metadata

    def _probe_runtime_metadata(self, *, server_command: str | None) -> dict[str, Any]:
        if not server_command:
            return {}

        python_path = _infer_python_from_server_command(server_command)
        if python_path is None:
            return {}
        cache_key = str(python_path)
        if cache_key in self._runtime_probe_cache:
            return self._runtime_probe_cache[cache_key]

        if not python_path.exists():
            self._runtime_probe_cache[cache_key] = {}
            return {}

        script = (
            "import json\n"
            "info = {'torch_version': '', 'vllm_commit': ''}\n"
            "try:\n"
            "    import torch\n"
            "    info['torch_version'] = getattr(torch, '__version__', '') or ''\n"
            "except Exception:\n"
            "    pass\n"
            "try:\n"
            "    import vllm\n"
            "    commit = getattr(vllm, '__commit__', '') or ''\n"
            "    if not commit:\n"
            "        version = getattr(vllm, '__version__', '') or ''\n"
            "        if '+g' in version:\n"
            "            commit = version.split('+g', 1)[1]\n"
            "        else:\n"
            "            commit = version\n"
            "    info['vllm_commit'] = commit\n"
            "except Exception:\n"
            "    pass\n"
            "print(json.dumps(info))\n"
        )
        try:
            completed = subprocess.run(
                [str(python_path), "-c", script],
                capture_output=True,
                text=True,
                check=False,
            )
            if completed.returncode != 0:
                self._runtime_probe_cache[cache_key] = {}
                return {}
            payload = json.loads(completed.stdout.strip() or "{}")
            if isinstance(payload, dict):
                clean = {
                    "torch_version": str(payload.get("torch_version", "") or ""),
                    "vllm_commit": str(payload.get("vllm_commit", "") or ""),
                }
                self._runtime_probe_cache[cache_key] = clean
                return clean
        except (subprocess.SubprocessError, json.JSONDecodeError):
            pass

        self._runtime_probe_cache[cache_key] = {}
        return {}

    def _wait_for_backend_ready(
        self,
        *,
        config,
        server: CampaignServerConfig,
        process: subprocess.Popen[str],
    ) -> None:
        last_error: str | None = None
        for _ in range(server.ready_check_retries):
            if process.poll() is not None:
                msg = f"Server process exited early with code {process.returncode}"
                raise RuntimeError(msg)
            try:
                asyncio.run(check_backend(config))
                return
            except Exception as exc:  # noqa: BLE001
                last_error = str(exc)
                time.sleep(server.ready_check_interval_s)
        msg = f"Timed out waiting for backend readiness: {last_error or 'unknown error'}"
        raise RuntimeError(msg)

    def _extract_rollup_metrics(self, run_dir: Path) -> dict[str, Any]:
        summary_path = run_dir / "aggregated.csv"
        if not summary_path.exists():
            return {}

        frame = pd.read_csv(summary_path)
        if frame.empty:
            return {}

        max_idx = frame["concurrency"].idxmax()
        max_row = frame.loc[max_idx]
        return {
            "peak_throughput_tokens_per_s": float(frame["throughput_tokens_per_s_mean"].max()),
            "max_concurrency": int(max_row["concurrency"]),
            "latency_p95_at_max_concurrency": float(max_row["latency_ms_p95"]),
            "error_rate_at_max_concurrency": float(max_row["error_rate"]),
        }

    def _write_dry_run_plan(
        self,
        *,
        config: CampaignConfig,
        campaign_dir: Path,
        max_workers: int,
    ) -> None:
        plan = {
            "campaign_name": config.name,
            "output_dir": str(campaign_dir),
            "experiment_count": len(config.experiments),
            "max_workers": max_workers,
            "baseline": config.baseline,
            "throughput_drop_pct_threshold": config.throughput_drop_pct_threshold,
            "latency_p95_increase_pct_threshold": config.latency_p95_increase_pct_threshold,
            "experiments": [
                {
                    "name": experiment.name,
                    "config_path": str(experiment.config_path),
                    "tags": experiment.tags,
                    "server_command": experiment.server.command if experiment.server is not None else None,
                }
                for experiment in config.experiments
            ],
        }
        write_json(campaign_dir / "dry_run_plan.json", plan)

    def _write_campaign_outputs(
        self,
        *,
        campaign: CampaignConfig,
        campaign_dir: Path,
        records: list[dict[str, Any]],
    ) -> None:
        if not records:
            return

        frame = pd.DataFrame(records)
        frame.to_csv(campaign_dir / "campaign_runs.csv", index=False)
        report = _build_campaign_report(campaign=campaign, frame=frame)
        (campaign_dir / "campaign_report.md").write_text(report, encoding="utf-8")


def _build_campaign_report(*, campaign: CampaignConfig, frame: pd.DataFrame) -> str:
    lines = [
        f"# Campaign report: {campaign.name}",
        "",
        f"- Total experiments: {len(frame)}",
        f"- Successful: {(frame['status'] == 'ok').sum()}",
        f"- Failed: {(frame['status'] == 'failed').sum()}",
        "",
    ]

    lines.append("## Regression checks")
    lines.append("")
    regression_lines = _build_regression_section(campaign=campaign, frame=frame)
    lines.extend(regression_lines)
    lines.append("")

    success_frame = frame[frame["status"] == "ok"].copy()
    if not success_frame.empty:
        sorted_frame = success_frame.sort_values("peak_throughput_tokens_per_s", ascending=False)
        lines.append("## Top throughput runs")
        lines.append("")
        lines.extend(
            _frame_to_markdown_lines(
                sorted_frame[
                    [
                        "experiment_name",
                        "peak_throughput_tokens_per_s",
                        "latency_p95_at_max_concurrency",
                        "max_concurrency",
                    ]
                ].head(10)
            )
        )
        lines.append("")

    failure_frame = frame[frame["status"] == "failed"].copy()
    if not failure_frame.empty:
        lines.append("## Failures")
        lines.append("")
        lines.extend(_frame_to_markdown_lines(failure_frame[["experiment_name", "error"]]))
        lines.append("")

    lines.append("## Full campaign table")
    lines.append("")
    lines.extend(_frame_to_markdown_lines(frame))
    lines.append("")
    return "\n".join(lines)


def _build_regression_section(*, campaign: CampaignConfig, frame: pd.DataFrame) -> list[str]:
    if campaign.baseline is None:
        return ["- Not enabled (set `baseline` in campaign YAML)."]

    success_frame = frame[frame["status"] == "ok"].copy()
    if success_frame.empty:
        return ["- No successful runs available for regression checks."]

    findings = _detect_regressions(campaign=campaign, frame=success_frame)
    if findings is None:
        return ["- Baseline did not match any successful run rows."]
    if not findings:
        return [
            "- ✅ No regressions exceeded thresholds.",
            (
                f"- Thresholds: throughput drop > {campaign.throughput_drop_pct_threshold:.1f}% "
                f"or p95 latency increase > {campaign.latency_p95_increase_pct_threshold:.1f}%."
            ),
        ]

    lines = [
        "- ⚠ Regression detected.",
        (
            f"- Thresholds: throughput drop > {campaign.throughput_drop_pct_threshold:.1f}% "
            f"or p95 latency increase > {campaign.latency_p95_increase_pct_threshold:.1f}%."
        ),
        "",
    ]
    for finding in findings:
        lines.append(f"config: {finding['config']}")
        lines.append(f"metric: {finding['metric']}")
        lines.append(
            f"{finding['baseline_label']}: {finding['baseline_value']} | "
            f"{finding['compare_label']}: {finding['compare_value']} "
            f"({finding['delta']})"
        )
        lines.append("")
    if lines and not lines[-1]:
        lines.pop()
    return lines


def _detect_regressions(*, campaign: CampaignConfig, frame: pd.DataFrame) -> list[dict[str, str]] | None:
    tag_columns = [column for column in frame.columns if column.startswith("tag_")]
    baseline_columns: dict[str, tuple[str, str | int | float | bool]] = {}
    for key, expected in campaign.baseline.items():
        resolved = _resolve_baseline_column(key=key, tag_columns=tag_columns)
        if resolved is None:
            return None
        baseline_columns[resolved] = (key, expected)

    baseline_mask = pd.Series(True, index=frame.index)
    for column, (_, expected_value) in baseline_columns.items():
        baseline_mask = baseline_mask & (frame[column].astype(str) == str(expected_value))

    baseline_rows = frame[baseline_mask].copy()
    if baseline_rows.empty:
        return None

    compare_rows = frame[~baseline_mask].copy()
    if compare_rows.empty:
        return []

    group_columns = [column for column in tag_columns if column not in baseline_columns]
    baseline_lookup: dict[tuple[str, ...], pd.Series] = {}
    for _, row in baseline_rows.iterrows():
        key = tuple(str(row[column]) for column in group_columns)
        if key not in baseline_lookup:
            baseline_lookup[key] = row

    findings: list[dict[str, str]] = []
    for _, compare_row in compare_rows.iterrows():
        key = tuple(str(compare_row[column]) for column in group_columns)
        baseline_row = baseline_lookup.get(key)
        if baseline_row is None:
            continue

        baseline_label = ", ".join(
            f"{original_key}={expected_value}"
            for original_key, expected_value in [item for item in baseline_columns.values()]
        )
        compare_label = ", ".join(
            f"{column.removeprefix('tag_')}={compare_row[column]}" for column in baseline_columns
        )
        config = ", ".join(
            f"{column.removeprefix('tag_')}={compare_row[column]}" for column in group_columns
        )
        if not config:
            config = "(all shared tags)"

        baseline_tp = _safe_float(baseline_row.get("peak_throughput_tokens_per_s"))
        compare_tp = _safe_float(compare_row.get("peak_throughput_tokens_per_s"))
        if baseline_tp > 0 and compare_tp >= 0:
            throughput_drop_pct = ((baseline_tp - compare_tp) / baseline_tp) * 100.0
            if throughput_drop_pct > campaign.throughput_drop_pct_threshold:
                findings.append(
                    {
                        "config": config,
                        "metric": "throughput",
                        "baseline_label": baseline_label,
                        "compare_label": compare_label,
                        "baseline_value": f"{baseline_tp:.3f} tok/s",
                        "compare_value": f"{compare_tp:.3f} tok/s",
                        "delta": f"-{throughput_drop_pct:.1f}%",
                    }
                )

        baseline_latency = _safe_float(baseline_row.get("latency_p95_at_max_concurrency"))
        compare_latency = _safe_float(compare_row.get("latency_p95_at_max_concurrency"))
        if baseline_latency > 0 and compare_latency >= 0:
            latency_increase_pct = ((compare_latency - baseline_latency) / baseline_latency) * 100.0
            if latency_increase_pct > campaign.latency_p95_increase_pct_threshold:
                findings.append(
                    {
                        "config": config,
                        "metric": "p95 latency",
                        "baseline_label": baseline_label,
                        "compare_label": compare_label,
                        "baseline_value": f"{baseline_latency / 1000.0:.2f}s",
                        "compare_value": f"{compare_latency / 1000.0:.2f}s",
                        "delta": f"+{latency_increase_pct:.1f}%",
                    }
                )
    return findings


def _resolve_baseline_column(*, key: str, tag_columns: list[str]) -> str | None:
    direct = f"tag_{key}"
    if direct in tag_columns:
        return direct

    aliases = {
        "version": ["tag_vllm_version"],
        "vllm_version": ["tag_version"],
    }
    for alias in aliases.get(key, []):
        if alias in tag_columns:
            return alias
    return None


def _safe_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _frame_to_markdown_lines(frame: pd.DataFrame) -> list[str]:
    columns = [str(column) for column in frame.columns]
    header = "| " + " | ".join(columns) + " |"
    divider = "| " + " | ".join(["---"] * len(columns)) + " |"
    lines = [header, divider]
    for _, row in frame.iterrows():
        values: list[str] = []
        for column in frame.columns:
            value = row[column]
            if pd.isna(value):
                values.append("")
            else:
                values.append(str(value))
        lines.append("| " + " | ".join(values) + " |")
    return lines


def _infer_python_from_server_command(command: str) -> Path | None:
    try:
        tokens = shlex.split(command)
    except ValueError:
        return None

    for token in tokens:
        path = Path(token)
        if token.endswith("/bin/vllm"):
            return path.with_name("python")
        if token.endswith("/bin/python") or token.endswith("/bin/python3"):
            return path
    return None


def _detect_cpu_model() -> str:
    cpuinfo_path = Path("/proc/cpuinfo")
    if cpuinfo_path.exists():
        for line in cpuinfo_path.read_text(encoding="utf-8").splitlines():
            if line.lower().startswith("model name"):
                _, _, value = line.partition(":")
                return value.strip()
    return ""
