# llm-inference-bench Summary

## Run Metadata

- **run_id**: `20260315_231051`
- **run_name**: `local-vllm-public-maxtokens192`
- **created_at**: `2026-03-15T23:10:52.040405Z`
- **engine**: `vllm`
- **model**: `Qwen/Qwen2-0.5B-Instruct`
- **git_commit**: `59c97cbfc847e30bd733111ee5917508357d180d`

## Aggregate Metrics

| engine | model | workload_label | concurrency | total_requests | successes | error_rate | latency_ms_p50 | latency_ms_p95 | latency_ms_p99 | ttft_ms_p50 | throughput_tokens_per_s_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| vllm | Qwen/Qwen2-0.5B-Instruct | quickstart | 1 | 24 | 24 | 0.000 | 6061.202 | 6765.971 | 7088.843 | nan | 28.385 |
| vllm | Qwen/Qwen2-0.5B-Instruct | quickstart | 2 | 24 | 24 | 0.000 | 8465.223 | 10510.688 | 10539.331 | nan | 19.788 |
| vllm | Qwen/Qwen2-0.5B-Instruct | quickstart | 4 | 24 | 24 | 0.000 | 10953.274 | 15780.605 | 16551.306 | nan | 16.070 |
| vllm | Qwen/Qwen2-0.5B-Instruct | quickstart | 8 | 24 | 24 | 0.000 | 20202.714 | 24868.247 | 24868.459 | nan | 8.525 |
| vllm | Qwen/Qwen2-0.5B-Instruct | quickstart | 16 | 24 | 24 | 0.000 | 37420.450 | 46541.358 | 46542.114 | nan | 4.964 |

## Top Failure Modes

No request failures observed.

## Generated Plots

- `latency_vs_concurrency.png`
- `throughput_vs_concurrency.png`
- `ttft_vs_concurrency.png`
- `error_rate_vs_concurrency.png`
