# backend/app/fleet/router.py
from fastapi import APIRouter
from sqlalchemy import select, func
from app.database import DB
from app.fleet.models import Vehicle

router = APIRouter()


@router.get("/fleet/state")
async def get_fleet_state(db: DB):
    result = await db.execute(
        select(Vehicle.current_status, func.count(Vehicle.vehicle_id).label("count"))
        .group_by(Vehicle.current_status)
    )
    rows = result.all()
    return [{"status": row.current_status, "count": row.count} for row in rows]
