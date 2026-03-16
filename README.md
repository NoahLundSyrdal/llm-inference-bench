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
