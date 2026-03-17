from __future__ import annotations

import asyncio
import itertools
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

    def run(self, config: CampaignConfig, *, dry_run: bool = False) -> Path:
        campaign_run_id = timestamp_slug()
        campaign_dir = create_run_directory(config.output_dir, config.name, campaign_run_id)
        if dry_run:
            self._write_dry_run_plan(config=config, campaign_dir=campaign_dir)
            return campaign_dir

        records: list[dict[str, Any]] = []
        for experiment in config.experiments:
            row = self._run_experiment(
                campaign=config,
                campaign_run_id=campaign_run_id,
                campaign_dir=campaign_dir,
                experiment=experiment,
            )
            records.append(row)

            if row["status"] == "failed" and not config.continue_on_error:
                break

        self._write_campaign_outputs(campaign=config, campaign_dir=campaign_dir, records=records)
        failures = [record for record in records if record["status"] == "failed"]
        if failures and not config.continue_on_error:
            first_error = failures[0].get("error", "unknown error")
            msg = f"Campaign stopped after failure: {first_error}"
            raise RuntimeError(msg)

        return campaign_dir

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

    def _write_dry_run_plan(self, *, config: CampaignConfig, campaign_dir: Path) -> None:
        plan = {
            "campaign_name": config.name,
            "output_dir": str(campaign_dir),
            "experiment_count": len(config.experiments),
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
