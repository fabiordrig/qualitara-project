# backend/app/fleet/models.py
from sqlalchemy import String, Float, DateTime, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.database import Base


class Vehicle(Base):
    __tablename__ = "vehicles"

    vehicle_id: Mapped[str] = mapped_column(String, primary_key=True)
    current_status: Mapped[str] = mapped_column(String, nullable=False, default="idle")
    current_battery: Mapped[float] = mapped_column(Float, nullable=False, default=100.0)
    latest_seen: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class Mission(Base):
    __tablename__ = "missions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vehicle_id: Mapped[str] = mapped_column(
        String, ForeignKey("vehicles.vehicle_id"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String, nullable=False, default="active"
    )  # active/cancelled/completed
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class MaintenanceRecord(Base):
    __tablename__ = "maintenance_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vehicle_id: Mapped[str] = mapped_column(
        String, ForeignKey("vehicles.vehicle_id"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default="now()"
    )
