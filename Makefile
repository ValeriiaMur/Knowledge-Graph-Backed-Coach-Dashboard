.PHONY: install dev test lint eval backend frontend check

install:
	cd backend && pip install -e ".[dev]"
	cd frontend && npm install

dev:
	@trap 'kill 0' INT; \
	(cd backend && python3 -m uvicorn app.main:app --reload --port 8000) & \
	(cd frontend && npm run dev) & \
	wait

backend:
	cd backend && python3 -m uvicorn app.main:app --reload --port 8000

frontend:
	cd frontend && npm run dev

test:
	cd backend && python -m pytest tests -q

lint:
	cd backend && ruff check . && ruff format --check .
	cd frontend && npm run lint

eval:
	cd backend && python -m app.eval.run

check: lint test
