.PHONY: help setup backend frontend test lint

help:
	@echo "WiFiDeck — dev targets"
	@echo "  make setup      create backend venv + install deps, install frontend deps"
	@echo "  make backend    run the API on 127.0.0.1:8787 (reload)"
	@echo "  make frontend   run the Vite dev server on :5173"
	@echo "  make test       run backend + frontend tests"
	@echo "  make lint       run backend (ruff) + frontend (eslint) linters"

setup:
	cd backend && python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
	cd frontend && npm install

backend:
	cd backend && . .venv/bin/activate 2>/dev/null; \
	WIFIDECK_TOKEN=$${WIFIDECK_TOKEN:-dev-token-change-me} \
	uvicorn app.main:app --reload --host 127.0.0.1 --port 8787

frontend:
	cd frontend && npm run dev

test:
	cd backend && PYTHONPATH=. python3 -m pytest -q
	cd frontend && npm run test

lint:
	cd backend && ruff check .
	cd frontend && npm run lint
