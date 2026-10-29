from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Fuel(Base):
    __tablename__ = "fuels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(16), unique=True)
    name: Mapped[str] = mapped_column(String(32))
    price: Mapped[float] = mapped_column(Float)


class Tariff(Base):
    __tablename__ = "tariffs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(16), unique=True)
    name: Mapped[str] = mapped_column(String(32))
    discount_percent: Mapped[float] = mapped_column(Float)


class Pump(Base):
    __tablename__ = "pumps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    number: Mapped[int] = mapped_column(Integer, unique=True)

    sessions: Mapped[list["FuelingSession"]] = relationship(back_populates="pump")


class FuelingSession(Base):
    __tablename__ = "fueling_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pump_id: Mapped[int] = mapped_column(ForeignKey("pumps.id"))
    fuel_id: Mapped[int] = mapped_column(ForeignKey("fuels.id"))
    tariff_id: Mapped[int] = mapped_column(ForeignKey("tariffs.id"))
    mode: Mapped[str] = mapped_column(String(16))
    requested_value: Mapped[float] = mapped_column(Float)
    price_per_liter: Mapped[float] = mapped_column(Float)
    target_liters: Mapped[float] = mapped_column(Float)
    target_total: Mapped[float] = mapped_column(Float)
    flow_lps: Mapped[float] = mapped_column(Float, default=1.8)
    dispensed_liters: Mapped[float] = mapped_column(Float, default=0)
    status: Mapped[str] = mapped_column(String(16), default="running")
    started_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    pump: Mapped[Pump] = relationship(back_populates="sessions")
    fuel: Mapped[Fuel] = relationship()
    tariff: Mapped[Tariff] = relationship()
