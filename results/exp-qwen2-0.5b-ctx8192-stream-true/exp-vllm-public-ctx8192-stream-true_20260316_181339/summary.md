# Summary

## Run Metadata

- **run_id**: `20260316_181339`
- **run_name**: `exp-vllm-public-ctx8192-stream-true`
- **created_at**: `2026-03-16T18:13:39.605591Z`
- **engine**: `vllm`
- **model**: `Qwen/Qwen2-0.5B-Instruct`
- **git_commit**: `4113eed862d5835fc6a3fb267b9c9d8c0e01ed01`

## Aggregate Metrics

| engine | model | workload_label | concurrency | total_requests | successes | error_rate | latency_ms_p50 | latency_ms_p95 | latency_ms_p99 | ttft_ms_p50 | throughput_tokens_per_s_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| vllm | Qwen/Qwen2-0.5B-Instruct | ctx-8192 | 1 | 24 | 24 | 0.000 | 28855.913 | 30294.300 | 32317.344 | 25119.197 | 1.558 |
| vllm | Qwen/Qwen2-0.5B-Instruct | ctx-8192 | 2 | 24 | 24 | 0.000 | 5820.966 | 6365.013 | 6374.361 | 428.078 | 7.384 |
| vllm | Qwen/Qwen2-0.5B-Instruct | ctx-8192 | 4 | 24 | 24 | 0.000 | 9729.224 | 9910.984 | 9912.146 | 955.836 | 4.568 |
| vllm | Qwen/Qwen2-0.5B-Instruct | ctx-8192 | 8 | 24 | 24 | 0.000 | 17290.419 | 17367.948 | 17375.855 | 1772.962 | 2.629 |
| vllm | Qwen/Qwen2-0.5B-Instruct | ctx-8192 | 16 | 24 | 24 | 0.000 | 32239.081 | 32242.358 | 32242.612 | 3101.854 | 1.767 |
| vllm | Qwen/Qwen2-0.5B-Instruct | ctx-8192 | 32 | 24 | 24 | 0.000 | 47820.405 | 47823.333 | 47824.636 | 4164.449 | 0.951 |

## Top Failure Modes

No request failures observed.

## Generated Plots

- `latency_vs_concurrency.png`
- `throughput_vs_concurrency.png`
- `ttft_vs_concurrency.png`
- `error_rate_vs_concurrency.png`
