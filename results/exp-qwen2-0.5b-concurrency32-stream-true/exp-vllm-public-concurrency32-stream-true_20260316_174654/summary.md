# Summary

## Run Metadata

- **run_id**: `20260316_174654`
- **run_name**: `exp-vllm-public-concurrency32-stream-true`
- **created_at**: `2026-03-16T17:46:54.836774Z`
- **engine**: `vllm`
- **model**: `Qwen/Qwen2-0.5B-Instruct`
- **git_commit**: `09564ce61d48ac574e28c2d72824c16afdcf72c3`

## Aggregate Metrics

| engine | model | workload_label | concurrency | total_requests | successes | error_rate | latency_ms_p50 | latency_ms_p95 | latency_ms_p99 | ttft_ms_p50 | throughput_tokens_per_s_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| vllm | Qwen/Qwen2-0.5B-Instruct | quickstart | 1 | 48 | 48 | 0.000 | 3549.089 | 3690.560 | 3712.621 | 56.433 | 21.119 |
| vllm | Qwen/Qwen2-0.5B-Instruct | quickstart | 2 | 48 | 48 | 0.000 | 3697.931 | 4032.610 | 4118.833 | 89.882 | 19.716 |
| vllm | Qwen/Qwen2-0.5B-Instruct | quickstart | 4 | 48 | 48 | 0.000 | 4235.571 | 4522.517 | 4561.868 | 103.121 | 17.423 |
| vllm | Qwen/Qwen2-0.5B-Instruct | quickstart | 8 | 48 | 48 | 0.000 | 4534.695 | 4975.409 | 4999.994 | 123.365 | 16.099 |
| vllm | Qwen/Qwen2-0.5B-Instruct | quickstart | 16 | 48 | 48 | 0.000 | 6293.252 | 6826.404 | 6826.820 | 174.694 | 11.782 |
| vllm | Qwen/Qwen2-0.5B-Instruct | quickstart | 32 | 48 | 48 | 0.000 | 9031.860 | 10577.523 | 10578.598 | 508.920 | 7.509 |

## Top Failure Modes

No request failures observed.

## Generated Plots

- `latency_vs_concurrency.png`
- `throughput_vs_concurrency.png`
- `ttft_vs_concurrency.png`
- `error_rate_vs_concurrency.png`
