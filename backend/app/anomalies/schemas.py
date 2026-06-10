# backend/app/anomalies/schemas.py
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class AnomalyResponse(BaseModel):
    id: int
    vehicle_id: str
    timestamp: datetime
    anomaly_type: str
    raw_event_id: Optional[int]

    model_config = ConfigDict(from_attributes=True)
