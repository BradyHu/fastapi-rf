from fastapi_rf.serializers import BaseSchemaModel as BaseModel
# from pydantic import Field


class UserBase(BaseModel):
    username: str|None = None
    nickname: str|None = None

    class Config:
        orm_mode = True


class UserCreate(UserBase):
    password: str


class UserRead(UserBase):
    id: int
    is_active: bool


class Token(BaseModel):
    access_token: str
    token_type: str
