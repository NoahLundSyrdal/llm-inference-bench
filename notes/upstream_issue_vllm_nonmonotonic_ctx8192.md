# Draft upstream issue (ready to file)

## Title
Non-monotonic latency with 8192-token prompts: p95 at concurrency 1 is 4.76x slower than concurrency 2 (Qwen2-0.5B, vLLM CPU)

## Body
Using `llm-inference-bench`, we observed a non-monotonic latency pattern with long prompts: concurrency `1` is significantly slower than concurrency `2` for the same workload.

### Environment
- vLLM: `0.15.0+cpu`
- torch: `2.10.0+cpu`
- model: `Qwen/Qwen2-0.5B-Instruct`
- hardware: `Intel(R) Xeon(R) Processor`, 4 vCPU
- OS: Linux (Ubuntu 24.04)

### Server command
`vllm serve Qwen/Qwen2-0.5B-Instruct --host 0.0.0.0 --port 8000`

### Reproduction
1. Start server using command above.
2. Run benchmark:
   `python -m llmbench.cli run configs/exp_vllm_public_ctx8192_stream_true.yaml`

Config used:

```yaml
name: exp-vllm-public-ctx8192-stream-true
backend:
  engine: vllm
  base_url: http://localhost:8000
  model: Qwen/Qwen2-0.5B-Instruct
  endpoint: /v1/chat/completions

generation:
  max_tokens: 64
  temperature: 0.0
  top_p: 1.0
  stream: true
  request_timeout_s: 900

workload:
  label: ctx-8192
  prompts_file: ../prompts/context_8192_tokens.json
  prompt_field: prompt
  num_requests: 24
  shuffle: true
  seed: 42

concurrency_sweep: [1, 2, 4, 8, 16, 32]
repetitions: 1
```

### Results
From `aggregated.csv`:

| concurrency | p95 latency (ms) | TTFT p50 (ms) | throughput tok/s |
|---|---:|---:|---:|
| 1 | 30294.3 | 25119.2 | 1.558 |
| 2 | 6365.0 | 428.1 | 7.384 |
| 4 | 9911.0 | 955.8 | 4.568 |
| 8 | 17367.9 | 1773.0 | 2.629 |
| 16 | 32242.4 | 3101.9 | 1.767 |
| 32 | 47823.3 | 4164.4 | 0.951 |

### Observation
- `p95(c=1) / p95(c=2) = 4.76x`, i.e. concurrency 2 is much faster than concurrency 1 on the same 8192-token workload.
- This looks non-monotonic and unexpected for a pure concurrency sweep.

### Additional context
Running the same methodology at shorter contexts:
- 512-token bucket: `p95(c=1)/p95(c=2) = 1.08x`
- 2048-token bucket: `p95(c=1)/p95(c=2) = 1.49x`

The 8192-token effect is much larger and may indicate sweep-order warm-state interaction (e.g. prefix cache behavior) rather than pure concurrency scaling.

### Attachments
- Plot: `latency_vs_concurrency.png`
- Plot: `ttft_vs_concurrency.png`
- Data: `aggregated.csv`
- Full run summary: `summary.md`

Artifact paths from this run:
- `results/exp-qwen2-0.5b-ctx8192-stream-true/exp-vllm-public-ctx8192-stream-true_20260316_181339/latency_vs_concurrency.png`
- `results/exp-qwen2-0.5b-ctx8192-stream-true/exp-vllm-public-ctx8192-stream-true_20260316_181339/ttft_vs_concurrency.png`
- `results/exp-qwen2-0.5b-ctx8192-stream-true/exp-vllm-public-ctx8192-stream-true_20260316_181339/aggregated.csv`
- `results/exp-qwen2-0.5b-ctx8192-stream-true/exp-vllm-public-ctx8192-stream-true_20260316_181339/summary.md`
