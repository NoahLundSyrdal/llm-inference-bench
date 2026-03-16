# Summary

## Run Metadata

- **run_id**: `20260316_000556`
- **run_name**: `local-vllm-public-long-prompts`
- **created_at**: `2026-03-16T00:05:56.277950Z`
- **engine**: `vllm`
- **model**: `Qwen/Qwen2-0.5B-Instruct`
- **git_commit**: `0dcc22c3dcacf70b61cf5a442bc50f53c4df1a48`

## Aggregate Metrics

| engine | model | workload_label | concurrency | total_requests | successes | error_rate | latency_ms_p50 | latency_ms_p95 | latency_ms_p99 | ttft_ms_p50 | throughput_tokens_per_s_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| vllm | Qwen/Qwen2-0.5B-Instruct | long-context | 1 | 24 | 24 | 0.000 | 3602.252 | 4394.309 | 4846.863 | nan | 23.809 |
| vllm | Qwen/Qwen2-0.5B-Instruct | long-context | 2 | 24 | 24 | 0.000 | 5432.375 | 6099.098 | 6111.381 | nan | 17.260 |
| vllm | Qwen/Qwen2-0.5B-Instruct | long-context | 4 | 24 | 24 | 0.000 | 7313.517 | 9460.013 | 9696.948 | nan | 12.508 |
| vllm | Qwen/Qwen2-0.5B-Instruct | long-context | 8 | 24 | 24 | 0.000 | 14284.293 | 18352.629 | 18584.403 | nan | 6.321 |
| vllm | Qwen/Qwen2-0.5B-Instruct | long-context | 16 | 24 | 24 | 0.000 | 25100.930 | 31655.184 | 31655.554 | nan | 4.292 |

## Top Failure Modes

No request failures observed.

## Generated Plots

- `latency_vs_concurrency.png`
- `throughput_vs_concurrency.png`
- `ttft_vs_concurrency.png`
- `error_rate_vs_concurrency.png`
