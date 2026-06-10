# backend/tests/test_telemetry_ingest.py
"""
Tests for telemetry ingestion: detect_anomaly pure logic and TelemetryEventCreate validation.

TDD RED phase: These tests are written BEFORE the implementation to drive the design.

Covers:
- detect_anomaly: all 6 cases (low battery, speed anomaly, error codes, fault status, normal)
- _anomaly_type: precedence (fault_status > low_battery > speed_anomaly > error_codes)
- TelemetryEventCreate: 4 invalid (422) cases + valid case
- POST /telemetry happy-path: persists row, returns {event_id, anomaly_detected}
- zone_entered ingest: increments zone's entry_count by exactly 1
"""
import pytest
from datetime import datetime, timezone
from httpx import AsyncClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _base_event(**overrides):
    """Build a minimal valid raw dict for TelemetryEventCreate."""
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


# ---------------------------------------------------------------------------
# detect_anomaly pure-function tests
# ---------------------------------------------------------------------------

class TestDetectAnomaly:
    """Pure unit tests — no DB required, import the function directly."""

    def _import(self):
        from app.telemetry.service import detect_anomaly, _anomaly_type
        from app.telemetry.schemas import TelemetryEventCreate
        return detect_anomaly, _anomaly_type, TelemetryEventCreate

    def test_low_battery_is_anomaly(self):
        detect_anomaly, _, TelemetryEventCreate = self._import()
        event = TelemetryEventCreate(**_base_event(battery_pct=10.0))
        assert detect_anomaly(event) is True

    def test_high_speed_non_moving_is_anomaly(self):
        detect_anomaly, _, TelemetryEventCreate = self._import()
        event = TelemetryEventCreate(**_base_event(speed_mps=9.0, status="idle"))
        assert detect_anomaly(event) is True

    def test_high_speed_while_moving_is_not_anomaly(self):
        detect_anomaly, _, TelemetryEventCreate = self._import()
        event = TelemetryEventCreate(**_base_event(speed_mps=9.0, status="moving"))
        assert detect_anomaly(event) is False

    def test_error_codes_is_anomaly(self):
        detect_anomaly, _, TelemetryEventCreate = self._import()
        event = TelemetryEventCreate(**_base_event(error_codes=["E01"]))
        assert detect_anomaly(event) is True

    def test_fault_status_is_anomaly(self):
        detect_anomaly, _, TelemetryEventCreate = self._import()
        event = TelemetryEventCreate(**_base_event(status="fault"))
        assert detect_anomaly(event) is True

    def test_normal_event_is_not_anomaly(self):
        detect_anomaly, _, TelemetryEventCreate = self._import()
        event = TelemetryEventCreate(**_base_event(
            battery_pct=50.0,
            speed_mps=2.0,
            status="idle",
            error_codes=[],
        ))
        assert detect_anomaly(event) is False

    def test_anomaly_type_fault_status_takes_precedence(self):
        """fault_status label returned even when battery is also low."""
        _, _anomaly_type, TelemetryEventCreate = self._import()
        event = TelemetryEventCreate(**_base_event(status="fault", battery_pct=5.0))
        assert _anomaly_type(event) == "fault_status"

    def test_anomaly_type_low_battery(self):
        _, _anomaly_type, TelemetryEventCreate = self._import()
        event = TelemetryEventCreate(**_base_event(battery_pct=10.0))
        assert _anomaly_type(event) == "low_battery"

    def test_anomaly_type_speed_anomaly(self):
        _, _anomaly_type, TelemetryEventCreate = self._import()
        event = TelemetryEventCreate(**_base_event(speed_mps=9.0, status="idle"))
        assert _anomaly_type(event) == "speed_anomaly"

    def test_anomaly_type_error_codes(self):
        _, _anomaly_type, TelemetryEventCreate = self._import()
        event = TelemetryEventCreate(**_base_event(error_codes=["E99"]))
        assert _anomaly_type(event) == "error_codes"


