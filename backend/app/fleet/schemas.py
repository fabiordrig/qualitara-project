# backend/app/fleet/schemas.py
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class FleetStateResponse(BaseModel):
    status: str
    count: int


class VehicleResponse(BaseModel):
    vehicle_id: str
    current_status: str
    current_battery: float
    latest_seen: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)
