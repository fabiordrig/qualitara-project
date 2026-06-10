# backend/tests/test_foundation.py
"""
Foundation tests for Phase 1 Plan 1.

Covers:
- ROADMAP success criterion 1: read endpoints reflect persisted data
- ROADMAP success criterion 5: fleet state counts vehicles, not events
- 20 zones seeded at entry_count=0
- 50 vehicles seeded
- Idempotent seeding (no duplicates on repeated seed calls)
- Fleet state counts per vehicle, not per event (FLEET-02, Pitfall 6)
"""
import pytest
import pytest_asyncio
from datetime import datetime, timezone
from httpx import AsyncClient

import app.database as _db_module
from app.seeds import seed_zones, seed_vehicles
from app.zones.models import Zone
from app.fleet.models import Vehicle
from app.telemetry.models import TelemetryEvent


@pytest.mark.asyncio
async def test_seeding_creates_20_zones(client: AsyncClient):
    """After app startup, GET /zones/counts returns exactly 20 zones at entry_count=0."""
    response = await client.get("/zones/counts")
    assert response.status_code == 200
    zones = response.json()
    assert len(zones) == 20, f"Expected 20 zones, got {len(zones)}"
    for zone in zones:
        assert zone["entry_count"] == 0, (
            f"Zone {zone['zone_id']} has entry_count={zone['entry_count']}, expected 0"
        )


@pytest.mark.asyncio
async def test_seeding_creates_50_vehicles(client: AsyncClient):
    """After startup, GET /fleet/state counts sum to 50 — one entry per vehicle."""
    response = await client.get("/fleet/state")
    assert response.status_code == 200
    fleet = response.json()
    total = sum(row["count"] for row in fleet)
    assert total == 50, f"Expected 50 vehicles total, got {total}"


@pytest.mark.asyncio
async def test_fleet_state_counts_vehicles_not_events(client: AsyncClient):
    """
    FLEET-02: GET /fleet/state queries the vehicles table (GROUP BY current_status),
    not the telemetry_events table.

    Proof: the response sums to exactly 50 (vehicle count), and has exactly 1 status
    group ("idle") since no telemetry has been processed. If the router were accidentally
    counting from telemetry_events the sum would be 0 (no events inserted via seeding).

    This validates Pitfall 6 avoidance: fleet state reflects per-vehicle current status,
    not cumulative event history.
    """
    response = await client.get("/fleet/state")
    assert response.status_code == 200
    fleet = response.json()

    # Must sum to exactly 50 vehicles
    total = sum(row["count"] for row in fleet)
    assert total == 50, (
        f"Fleet state sums to {total} instead of 50; "
        f"indicates events are being counted instead of vehicles (Pitfall 6). "
        f"Fleet response: {fleet}"
    )

    # At seeding time all vehicles are 'idle' — fleet state must reflect vehicle table
    statuses = {row["status"]: row["count"] for row in fleet}
    assert "idle" in statuses, f"Expected 'idle' status group in fleet state; got: {statuses}"
    assert statuses["idle"] == 50, (
        f"Expected 50 idle vehicles at seed time, got {statuses['idle']}"
    )


@pytest.mark.asyncio
async def test_seeding_idempotent(client: AsyncClient):
    """
    Running seed_zones/seed_vehicles multiple times must produce no duplicates
    and no IntegrityError — idempotent via on_conflict_do_nothing.

    We invoke seeding explicitly (in addition to the lifespan seeding triggered by
    the client fixture) and then verify the zone/vehicle counts remain at 20/50.
    """
    async with _db_module.async_session_maker() as session:
        async with session.begin():
            # Second seed call — on_conflict_do_nothing must absorb it silently
            await seed_zones(session)
            await seed_vehicles(session)

    # After double-seeding, counts must still be exactly 20 and 50
    zone_response = await client.get("/zones/counts")
    assert zone_response.status_code == 200
    assert len(zone_response.json()) == 20

    fleet_response = await client.get("/fleet/state")
    assert fleet_response.status_code == 200
    total = sum(row["count"] for row in fleet_response.json())
    assert total == 50, f"After double-seeding, expected 50 vehicles but got {total}"
