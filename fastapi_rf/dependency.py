from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from config.database import DATABASE


async def get_db(request: Request) -> AsyncSession:
    session: AsyncSession

    async with DATABASE.get_engine() as engine:
        session = sessionmaker(engine, autoflush=False, class_=AsyncSession)
        async with session() as db:
            yield db
            await db.commit()
