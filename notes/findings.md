# Findings

**Baseline:** `results/qwen2-0.5b-local-first-run/` — `configs/local_vllm_public.yaml`, max_tokens=96.

**Higher max_tokens:** `results/qwen2-0.5b-maxtokens192/` — `configs/local_vllm_public_maxtokens192.yaml`, max_tokens=192.

| Concurrency | p50 (96 tok) | p50 (192 tok) | tok/s (96) | tok/s (192) |
|-------------|--------------|---------------|------------|-------------|
| 1           | ~3.3 s       | ~6.1 s        | ~28.8      | ~28.4       |
| 16          | ~24 s        | ~37 s         | ~5.2       | ~5.0        |

Doubling max_tokens roughly doubled latency; tok/s stayed the same. Single worker is bottlenecked on token rate. No errors; curves were smooth.

**Longer prompts / larger context (third experiment):** `configs/local_vllm_public_long_prompts.yaml` — same model, same concurrency sweep [1, 2, 4, 8, 16], max_tokens=96, but workload uses `prompts/long_context.json` (significantly longer input prompts). Output dir: `results/qwen2-0.5b-long-prompts`. Run: `make bench CONFIG=configs/local_vllm_public_long_prompts.yaml`

| Concurrency | p50 (short) | p50 (long prompts) | tok/s (short) | tok/s (long prompts) |
|-------------|-------------|---------------------|---------------|----------------------|
| 1           | ~3.3 s      | ~3.6 s              | ~28.8         | ~23.8                |
| 16          | ~24 s       | ~25 s               | ~5.2          | ~4.3                 |

Longer context adds prefill cost: at c=1, latency and tok/s both reflect more input work; at high concurrency the gap is smaller (GPU bound on both). TTFT not populated in this run (backend/stream=false).

**Systems story:** Output length affects latency linearly (exp 2); longer context changes prefill and effective tok/s (exp 3). So: output length ≈ linear latency; input context ≈ different TTFT/prefill and slightly lower tok/s.

---

## Experiment batch: concurrency 32 + streaming + long prompts

Environment:
- vLLM: `0.15.0+cpu`
- torch: `2.10.0+cpu`
- model: `Qwen/Qwen2-0.5B-Instruct`
- hardware: 4 vCPU (`Intel(R) Xeon(R) Processor`)
- server command: `.venv/bin/vllm serve Qwen/Qwen2-0.5B-Instruct --host 0.0.0.0 --port 8000`

Configs:
- `configs/exp_vllm_public_concurrency32_stream_false.yaml`
- `configs/exp_vllm_public_concurrency32_stream_true.yaml`
- `configs/exp_vllm_public_long_prompts_concurrency32.yaml`

Run directories:
- `results/exp-qwen2-0.5b-concurrency32-stream-false/exp-vllm-public-concurrency32-stream-false_20260316_174216`
- `results/exp-qwen2-0.5b-concurrency32-stream-true/exp-vllm-public-concurrency32-stream-true_20260316_174654`
- `results/exp-qwen2-0.5b-long-prompts-concurrency32/exp-vllm-public-long-prompts-concurrency32_20260316_175154`

### A) Throughput scaling (`stream: false`)

| Concurrency | p95 latency | throughput tok/s |
|-------------|-------------|------------------|
| 1           | 3.41 s      | 29.19            |
| 8           | 4.97 s      | 19.36            |
| 16          | 6.96 s      | 14.10            |
| 32          | 10.64 s     | 9.50             |

Observations:
- Throughput declines steadily as concurrency increases (32 is ~32.6% of c=1 throughput).
- Latency rises superlinearly at higher concurrency; p95 is 1.53x higher at c=32 vs c=16.

### B) Streaming behavior (`stream: true` vs `stream: false`)

At concurrency 32:
- `stream=false`: p95 10.64 s, tok/s 9.50
- `stream=true`:  p95 10.58 s, tok/s 7.51, TTFT p50 508.9 ms

Observations:
- End-to-end p95 latency is similar between modes at c=32.
- Streaming TTFT p50 increases sharply with load (174.7 ms at c=16 to 508.9 ms at c=32, 2.91x).
- Streaming run has lower mean tok/s than non-streaming in this CPU setup.

### C) Longer prompts (context stress)

At concurrency 32:
- baseline prompts (`stream=false`): p95 10.64 s
- long prompts (`stream=false`): p95 13.81 s

Observation:
- Longer prompts increase tail latency under high concurrency (+29.8% p95 at c=32 vs baseline prompts).

### High-signal upstream candidate

Potential issue title:
- `TTFT jump at concurrency 32 with Qwen2-0.5B-Instruct on vLLM CPU backend`

Candidate claim from this batch:
- In `stream=true`, TTFT p50 jumps 2.91x between concurrency 16 and 32 (174.7 ms -> 508.9 ms), while p95 latency changes less sharply.

