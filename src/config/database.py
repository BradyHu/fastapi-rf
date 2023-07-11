from sqlalchemy.orm import sessionmaker
from .settings import DATABASE as _DB
from sqlalchemy.future.engine import Engine
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio import AsyncSession


class Database:
    url: str
    engine: Engine

    def __init__(self, url, connect_args=None, **kwargs) -> None:
        self.url = url
        self.engine = create_async_engine(url, connect_args=connect_args, future=True)
        self.SessionLocal = sessionmaker(self.engine, autoflush=False, class_=AsyncSession)


DATABASE = Database(**_DB)
