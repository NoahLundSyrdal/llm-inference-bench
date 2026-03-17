# llm-inference-bench

[![CI](https://github.com/noahlundsyrdal/llm-inference-bench/actions/workflows/ci.yml/badge.svg)](https://github.com/noahlundsyrdal/llm-inference-bench/actions/workflows/ci.yml)

**A lightweight benchmark harness for local vLLM serving** — measure latency and throughput across concurrency sweeps with YAML configs, an async client, CSV outputs, and plots.

---

## 30-second quickstart

```bash
python3 -m venv .venv && source .venv/bin/activate
make install && pip install vllm
make serve VLLM_MODEL=Qwen/Qwen2-0.5B-Instruct
make check CONFIG=configs/local_vllm_public.yaml
make bench CONFIG=configs/local_vllm_public.yaml
```

No Hugging Face login required for the public Qwen config. The default Llama config is gated; use `huggingface-cli login` if you want to run that.

---

## First benchmark (Qwen2-0.5B-Instruct)

![Latency vs concurrency](results/qwen2-0.5b-local-first-run/latency_vs_concurrency.png)

**Finding:** p50 latency rose from ~3.3s at concurrency 1 to ~24s at 16, while throughput fell from ~29 tok/s to ~5 tok/s. On this single-worker local setup, additional concurrency increased queueing much more than useful throughput. A second run with max_tokens=192 showed similar token generation rate, suggesting generation speed—not request overhead—was the main bottleneck.

**More runs and comparison:** [notes/findings.md](notes/findings.md)

---

## Usage notes

- **Output:** `output_dir/<run_name>_<timestamp>/` — `raw_requests.jsonl`, `aggregated.csv`, `summary.md`, PNGs.
- **Config:** [`configs/local_vllm_public.yaml`](configs/local_vllm_public.yaml) (public model), [`configs/local_vllm.yaml`](configs/local_vllm.yaml) (Llama, gated). Set `backend.base_url`, `backend.model`, `concurrency_sweep`, `workload.prompts_file`.
- **Commands:** `make serve` (vLLM on 8000), `make check`, `make bench`, `make lint`, `make test`. Override: `CONFIG=...`, `VLLM_MODEL=...`.

## Overnight campaign runs (regressions + tuning)

Use the campaign runner to execute many benchmark experiments from one YAML (including vLLM version regressions, CPU vs GPU, and scheduler-flag sweeps).

Example:

```bash
make campaign CONFIG=configs/nightly_vllm_regression_campaign.yaml
```

Optional bounded parallelism:

```bash
python -m llmbench.cli campaign configs/nightly_vllm_regression_campaign.yaml --max-workers 2
```

Dry-run first to inspect the generated experiment plan:

```bash
python -m llmbench.cli campaign configs/nightly_vllm_regression_campaign.yaml --dry-run
```

The sample campaign config already includes:
- Regression axes for `0.14.0`, `0.15.0`, and `main`
- Device axis for `cpu` vs `cuda`
- Scheduler axes for `--max-num-batched-tokens`, `--max-model-len`, and `--gpu-memory-utilization`

Campaign output includes:
- `campaign_runs.csv` (one row per experiment with key rollup metrics)
- `campaign_report.md` (ranked throughput table + failures)
- Per-experiment run directories and server logs

To run all night in the background:

```bash
nohup .venv/bin/python -m llmbench.cli campaign configs/nightly_vllm_regression_campaign.yaml > /tmp/llmbench_campaign.log 2>&1 &
```

## Regression campaign example

Run a 48-experiment sweep across versions and scheduler flags:

```bash
make campaign CONFIG=configs/nightly_vllm_regression_campaign.yaml
```

Top-level outputs (inside the campaign run directory):

```text
results/campaigns/<campaign_name_timestamp>/
  campaign_runs.csv
  campaign_report.md
  runs/
    exp_...
```

## Using this for OSS contributions

Treat this repo as a performance investigation tool for upstream projects.

### Investigation loop

1. Run benchmark.
2. Observe odd behavior.
3. Create minimal reproduction.
4. Open upstream issue.
5. Potentially submit fix.

Start with the project this repo already supports well: **vLLM**.

### High-signal vLLM investigations

1. **Throughput scaling**
   - Sweep concurrency: `[1, 2, 4, 8, 16, 32]`
   - Look for early throughput plateaus, sudden drops, and instability.
2. **Context-length scaling**
   - Test prompt lengths: `512`, `2048`, `8192` tokens.
   - Look for large TTFT spikes and nonlinear latency growth.
3. **Streaming behavior**
   - Compare `stream: true` vs `stream: false`.
   - Compare TTFT and end-to-end latency.

### What makes a good upstream issue

Maintainers respond best to issues that are reproducible and artifact-backed.

- **Title:** specific symptom + model + condition (example: `Latency spike at concurrency 16 with Qwen2-0.5B on vLLM`)
- **Environment:** vLLM version, GPU, model, server command
- **Reproduction:** exact serve command and benchmark command
- **Benchmark config:** YAML snippet
- **Results:** attached plot + `aggregated.csv`
- **Observation:** one clear quantitative claim (example: `p95 latency increases 3x between concurrency 8 and 16`)

Minimal issue body template:

```text
Using llm-inference-bench we observed a latency cliff when increasing concurrency.

Environment:
- vLLM:
- GPU:
- Model:
- Server command:

Reproduction:
1) vllm serve ...
2) make bench CONFIG=...

Benchmark config:
<yaml snippet>

Results:
- plot: <attach>
- aggregated.csv: <attach>

Observation:
- p95 latency increases ...
```

### Other contribution paths

- Add benchmark coverage upstream (example targets in vLLM: `benchmarks/local_concurrency_scaling.py`, `docs/performance/local_serving_benchmarks.md`).
- File regression reports across versions (example: vLLM `0.5.0` vs `0.5.1` throughput regression).
- Extend later to compare other backends (TGI, SGLang, llama.cpp) once vLLM workflow is solid.

The most valuable OSS output from this repo is **high-quality performance regression evidence**.

## Repo layout

- `configs/` — benchmark configs
- `prompts/` — prompt datasets
- `results/` — saved benchmark runs
- `notes/` — experiment summaries
- `src/llmbench/` — benchmark implementation

## Why this exists

Local serving stacks are easy to run but harder to evaluate consistently. This project makes it easy to run reproducible concurrency sweeps against vLLM, inspect request-level behavior, and generate artifacts that are useful for debugging regressions, performance bottlenecks, or future upstream issues.

## Roadmap

- Longer-context benchmarks
- Stream-mode TTFT validation
- Additional public model comparisons
- Future multi-backend support
