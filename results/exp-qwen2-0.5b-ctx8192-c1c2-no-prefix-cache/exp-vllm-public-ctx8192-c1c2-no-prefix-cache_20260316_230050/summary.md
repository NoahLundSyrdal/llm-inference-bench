# Summary

## Run Metadata

- **run_id**: `20260316_230050`
- **run_name**: `exp-vllm-public-ctx8192-c1c2-no-prefix-cache`
- **created_at**: `2026-03-16T23:00:50.435539Z`
- **engine**: `vllm`
- **model**: `Qwen/Qwen2-0.5B-Instruct`
- **git_commit**: `9a96c90e3e20f3dd0b010c3e7c4f3cd7f1284fc1`

## Aggregate Metrics

| engine | model | workload_label | concurrency | total_requests | successes | error_rate | latency_ms_p50 | latency_ms_p95 | latency_ms_p99 | ttft_ms_p50 | throughput_tokens_per_s_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| vllm | Qwen/Qwen2-0.5B-Instruct | ctx-8192-no-prefix-cache | 1 | 24 | 24 | 0.000 | 30801.693 | 31932.846 | 32349.026 | 27256.517 | 1.393 |
| vllm | Qwen/Qwen2-0.5B-Instruct | ctx-8192-no-prefix-cache | 2 | 24 | 24 | 0.000 | 60104.141 | 61106.176 | 72321.832 | 34340.747 | 0.703 |

## Top Failure Modes

No request failures observed.

## Generated Plots

- `latency_vs_concurrency.png`
- `throughput_vs_concurrency.png`
- `ttft_vs_concurrency.png`
- `error_rate_vs_concurrency.png`
