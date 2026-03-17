# Summary

## Run Metadata

- **run_id**: `20260317_051532`
- **run_name**: `exp-vllm-public-ctx8192-coldstart-c1`
- **created_at**: `2026-03-17T05:15:32.793311Z`
- **engine**: `vllm`
- **model**: `Qwen/Qwen2-0.5B-Instruct`
- **git_commit**: `9c66c04eb9e275ed3488fb76ebca2b37db0740a4`

## Aggregate Metrics

| engine | model | workload_label | concurrency | total_requests | successes | error_rate | latency_ms_p50 | latency_ms_p95 | latency_ms_p99 | ttft_ms_p50 | throughput_tokens_per_s_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| vllm | Qwen/Qwen2-0.5B-Instruct | ctx-8192-coldstart-c1 | 1 | 24 | 24 | 0.000 | 31381.504 | 37559.749 | 41185.303 | 27516.523 | 1.299 |

## Top Failure Modes

No request failures observed.

## Generated Plots

- `latency_vs_concurrency.png`
- `throughput_vs_concurrency.png`
- `ttft_vs_concurrency.png`
- `error_rate_vs_concurrency.png`
