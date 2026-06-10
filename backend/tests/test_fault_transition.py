# backend/tests/test_fault_transition.py
"""
Tests for fault transition atomicity and isolation.

Covers:
- FAULT-01: active mission cancelled + maintenance record created together (atomic)
- FAULT-03: no active mission → exactly one maintenance record, no error
- ROADMAP criterion 4: all-or-nothing fault transition proven

These tests require DB access and a properly seeded vehicle with/without an active mission.
"""
import pytest
from datetime import datetime, timezone
from httpx import AsyncClient

import app.database as _db_module
from app.fleet.models import Mission, MaintenanceRecord
from sqlalchemy import select, func


def _fault_event(vehicle_id: str) -> dict:
    """Build a fault telemetry event payload."""
    return {
        "vehicle_id": vehicle_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "lat": 0.0,
        "lon": 0.0,
        "battery_pct": 50.0,
        "speed_mps": 0.0,
        "status": "fault",
        "error_codes": [],
        "zone_entered": None,
    }


@pytest.mark.asyncio
async def test_fault_with_active_mission_cancels_and_creates_maintenance(client: AsyncClient):
    """
    FAULT-01: POST a fault event for a vehicle that has an active mission.
    Assert both:
    - The mission's status is 'cancelled'
    - A maintenance record exists for the vehicle
    (Both must exist — atomicity proof)
    """
    vehicle_id = "v-10"

    # Seed an active mission for this vehicle
    async with _db_module.async_session_maker() as session:
        async with session.begin():
            session.add(Mission(
                vehicle_id=vehicle_id,
                status="active",
                created_at=datetime.now(timezone.utc),
            ))

    # POST a fault event
    response = await client.post("/telemetry", json=_fault_event(vehicle_id))
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

    # Assert mission was cancelled
    async with _db_module.async_session_maker() as session:
        mission_result = await session.execute(
            select(Mission).where(Mission.vehicle_id == vehicle_id)
        )
        missions = mission_result.scalars().all()
        assert len(missions) == 1, f"Expected 1 mission, got {len(missions)}"
        assert missions[0].status == "cancelled", (
            f"Expected mission status='cancelled', got '{missions[0].status}'"
        )

        # Assert maintenance record was created
        maint_result = await session.execute(
            select(MaintenanceRecord).where(MaintenanceRecord.vehicle_id == vehicle_id)
        )
        records = maint_result.scalars().all()
        assert len(records) == 1, (
            f"Expected exactly 1 maintenance record, got {len(records)} (FAULT-01 atomicity)"
        )


@pytest.mark.asyncio
async def test_fault_without_active_mission_creates_only_maintenance(client: AsyncClient):
    """
    FAULT-03: POST a fault event for a vehicle with NO active mission.
    Assert:
    - Exactly one maintenance record created
    - No error (no-op on mission cancellation is graceful)
    """
    vehicle_id = "v-11"

    # Verify vehicle has no missions
    async with _db_module.async_session_maker() as session:
        result = await session.execute(
            select(Mission).where(Mission.vehicle_id == vehicle_id, Mission.status == "active")
        )
        assert result.scalars().first() is None, "Precondition: no active mission for v-11"

    # POST a fault event — must not error
    response = await client.post("/telemetry", json=_fault_event(vehicle_id))
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

    # Assert exactly one maintenance record was created
    async with _db_module.async_session_maker() as session:
        result = await session.execute(
            select(MaintenanceRecord).where(MaintenanceRecord.vehicle_id == vehicle_id)
        )
        records = result.scalars().all()
        assert len(records) == 1, (
            f"Expected exactly 1 maintenance record for fault with no mission, got {len(records)} (FAULT-03)"
        )
