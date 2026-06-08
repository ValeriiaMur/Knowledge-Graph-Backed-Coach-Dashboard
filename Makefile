.PHONY: install dev test lint eval eval-ragas backend frontend check

# Use python3 by default (macOS has no bare `python`). Override: make PY=python test
PY ?= python3

install:
	cd backend && $(PY) -m pip install -e ".[dev]"
	cd frontend && npm install

dev:
	@trap 'kill 0' INT; \
	(cd backend && $(PY) -m uvicorn app.main:app --reload --port 8000) & \
	(cd frontend && npm run dev) & \
	wait

backend:
	cd backend && $(PY) -m uvicorn app.main:app --reload --port 8000

frontend:
	cd frontend && npm run dev

test:
	cd backend && $(PY) -m pytest tests -q

lint:
	cd backend && ruff check . && ruff format --check .
	cd frontend && npm run lint

eval:
	cd backend && $(PY) -m app.eval.run

# Answer-quality eval for the copilot (LLM-judge, non-deterministic). Separate
# from `eval` on purpose — needs API keys + `.[eval]` deps; not a CI gate.
eval-ragas:
	cd backend && $(PY) -m app.eval.ragas_eval

check: lint test
