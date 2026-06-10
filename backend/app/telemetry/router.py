# backend/app/telemetry/router.py
from fastapi import APIRouter
from app.database import DB
from app.telemetry.schemas import TelemetryEventCreate, TelemetryEventResponse
from app.telemetry.service import ingest_telemetry

router = APIRouter()


@router.post("/telemetry", response_model=TelemetryEventResponse)
async def post_telemetry(event: TelemetryEventCreate, db: DB):
    """Ingest a single vehicle telemetry event.

    Validates input via Pydantic (422 on bad data), then delegates all
    persistence logic to ingest_telemetry (thin controller pattern).
    Returns only {event_id, anomaly_detected} — no full-event echo (D-10).
    """
    return await ingest_telemetry(db, event)
