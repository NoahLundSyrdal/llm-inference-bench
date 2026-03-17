# vLLM 0.15.0 vs main: overnight-style regression investigation (CPU)

## Scope
- Compared only `vLLM 0.15.0` vs `vLLM main` using existing campaign workflow.
- Used repo campaign runner/configs with conservative parallelism (`--max-workers 1`).
- GPU comparison was not possible in this environment (`nvidia-smi` unavailable), so this report is CPU-only.

## Campaigns run
1. Full matrix (clean run with preload):
   - `results/campaigns/overnight-vllm-015-main-cpu-regression_20260317_073938/`
2. Confirmation sweep (`max_model_len=4096`, long-prompts):
   - `results/campaigns/confirm-vllm-015-main-longprompts-mbt-sweep_20260317_075750/`
3. Confirmation sweep (`max_model_len=8192`, long-prompts):
   - `results/campaigns/confirm-vllm-015-main-longprompts-mbt-sweep-ml8192_20260317_080847/`

Merged machine-readable table:
- `results/campaign_runs.csv`

## Strongest validated finding (credible regression candidate)
Long-prompts workload with `max_num_batched_tokens=4096` shows repeatable `main` slowdown vs `0.15.0`:

- Confirm (ml4096): `41.18 -> 33.51 tok/s` (`-18.6%`), p95 `+9.6%`
- Confirm (ml8192): `42.25 -> 32.37 tok/s` (`-23.4%`), p95 `+15.4%`

Classification: **credible regression candidate**.
- Reason: reproduced in independent confirmation campaigns with both versions successful and `error_rate_at_max_concurrency=0.0`.

## Non-obvious behavior that did NOT survive controls
Long-prompts with `max_num_batched_tokens=2048` was unstable for `0.15.0`:
- Some runs showed high throughput, others collapsed with `error_rate=1.0` and low throughput.
- Example in confirmations: `0.15.0` at mbt2048 had `error_rate=1.0` while `main` was `error_rate=0.0`.

Classification: **likely benchmark/runtime artifact**, not a trustworthy regression signal.

## Environment/startup artifacts observed
- Main CPU runs can fail without `LD_PRELOAD` for `libtcmalloc` (`RuntimeError: libtcmalloc is not found in LD_PRELOAD`).
- Some early runs failed from this startup condition and were excluded from regression conclusions.

Classification: **environment artifact**.

## Reproduction commands (exact)
From repo root:

1) Full matrix run used for broad scan:
- `.venv-vllm-0.15.0/bin/python -m llmbench.cli campaign configs/overnight_vllm_015_main_campaign.yaml --max-workers 1`

2) Confirmation (ml4096):
- `.venv-vllm-0.15.0/bin/python -m llmbench.cli campaign configs/confirm_vllm_015_main_longprompts_mbt_sweep.yaml --max-workers 1`

3) Confirmation (ml8192):
- `.venv-vllm-0.15.0/bin/python -m llmbench.cli campaign configs/confirm_vllm_015_main_longprompts_mbt_sweep_ml8192.yaml --max-workers 1`

Each campaign config includes:
- `LD_PRELOAD=/lib/x86_64-linux-gnu/libtcmalloc_minimal.so.4`
- `baseline.version: "0.15.0"`

## Upstream issue readiness
Recommendation: **Yes, strong enough for an upstream issue**, focused on:
- CPU backend
- long-prompts workload
- `max_num_batched_tokens=4096`
- `main` throughput/p95 regression relative to `0.15.0`

Include both confirmation campaign directories above as attachments.
