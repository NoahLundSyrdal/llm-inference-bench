# Summary

## Run Metadata

- **run_id**: `20260316_180935`
- **run_name**: `exp-vllm-public-ctx2048-stream-true`
- **created_at**: `2026-03-16T18:09:35.820295Z`
- **engine**: `vllm`
- **model**: `Qwen/Qwen2-0.5B-Instruct`
- **git_commit**: `4113eed862d5835fc6a3fb267b9c9d8c0e01ed01`

## Aggregate Metrics

| engine | model | workload_label | concurrency | total_requests | successes | error_rate | latency_ms_p50 | latency_ms_p95 | latency_ms_p99 | ttft_ms_p50 | throughput_tokens_per_s_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| vllm | Qwen/Qwen2-0.5B-Instruct | ctx-2048 | 1 | 24 | 24 | 0.000 | 4872.022 | 5076.614 | 5236.819 | 2025.324 | 9.289 |
| vllm | Qwen/Qwen2-0.5B-Instruct | ctx-2048 | 2 | 24 | 24 | 0.000 | 3327.905 | 3415.768 | 3419.513 | 177.160 | 13.842 |
| vllm | Qwen/Qwen2-0.5B-Instruct | ctx-2048 | 4 | 24 | 24 | 0.000 | 4219.557 | 4257.342 | 4258.896 | 262.780 | 10.666 |
| vllm | Qwen/Qwen2-0.5B-Instruct | ctx-2048 | 8 | 24 | 24 | 0.000 | 6514.763 | 6518.770 | 6527.408 | 463.761 | 7.080 |
| vllm | Qwen/Qwen2-0.5B-Instruct | ctx-2048 | 16 | 24 | 24 | 0.000 | 10908.283 | 10911.120 | 10911.551 | 923.198 | 5.285 |
| vllm | Qwen/Qwen2-0.5B-Instruct | ctx-2048 | 32 | 24 | 24 | 0.000 | 16336.435 | 16338.548 | 16338.823 | 1350.540 | 2.897 |

## Top Failure Modes

No request failures observed.

## Generated Plots

- `latency_vs_concurrency.png`
- `throughput_vs_concurrency.png`
- `ttft_vs_concurrency.png`
- `error_rate_vs_concurrency.png`
