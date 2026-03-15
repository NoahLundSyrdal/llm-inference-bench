# llm-inference-bench

[![CI](https://github.com/noahlundsyrdal/llm-inference-bench/actions/workflows/ci.yml/badge.svg)](https://github.com/noahlundsyrdal/llm-inference-bench/actions/workflows/ci.yml)

Benchmark local vLLM via the OpenAI-compatible API. YAML configs, async runner, CSV + plots.

## Quickstart

```bash
python3 -m venv .venv
source .venv/bin/activate
make install
pip install vllm
make serve
make check
make bench
```

Without Hugging Face login: `make serve VLLM_MODEL=Qwen/Qwen2-0.5B-Instruct`, then `make check CONFIG=configs/local_vllm_public.yaml` and `make bench CONFIG=configs/local_vllm_public.yaml`. Default model (Llama) is gated — use `huggingface-cli login` if you need it.

### Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

### Start vLLM server

```bash
pip install vllm
make serve
```

Public model (no HF login): `make serve VLLM_MODEL=Qwen/Qwen2-0.5B-Instruct`

### Check + run benchmark

```bash
make check
make bench
```

Use `CONFIG=configs/local_vllm_public.yaml` for the public model.

## Example run (Qwen2-0.5B-Instruct)

```bash
make serve VLLM_MODEL=Qwen/Qwen2-0.5B-Instruct
make bench CONFIG=configs/local_vllm_public.yaml
```

Artifacts: `results/qwen2-0.5b-local-first-run/`

Latency went up with concurrency (p50 ~3.3s at c=1 to ~24s at c=16); throughput dropped (~29 to ~5 tok/s). Single worker saturates — more concurrency just added queueing.

![Latency vs concurrency](results/qwen2-0.5b-local-first-run/latency_vs_concurrency.png)

Second run with max_tokens=192: `results/qwen2-0.5b-maxtokens192/`. [notes/findings.md](notes/findings.md) has the comparison.

## Output layout

Run dir is `output_dir/<run_name>_<timestamp>/`. Contains: `raw_requests.jsonl`, `raw_requests.csv`, `aggregated.csv`, `failures.csv`, `summary.md`, `run_metadata.json`, `config_snapshot.yaml`, and the PNGs (`latency_vs_concurrency.png`, etc.).

## Config

[`configs/local_vllm.yaml`](configs/local_vllm.yaml) (Llama, gated) and [`configs/local_vllm_public.yaml`](configs/local_vllm_public.yaml) (Qwen2, no login). Important: `backend.base_url`, `backend.model`, `concurrency_sweep`, `workload.prompts_file`.

## Commands

- `make install` — install (Makefile uses `.venv/bin/python` if present)
- `make serve` — vLLM on port 8000. `VLLM_MODEL=...` to override model
- `make check` — ping vLLM and check model. `CONFIG=...` to pick config
- `make bench` — run benchmark
- `make lint`, `make test` — ruff + pytest
