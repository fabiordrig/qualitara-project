# backend/app/seeds.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert
from app.fleet.models import Vehicle
from app.zones.models import Zone
from app.zones.constants import ZONE_NAMES

VEHICLE_IDS = [f"v-{i}" for i in range(1, 51)]


async def seed_zones(session: AsyncSession) -> None:
    stmt = pg_insert(Zone).values([
        {"zone_id": z, "entry_count": 0} for z in ZONE_NAMES
    ])
    stmt = stmt.on_conflict_do_nothing(index_elements=["zone_id"])
    await session.execute(stmt)


async def seed_vehicles(session: AsyncSession) -> None:
    stmt = pg_insert(Vehicle).values([
        {"vehicle_id": v, "current_status": "idle", "current_battery": 100.0}
        for v in VEHICLE_IDS
    ])
    stmt = stmt.on_conflict_do_nothing(index_elements=["vehicle_id"])
    await session.execute(stmt)


if __name__ == "__main__":
    import asyncio
    from app.database import engine, async_session_maker

    async def main() -> None:
        async with async_session_maker() as session:
            async with session.begin():
                await seed_zones(session)
                await seed_vehicles(session)
        await engine.dispose()

    asyncio.run(main())
