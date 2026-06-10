# backend/app/zones/schemas.py
from pydantic import BaseModel


class ZoneCountResponse(BaseModel):
    zone_id: str
    entry_count: int

    model_config = {"from_attributes": True}
