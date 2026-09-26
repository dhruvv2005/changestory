# ChangeStory Makefile for local development and testing

.PHONY: help install dev-backend dev-frontend test test-backend test-sample build-frontend demo-a demo-b demo-c

help:
	@echo "ChangeStory Developer Commands:"
	@echo "  make install         - Install CLI and dependencies"
	@echo "  make dev-backend     - Run FastAPI backend on port 8000"
	@echo "  make dev-frontend    - Run Next.js dashboard on port 3000"
	@echo "  make test            - Run all backend and sample project tests"
	@echo "  make test-backend    - Run backend unit and integration tests"
	@echo "  make test-sample     - Run sample project test suite"
	@echo "  make build-frontend  - Build production Next.js frontend"
	@echo "  make demo-a          - Run CLI analysis on Scenario A"
	@echo "  make demo-b          - Run CLI analysis on Scenario B"
	@echo "  make demo-c          - Run CLI analysis on Scenario C"

install:
	.\venv\Scripts\pip install -e .\cli
	cd frontend && npm install

dev-backend:
	cd backend && ..\venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

dev-frontend:
	cd frontend && npm run dev

test: test-backend test-sample

test-backend:
	cd backend && ..\venv\Scripts\python -m pytest tests -v

test-sample:
	.\venv\Scripts\python -m pytest sample-project\tests -v

build-frontend:
	cd frontend && npm run build

demo-a:
	.\venv\Scripts\changestory analyze --diff-file fixtures\diffs\scenario_a.diff --no-browser

demo-b:
	.\venv\Scripts\changestory analyze --diff-file fixtures\diffs\scenario_b.diff --no-browser

demo-c:
	.\venv\Scripts\changestory analyze --diff-file fixtures\diffs\scenario_c.diff --no-browser
