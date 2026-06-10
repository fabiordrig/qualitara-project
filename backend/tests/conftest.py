# backend/tests/conftest.py
"""
Test fixtures for the Fleet Telemetry Monitor backend.

Database isolation strategy:
- Uses a dedicated `fleet_test` database (separate from dev `fleet` database).
- DATABASE_URL env var is set before app module import so app/database.py reads the test URL.
- The engine used in the app's `get_db` dependency is replaced per-test with a NullPool
  engine so asyncpg connections are not pooled and do not bind to a stale event loop.
  This prevents the "Future attached to a different loop" RuntimeError that occurs when
  pytest-asyncio creates a new event loop per test but the module-level pool was created
  in a prior loop.
- Each test gets a fresh ASGI client that runs the lifespan (seeding). Seeding is safe to
  run per-test because seed functions use on_conflict_do_nothing.
- Transient tables (missions, maintenance_records, telemetry_events, anomalies) are
  TRUNCATED and zone entry_counts are RESET to 0 before each test that uses the DB.
  This is required because concurrent-commit tests (test_concurrency.py,
  test_fault_transition.py) commit real data that must not leak between tests.
  Pure unit tests (TestDetectAnomaly, TestTelemetryEventCreateValidation) do not use
  DB and are unaffected by this truncation.
"""
import os

# Must set DATABASE_URL before any app module import — database.py reads it at load time
_current_user = os.environ.get("USER", "postgres")
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    f"postgresql+asyncpg://{_current_user}@localhost/fleet_test",
)
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from httpx import AsyncClient, ASGITransport  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker  # noqa: E402
from sqlalchemy.pool import NullPool  # noqa: E402

import app.database as _db_module  # noqa: E402 — import module to patch it
from app.main import app  # noqa: E402 — import after env override


@pytest_asyncio.fixture(autouse=True)
async def patch_db_engine():
    """
    Replace the app's module-level engine and session_maker with NullPool variants
    for each test. This prevents asyncpg connections from being pooled across tests
    (each pytest-asyncio test runs in its own event loop in asyncio_mode=auto).
    """
    test_engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool, echo=False)
    test_session_maker = async_sessionmaker(test_engine, expire_on_commit=False)

    # Patch the module-level objects that app code references
    original_engine = _db_module.engine
    original_session_maker = _db_module.async_session_maker

    _db_module.engine = test_engine
    _db_module.async_session_maker = test_session_maker

    # Truncate transient tables before each test so committed data from previous
    # tests does not bleed into the next. This is required for tests that commit
    # real data (fault transitions, concurrency) instead of wrapping in rollback.
    # TRUNCATE ... CASCADE handles FK dependencies (anomalies → telemetry_events).
    # Zone entry_counts are reset to 0 so concurrency counter tests start clean.
    # Vehicle statuses are reset to 'idle'/100% battery so fleet-state tests pass
    # after fault or ingest tests have mutated vehicle rows.
    async with test_engine.connect() as conn:
        await conn.execute(text(
            "TRUNCATE TABLE anomalies, maintenance_records, missions, telemetry_events CASCADE"
        ))
        await conn.execute(text("UPDATE zones SET entry_count = 0"))
        await conn.execute(text(
            "UPDATE vehicles SET current_status = 'idle', current_battery = 100.0, latest_seen = NULL"
        ))
        await conn.commit()

    yield

    # Restore originals and dispose test engine
    _db_module.engine = original_engine
    _db_module.async_session_maker = original_session_maker
    await test_engine.dispose()


@pytest_asyncio.fixture
async def client(patch_db_engine):
    """
    Per-test ASGI client with the lifespan (seeding) running via the patched engine.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
