# Summary

## Run Metadata

- **run_id**: `20260317_043809`
- **run_name**: `exp-vllm-public-ctx8192-stream-true`
- **created_at**: `2026-03-17T04:38:09.377865Z`
- **engine**: `vllm`
- **model**: `Qwen/Qwen2-0.5B-Instruct`
- **git_commit**: `1c12a1f15994e545c5cb3d35953a3f16a897089e`

## Aggregate Metrics

| engine | model | workload_label | concurrency | total_requests | successes | error_rate | latency_ms_p50 | latency_ms_p95 | latency_ms_p99 | ttft_ms_p50 | throughput_tokens_per_s_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| vllm | Qwen/Qwen2-0.5B-Instruct | ctx-8192 | 1 | 24 | 24 | 0.000 | 30812.099 | 33682.167 | 36942.882 | 26630.549 | 1.404 |
| vllm | Qwen/Qwen2-0.5B-Instruct | ctx-8192 | 2 | 24 | 24 | 0.000 | 6514.536 | 7015.190 | 7044.164 | 473.793 | 6.717 |
| vllm | Qwen/Qwen2-0.5B-Instruct | ctx-8192 | 4 | 24 | 24 | 0.000 | 9843.803 | 11666.530 | 11775.063 | 741.147 | 4.309 |
| vllm | Qwen/Qwen2-0.5B-Instruct | ctx-8192 | 8 | 24 | 24 | 0.000 | 19140.873 | 19704.716 | 19705.054 | 1448.526 | 2.414 |
| vllm | Qwen/Qwen2-0.5B-Instruct | ctx-8192 | 16 | 24 | 24 | 0.000 | 32205.571 | 32210.549 | 32211.955 | 2869.052 | 1.774 |
| vllm | Qwen/Qwen2-0.5B-Instruct | ctx-8192 | 32 | 24 | 24 | 0.000 | 49556.891 | 49564.602 | 49565.858 | 3835.444 | 0.887 |

## Top Failure Modes

No request failures observed.

## Generated Plots

- `latency_vs_concurrency.png`
- `throughput_vs_concurrency.png`
- `ttft_vs_concurrency.png`
- `error_rate_vs_concurrency.png`
