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
