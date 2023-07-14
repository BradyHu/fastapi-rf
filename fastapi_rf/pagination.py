from typing import Any
from sqlalchemy.sql import Select
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
# Dependency
from fastapi_rf.dependency import get_db
from fastapi_rf.serializers import BaseSchemaModel


class BasePagination:
    _cache_return_type = {}

    async def paginate(self, qs: Select) -> Any:
        raise NotImplementedError

    @classmethod
    def get_paginated_return_type(cls, T: Any):
        if cls._cache_return_type.get(T):
            return cls._cache_return_type[T]
        ret = cls.get_schema(T)
        cls._cache_return_type[T] = ret
        return ret

    @classmethod
    def get_schema(cls, T):
        class PaginatedResponse(BaseSchemaModel):
            results: list[T]
        return PaginatedResponse


class LimitOffsetPagination(BasePagination):
    DEFAULT_LIMIT = 20

    def __init__(self, limit: int = DEFAULT_LIMIT, offset: int = 0, db: AsyncSession = Depends(get_db)):
        self.limit = limit
        self.offset = offset
        self.db = db

    @classmethod
    def get_schema(cls, T: Any):
        klass = type(f"{T.__name__}LimitOffsetResponse", (BaseSchemaModel,), {
            "__annotations__": {
                "total": int,
                "limit": int,
                "offset": int,
                "results": list[T]
            }
        })
        return klass

    async def paginate(self, qs: Select):
        ret = await self.db.scalars(
            qs.limit(self.limit).offset(self.offset)
        )
        ret = ret.all()
        return {
            "total": await self.db.scalar(select(func.count("*")).select_from(qs)),
            "limit": self.limit,
            "offset": self.offset,
            "results": ret
        }
