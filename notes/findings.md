# Findings

**Baseline:** `results/qwen2-0.5b-local-first-run/` — `configs/local_vllm_public.yaml`, max_tokens=96.

**Higher max_tokens:** `results/qwen2-0.5b-maxtokens192/` — `configs/local_vllm_public_maxtokens192.yaml`, max_tokens=192.

| Concurrency | p50 (96 tok) | p50 (192 tok) | tok/s (96) | tok/s (192) |
|-------------|--------------|---------------|------------|-------------|
| 1           | ~3.3 s       | ~6.1 s        | ~28.8      | ~28.4       |
| 16          | ~24 s        | ~37 s         | ~5.2       | ~5.0        |

Doubling max_tokens roughly doubled latency; tok/s stayed the same. Single worker is bottlenecked on token rate. No errors; curves were smooth.
