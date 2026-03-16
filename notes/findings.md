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
