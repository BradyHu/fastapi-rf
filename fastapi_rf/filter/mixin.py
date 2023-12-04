import typing as t

from fastapi import Depends
from sqlalchemy import Select

from fastapi_rf.core import GenericViewSet, add_dependency_to_self
from .base import BaseFilterModel, FilterDepends


class FilterMixin(GenericViewSet, ignores=['filter_class']):
    filter_class: t.Type[BaseFilterModel] | None = None
    if t.TYPE_CHECKING:
        filter_class: BaseFilterModel | None = None

    async def get_queryset(self) -> Select:
        queryset = await super().get_queryset()
        if self.filter_class is not None:
            queryset = self.filter_class.filter(queryset)
        return queryset

    @classmethod
    def update_endpoint_signature(cls, func):
        func = super().update_endpoint_signature(func)
        if cls.filter_class is None:
            return func
        if func.detail or func.method !='get':
            new_func = add_dependency_to_self('filter_class', func, default=Depends(lambda: None))
            return new_func
        new_func = add_dependency_to_self('filter_class', func, default=FilterDepends(cls.filter_class), )
        return new_func
