# backend/app/telemetry/service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.exc import NoResultFound
from fastapi import HTTPException
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


async def _assert_vehicle_exists(session: AsyncSession, vehicle_id: str) -> None:
    """Raise HTTP 404 if vehicle_id does not exist in the vehicles table.

    Called for non-fault events before any INSERT to prevent orphaned telemetry
    and anomaly rows referencing a non-existent vehicle (CR-01).
    """
    result = await session.execute(
        select(Vehicle.vehicle_id).where(Vehicle.vehicle_id == vehicle_id)
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail=f"Vehicle '{vehicle_id}' not found")


async def ingest_telemetry(
    session: AsyncSession, event: TelemetryEventCreate
) -> TelemetryEventResponse:
    """Ingest a single telemetry event atomically.

    All operations run inside ONE session.begin() block — atomic commit or full rollback:
    1. If status=fault: SELECT FOR UPDATE on vehicle to acquire row lock and read
       committed pre-update status (FAULT-01, FAULT-02). Must happen BEFORE the
       vehicle UPDATE so the lock is acquired while the committed status is still
       the pre-fault state; this lets the idempotency check in step 5 see the true
       "was it already fault?" answer based on committed data.
    2. INSERT TelemetryEvent + flush to get auto-generated id (TELE-01)
    3. Anomaly detection + INSERT Anomaly row if detected (ANOM-01)
    4. Atomic zone counter increment via single-statement UPDATE (ZONE-01, Pattern 3)
    5. UPDATE vehicle denormalized state (D-01)
    6. Fault transition — cancel mission + create maintenance record — only if vehicle
       was NOT already in fault status at lock-acquire time (FAULT-01, FAULT-02, FAULT-03)
    """
    async with session.begin():
        # 1. For fault events: row-lock the vehicle FIRST to read committed status
        #    before this transaction's UPDATE changes it. This is the SELECT FOR UPDATE
        #    that serializes concurrent fault events for the same vehicle (FAULT-02).
        #    Different vehicles lock different rows — no table-level serialization.
        #    For non-fault events: assert vehicle exists to prevent orphaned rows (CR-01).
        pre_fault_status: str | None = None
        if event.status == "fault":
            pre_fault_status = await _lock_vehicle_and_read_status(session, event.vehicle_id)
        else:
            await _assert_vehicle_exists(session, event.vehicle_id)

        # 2. Insert telemetry event
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

        # 3. Anomaly detection
        anomaly_detected = detect_anomaly(event)
        if anomaly_detected:
            session.add(Anomaly(
                vehicle_id=event.vehicle_id,
                timestamp=event.timestamp,
                anomaly_type=_anomaly_type(event),
                raw_event_id=telemetry_row.id,
            ))

        # 4. Atomic zone counter increment (Pattern 3 — no SELECT needed)
        if event.zone_entered:
            await session.execute(
                update(Zone)
                .where(Zone.zone_id == event.zone_entered)
                .values(entry_count=Zone.entry_count + 1)
            )

        # 5. Update vehicle denormalized state (D-01)
        await session.execute(
            update(Vehicle)
            .where(Vehicle.vehicle_id == event.vehicle_id)
            .values(
                current_status=event.status.value,
                current_battery=event.battery_pct,
                latest_seen=event.timestamp,
            )
        )

        # 6. Fault transition — only if vehicle was NOT already in fault status
        #    at lock-acquire time (idempotency guard, FAULT-02, Pitfall 5)
        if event.status == "fault" and pre_fault_status != "fault":
            await _handle_fault_transition(session, event.vehicle_id)

    return TelemetryEventResponse(
        event_id=telemetry_row.id,
        anomaly_detected=anomaly_detected,
    )


async def _lock_vehicle_and_read_status(session: AsyncSession, vehicle_id: str) -> str:
    """Acquire a row lock on the vehicle and return its committed current_status.

    Called at the START of a fault-event ingest, BEFORE the vehicle UPDATE.
    This ensures the SELECT FOR UPDATE captures the committed state (not the
    in-transaction state after this transaction's own UPDATE modifies it).

    The row lock prevents two concurrent fault transactions for the SAME vehicle
    from both proceeding past this point simultaneously (Pitfall 5, FAULT-02).
    Different vehicle_ids lock different rows — no table-level serialization.

    Returns:
        The committed current_status value (e.g. "idle", "fault", "moving").
        Callers use this to decide whether the fault transition is needed.
    """
    result = await session.execute(
        select(Vehicle)
        .where(Vehicle.vehicle_id == vehicle_id)
        .with_for_update()
    )
    try:
        vehicle = result.scalar_one()
    except NoResultFound:
        raise HTTPException(status_code=404, detail=f"Vehicle '{vehicle_id}' not found")
    return vehicle.current_status


async def _handle_fault_transition(session: AsyncSession, vehicle_id: str) -> None:
    """Handle fault transition inside the caller's transaction.

    Called only when the vehicle was NOT already in 'fault' status at lock-acquire
    time (the idempotency guard in ingest_telemetry step 6).

    - Cancels the active mission if one exists (FAULT-03: no-op if none)
    - Always creates a MaintenanceRecord for this fault transition (FAULT-01)
    """
    # Cancel active mission — no-op if none (FAULT-03)
    await session.execute(
        update(Mission)
        .where(Mission.vehicle_id == vehicle_id, Mission.status == "active")
        .values(status="cancelled", cancelled_at=func.now())
    )

    # Create maintenance record
    session.add(MaintenanceRecord(vehicle_id=vehicle_id))
