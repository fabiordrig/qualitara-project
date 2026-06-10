# Fleet Telemetry Monitor

Real-time dashboard for 50 autonomous industrial vehicles — concurrent telemetry ingest, live anomaly detection, and atomic fault transitions backed by FastAPI + PostgreSQL.

## Quick Start

```bash
# 1. Clone and enter the repo
git clone <repo-url> && cd qualitara-project

# 2. Set up Python backend
python -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt

# 3. Set up frontend
cd frontend && npm install && cd ..

# 4. Configure the database
cp backend/.env.example backend/.env
# Edit backend/.env — set DATABASE_URL to your local PostgreSQL instance

# 5. Run migrations and start
make migrate
make dev
```

Open http://localhost:3000

## Prerequisites

- **Python 3.11+** — backend runtime
- **Node 18+** — frontend dev server
- **PostgreSQL** running locally with a `fleet` database created (`createdb fleet`)

No Docker required.

## Configuration

Only one environment variable is required:

```
DATABASE_URL=postgresql+asyncpg://user:password@localhost/fleet
```

Copy `backend/.env.example` to `backend/.env` and replace `user` and `password` with your PostgreSQL credentials. The `fleet` database must exist before running migrations.

## Running

| Target | What it does |
|--------|-------------|
| `make dev` | Start backend on :8000 and frontend on :3000 concurrently |
| `make migrate` | Run Alembic migrations (`alembic upgrade head`) |
| `make seed` | Seed 50 vehicles (v-1..v-50) and 20 zones — runs automatically on startup |
| `make format` | Format backend (black) and frontend (prettier) |
| `make lint` | Lint backend (ruff) and frontend (eslint) |
| `make test` | Run backend pytest suite |

> CORS is configured for `http://localhost:3000`. The frontend **must** run on port 3000 — if you change the port, update `backend/app/main.py` CORS settings accordingly.

## Architecture Overview

The backend is an async FastAPI service with SQLAlchemy + asyncpg writing to PostgreSQL. Zone traversal counters use atomic `UPDATE ... SET entry_count = entry_count + 1` statements; fault transitions use `SELECT FOR UPDATE` row-level locking to atomically cancel missions and create maintenance records in a single transaction. The React + TypeScript dashboard polls all endpoints every 2500ms via React Query.

See [docs/ADR.md](docs/ADR.md) for the full architecture decision record — key decisions, spec assumptions, scale path, and deliberate omissions.
