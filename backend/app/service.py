from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Fuel, FuelingSession, Pump, Tariff
from app.schemas import PumpOut, SessionOut

FLOW_LPS = 1.8


def price_for(fuel: Fuel, tariff: Tariff) -> float:
    return round(fuel.price * (1 - tariff.discount_percent / 100), 2)


def _elapsed_liters(session: FuelingSession, now: datetime) -> float:
    elapsed = max((now - session.started_at).total_seconds(), 0)
    return min(session.target_liters, elapsed * session.flow_lps)


def sync_session(db: Session, session: FuelingSession, now: datetime | None = None) -> FuelingSession:
    if session.status != "running":
        return session
    now = now or datetime.now()
    dispensed = _elapsed_liters(session, now)
    if dispensed + 1e-6 >= session.target_liters:
        session.dispensed_liters = session.target_liters
        session.status = "completed"
        session.finished_at = now
        db.commit()
        db.refresh(session)
    return session


def to_session_out(session: FuelingSession, now: datetime | None = None) -> SessionOut:
    now = now or datetime.now()
    if session.status == "running":
        dispensed = _elapsed_liters(session, now)
    else:
        dispensed = session.dispensed_liters
    if dispensed >= session.target_liters - 1e-9:
        total = session.target_total
    else:
        total = round(dispensed * session.price_per_liter, 2)
    progress = 0.0 if session.target_liters == 0 else min(dispensed / session.target_liters, 1)
    return SessionOut(
        id=session.id,
        pump_id=session.pump_id,
        pump_number=session.pump.number,
        fuel_id=session.fuel_id,
        fuel_name=session.fuel.name,
        tariff_id=session.tariff_id,
        tariff_name=session.tariff.name,
        mode=session.mode,
        requested_value=session.requested_value,
        price_per_liter=session.price_per_liter,
        target_liters=session.target_liters,
        target_total=session.target_total,
        dispensed_liters=round(dispensed, 3),
        dispensed_total=total,
        progress=round(progress, 4),
        status=session.status,
        started_at=session.started_at,
        finished_at=session.finished_at,
    )


def _load_session(db: Session, session_id: int) -> FuelingSession:
    session = db.scalar(
        select(FuelingSession)
        .options(
            selectinload(FuelingSession.pump),
            selectinload(FuelingSession.fuel),
            selectinload(FuelingSession.tariff),
        )
        .where(FuelingSession.id == session_id)
    )
    if session is None:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    return session


def list_pumps(db: Session) -> list[PumpOut]:
    pumps = db.scalars(select(Pump).order_by(Pump.number)).all()
    running = db.scalars(
        select(FuelingSession)
        .options(
            selectinload(FuelingSession.pump),
            selectinload(FuelingSession.fuel),
            selectinload(FuelingSession.tariff),
        )
        .where(FuelingSession.status == "running")
    ).all()
    now = datetime.now()
    by_pump: dict[int, FuelingSession] = {}
    for session in running:
        session = sync_session(db, session, now)
        if session.status == "running":
            by_pump[session.pump_id] = session
    result = []
    for pump in pumps:
        active = by_pump.get(pump.id)
        result.append(
            PumpOut(
                id=pump.id,
                number=pump.number,
                status="busy" if active else "idle",
                active_session=to_session_out(active, now) if active else None,
            )
        )
    return result


def start_session(db: Session, pump_id: int, fuel_id: int, tariff_id: int, mode: str, value: float) -> SessionOut:
    pump = db.get(Pump, pump_id)
    fuel = db.get(Fuel, fuel_id)
    tariff = db.get(Tariff, tariff_id)
    if pump is None or fuel is None or tariff is None:
        raise HTTPException(status_code=400, detail="Колонка, топливо или тариф не найдены")

    busy = db.scalar(
        select(FuelingSession.id).where(
            FuelingSession.pump_id == pump_id,
            FuelingSession.status == "running",
        )
    )
    if busy is not None:
        raise HTTPException(status_code=409, detail="Колонка уже занята")

    price = price_for(fuel, tariff)
    if price <= 0:
        raise HTTPException(status_code=400, detail="Некорректная цена")

    if mode == "liters":
        if value > 200:
            raise HTTPException(status_code=400, detail="Не больше 200 литров за одну заправку")
        target_liters = round(value, 3)
        target_total = round(target_liters * price, 2)
    else:
        target_total = round(value, 2)
        target_liters = round(target_total / price, 3)
        if target_liters > 200:
            raise HTTPException(status_code=400, detail="Сумма превышает 200 литров")

    session = FuelingSession(
        pump_id=pump.id,
        fuel_id=fuel.id,
        tariff_id=tariff.id,
        mode=mode,
        requested_value=value,
        price_per_liter=price,
        target_liters=target_liters,
        target_total=target_total,
        flow_lps=FLOW_LPS,
        dispensed_liters=0,
        status="running",
        started_at=datetime.now(),
    )
    db.add(session)
    db.commit()
    return to_session_out(_load_session(db, session.id))


def get_session(db: Session, session_id: int) -> SessionOut:
    session = sync_session(db, _load_session(db, session_id))
    return to_session_out(session)


def list_sessions(db: Session, limit: int = 20) -> list[SessionOut]:
    rows = db.scalars(
        select(FuelingSession)
        .options(
            selectinload(FuelingSession.pump),
            selectinload(FuelingSession.fuel),
            selectinload(FuelingSession.tariff),
        )
        .order_by(FuelingSession.id.desc())
        .limit(limit)
    ).all()
    now = datetime.now()
    result = []
    for row in rows:
        row = sync_session(db, row, now)
        result.append(to_session_out(row, now))
    return result


def stop_session(db: Session, session_id: int) -> SessionOut:
    session = _load_session(db, session_id)
    now = datetime.now()
    if session.status != "running":
        return to_session_out(session, now)
    session.dispensed_liters = round(_elapsed_liters(session, now), 3)
    session.status = "stopped"
    session.finished_at = now
    db.commit()
    db.refresh(session)
    return to_session_out(_load_session(db, session.id), now)
