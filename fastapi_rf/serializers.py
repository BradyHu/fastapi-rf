import datetime

import pydantic

from fastapi_rf import utils


class BaseSchemaModel(pydantic.BaseModel):
    class Config:
        orm_mode: bool = True
        validate_assignment: bool = True
        allow_population_by_field_name: bool = True
        json_encoders: dict = {datetime.datetime: utils.format_datetime_into_isoformat}
        # alias_generator: typing.Any = utils.format_dict_key_to_camel_case
