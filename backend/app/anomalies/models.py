# backend/app/anomalies/models.py
from sqlalchemy import String, DateTime, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.database import Base


class Anomaly(Base):
    __tablename__ = "anomalies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vehicle_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    anomaly_type: Mapped[str] = mapped_column(String, nullable=False)
    raw_event_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("telemetry_events.id"), nullable=True
    )
