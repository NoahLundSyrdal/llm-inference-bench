# Summary

## Run Metadata

- **run_id**: `20260317_053059`
- **run_name**: `exp-vllm-public-ctx8192-coldstart-c2`
- **created_at**: `2026-03-17T05:30:59.656024Z`
- **engine**: `vllm`
- **model**: `Qwen/Qwen2-0.5B-Instruct`
- **git_commit**: `9c66c04eb9e275ed3488fb76ebca2b37db0740a4`

## Aggregate Metrics

| engine | model | workload_label | concurrency | total_requests | successes | error_rate | latency_ms_p50 | latency_ms_p95 | latency_ms_p99 | ttft_ms_p50 | throughput_tokens_per_s_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| vllm | Qwen/Qwen2-0.5B-Instruct | ctx-8192-coldstart-c2 | 2 | 24 | 24 | 0.000 | 62742.176 | 70999.252 | 75916.651 | 38481.613 | 0.674 |

## Top Failure Modes

No request failures observed.

## Generated Plots

- `latency_vs_concurrency.png`
- `throughput_vs_concurrency.png`
- `ttft_vs_concurrency.png`
- `error_rate_vs_concurrency.png`
