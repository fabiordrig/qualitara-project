# backend/tests/test_anomalies.py
"""
End-to-end tests for GET /anomalies — ANOM-03 filter coverage and four-condition surfacing.

Covers:
- GET /anomalies?vehicle_id=<id>  returns only anomalies for the specified vehicle
- GET /anomalies?from=<ts>&to=<ts> returns only in-window anomalies (inclusive bounds)
- GET /anomalies with no filters returns all anomalies ordered most-recent-first
- All four anomaly conditions surface in GET /anomalies after a matching POST /telemetry
  (ROADMAP criterion 3): low_battery, speed_anomaly, error_codes, fault_status

Anomalies are created via POST /telemetry through the ASGI client (no direct DB inserts),
proving the full ingest→query path through Plan 02's ingest_telemetry service.

Scope: GET /anomalies read/filter contract only.
Does NOT re-test: ingest atomicity, zone increments, fault-transition behavior (Plan 02).
"""

import pytest
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _base_event(**overrides):
    """Build a minimal valid raw dict for POST /telemetry with no anomaly by default."""
    event = {
        "vehicle_id": "v-1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "lat": 0.0,
        "lon": 0.0,
        "battery_pct": 50.0,
        "speed_mps": 2.0,
        "status": "idle",
        "error_codes": [],
        "zone_entered": None,
    }
    event.update(overrides)
    return event


def _fault_event(vehicle_id: str, **overrides):
    """Build a fault-status event (always anomalous)."""
    return _base_event(vehicle_id=vehicle_id, status="fault", **overrides)


# ---------------------------------------------------------------------------
# vehicle_id filter
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_anomalies_filters_by_vehicle_id(client: AsyncClient):
    """
    POST a fault event for v-1 and v-2.
    GET /anomalies?vehicle_id=v-1 must return only v-1 rows.
    """
    await client.post("/telemetry", json=_fault_event("v-1"))
    await client.post("/telemetry", json=_fault_event("v-2"))

    response = await client.get("/anomalies", params={"vehicle_id": "v-1"})
    assert response.status_code == 200, response.text
    rows = response.json()
    assert len(rows) >= 1, "Expected at least one anomaly for v-1"
    for row in rows:
        assert row["vehicle_id"] == "v-1", (
            f"Expected vehicle_id='v-1' but got '{row['vehicle_id']}'"
        )
    vehicle_ids = {row["vehicle_id"] for row in rows}
    assert "v-2" not in vehicle_ids, (
        "v-2 anomalies must be excluded when filtering by v-1"
    )


# ---------------------------------------------------------------------------
# from/to time-range filter (inclusive bounds, public keys are `from`/`to`)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_anomalies_filters_by_time_range(client: AsyncClient):
    """
    POST two anomaly events with timestamps inside and outside a target window.
    GET /anomalies?from=<lo>&to=<hi> must return only the in-window anomaly.
    Uses public query keys `from` and `to` (alias for from_time/to_time, ANOM-03).
    Inclusive bounds: lo and hi endpoints are included.
    """
    now = datetime.now(timezone.utc).replace(microsecond=0)
    inside_ts = now
    outside_ts = now - timedelta(hours=2)

    # Inside window
    await client.post(
        "/telemetry",
        json=_fault_event(
            "v-3",
            timestamp=inside_ts.isoformat(),
        ),
    )
    # Outside window
    await client.post(
        "/telemetry",
        json=_fault_event(
            "v-4",
            timestamp=outside_ts.isoformat(),
        ),
    )

    lo = (inside_ts - timedelta(minutes=5)).isoformat()
    hi = (inside_ts + timedelta(minutes=5)).isoformat()

    response = await client.get("/anomalies", params={"from": lo, "to": hi})
    assert response.status_code == 200, response.text
    rows = response.json()

    # Only v-3's anomaly falls inside the window
    returned_vehicles = {row["vehicle_id"] for row in rows}
    assert "v-3" in returned_vehicles, (
        "In-window anomaly for v-3 must appear in results"
    )
    assert "v-4" not in returned_vehicles, (
        "Out-of-window anomaly for v-4 must be excluded"
    )


# ---------------------------------------------------------------------------
# Most-recent-first ordering
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_anomalies_orders_most_recent_first(client: AsyncClient):
    """
    POST two anomaly events with known timestamps (older then newer).
    GET /anomalies must return them in descending timestamp order.
    """
    now = datetime.now(timezone.utc).replace(microsecond=0)
    older_ts = (now - timedelta(minutes=10)).isoformat()
    newer_ts = now.isoformat()

    await client.post("/telemetry", json=_fault_event("v-5", timestamp=older_ts))
    await client.post("/telemetry", json=_fault_event("v-5", timestamp=newer_ts))

    response = await client.get("/anomalies", params={"vehicle_id": "v-5"})
    assert response.status_code == 200, response.text
    rows = response.json()
    assert len(rows) >= 2, "Expected at least two anomalies for v-5"

    timestamps = [row["timestamp"] for row in rows]
    assert timestamps == sorted(timestamps, reverse=True), (
        f"Results must be ordered most-recent-first; got: {timestamps}"
    )


# ---------------------------------------------------------------------------
# All four anomaly conditions surface (ROADMAP criterion 3)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_all_four_anomaly_conditions_surface(client: AsyncClient):
    """
    POST one event per anomaly condition to separate vehicles.
    GET /anomalies (no filter) must include rows whose anomaly_type values
    cover {low_battery, speed_anomaly, error_codes, fault_status}.

    Four conditions (ANOM-02):
    1. battery_pct=10 → low_battery
    2. speed_mps=9.0 + status=idle → speed_anomaly
    3. error_codes=["E01"] → error_codes
    4. status=fault → fault_status
    """
    # 1. low_battery
    await client.post(
        "/telemetry",
        json=_base_event(
            vehicle_id="v-10",
            battery_pct=10.0,
            status="idle",
            speed_mps=2.0,
            error_codes=[],
        ),
    )

    # 2. speed_anomaly (speed > 8 & status != moving)
    await client.post(
        "/telemetry",
        json=_base_event(
            vehicle_id="v-11",
            speed_mps=9.0,
            status="idle",
            battery_pct=50.0,
            error_codes=[],
        ),
    )

    # 3. error_codes
    await client.post(
        "/telemetry",
        json=_base_event(
            vehicle_id="v-12",
            error_codes=["E01"],
            battery_pct=50.0,
            speed_mps=2.0,
            status="idle",
        ),
    )

    # 4. fault_status
    await client.post("/telemetry", json=_fault_event("v-13"))

    response = await client.get("/anomalies")
    assert response.status_code == 200, response.text
    rows = response.json()

    returned_types = {row["anomaly_type"] for row in rows}
    required = {"low_battery", "speed_anomaly", "error_codes", "fault_status"}
    assert required.issubset(returned_types), (
        f"Expected all four anomaly types {required!r} to be present; got {returned_types!r}"
    )


# ---------------------------------------------------------------------------
# No-filter returns all
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_anomalies_no_filters_returns_all(client: AsyncClient):
    """
    POST three anomaly events.
    GET /anomalies with no query params must return at least all three rows.
    """
    await client.post("/telemetry", json=_fault_event("v-20"))
    await client.post("/telemetry", json=_fault_event("v-21"))
    await client.post("/telemetry", json=_fault_event("v-22"))

    response = await client.get("/anomalies")
    assert response.status_code == 200, response.text
    rows = response.json()
    assert len(rows) >= 3, (
        f"Expected at least 3 anomalies with no filters; got {len(rows)}"
    )
