PYTHON ?= $(if $(wildcard .venv/bin/python),.venv/bin/python,python3)
CONFIG ?= configs/local_vllm.yaml

.PHONY: install lint test check bench serve campaign

VLLM_MODEL ?= meta-llama/Llama-3.1-8B-Instruct
serve:
	.venv/bin/vllm serve $(VLLM_MODEL) --host 0.0.0.0 --port 8000

install:
	$(PYTHON) -m pip install -e '.[dev]'

lint:
	$(PYTHON) -m ruff check src tests

test:
	$(PYTHON) -m pytest -q

check:
	$(PYTHON) -m llmbench.cli check $(CONFIG)

bench:
	$(PYTHON) -m llmbench.cli run $(CONFIG)

campaign:
	$(PYTHON) -m llmbench.cli campaign $(CONFIG)
