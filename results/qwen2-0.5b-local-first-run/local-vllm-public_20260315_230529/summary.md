# llm-inference-bench Summary

## Run Metadata

- **run_id**: `20260315_230529`
- **run_name**: `local-vllm-public`
- **created_at**: `2026-03-15T23:05:29.035091Z`
- **engine**: `vllm`
- **model**: `Qwen/Qwen2-0.5B-Instruct`
- **git_commit**: `9fa10afedaa79de18601c36c4de8dd3b4ab66837`

## Aggregate Metrics

| engine | model | workload_label | concurrency | total_requests | successes | error_rate | latency_ms_p50 | latency_ms_p95 | latency_ms_p99 | ttft_ms_p50 | throughput_tokens_per_s_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| vllm | Qwen/Qwen2-0.5B-Instruct | quickstart | 1 | 24 | 24 | 0.000 | 3329.299 | 3576.354 | 3673.711 | nan | 28.778 |
| vllm | Qwen/Qwen2-0.5B-Instruct | quickstart | 2 | 24 | 24 | 0.000 | 4799.685 | 4984.059 | 5029.849 | nan | 20.036 |
| vllm | Qwen/Qwen2-0.5B-Instruct | quickstart | 4 | 24 | 24 | 0.000 | 7758.164 | 8090.069 | 8094.350 | nan | 12.445 |
| vllm | Qwen/Qwen2-0.5B-Instruct | quickstart | 8 | 24 | 24 | 0.000 | 13667.460 | 14926.875 | 14928.159 | nan | 7.201 |
| vllm | Qwen/Qwen2-0.5B-Instruct | quickstart | 16 | 24 | 24 | 0.000 | 23936.762 | 24052.601 | 24054.487 | nan | 5.209 |

## Top Failure Modes

No request failures observed.

## Generated Plots

- `latency_vs_concurrency.png`
- `throughput_vs_concurrency.png`
- `ttft_vs_concurrency.png`
- `error_rate_vs_concurrency.png`
