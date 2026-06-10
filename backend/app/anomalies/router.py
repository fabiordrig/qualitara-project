# backend/app/anomalies/router.py
from fastapi import APIRouter, Query
from sqlalchemy import select
from datetime import datetime
from typing import Optional
from app.database import DB
from app.anomalies.models import Anomaly
from app.anomalies.schemas import AnomalyResponse

router = APIRouter()


@router.get("/anomalies", response_model=list[AnomalyResponse])
async def get_anomalies(
    db: DB,
    vehicle_id: Optional[str] = Query(None),
    from_time: Optional[datetime] = Query(None, alias="from"),
    to_time: Optional[datetime] = Query(None, alias="to"),
):
    stmt = select(Anomaly).order_by(Anomaly.timestamp.desc())
    if vehicle_id:
        stmt = stmt.where(Anomaly.vehicle_id == vehicle_id)
    if from_time:
        stmt = stmt.where(Anomaly.timestamp >= from_time)
    if to_time:
        stmt = stmt.where(Anomaly.timestamp <= to_time)
    result = await db.execute(stmt)
    return result.scalars().all()
