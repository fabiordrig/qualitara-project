# backend/app/fleet/router.py
from fastapi import APIRouter
from sqlalchemy import select, func
from app.database import DB
from app.fleet.models import Vehicle
from app.fleet.schemas import VehicleResponse, FleetStateResponse

router = APIRouter()


@router.get("/fleet/state", response_model=list[FleetStateResponse])
async def get_fleet_state(db: DB):
    result = await db.execute(
        select(Vehicle.current_status, func.count(Vehicle.vehicle_id).label("count"))
        .group_by(Vehicle.current_status)
    )
    rows = result.all()
    return [{"status": row.current_status, "count": row.count} for row in rows]


@router.get("/vehicles", response_model=list[VehicleResponse])
async def get_vehicles(db: DB):
    result = await db.execute(select(Vehicle).order_by(Vehicle.vehicle_id))
    return result.scalars().all()
