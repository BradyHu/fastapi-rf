from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import select

from core.dependency import get_db
from core.views import BaseViewSet, register, action

from user import serializers
from user import models
from user import utils


router = APIRouter()


@register(router, 'account')
class AccountViewSet(BaseViewSet):
    db: AsyncSession = Depends(get_db)

    @action('post', 'register')
    async def _register(self, user: serializers.UserCreate,) -> serializers.UserRead:

        # @router.post('/register')
        # async def register(user: serializers.UserCreate, db: AsyncSession = Depends(get_db)) -> serializers.UserRead:
        query = select(models.User).filter_by(username=user.username)
        if await self.db.scalar(query):
            raise HTTPException(status_code=400, detail='Username has been used, please use another one.')
        instance = models.User(
            username=user.username,
            nickname=user.nickname,
            password=utils.get_password_hash(user.password),
        )
        self.db.add(instance)
        await self.db.flush()
        return instance

    @action('post')
    async def token(self, form_data: OAuth2PasswordRequestForm = Depends()) -> serializers.Token:
        query = select(models.User).filter_by(username=form_data.username)
        instance = await self.db.scalar(query)
        if instance is None:
            raise HTTPException(401, "Can not Find User")
        if not utils.verify_password(form_data.password, instance.password):
            raise HTTPException(401, "Wrong Password")
        token = utils.create_access_token({
            "id": instance.id
        })
        return {"access_token": token, 'token_type': "bearer"}
