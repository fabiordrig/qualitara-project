# backend/app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, async_session_maker
from app.seeds import seed_zones, seed_vehicles
from app.telemetry.router import router as telemetry_router
from app.anomalies.router import router as anomalies_router
from app.zones.router import router as zones_router
from app.fleet.router import router as fleet_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with async_session_maker() as session:
        async with session.begin():
            await seed_zones(session)
            await seed_vehicles(session)
    yield
    await engine.dispose()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000"
    ],  # Phase 2 React dev server; NOT wildcard (ASVS V14)
    allow_credentials=False,  # no cookies/credentials are used
    allow_methods=["GET"],  # dashboard is read-only
    allow_headers=["Content-Type"],
)

app.include_router(telemetry_router)
app.include_router(anomalies_router)
app.include_router(zones_router)
app.include_router(fleet_router)
