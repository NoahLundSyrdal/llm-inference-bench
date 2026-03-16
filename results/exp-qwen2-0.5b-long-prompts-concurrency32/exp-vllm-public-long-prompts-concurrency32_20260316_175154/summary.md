# Summary

## Run Metadata

- **run_id**: `20260316_175154`
- **run_name**: `exp-vllm-public-long-prompts-concurrency32`
- **created_at**: `2026-03-16T17:51:54.893877Z`
- **engine**: `vllm`
- **model**: `Qwen/Qwen2-0.5B-Instruct`
- **git_commit**: `09564ce61d48ac574e28c2d72824c16afdcf72c3`

## Aggregate Metrics

| engine | model | workload_label | concurrency | total_requests | successes | error_rate | latency_ms_p50 | latency_ms_p95 | latency_ms_p99 | ttft_ms_p50 | throughput_tokens_per_s_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| vllm | Qwen/Qwen2-0.5B-Instruct | long-context | 1 | 48 | 48 | 0.000 | 3593.603 | 4533.505 | 4699.532 | nan | 24.859 |
| vllm | Qwen/Qwen2-0.5B-Instruct | long-context | 2 | 48 | 48 | 0.000 | 3942.574 | 4073.387 | 4104.200 | nan | 23.983 |
| vllm | Qwen/Qwen2-0.5B-Instruct | long-context | 4 | 48 | 48 | 0.000 | 4114.001 | 4325.552 | 4352.621 | nan | 22.952 |
| vllm | Qwen/Qwen2-0.5B-Instruct | long-context | 8 | 48 | 48 | 0.000 | 4788.601 | 4980.777 | 4988.905 | nan | 19.582 |
| vllm | Qwen/Qwen2-0.5B-Instruct | long-context | 16 | 48 | 48 | 0.000 | 7664.762 | 8071.938 | 8072.970 | nan | 12.451 |
| vllm | Qwen/Qwen2-0.5B-Instruct | long-context | 32 | 48 | 48 | 0.000 | 11322.483 | 13810.437 | 13858.753 | nan | 8.403 |

## Top Failure Modes

No request failures observed.

## Generated Plots

- `latency_vs_concurrency.png`
- `throughput_vs_concurrency.png`
- `ttft_vs_concurrency.png`
- `error_rate_vs_concurrency.png`
