from core.serializers import BaseSchemaModel as BaseModel
# from pydantic import Field


class UserBase(BaseModel):
    username: str = None
    nickname: str

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
