.PHONY: dev migrate seed format lint test install

VENV := backend/.venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

# Load .env if present
ifneq (,$(wildcard backend/.env))
  include backend/.env
  export
endif

# Start backend (uvicorn :8000) and frontend (vite :3000) concurrently.
# Ctrl-C kills both via the trap.
dev:
	@trap 'kill 0' INT TERM EXIT; \
	(cd backend && $(CURDIR)/$(VENV)/bin/uvicorn app.main:app --reload --port 8000) & \
	(cd frontend && npm run dev) & \
	wait

# Apply Alembic migrations.
migrate:
	cd backend && $(CURDIR)/$(VENV)/bin/alembic upgrade head

# Seed 50 vehicles (v-1..v-50) and 20 zones — idempotent (safe to re-run).
seed:
	cd backend && $(CURDIR)/$(VENV)/bin/python -m app.seeds

# Format backend with ruff, frontend with eslint --fix.
format:
	$(CURDIR)/$(VENV)/bin/ruff format backend/
	cd frontend && npm run lint -- --fix

# Lint backend with ruff, frontend with eslint.
lint:
	$(CURDIR)/$(VENV)/bin/ruff check backend/
	cd frontend && npm run lint

# Run backend pytest suite.
test:
	cd backend && $(CURDIR)/$(VENV)/bin/pytest

# Install Python and Node dependencies.
install:
	$(PIP) install -r backend/requirements.txt
	cd frontend && npm install
