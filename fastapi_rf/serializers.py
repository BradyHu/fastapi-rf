import datetime
from typing import Container, Optional, Type

import pydantic
from pydantic import BaseConfig, BaseModel, create_model
from sqlalchemy.inspection import inspect
from sqlalchemy.orm.properties import ColumnProperty

from fastapi_rf import utils


class BaseSchemaModel(pydantic.BaseModel):
    class Config(BaseConfig):
        orm_mode: bool = True
        validate_assignment: bool = True
        allow_population_by_field_name: bool = True
        json_encoders: dict = {datetime.datetime: utils.format_datetime_into_isoformat}
        # alias_generator: typing.Any = utils.format_dict_key_to_camel_case


class AllOptional(pydantic.main.ModelMetaclass):
    def __new__(cls, name, bases, namespaces, **kwargs):
        sub_cls = super().__new__(cls, name, bases, namespaces, **kwargs)
        for field in sub_cls.__fields__.values():
            field.required = False
        return sub_cls


def sqlalchemy_to_pydantic(
        db_model: Type, *, config: Type = BaseSchemaModel.Config, exclude: Container[str] = []
) -> Type[BaseModel]:
    mapper = inspect(db_model)
    fields = {}
    for attr in mapper.attrs:
        if isinstance(attr, ColumnProperty):
            if attr.columns:
                name = attr.key
                if name in exclude:
                    continue
                column = attr.columns[0]
                python_type: Optional[type] = None
                if hasattr(column.type, "impl"):
                    if hasattr(column.type.impl, "python_type"):
                        python_type = column.type.impl.python_type
                elif hasattr(column.type, "python_type"):
                    python_type = column.type.python_type
                assert python_type, f"Could not infer python_type for {column}"
                default = None
                if column.default is None and not column.nullable:
                    default = ...
                fields[name] = (python_type, pydantic.Field(default=default, description=column.comment))
    pydantic_model = create_model(
        db_model.__name__, __config__=config, **fields  # type: ignore
    )
    return pydantic_model
