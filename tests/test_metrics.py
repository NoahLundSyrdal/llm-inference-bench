from __future__ import annotations

import math

from llmbench.metrics import aggregate_metrics, records_to_dataframe, top_failure_modes


def test_aggregate_metrics_computes_percentiles_and_error_rate() -> None:
    records = [
        {
            "request_id": "1",
            "run_id": "r1",
            "run_name": "run",
            "workload_label": "synthetic",
            "repetition": 1,
            "concurrency": 4,
            "prompt_index": 0,
            "prompt": "a",
            "engine": "vllm",
            "model": "m",
            "stream": True,
            "started_at": "2026-01-01T00:00:00Z",
            "ended_at": "2026-01-01T00:00:01Z",
            "latency_ms": 100.0,
            "ttft_ms": 20.0,
            "completion_time_ms": 100.0,
            "output_tokens": 20,
            "output_tokens_estimated": False,
            "tokens_per_sec": 200.0,
            "success": True,
            "status_code": 200,
            "error_type": None,
            "error_message": None,
        },
        {
            "request_id": "2",
            "run_id": "r1",
            "run_name": "run",
            "workload_label": "synthetic",
            "repetition": 1,
            "concurrency": 4,
            "prompt_index": 1,
            "prompt": "b",
            "engine": "vllm",
            "model": "m",
            "stream": True,
            "started_at": "2026-01-01T00:00:00Z",
            "ended_at": "2026-01-01T00:00:01Z",
            "latency_ms": 300.0,
            "ttft_ms": 40.0,
            "completion_time_ms": 300.0,
            "output_tokens": 30,
            "output_tokens_estimated": False,
            "tokens_per_sec": 100.0,
            "success": True,
            "status_code": 200,
            "error_type": None,
            "error_message": None,
        },
        {
            "request_id": "3",
            "run_id": "r1",
            "run_name": "run",
            "workload_label": "synthetic",
            "repetition": 1,
            "concurrency": 4,
            "prompt_index": 2,
            "prompt": "c",
            "engine": "vllm",
            "model": "m",
            "stream": True,
            "started_at": "2026-01-01T00:00:00Z",
            "ended_at": "2026-01-01T00:00:01Z",
            "latency_ms": 500.0,
            "ttft_ms": None,
            "completion_time_ms": 500.0,
            "output_tokens": 0,
            "output_tokens_estimated": False,
            "tokens_per_sec": 0.0,
            "success": False,
            "status_code": 500,
            "error_type": "HTTPStatusError",
            "error_message": "boom",
        },
    ]

    df = records_to_dataframe(records)
    summary = aggregate_metrics(df)

    assert len(summary) == 1
    row = summary.iloc[0]
    assert row["total_requests"] == 3
    assert row["successes"] == 2
    assert math.isclose(row["error_rate"], 1.0 / 3.0, rel_tol=1e-5)
    assert row["latency_ms_p50"] == 200.0
    assert row["throughput_tokens_per_s_median"] == 150.0


def test_top_failure_modes_returns_grouped_counts() -> None:
    df = records_to_dataframe(
        [
            {
                "request_id": "1",
                "run_id": "r1",
                "run_name": "run",
                "workload_label": "w",
                "repetition": 1,
                "concurrency": 1,
                "prompt_index": 0,
                "prompt": "p",
                "engine": "vllm",
                "model": "m",
                "stream": False,
                "started_at": "2026-01-01T00:00:00Z",
                "ended_at": "2026-01-01T00:00:00Z",
                "latency_ms": 1,
                "ttft_ms": None,
                "completion_time_ms": 1,
                "output_tokens": 0,
                "output_tokens_estimated": False,
                "tokens_per_sec": 0,
                "success": False,
                "status_code": 500,
                "error_type": "HTTPStatusError",
                "error_message": "A",
            },
            {
                "request_id": "2",
                "run_id": "r1",
                "run_name": "run",
                "workload_label": "w",
                "repetition": 1,
                "concurrency": 1,
                "prompt_index": 1,
                "prompt": "p",
                "engine": "vllm",
                "model": "m",
                "stream": False,
                "started_at": "2026-01-01T00:00:00Z",
                "ended_at": "2026-01-01T00:00:00Z",
                "latency_ms": 1,
                "ttft_ms": None,
                "completion_time_ms": 1,
                "output_tokens": 0,
                "output_tokens_estimated": False,
                "tokens_per_sec": 0,
                "success": False,
                "status_code": 500,
                "error_type": "HTTPStatusError",
                "error_message": "A",
            },
        ]
    )

    failures = top_failure_modes(df)
    assert len(failures) == 1
    assert failures.iloc[0]["count"] == 2
