from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Fuel, Pump, Tariff

FUELS = [
    ("ai92", "АИ-92", 54.90),
    ("ai95", "АИ-95", 59.40),
    ("ai98", "АИ-98", 68.20),
    ("dt", "ДТ", 62.10),
]

TARIFFS = [
    ("base", "Базовый", 0.0),
    ("card", "Карта", 5.0),
    ("night", "Ночной", 8.0),
]

PUMP_NUMBERS = (1, 2, 3, 4)


def seed(db: Session) -> None:
    if db.scalar(select(Fuel.id).limit(1)) is None:
        db.add_all(Fuel(code=code, name=name, price=price) for code, name, price in FUELS)
    if db.scalar(select(Tariff.id).limit(1)) is None:
        db.add_all(
            Tariff(code=code, name=name, discount_percent=discount)
            for code, name, discount in TARIFFS
        )
    if db.scalar(select(Pump.id).limit(1)) is None:
        db.add_all(Pump(number=number) for number in PUMP_NUMBERS)
    db.commit()
