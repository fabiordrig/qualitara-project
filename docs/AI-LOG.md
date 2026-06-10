# AI Interaction Log

## Prompts Issued

The entire project was driven by the GSD (Get Shit Done) plan-then-execute workflow. No ad-hoc prompting or inline code generation was used outside of structured plan execution.

- `/gsd-plan-phase 1` — gathered context for backend core (schema, ORM, API shape, concurrency patterns); produced 03 plans covering DB foundation, telemetry ingest with TDD, anomalies/zone/fleet endpoints.
- `/gsd-execute-phase 1` — executed Phase 1 plans atomically: DB schema + Alembic migrations + startup seeding (plan 01), telemetry ingest with atomic zone counter and fault transition (plan 02, TDD), GET /anomalies + /zones/counts + /fleet/state endpoints (plan 03).
- `/gsd-plan-phase 2` — gathered context for React dashboard; produced plans for GET /vehicles backend addition, Vite scaffold + React Query wiring, VehicleTable component (TanStack Table + shadcn), and header/zone panel composition.
- `/gsd-execute-phase 2` — executed Phase 2 plans: added GET /vehicles to backend fleet router, scaffolded Vite + React + TypeScript project, built VehicleTable with column sort, wired fleet summary header and zone counts panel.
- `/gsd-plan-phase 3` — gathered context for documentation deliverables; produced plans for ADR + AI log + README (this plan) and Makefile.
- `/gsd-execute-phase 3` — executing Phase 3 plans: writing ADR, AI log, README, and Makefile.

## Outputs Received

- **Phase 1** — An async FastAPI backend with SQLAlchemy 2.0 + asyncpg ORM, Alembic migration for `vehicles`, `missions`, `anomalies`, and `zones` tables, and startup seeding of 50 vehicles (v-1..v-50) and 20 zones. Telemetry ingest at POST /telemetry atomically increments zone counters via `UPDATE zones SET entry_count = entry_count + 1 WHERE zone_id = $1`, handles fault transitions using `SELECT FOR UPDATE` on the vehicle row inside a single transaction (cancel active mission + insert maintenance record), and detects anomalies inline. GET /fleet/state, GET /zones/counts, GET /anomalies, and GET /vehicles endpoints were all delivered with passing concurrency tests.

- **Phase 2** — A Vite + React + TypeScript frontend polling the backend every 2500ms via React Query (`refetchInterval: 2500`) and Axios. Delivered: a TanStack Table vehicle list (50 rows, column sort, status badge, latest-anomaly inline), a fleet summary header (idle/moving/charging/fault counts + "last updated" timestamp), a zone-count panel (sorted descending by entry count), and a shared `lib/apiClient.ts` Axios instance pointing to `http://localhost:8000`.

- **Phase 3** — Three assessment deliverable documents: this AI log, the ADR at `docs/ADR.md`, and a root `README.md`.

## Corrections Made

All corrections were caught during the structured verification step in each plan's execution, not during code review. The human reviewer identified discrepancies between the plan's acceptance criteria and the produced code; Claude corrected them:

- **WR-06: WHERE filters applied before LIMIT/OFFSET in anomaly query** — the initial anomaly query applied `LIMIT`/`OFFSET` before the `vehicle_id`/time-range `WHERE` clause, producing incorrect pagination results. Fixed by reordering the query builder to apply filters first.
- **WR-05: Shared Axios instance extracted to `lib/apiClient.ts` with env var** — each API hook was constructing its own Axios instance with a hardcoded base URL. Extracted to a single `lib/apiClient.ts` module reading `VITE_API_BASE_URL` from the environment, with `http://localhost:8000` as the fallback.
- **WR-04: CORS tightened to `allow_credentials=False`, GET-only, `Content-Type` only** — initial CORS middleware was overly permissive. Tightened to match the dashboard's actual access pattern: read-only GET requests, no credentials, only `Content-Type` header allowed.
- **WR-03: `FleetStateResponse` wired as `response_model` on `GET /fleet/state`** — the endpoint was returning the correct data but without the Pydantic `response_model` declaration, which meant FastAPI was not validating or serializing the response shape. Added the `response_model=list[FleetStateResponse]` annotation.
- **WR-02: Guarded `dataUpdatedAt === 0` to show a dash before first fetch** — the "last updated" timestamp in the header showed an invalid date string before the first successful poll. Added a guard to display `—` until `dataUpdatedAt` is non-zero.

## Reflection

- **What worked** — the plan-then-execute GSD workflow enforced a clear boundary between design and implementation. Specifying concurrency patterns explicitly in the plan (which SQL statement to use for zone counters, which lock mode for fault transitions) produced correct concurrent behavior on the first implementation attempt. The structured verification step in each plan caught all five regressions before they were merged.

- **What didn't** — several plans required correction passes before acceptance. The anomaly pagination bug (WR-06) and the CORS misconfiguration (WR-04) suggest that Claude defaults to "obvious" implementations that may not match the exact constraints specified. Tighter acceptance criteria in the plan (e.g., an explicit SQL snippet for the query order) would reduce correction cycles.

- **What surprised** — the amount of concurrency-pattern domain knowledge that had to be encoded in the plan to get correct output. Stating "use SELECT FOR UPDATE" vs. "use an atomic UPDATE" for different operations was necessary; without those constraints, both patterns look equivalent from a pure-Python perspective and Claude would have chosen one arbitrarily.

- **Takeaway** — for correctness-critical paths (concurrency, security, pagination), the planner must encode the exact implementation constraint, not just the outcome. Outcome-only specifications ("zone counts must be accurate under concurrency") produce ambiguous implementation space; mechanism-level specifications ("use `UPDATE zones SET entry_count = entry_count + 1 WHERE zone_id = $1`") eliminate the ambiguity.
