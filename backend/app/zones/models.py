# backend/app/zones/models.py
from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class Zone(Base):
    __tablename__ = "zones"

    zone_id: Mapped[str] = mapped_column(String, primary_key=True)
    entry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