Next experiment step:
- Add explicit prompt-length buckets targeting ~512, ~2048, and ~8192 input tokens, then rerun the same concurrency sweep for strict context-length scaling curves.

---

## Experiment batch: explicit token buckets (512 / 2048 / 8192)

Environment:
- vLLM: `0.15.0+cpu`
- torch: `2.10.0+cpu`
- model: `Qwen/Qwen2-0.5B-Instruct`
- hardware: 4 vCPU (`Intel(R) Xeon(R) Processor`)
- server command: `.venv/bin/vllm serve Qwen/Qwen2-0.5B-Instruct --host 0.0.0.0 --port 8000`

Configs:
- `configs/exp_vllm_public_ctx512_stream_true.yaml`
- `configs/exp_vllm_public_ctx2048_stream_true.yaml`
- `configs/exp_vllm_public_ctx8192_stream_true.yaml`

Prompt sets (24 prompts each; exact bucketed token lengths):
- `prompts/context_512_tokens.json`
- `prompts/context_2048_tokens.json`
- `prompts/context_8192_tokens.json`

Run directories:
- `results/exp-qwen2-0.5b-ctx512-stream-true/exp-vllm-public-ctx512-stream-true_20260316_180650`
- `results/exp-qwen2-0.5b-ctx2048-stream-true/exp-vllm-public-ctx2048-stream-true_20260316_180935`
- `results/exp-qwen2-0.5b-ctx8192-stream-true/exp-vllm-public-ctx8192-stream-true_20260316_181339`

### Key metrics (stream=true)

| Bucket | Concurrency | p95 latency | TTFT p50 | Throughput tok/s |
|--------|-------------|-------------|----------|------------------|
| 512    | 1           | 3.05 s      | 315 ms   | 15.62            |
| 512    | 32          | 8.85 s      | 596 ms   | 5.10             |
| 2048   | 1           | 5.08 s      | 2.03 s   | 9.29             |
| 2048   | 32          | 16.34 s     | 1.35 s   | 2.90             |
| 8192   | 1           | 30.29 s     | 25.12 s  | 1.56             |
| 8192   | 32          | 47.82 s     | 4.16 s   | 0.95             |

### Strongest anomaly

For the 8192-token bucket, increasing concurrency from 1 to 2 *reduced* p95 latency sharply:
- p95(c=1): 30.29 s
- p95(c=2): 6.37 s
- ratio: **4.76x faster at c=2 than c=1**

This non-monotonic result is much larger than the same ratio at shorter buckets:
- 512 bucket: 1.08x (c1/c2)
- 2048 bucket: 1.49x (c1/c2)

Potential interpretation to validate upstream:
- Prefix-cache/warm-state effects across sweep steps may dominate c=1 in long-context runs, making raw concurrency curves misleading unless cache effects are controlled.

### Control run: disable prefix caching (c=1 vs c=2 only)

To check whether the c1->c2 inversion was a cache artifact, I reran 8192-token prompts on a separate server with prefix caching disabled:

- server: `.venv/bin/vllm serve Qwen/Qwen2-0.5B-Instruct --host 0.0.0.0 --port 8001 --no-enable-prefix-caching`
- config: `configs/exp_vllm_public_ctx8192_c1c2_no_prefix_cache.yaml`
- run dir: `results/exp-qwen2-0.5b-ctx8192-c1c2-no-prefix-cache/exp-vllm-public-ctx8192-c1c2-no-prefix-cache_20260316_230050`

Results:
- c=1: p95 31.93 s, TTFT p50 27.26 s, tok/s 1.393
- c=2: p95 61.11 s, TTFT p50 34.34 s, tok/s 0.703

Conclusion:
- With prefix caching disabled, latency behaves in the expected direction (c=2 slower than c=1).
- The earlier c1<c2 inversion is likely not a scheduler bug by itself; it is strongly confounded by warm-state/prefix-cache behavior across sweep order.

### Rerun with fixed thread settings (maintainer suggestion)

I reran the original 8192-token benchmark with fixed thread env vars on port 8000:

- server: `OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 vllm serve Qwen/Qwen2-0.5B-Instruct --host 0.0.0.0 --port 8000`
- config: `configs/exp_vllm_public_ctx8192_stream_true.yaml`
- run dir: `results/exp-qwen2-0.5b-ctx8192-stream-true/exp-vllm-public-ctx8192-stream-true_20260317_043809`

Results (still non-monotonic at low concurrency):
- c=1: p95 33.68 s, TTFT p50 26.63 s, tok/s 1.404
- c=2: p95 7.02 s, TTFT p50 0.47 s, tok/s 6.717
- ratio: **p95(c1)/p95(c2) = 4.80x**

Interpretation:
- Fixing OMP/MKL thread counts did **not** remove the c1->c2 inversion in this setup.
- This means thread variability alone does not explain the original anomaly.
