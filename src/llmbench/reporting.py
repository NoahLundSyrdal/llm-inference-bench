from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


def generate_summary_markdown(
    metadata: dict[str, Any],
    summary_df: pd.DataFrame,
    failure_df: pd.DataFrame,
    plot_paths: list[Path],
) -> str:
    lines: list[str] = []
    lines.append("# Summary")
    lines.append("")
    lines.append("## Run Metadata")
    lines.append("")
    for key in ["run_id", "run_name", "created_at", "engine", "model", "git_commit"]:
        if key in metadata:
            lines.append(f"- **{key}**: `{metadata[key]}`")
    lines.append("")

    lines.append("## Aggregate Metrics")
    lines.append("")
    if summary_df.empty:
        lines.append("No aggregate metrics available.")
    else:
        metric_cols = [
            "engine",
            "model",
            "workload_label",
            "concurrency",
            "total_requests",
            "successes",
            "error_rate",
            "latency_ms_p50",
            "latency_ms_p95",
            "latency_ms_p99",
            "ttft_ms_p50",
            "throughput_tokens_per_s_mean",
        ]
        available_cols = [col for col in metric_cols if col in summary_df.columns]
        lines.append(dataframe_to_markdown(summary_df[available_cols]))
    lines.append("")

    lines.append("## Top Failure Modes")
    lines.append("")
    if failure_df.empty:
        lines.append("No request failures observed.")
    else:
        lines.append(dataframe_to_markdown(failure_df))
    lines.append("")

    lines.append("## Generated Plots")
    lines.append("")
    if not plot_paths:
        lines.append("No plots generated.")
    else:
        for plot_path in plot_paths:
            lines.append(f"- `{plot_path.name}`")

    return "\n".join(lines) + "\n"


def dataframe_to_markdown(df: pd.DataFrame, max_rows: int = 30) -> str:
    if df.empty:
        return "No rows."

    display = df.head(max_rows).copy()
    for column in display.columns:
        if pd.api.types.is_numeric_dtype(display[column]):
            display[column] = display[column].map(lambda value: _fmt_numeric(value))

    headers = list(display.columns)
    divider = ["---"] * len(headers)

    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(divider) + " |",
    ]

    for _, row in display.iterrows():
        values = [str(row[col]) for col in headers]
        lines.append("| " + " | ".join(values) + " |")

    if len(df) > max_rows:
        lines.append("")
        lines.append(f"_Showing first {max_rows} of {len(df)} rows._")

    return "\n".join(lines)


def _fmt_numeric(value: Any) -> str:
    if value is None:
        return ""
    if pd.isna(value):
        return ""
    if isinstance(value, int):
        return str(value)
    try:
        return f"{float(value):.3f}"
    except (TypeError, ValueError):
        return str(value)
