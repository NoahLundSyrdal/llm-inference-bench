# AGENTS.md

## Cursor Cloud specific instructions

This is a Python benchmarking CLI (`llmbench`) for measuring vLLM inference latency/throughput. No Docker, databases, or web frontend involved.

### Quick reference

- **Lint:** `make lint` (runs `ruff check src tests`)
- **Test:** `make test` (runs `pytest -q`; all tests mock the backend — no GPU or vLLM server needed)
- **CLI:** `python -m llmbench.cli --help` for available commands (`check`, `run`)
- **Install deps:** `make install` (runs `pip install -e '.[dev]'`)

See `README.md` and `Makefile` for the full set of available commands.

### Environment notes

- Python >=3.11 is required. The venv lives at `.venv/`.
- Always activate the venv before running commands: `source .venv/bin/activate`
- The `python3.12-venv` system package is needed to create the venv on Ubuntu (not installed by default in this VM image).
- Running `make check` or `make bench` requires a live vLLM server on `localhost:8000`, which requires a GPU. In GPU-less environments, the CLI will report "Could not connect to vllm" — this is expected.
- Unit tests do **not** require a vLLM server; they mock the backend.
