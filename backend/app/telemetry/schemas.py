# backend/app/telemetry/schemas.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class VehicleStatus(str, Enum):
    idle = "idle"
    moving = "moving"
    charging = "charging"
    fault = "fault"


class TelemetryEventCreate(BaseModel):
    vehicle_id: str
    timestamp: datetime
    lat: float
    lon: float
    battery_pct: float = Field(ge=0, le=100)
    speed_mps: float = Field(ge=0)
    status: VehicleStatus
    error_codes: list[str] = []
    zone_entered: Optional[str] = None


class TelemetryEventResponse(BaseModel):
    event_id: int
    anomaly_detected: bool
