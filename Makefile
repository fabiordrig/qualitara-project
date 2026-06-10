.PHONY: dev migrate seed format lint test install

# Start backend (uvicorn :8000) and frontend (vite :3000) concurrently.
# Ctrl-C kills both via the trap.
dev:
	@trap 'kill 0' INT TERM EXIT; \
	(cd backend && uvicorn app.main:app --reload --port 8000) & \
	(cd frontend && npm run dev) & \
	wait

# Apply Alembic migrations.
migrate:
	cd backend && alembic upgrade head

# Seed 50 vehicles (v-1..v-50) and 20 zones — idempotent (safe to re-run).
seed:
	cd backend && python -m app.seeds

# Format backend with ruff, frontend with eslint --fix.
format:
	cd backend && ruff format .
	cd frontend && npm run lint -- --fix

# Lint backend with ruff, frontend with eslint.
lint:
	cd backend && ruff check .
	cd frontend && npm run lint

# Run backend pytest suite.
test:
	cd backend && pytest

# Install Python and Node dependencies.
install:
	pip install -r backend/requirements.txt
	cd frontend && npm install
