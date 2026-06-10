# backend/tests/test_vehicles.py
"""
End-to-end tests for GET /vehicles — DASH-01 per-vehicle data source.

Covers:
- GET /vehicles returns 200 with exactly 50 vehicles after fresh seeding
- Every vehicle object has the four required keys: vehicle_id, current_status,
  current_battery, latest_seen
- A freshly seeded vehicle has current_status == "idle" and current_battery == 100.0
- GET /vehicles reflects state changes driven by POST /telemetry (live denormalized state)

Vehicles are created via the lifespan seeding (conftest.py client fixture).
Telemetry updates are posted via the ASGI client to prove the full ingest→read path.
"""
import pytest
from datetime import datetime, timezone
from httpx import AsyncClient


# ---------------------------------------------------------------------------
# Test 1: Returns all 50 seeded vehicles with correct shape
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_vehicles_returns_all_fifty(client: AsyncClient):
    """
    After fresh seeding GET /vehicles must return exactly 50 vehicles.
    Each vehicle must have the four required keys.
    Freshly seeded vehicles are idle at 100% battery with latest_seen == null.
    """
    response = await client.get("/vehicles")
    assert response.status_code == 200, response.text
    rows = response.json()

    assert len(rows) == 50, f"Expected 50 vehicles, got {len(rows)}"

    required_keys = {"vehicle_id", "current_status", "current_battery", "latest_seen"}
    for row in rows:
        assert required_keys == set(row.keys()), (
            f"Vehicle row missing/extra keys. Expected {required_keys}, got {set(row.keys())}"
        )

    # Fresh seeds should all be idle at 100.0 battery
    for row in rows:
        assert row["current_status"] == "idle", (
            f"Expected freshly seeded vehicle to have current_status='idle', "
            f"got '{row['current_status']}' for {row['vehicle_id']}"
        )
        assert row["current_battery"] == 100.0, (
            f"Expected freshly seeded vehicle to have current_battery=100.0, "
            f"got {row['current_battery']} for {row['vehicle_id']}"
        )
        assert row["latest_seen"] is None, (
            f"Expected freshly seeded vehicle to have latest_seen=null, "
            f"got '{row['latest_seen']}' for {row['vehicle_id']}"
        )


# ---------------------------------------------------------------------------
# Test 2: Reflects live telemetry-driven state changes (DASH-01)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_vehicles_reflects_telemetry_update(client: AsyncClient):
    """
    POST /telemetry for vehicle v-1 with status=charging and battery_pct=42.0.
    GET /vehicles must reflect the new current_status and current_battery for v-1.
    This proves GET /vehicles serves live denormalized state for the DASH-01 vehicle list.
    """
    event = {
        "vehicle_id": "v-1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "lat": 0.0,
        "lon": 0.0,
        "battery_pct": 42.0,
        "speed_mps": 0.0,
        "status": "charging",
        "error_codes": [],
        "zone_entered": None,
    }
    ingest_resp = await client.post("/telemetry", json=event)
    assert ingest_resp.status_code == 200, (
        f"POST /telemetry failed: {ingest_resp.text}"
    )

    response = await client.get("/vehicles")
    assert response.status_code == 200, response.text
    rows = response.json()

    v1_rows = [row for row in rows if row["vehicle_id"] == "v-1"]
    assert len(v1_rows) == 1, f"Expected exactly one row for v-1, got {len(v1_rows)}"

    v1 = v1_rows[0]
    assert v1["current_status"] == "charging", (
        f"Expected v-1 current_status='charging' after telemetry POST, "
        f"got '{v1['current_status']}'"
    )
    assert v1["current_battery"] == 42.0, (
        f"Expected v-1 current_battery=42.0 after telemetry POST, "
        f"got {v1['current_battery']}"
    )
