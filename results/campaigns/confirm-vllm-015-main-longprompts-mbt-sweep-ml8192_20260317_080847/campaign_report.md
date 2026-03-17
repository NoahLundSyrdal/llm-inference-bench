# Campaign report: confirm-vllm-015-main-longprompts-mbt-sweep-ml8192

- Total experiments: 4
- Successful: 4
- Failed: 0

## Regression checks

- ⚠ Regression detected.
- Thresholds: throughput drop > 10.0% or p95 latency increase > 15.0%.

config: max_num_batched_tokens=4096, max_model_len=8192, benchmark_family=vllm-015-main-confirmation
metric: throughput
version=0.15.0: 42.249 tok/s | version=main: 32.371 tok/s (-23.4%)

config: max_num_batched_tokens=4096, max_model_len=8192, benchmark_family=vllm-015-main-confirmation
metric: p95 latency
version=0.15.0: 4.13s | version=main: 4.76s (+15.4%)

## Top throughput runs

| experiment_name | peak_throughput_tokens_per_s | latency_p95_at_max_concurrency | max_concurrency |
| --- | --- | --- | --- |
| confirm-vllm-0.15.0-longprompts-mbt4096-ml8192 | 42.248834427221 | 4125.456243801091 | 16 |
| confirm-vllm-main-longprompts-mbt4096-ml8192 | 32.37116147292159 | 4759.1499037991525 | 16 |
| confirm-vllm-main-longprompts-mbt2048-ml8192 | 30.62004082658146 | 4386.303189599857 | 16 |
| confirm-vllm-0.15.0-longprompts-mbt2048-ml8192 | 18.531584897335765 |  | 16 |

## Full campaign table

| campaign_name | campaign_run_id | experiment_name | status | run_dir | error | tag_version | tag_max_num_batched_tokens | tag_max_model_len | tag_benchmark_family | git_sha | vllm_commit | torch_version | cpu_model | num_threads | peak_throughput_tokens_per_s | max_concurrency | latency_p95_at_max_concurrency | error_rate_at_max_concurrency | server_log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| confirm-vllm-015-main-longprompts-mbt-sweep-ml8192 | 20260317_080847 | confirm-vllm-0.15.0-longprompts-mbt2048-ml8192 | ok | /workspace/results/campaigns/confirm-vllm-015-main-longprompts-mbt-sweep-ml8192_20260317_080847/runs/confirm-vllm-0-15-0-longprompts-mbt2048-ml8192/local-vllm-public-long-prompts-confirm-vllm-0-15-0-longprompts-mbt2048-ml8192_20260317_080849 |  | 0.15.0 | 2048 | 8192 | vllm-015-main-confirmation | 973499d0c4f220a3d30bb9ab24170560edd8ec3c | 0.15.0 | 2.10.0+cpu | Intel(R) Xeon(R) Processor | 4 | 18.531584897335765 | 16 |  | 1.0 | /workspace/results/campaigns/confirm-vllm-015-main-longprompts-mbt-sweep-ml8192_20260317_080847/logs/confirm-vllm-0-15-0-longprompts-mbt2048-ml8192.log |
| confirm-vllm-015-main-longprompts-mbt-sweep-ml8192 | 20260317_080847 | confirm-vllm-0.15.0-longprompts-mbt4096-ml8192 | ok | /workspace/results/campaigns/confirm-vllm-015-main-longprompts-mbt-sweep-ml8192_20260317_080847/runs/confirm-vllm-0-15-0-longprompts-mbt4096-ml8192/local-vllm-public-long-prompts-confirm-vllm-0-15-0-longprompts-mbt4096-ml8192_20260317_081023 |  | 0.15.0 | 4096 | 8192 | vllm-015-main-confirmation | 973499d0c4f220a3d30bb9ab24170560edd8ec3c | 0.15.0 | 2.10.0+cpu | Intel(R) Xeon(R) Processor | 4 | 42.248834427221 | 16 | 4125.456243801091 | 0.0 | /workspace/results/campaigns/confirm-vllm-015-main-longprompts-mbt-sweep-ml8192_20260317_080847/logs/confirm-vllm-0-15-0-longprompts-mbt4096-ml8192.log |
| confirm-vllm-015-main-longprompts-mbt-sweep-ml8192 | 20260317_080847 | confirm-vllm-main-longprompts-mbt2048-ml8192 | ok | /workspace/results/campaigns/confirm-vllm-015-main-longprompts-mbt-sweep-ml8192_20260317_080847/runs/confirm-vllm-main-longprompts-mbt2048-ml8192/local-vllm-public-long-prompts-confirm-vllm-main-longprompts-mbt2048-ml8192_20260317_081206 |  | main | 2048 | 8192 | vllm-015-main-confirmation | 973499d0c4f220a3d30bb9ab24170560edd8ec3c | 8a680463f | 2.10.0+cpu | Intel(R) Xeon(R) Processor | 4 | 30.62004082658146 | 16 | 4386.303189599857 | 0.0 | /workspace/results/campaigns/confirm-vllm-015-main-longprompts-mbt-sweep-ml8192_20260317_080847/logs/confirm-vllm-main-longprompts-mbt2048-ml8192.log |
| confirm-vllm-015-main-longprompts-mbt-sweep-ml8192 | 20260317_080847 | confirm-vllm-main-longprompts-mbt4096-ml8192 | ok | /workspace/results/campaigns/confirm-vllm-015-main-longprompts-mbt-sweep-ml8192_20260317_080847/runs/confirm-vllm-main-longprompts-mbt4096-ml8192/local-vllm-public-long-prompts-confirm-vllm-main-longprompts-mbt4096-ml8192_20260317_081432 |  | main | 4096 | 8192 | vllm-015-main-confirmation | 973499d0c4f220a3d30bb9ab24170560edd8ec3c | 8a680463f | 2.10.0+cpu | Intel(R) Xeon(R) Processor | 4 | 32.37116147292159 | 16 | 4759.1499037991525 | 0.0 | /workspace/results/campaigns/confirm-vllm-015-main-longprompts-mbt-sweep-ml8192_20260317_080847/logs/confirm-vllm-main-longprompts-mbt4096-ml8192.log |
