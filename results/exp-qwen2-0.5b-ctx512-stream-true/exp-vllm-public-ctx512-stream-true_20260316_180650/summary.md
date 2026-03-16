# Summary

## Run Metadata

- **run_id**: `20260316_180650`
- **run_name**: `exp-vllm-public-ctx512-stream-true`
- **created_at**: `2026-03-16T18:06:50.437838Z`
- **engine**: `vllm`
- **model**: `Qwen/Qwen2-0.5B-Instruct`
- **git_commit**: `4113eed862d5835fc6a3fb267b9c9d8c0e01ed01`

## Aggregate Metrics

| engine | model | workload_label | concurrency | total_requests | successes | error_rate | latency_ms_p50 | latency_ms_p95 | latency_ms_p99 | ttft_ms_p50 | throughput_tokens_per_s_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| vllm | Qwen/Qwen2-0.5B-Instruct | ctx-512 | 1 | 24 | 24 | 0.000 | 2895.564 | 3051.187 | 3279.414 | 314.875 | 15.621 |
| vllm | Qwen/Qwen2-0.5B-Instruct | ctx-512 | 2 | 24 | 24 | 0.000 | 2763.021 | 2837.456 | 2841.222 | 92.441 | 16.442 |
| vllm | Qwen/Qwen2-0.5B-Instruct | ctx-512 | 4 | 24 | 24 | 0.000 | 2969.119 | 3022.876 | 3024.462 | 145.529 | 15.377 |
| vllm | Qwen/Qwen2-0.5B-Instruct | ctx-512 | 8 | 24 | 24 | 0.000 | 4431.795 | 4475.127 | 4479.552 | 267.136 | 10.181 |
| vllm | Qwen/Qwen2-0.5B-Instruct | ctx-512 | 16 | 24 | 24 | 0.000 | 6136.942 | 6211.523 | 6211.839 | 265.938 | 9.125 |
| vllm | Qwen/Qwen2-0.5B-Instruct | ctx-512 | 32 | 24 | 24 | 0.000 | 8845.424 | 8846.592 | 8847.092 | 596.124 | 5.098 |

## Top Failure Modes

No request failures observed.

## Generated Plots

- `latency_vs_concurrency.png`
- `throughput_vs_concurrency.png`
- `ttft_vs_concurrency.png`
- `error_rate_vs_concurrency.png`
