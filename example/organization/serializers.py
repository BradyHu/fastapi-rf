from fastapi_rf.serializers import BaseSchemaModel as BaseModel

class OrganizationBase(BaseModel):
    pass


class OrganizationCreate(BaseModel):
    name: str


class OrganizationRead(BaseModel):
    id: int
    uuid: str
    name: str