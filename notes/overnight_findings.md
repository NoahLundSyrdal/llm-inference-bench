# Overnight findings: vLLM 0.15.0 vs main (CPU)

## What was run
- Full campaign:
  - `configs/overnight_vllm_015_main_campaign.yaml`
  - command: `.venv-vllm-0.15.0/bin/python -m llmbench.cli campaign configs/overnight_vllm_015_main_campaign.yaml --max-workers 1`
  - output: `results/campaigns/overnight-vllm-015-main-cpu-regression_20260317_073938/`
- Confirmation campaign (`ml4096`):
  - `configs/confirm_vllm_015_main_longprompts_mbt_sweep.yaml`
  - command: `.venv-vllm-0.15.0/bin/python -m llmbench.cli campaign configs/confirm_vllm_015_main_longprompts_mbt_sweep.yaml --max-workers 1`
  - output: `results/campaigns/confirm-vllm-015-main-longprompts-mbt-sweep_20260317_075750/`
- Confirmation campaign (`ml8192`):
  - `configs/confirm_vllm_015_main_longprompts_mbt_sweep_ml8192.yaml`
  - command: `.venv-vllm-0.15.0/bin/python -m llmbench.cli campaign configs/confirm_vllm_015_main_longprompts_mbt_sweep_ml8192.yaml --max-workers 1`
  - output: `results/campaigns/confirm-vllm-015-main-longprompts-mbt-sweep-ml8192_20260317_080847/`

## Strongest finding
For long-prompts + `max_num_batched_tokens=4096`, `main` is consistently slower than `0.15.0`:
- `ml4096`: `41.18 -> 33.51 tok/s` (`-18.6%`)
- `ml8192`: `42.25 -> 32.37 tok/s` (`-23.4%`), with p95 `+15.4%`

## Classification
- Strongest finding: **credible regression / upstream issue candidate**.
- Additional anomalies at `max_num_batched_tokens=2048`: **likely benchmark/runtime artifact** (0.15.0 intermittently showed `error_rate=1.0`, making those pairwise comparisons unreliable).
- Missing GPU branch: **environment limitation** (no GPU tooling/runtime detected).

## Exact reproducibility setup
Versioned vLLM envs used:
- `.venv-vllm-0.15.0` with `vllm 0.15.0+cpu`
- `.venv-vllm-main` with `vllm 0.17.2rc1.dev4+g8a680463f` (main build)

Common server control included in campaign configs:
- `LD_PRELOAD=/lib/x86_64-linux-gnu/libtcmalloc_minimal.so.4`

To reproduce strongest finding quickly:
1. Run `configs/confirm_vllm_015_main_longprompts_mbt_sweep.yaml`
2. Run `configs/confirm_vllm_015_main_longprompts_mbt_sweep_ml8192.yaml`
3. Compare rows where `max_num_batched_tokens=4096` and `error_rate_at_max_concurrency=0.0`.

## Is this strong enough for an upstream vLLM issue?
**Yes.**  
The mbt=4096 long-prompts regression reproduced in two independent confirmation campaigns with clean (`error_rate=0.0`) comparisons across both versions.
