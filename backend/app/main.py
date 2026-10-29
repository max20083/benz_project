from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.database import Base, SessionLocal, engine, get_db
from app.models import Fuel, Tariff
from app.schemas import CatalogOut, FuelOut, SessionCreate, SessionOut, TariffOut
from app.seed import seed
from app import service


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()
    yield


app = FastAPI(title="АЗС Бенз", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/catalog", response_model=CatalogOut)
def catalog(db: Session = Depends(get_db)) -> CatalogOut:
    fuels = db.query(Fuel).order_by(Fuel.id).all()
    tariffs = db.query(Tariff).order_by(Tariff.id).all()
    return CatalogOut(
        fuels=[FuelOut.model_validate(item) for item in fuels],
        tariffs=[TariffOut.model_validate(item) for item in tariffs],
        pumps=service.list_pumps(db),
    )


@app.post("/api/sessions", response_model=SessionOut, status_code=201)
def create_session(payload: SessionCreate, db: Session = Depends(get_db)) -> SessionOut:
    return service.start_session(
        db,
        pump_id=payload.pump_id,
        fuel_id=payload.fuel_id,
        tariff_id=payload.tariff_id,
        mode=payload.mode,
        value=payload.value,
    )


@app.get("/api/sessions", response_model=list[SessionOut])
def sessions(limit: int = 20, db: Session = Depends(get_db)) -> list[SessionOut]:
    return service.list_sessions(db, limit=min(limit, 100))


@app.get("/api/sessions/{session_id}", response_model=SessionOut)
def session_detail(session_id: int, db: Session = Depends(get_db)) -> SessionOut:
    return service.get_session(db, session_id)


@app.post("/api/sessions/{session_id}/stop", response_model=SessionOut)
def stop_session(session_id: int, db: Session = Depends(get_db)) -> SessionOut:
    return service.stop_session(db, session_id)
