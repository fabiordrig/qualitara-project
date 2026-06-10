# backend/app/fleet/schemas.py
from pydantic import BaseModel


class FleetStateResponse(BaseModel):
    status: str
    count: int
