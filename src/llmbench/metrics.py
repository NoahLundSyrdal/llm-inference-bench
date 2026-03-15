from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import pandas as pd

from llmbench.models import RequestRecord

SUMMARY_COLUMNS = [
    "engine",
    "model",
    "workload_label",
    "concurrency",
    "total_requests",
    "successes",
    "failures",
    "error_rate",
    "latency_ms_p50",
    "latency_ms_p95",
    "latency_ms_p99",
    "ttft_ms_p50",
    "ttft_ms_p95",
    "throughput_tokens_per_s_mean",
    "throughput_tokens_per_s_median",
]


def records_to_dataframe(records: Sequence[RequestRecord | dict[str, Any]]) -> pd.DataFrame:
    rows = [
        record.model_dump(mode="json") if isinstance(record, RequestRecord) else record
        for record in records
    ]
    if not rows:
        return pd.DataFrame()

    frame = pd.DataFrame(rows)
    if "success" in frame.columns:
        frame["success"] = frame["success"].astype(bool)
    return frame


def aggregate_metrics(records_df: pd.DataFrame) -> pd.DataFrame:
    if records_df.empty:
        return pd.DataFrame(columns=SUMMARY_COLUMNS)

    grouped = records_df.groupby(["engine", "model", "workload_label", "concurrency"], dropna=False)
    rows: list[dict[str, Any]] = []

    for (engine, model, workload_label, concurrency), group in grouped:
        success = group[group["success"]]
        total = len(group)
        successes = len(success)
        failures = total - successes

        rows.append(
            {
                "engine": engine,
                "model": model,
                "workload_label": workload_label,
                "concurrency": int(concurrency),
                "total_requests": int(total),
                "successes": int(successes),
                "failures": int(failures),
                "error_rate": _safe_div(failures, total),
                "latency_ms_p50": _quantile(success.get("latency_ms"), 0.50),
                "latency_ms_p95": _quantile(success.get("latency_ms"), 0.95),
                "latency_ms_p99": _quantile(success.get("latency_ms"), 0.99),
                "ttft_ms_p50": _quantile(success.get("ttft_ms"), 0.50),
                "ttft_ms_p95": _quantile(success.get("ttft_ms"), 0.95),
                "throughput_tokens_per_s_mean": _mean(success.get("tokens_per_sec")),
                "throughput_tokens_per_s_median": _median(success.get("tokens_per_sec")),
            }
        )

    summary = pd.DataFrame(rows)
    return summary.sort_values(["engine", "workload_label", "concurrency"]).reset_index(drop=True)


def top_failure_modes(records_df: pd.DataFrame, limit: int = 5) -> pd.DataFrame:
    if records_df.empty:
        return pd.DataFrame(columns=["error_type", "error_message", "count"])

    failures = records_df[~records_df["success"]]
    if failures.empty:
        return pd.DataFrame(columns=["error_type", "error_message", "count"])

    return (
        failures.fillna({"error_type": "unknown", "error_message": "unknown"})
        .groupby(["error_type", "error_message"], dropna=False)
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
        .head(limit)
        .reset_index(drop=True)
    )


def _quantile(series: pd.Series | None, q: float) -> float | None:
    if series is None:
        return None
    clean = pd.to_numeric(series, errors="coerce").dropna()
    if clean.empty:
        return None
    return float(clean.quantile(q))


def _mean(series: pd.Series | None) -> float | None:
    if series is None:
        return None
    clean = pd.to_numeric(series, errors="coerce").dropna()
    if clean.empty:
        return None
    return float(clean.mean())


def _median(series: pd.Series | None) -> float | None:
    if series is None:
        return None
    clean = pd.to_numeric(series, errors="coerce").dropna()
    if clean.empty:
        return None
    return float(clean.median())


def _safe_div(numerator: float, denominator: float) -> float:
    return float(numerator) / float(denominator) if denominator else 0.0
