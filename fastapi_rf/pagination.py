import inspect
import typing as t
from typing import Any

from fastapi import Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from fastapi_rf.core import BaseViewSet, add_dependency_to_self
# Dependency
from fastapi_rf.dependency import get_db
from fastapi_rf.serializers import BaseSchemaModel


class BasePagination:
    _cache_return_type = {}

    async def paginate(self, qs: Select) -> Any:
        raise NotImplementedError

    @classmethod
    def get_paginated_return_type(cls, model: Any):
        if cls._cache_return_type.get(model):
            return cls._cache_return_type[model]
        ret = cls.get_schema(model)
        cls._cache_return_type[model] = ret
        return ret

    @classmethod
    def get_schema(cls, model):
        class PaginatedResponse(BaseSchemaModel):
            results: list[model]

        return PaginatedResponse


class LimitOffsetPagination(BasePagination):
    DEFAULT_LIMIT = 20

    def __init__(self, limit: int = DEFAULT_LIMIT, offset: int = 0, db: AsyncSession = Depends(get_db)):
        self.limit = limit
        self.offset = offset
        self.db = db

    @classmethod
    def get_schema(cls, model: Any):
        klass = type(f"{model.__name__}LimitOffsetResponse", (BaseSchemaModel,), {
            "__annotations__": {
                "total": int,
                "limit": int,
                "offset": int,
                "results": list[model]
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


class PaginationMixin(BaseViewSet):
    _pagination_class: t.Type[BasePagination] | None = None
    if t.TYPE_CHECKING:
        _pagination_class: BasePagination | None = None

    @classmethod
    def update_endpoint_signature(cls, func):
        func = super().update_endpoint_signature(func)
        if cls._pagination_class is None:
            if func.__name__ == 'list':
                old_signature = inspect.signature(func)
                return_annotation = list[getattr(cls, '_serializer_read', dict)]
                new_signature = old_signature.replace(return_annotation=return_annotation)
                setattr(func, "__signature__", new_signature)
            return func

        if func.__name__ != 'list':
            # remove_dependency_from_self('pagination_class', func)
            return func
        # 处理翻页涉及的list endpoint
        old_signature = inspect.signature(func)
        return_annotation = cls._pagination_class.get_paginated_return_type(getattr(cls, '_serializer_read', dict))
        new_signature = old_signature.replace(return_annotation=return_annotation)
        setattr(func, "__signature__", new_signature)
        new_func = add_dependency_to_self('_pagination_class', func, default=Depends(cls._pagination_class), )
        return new_func
