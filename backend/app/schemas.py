from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class FuelOut(BaseModel):
    id: int
    code: str
    name: str
    price: float

    model_config = {"from_attributes": True}


class TariffOut(BaseModel):
    id: int
    code: str
    name: str
    discount_percent: float

    model_config = {"from_attributes": True}


class SessionOut(BaseModel):
    id: int
    pump_id: int
    pump_number: int
    fuel_id: int
    fuel_name: str
    tariff_id: int
    tariff_name: str
    mode: str
    requested_value: float
    price_per_liter: float
    target_liters: float
    target_total: float
    dispensed_liters: float
    dispensed_total: float
    progress: float
    status: str
    started_at: datetime
    finished_at: datetime | None


class PumpOut(BaseModel):
    id: int
    number: int
    status: str
    active_session: SessionOut | None


class CatalogOut(BaseModel):
    fuels: list[FuelOut]
    tariffs: list[TariffOut]
    pumps: list[PumpOut]


class SessionCreate(BaseModel):
    pump_id: int
    fuel_id: int
    tariff_id: int
    mode: Literal["liters", "money"]
    value: float = Field(gt=0, le=20000)
