# -*- coding: utf-8 -*-
import re
from enum import Enum
from typing import Union
from warnings import warn

from pydantic import validator
from sqlalchemy.orm import Query
from sqlalchemy.sql.selectable import Select

from .base import BaseFilterModel


def _backward_compatible_value_for_like_and_ilike(value: str):
    """Add % if not in value to be backward compatible.

    Args:
        value (str): The value to filter.

    Returns:
        Either the unmodified value if a percent sign is present, the value wrapped in % otherwise to preserve
        current behavior.
    """
    if value[0] != '%' and value[-1] != '%':
        value = f"%{value}%"
    return value


_orm_operator_transformer = {
    "neq": lambda value: ("__ne__", value),
    "gt": lambda value: ("__gt__", value),
    "gte": lambda value: ("__ge__", value),
    "in": lambda value: ("in_", value),
    "isnull": lambda value: ("is_", None) if value is True else ("is_not", None),
    "lt": lambda value: ("__lt__", value),
    "lte": lambda value: ("__le__", value),
    "like": lambda value: ("like", _backward_compatible_value_for_like_and_ilike(value)),
    "ilike": lambda value: ("ilike", _backward_compatible_value_for_like_and_ilike(value)),
    # XXX(arthurio): Mysql excludes None values when using `in` or `not in` filters.
    "not": lambda value: ("is_not", value),
    "notin": lambda value: ("not_in", value),
}
"""Operators à la Django.

Examples:
    my_datetime__gte
    count__lt
    name__isnull
    user_id__in
"""


class Filter(BaseFilterModel):
    """Base filter for orm related filters.

    All children must set:
        ```python
        class Constants(Filter.Constants):
            model = MyModel
        ```

    It can handle regular field names and Django style operators.

    Example:
        ```python
        class MyModel:
            id: PrimaryKey()
            name: StringField(nullable=True)
            count: IntegerField()
            created_at: DatetimeField()

        class MyModelFilter(Filter):
            id: Optional[int]
            id__in: Optional[str]
            count: Optional[int]
            count__lte: Optional[int]
            created_at__gt: Optional[datetime]
            name__isnull: Optional[bool]
    """

    class Direction(str, Enum):
        asc = "asc"
        desc = "desc"

    @validator("*", pre=True)
    def split_str(cls, value, field):
        if (
                field.name.endswith("__in")
                or field.name.endswith("__not_in")
        ) and isinstance(value, str):
            return [field.type_(v) for v in value.split(",")]
        return value

    def filter(self, query: Union[Query, Select]):
        for field_name, value in self.filtering_fields:
            if value is None or value == '':
                continue
            field_value = getattr(self, field_name)
            if isinstance(field_value, Filter):
                query = field_value.filter(query.join(field_value.Constants.model, field_value.Constants.onclause))
            else:
                if "__" in field_name:
                    field_name, operator = re.compile(r'(.*?)__(\w+)$').findall(field_name)[0]
                    operator, value = _orm_operator_transformer[operator](value)
                else:
                    operator = "__eq__"

                model_field = getattr(self.Constants.model, field_name)
                query = query.filter(getattr(model_field, operator)(value))

        return query