# ---------------------------------------------------------------------------
# TelemetryEventCreate Pydantic validation (422 cases)
# ---------------------------------------------------------------------------

class TestTelemetryEventCreateValidation:
    """Verify Pydantic v2 constraints produce ValidationError on bad input."""

    def _schema(self):
        from app.telemetry.schemas import TelemetryEventCreate
        return TelemetryEventCreate

    def test_battery_pct_over_100_raises(self):
        from pydantic import ValidationError
        TelemetryEventCreate = self._schema()
        with pytest.raises(ValidationError):
            TelemetryEventCreate(**_base_event(battery_pct=150))

    def test_speed_mps_negative_raises(self):
        from pydantic import ValidationError
        TelemetryEventCreate = self._schema()
        with pytest.raises(ValidationError):
            TelemetryEventCreate(**_base_event(speed_mps=-1))

    def test_invalid_status_raises(self):
        from pydantic import ValidationError
        TelemetryEventCreate = self._schema()
        with pytest.raises(ValidationError):
            TelemetryEventCreate(**_base_event(status="flying"))

    def test_missing_vehicle_id_raises(self):
        from pydantic import ValidationError
        TelemetryEventCreate = self._schema()
        data = _base_event()
        del data["vehicle_id"]
        with pytest.raises(ValidationError):
            TelemetryEventCreate(**data)


# ---------------------------------------------------------------------------
# POST /telemetry — integration tests (require DB + ASGI client)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_post_telemetry_happy_path(client: AsyncClient):
    """
    POST /telemetry with a valid event must:
    - Return 200 with exactly {event_id: int, anomaly_detected: bool}
    - Persist the telemetry_events row (TELE-01)
    """
    payload = _base_event(
        vehicle_id="v-1",
        battery_pct=50.0,
        speed_mps=2.0,
        status="idle",
        error_codes=[],
        zone_entered=None,
    )
    response = await client.post("/telemetry", json=payload)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    body = response.json()
    assert set(body.keys()) == {"event_id", "anomaly_detected"}, (
        f"Response must have exactly event_id and anomaly_detected; got: {set(body.keys())}"
    )
    assert isinstance(body["event_id"], int)
    assert body["anomaly_detected"] is False


@pytest.mark.asyncio
async def test_post_telemetry_anomaly_detected(client: AsyncClient):
    """Low battery event must return anomaly_detected=True (ANOM-01)."""
    payload = _base_event(vehicle_id="v-2", battery_pct=5.0)
    response = await client.post("/telemetry", json=payload)
    assert response.status_code == 200
    assert response.json()["anomaly_detected"] is True


@pytest.mark.asyncio
async def test_post_telemetry_invalid_battery_returns_422(client: AsyncClient):
    """battery_pct=150 must be rejected with 422 (T-01-05, D-11)."""
    payload = _base_event(battery_pct=150)
    response = await client.post("/telemetry", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_post_telemetry_zone_increments_count(client: AsyncClient):
    """
    POST /telemetry with zone_entered must increment that zone's entry_count by 1 (ZONE-01).
    Verified by reading GET /zones/counts before and after.
    """
    zone_id = "inbound_dock_a"

    # Read baseline
    zones_before = {z["zone_id"]: z["entry_count"] for z in (await client.get("/zones/counts")).json()}
    baseline = zones_before.get(zone_id, 0)

    payload = _base_event(vehicle_id="v-3", zone_entered=zone_id)
    response = await client.post("/telemetry", json=payload)
    assert response.status_code == 200

    # Verify count incremented by exactly 1
    zones_after = {z["zone_id"]: z["entry_count"] for z in (await client.get("/zones/counts")).json()}
    assert zones_after[zone_id] == baseline + 1, (
        f"Expected zone {zone_id} entry_count={baseline + 1}, got {zones_after[zone_id]}"
    )
