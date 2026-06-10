# ADR: Fleet Telemetry Monitor

## Key Decisions & Rationale

- **FastAPI over Django REST** — async-native; ASGI handles concurrent 50 Hz telemetry writes from 50 vehicles without thread-pool overhead; co-operative multitasking means each write yields at the DB call, not at an OS thread boundary.
- **PostgreSQL over SQLite** — `SELECT FOR UPDATE` provides true row-level locking for atomic fault transitions (cancel mission + create maintenance record in one transaction); zone traversal counters use `UPDATE zones SET entry_count = entry_count + 1 WHERE zone_id = $1`, which is safe under concurrent writes with no read needed.
- **Polling over WebSockets** — 2-3s lag is invisible to human operators monitoring 50 vehicles; polling eliminates connection-registry, keepalive, and reconnect complexity that would consume disproportionate budget.
- **Anomaly thresholds** — `battery_pct < 15` (critical low), `speed_mps > 8.0` while `status != moving` (motion anomaly), `error_codes` non-empty (any reported error), `status = fault` (explicit fault status transition).

## Spec Assumptions

- **Zone geometry** — the spec assumes the edge client populates `zone_entered` correctly on each telemetry event; the server performs no spatial computation. If GPS coordinates were provided instead, a spatial index (PostGIS) would be required.
- **Vehicle IDs** — vehicles are assumed to be `v-1` through `v-50`, pre-seeded at startup. There is no vehicle-registration endpoint; the 50-vehicle roster is a fixed constant. Any unknown `vehicle_id` in a telemetry event would fail a foreign-key check.

## Scale Path

- **Connection pool** — current `pool_size=10` (SQLAlchemy default with `max_overflow=20`). At ~500 vehicles, add PgBouncer in transaction-pooling mode to multiplex hundreds of short-lived connections onto the fixed pool.
- **Read replicas** — `GET /fleet/state` and `GET /anomalies` are read-only aggregations; route them to a PostgreSQL streaming replica to offload the primary under high-read load.
- **Redis cache** — fleet-state aggregation (`GROUP BY status`) is computed per-request; a short-lived Redis cache (TTL ~2s) would absorb polling bursts from many dashboard clients at scale.

## Deliberate Omissions

- **WebSocket real-time push** — polling at 2-3s meets the operator use-case; connection lifecycle adds complexity not justified for this assessment scope.
- **Docker Compose** — not required; local dev instructions assume PostgreSQL installed directly. Docker Compose is a v2 operations requirement (OPS-01).
- **Authentication / RBAC** — single-operator assessment scope; no user identity or access-control model required.
- **Mission management CRUD** — only the atomic fault→cancel-active-mission + create-maintenance-record operation is required. Full mission lifecycle (create, update, query) is out of scope.
- **Historical analytics / aggregations** — `GET /anomalies` supports time-range filtering for recent anomalies; no aggregation, trend, or time-series analytics are implemented.
- **Server-side zone geometry computation** — zone boundary evaluation is the edge client's responsibility; the server trusts `zone_entered` as declared.
