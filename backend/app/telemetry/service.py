# backend/app/telemetry/service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.telemetry.schemas import TelemetryEventCreate, TelemetryEventResponse
from app.telemetry.models import TelemetryEvent
from app.anomalies.models import Anomaly
from app.zones.models import Zone
from app.fleet.models import Vehicle, Mission, MaintenanceRecord
from sqlalchemy.sql import func

# Locked thresholds (ANOM-02, PROJECT.md)
BATTERY_CRITICAL_THRESHOLD = 15.0
SPEED_ANOMALY_THRESHOLD = 8.0


def detect_anomaly(event: TelemetryEventCreate) -> bool:
    """Pure function: returns True if the event triggers any anomaly condition.

    Rule precedence (first match wins):
    1. battery_pct < 15.0 (low_battery)
    2. speed_mps > 8.0 AND status != moving (speed_anomaly)
    3. error_codes non-empty (error_codes)
    4. status == fault (fault_status)
    """
    if event.battery_pct < BATTERY_CRITICAL_THRESHOLD:
        return True
    if event.speed_mps > SPEED_ANOMALY_THRESHOLD and event.status != "moving":
        return True
    if event.error_codes:
        return True
    if event.status == "fault":
        return True
    return False


def _anomaly_type(event: TelemetryEventCreate) -> str:
    """Return the anomaly type label for the first-matching rule.

    Precedence: fault_status > low_battery > speed_anomaly > error_codes
    (Note: fault_status is checked FIRST even though detect_anomaly checks battery first,
    because the label 'fault_status' takes precedence per PATTERNS.md _anomaly_type.)
    """
    if event.status == "fault":
        return "fault_status"
    if event.battery_pct < BATTERY_CRITICAL_THRESHOLD:
        return "low_battery"
    if event.speed_mps > SPEED_ANOMALY_THRESHOLD and event.status != "moving":
        return "speed_anomaly"
    if event.error_codes:
        return "error_codes"
    return "unknown"


async def ingest_telemetry(
    session: AsyncSession, event: TelemetryEventCreate
) -> TelemetryEventResponse:
    """Ingest a single telemetry event atomically.

    All five operations run inside ONE session.begin() block — atomic commit or full rollback:
    1. INSERT TelemetryEvent + flush to get auto-generated id (TELE-01)
    2. Anomaly detection + INSERT Anomaly row if detected (ANOM-01)
    3. Atomic zone counter increment via single-statement UPDATE (ZONE-01, Pattern 3)
    4. UPDATE vehicle denormalized state (D-01)
    5. Fault transition with SELECT FOR UPDATE row-lock (FAULT-01, FAULT-02, Pattern 4)
    """
    async with session.begin():
        # 1. Insert telemetry event
        telemetry_row = TelemetryEvent(
            vehicle_id=event.vehicle_id,
            timestamp=event.timestamp,
            lat=event.lat,
            lon=event.lon,
            battery_pct=event.battery_pct,
            speed_mps=event.speed_mps,
            status=event.status.value,
            error_codes=event.error_codes,
            zone_entered=event.zone_entered,
        )
        session.add(telemetry_row)
        await session.flush()  # populates telemetry_row.id before commit

        # 2. Anomaly detection
        anomaly_detected = detect_anomaly(event)
        if anomaly_detected:
            session.add(Anomaly(
                vehicle_id=event.vehicle_id,
                timestamp=event.timestamp,
                anomaly_type=_anomaly_type(event),
                raw_event_id=telemetry_row.id,
            ))

        # 3. Atomic zone counter increment (Pattern 3 — no SELECT needed)
        if event.zone_entered:
            await session.execute(
                update(Zone)
                .where(Zone.zone_id == event.zone_entered)
                .values(entry_count=Zone.entry_count + 1)
            )

        # 4. Update vehicle denormalized state (D-01)
        await session.execute(
            update(Vehicle)
            .where(Vehicle.vehicle_id == event.vehicle_id)
            .values(
                current_status=event.status.value,
                current_battery=event.battery_pct,
                latest_seen=event.timestamp,
            )
        )

        # 5. Fault transition (Pattern 4 — SELECT FOR UPDATE)
        if event.status == "fault":
            await _handle_fault_transition(session, event.vehicle_id)

    return TelemetryEventResponse(
        event_id=telemetry_row.id,
        anomaly_detected=anomaly_detected,
    )


async def _handle_fault_transition(session: AsyncSession, vehicle_id: str) -> None:
    """Handle fault transition inside the caller's transaction.

    Uses SELECT FOR UPDATE to row-lock the vehicle row, preventing concurrent fault
    events for the same vehicle from both inserting a maintenance record (Pitfall 5,
    FAULT-02). Different vehicles use different row locks — no table-level serialization.

    - Cancels the active mission if one exists (FAULT-03: no-op if none)
    - Always creates a MaintenanceRecord (FAULT-01)
    """
    # Row-lock prevents concurrent fault for same vehicle (FAULT-01, FAULT-02)
    result = await session.execute(
        select(Vehicle)
        .where(Vehicle.vehicle_id == vehicle_id)
        .with_for_update()
    )
    result.scalar_one()  # raises if vehicle missing — fail fast

    # Cancel active mission — no-op if none (FAULT-03)
    await session.execute(
        update(Mission)
        .where(Mission.vehicle_id == vehicle_id, Mission.status == "active")
        .values(status="cancelled", cancelled_at=func.now())
    )

    # Always create maintenance record
    session.add(MaintenanceRecord(vehicle_id=vehicle_id))
