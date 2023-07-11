from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from config.database import DATABASE


async def get_db(request: Request) -> AsyncSession:
    session: AsyncSession
    async with DATABASE.SessionLocal() as session:
        yield session
        await session.commit()
