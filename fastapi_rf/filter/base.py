import re
from collections.abc import Iterable
from copy import deepcopy
from typing import Any, Dict, Optional, Tuple, Type, Union, Annotated, get_args

from fastapi import Depends, Query
from fastapi.exceptions import RequestValidationError
from fastapi.params import Depends
from pydantic import BaseModel, Extra, ValidationError, create_model, fields, validator
from pydantic.fields import FieldInfo


class BaseFilterModel(BaseModel, extra=Extra.forbid):
    """Abstract base filter class.

    Provides the interface for filtering.

    # Filtering

    ## Query string examples:

        >>> "?my_field__gt=12&my_other_field=Tomato"
        >>> "?my_field__in=12,13,15&my_other_field__not_in=Tomato,Pepper"
    """

    class Constants:  # pragma: no cover
        model: Type
        prefix: str
        # join options
        onclause = None

    def filter(self, query):  # pragma: no cover
        ...

    @property
    def filtering_fields(self):
        fields = self.dict(exclude_none=True, exclude_unset=True)
        return fields.items()

    @validator("*", pre=True)
    def split_str(cls, value, field):  # pragma: no cover
        ...


def with_prefix(prefix: str, Filter: Type[BaseFilterModel]):
    """Allow re-using existing filter under a prefix.

    Example:
        ```python
        from pydantic import BaseModel

        from fastapi_filter.filter import FilterDepends

        class NumberFilter(BaseModel):
            count: Optional[int]

        class MainFilter(BaseModel):
            name: str
            number_filter: Optional[Filter] = FilterDepends(with_prefix("number_filter", Filter))
        ```

    As a result, you'll get the following filters:
        * name
        * number_filter__count

    # Limitation

    The alias generator is the last to be picked in order of prevalence. So if one of the fields has a `Query` as
    default and declares an alias already, this will be picked first and you won't get the prefix.

    Example:
        ```python
         from pydantic import BaseModel

        class NumberFilter(BaseModel):
            count: Optional[int] = Query(default=10, alias=counter)

        class MainFilter(BaseModel):
            name: str
            number_filter: Optional[Filter] = FilterDepends(with_prefix("number_filter", Filter))
        ```

    As a result, you'll get the following filters:
        * name
        * counter (*NOT* number_filter__counter)
    """

    class NestedFilter(Filter):  # type: ignore[misc, valid-type]
        class Config:
            extra = Extra.forbid

            @classmethod
            def alias_generator(cls, string: str) -> str:
                return f"{prefix}__{string}"

        class Constants(Filter.Constants):  # type: ignore[name-defined]
            ...

    NestedFilter.Constants.prefix = prefix

    return NestedFilter


def _list_to_str_fields(filter_class: Type[BaseFilterModel]):
    # ret: Dict[str, Tuple[Union[object, Type], Optional[FieldInfo]]] = {}
    ret = {
        "__annotations__": {}
    }
    for f in filter_class.__fields__.values():
        field_info = deepcopy(f.field_info)
        if f.shape == fields.SHAPE_LIST:
            if isinstance(field_info.default, Iterable):
                field_info.default = ",".join(field_info.default)
            if f.default is not None:
                ret[f.name] = f.default
            if type(None) in get_args(f.annotation):
                ret['__annotations__'][f.name] = str | None
            else:
                ret['__annotations__'][f.name] = str
    NestedFilter = type("NestedFilter", (filter_class,), ret)
    return NestedFilter


def _with_description(filter_class: Type[BaseFilterModel]):
    ret: Dict[str, Tuple[Union[object, Type], FieldInfo | None]] = {
        "__annotations__": {}
    }
    for f in filter_class.__fields__.values():
        field_info: FieldInfo = deepcopy(f.field_info)
        field_type = filter_class.__annotations__.get(f.name, f.outer_type_)
        field_type = field_type if f.required else Optional[field_type]
        # get field comment
        field_name = f.name
        if "__" in field_name:
            field_name, operator = re.compile(r'(.*?)__(\w+)$').findall(field_name)[0]
        model_field = getattr(filter_class.Constants.model, field_name)
        description = getattr(model_field, 'comment', None)
        if isinstance(f.default, Depends):
            continue
        ret[f.name] = f.default
        ret['__annotations__'][f.name] = Annotated[field_type, Query(description=description)]
        # ret[f.name] = (Annotated[field_type, Query(description=description)], field_info)

    NestedFilter = type("NestedFilter", (filter_class,), ret)
    return NestedFilter


def FilterDepends(Filter: Type[BaseFilterModel], *, by_alias: bool = False, use_cache: bool = True) -> Any:
    """Use a hack to support lists in filters.

    FastAPI doesn't support it yet: https://github.com/tiangolo/fastapi/issues/50

    What we do is loop through the fields of a filter and change any `list` field to a `str` one so that it won't be
    excluded from the possible query parameters.

    When we apply the filter, we build the original filter to properly validate the data (i.e. can the string be parsed
    and formatted as a list of <type>?)
    """
    GeneratedFilter = _with_description(_list_to_str_fields(Filter))

    # GeneratedFilter = _list_to_str_fields(Filter)

    class FilterWrapper(GeneratedFilter):  # type: ignore[misc,valid-type]
        def filter(self, *args, **kwargs):
            try:
                original_filter = Filter(**self.dict(by_alias=by_alias))
            except ValidationError as e:
                raise RequestValidationError(e.raw_errors) from e
            return original_filter.filter(*args, **kwargs)

    return Depends(GeneratedFilter)
