# backend/app/telemetry/models.py
from sqlalchemy import String, Float, DateTime, JSON, Integer
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.database import Base


class TelemetryEvent(Base):
    __tablename__ = "telemetry_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vehicle_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lon: Mapped[float] = mapped_column(Float, nullable=False)
    battery_pct: Mapped[float] = mapped_column(Float, nullable=False)
    speed_mps: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    error_codes: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    zone_entered: Mapped[str | None] = mapped_column(String, nullable=True)
