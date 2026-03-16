# Summary

## Run Metadata

- **run_id**: `20260316_174216`
- **run_name**: `exp-vllm-public-concurrency32-stream-false`
- **created_at**: `2026-03-16T17:42:16.577982Z`
- **engine**: `vllm`
- **model**: `Qwen/Qwen2-0.5B-Instruct`
- **git_commit**: `09564ce61d48ac574e28c2d72824c16afdcf72c3`

## Aggregate Metrics

| engine | model | workload_label | concurrency | total_requests | successes | error_rate | latency_ms_p50 | latency_ms_p95 | latency_ms_p99 | ttft_ms_p50 | throughput_tokens_per_s_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| vllm | Qwen/Qwen2-0.5B-Instruct | quickstart | 1 | 48 | 48 | 0.000 | 3200.903 | 3411.638 | 3480.660 | nan | 29.189 |
| vllm | Qwen/Qwen2-0.5B-Instruct | quickstart | 2 | 48 | 48 | 0.000 | 3421.856 | 3597.086 | 3607.243 | nan | 27.034 |
| vllm | Qwen/Qwen2-0.5B-Instruct | quickstart | 4 | 48 | 48 | 0.000 | 3651.160 | 3711.392 | 3723.952 | nan | 25.759 |
| vllm | Qwen/Qwen2-0.5B-Instruct | quickstart | 8 | 48 | 48 | 0.000 | 4807.324 | 4973.734 | 4981.613 | nan | 19.362 |
| vllm | Qwen/Qwen2-0.5B-Instruct | quickstart | 16 | 48 | 48 | 0.000 | 6543.020 | 6956.376 | 6957.936 | nan | 14.100 |
| vllm | Qwen/Qwen2-0.5B-Instruct | quickstart | 32 | 48 | 48 | 0.000 | 9139.254 | 10640.784 | 10642.943 | nan | 9.502 |

## Top Failure Modes

No request failures observed.

## Generated Plots

- `latency_vs_concurrency.png`
- `throughput_vs_concurrency.png`
- `ttft_vs_concurrency.png`
- `error_rate_vs_concurrency.png`
