# backend/app/zones/router.py
from fastapi import APIRouter
from sqlalchemy import select
from app.database import DB
from app.zones.models import Zone
from app.zones.schemas import ZoneCountResponse

router = APIRouter()


@router.get("/zones/counts", response_model=list[ZoneCountResponse])
async def get_zone_counts(db: DB):
    result = await db.execute(select(Zone).order_by(Zone.zone_id))
    return result.scalars().all()
