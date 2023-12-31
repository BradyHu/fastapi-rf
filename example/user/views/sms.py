import enum

from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import select, delete

from fastapi_rf.core import BaseViewSet, register, action
from fastapi_rf.dependency import get_db
from fastapi_rf.serializers import BaseSchemaModel
from user import models
from user import serializers
from user import utils

router = APIRouter()


class Action(str, enum.Enum):
    register = "register"
    login = "login"
    reset = "reset"
    rebind = "rebind"


class SendSMS(BaseSchemaModel):
    mobile: str
    action: str


@register(router, 'sms')
class SmsViewSet(BaseViewSet):
    db: AsyncSession = Depends(get_db)

    @action('post', detail=False)
    async def code(self, data: SendSMS):
        mobile = data.mobile
        action = data.action
        code = utils.generate_sms_code()
        query = delete(models.VerifyCode).filter_by(
            mobile=mobile
        )
        await self.db.execute(query)
        instance = models.VerifyCode(
            mobile=mobile,
            code=code,
            action=action
        )
        self.db.add(instance)
        await self.db.flush()
        return {
            "mobile": mobile,
            "action": action,
            "code": code
        }

    @action('post', 'register', detail=False)
    async def _register(self, mobile: str, code: str) -> serializers.UserRead:
        """注册接口不是必须的，因为登录接口会默认给用户做注册"""
        query = select(models.VerifyCode).filter_by(
            mobile=mobile,
            action=Action.register
        )
        instance = await self.db.scalar(query)
        if instance.code != code:
            raise HTTPException(
                400,
                "验证码错误"
            )
        if instance is None:
            raise HTTPException(
                400,
                "请先发送验证码"
            )

        instance = await self.do_register(mobile)
        return instance

    async def do_register(self, mobile):
        query = select(models.User).where(models.User.mobile == mobile)

        instance = await self.db.scalar(query)
        if instance is not None:
            raise HTTPException(
                400,
                '该用户已注册'
            )
        instance = models.User(
            mobile=mobile,
            nickname=mobile,
        )
        self.db.add(instance)
        await self.db.flush()
        return instance

    @action('post', 'login', detail=False)
    async def login(self, mobile: str = Form(), code: str = Form(), ) -> serializers.Token:
        query = select(models.VerifyCode).filter_by(
            mobile=mobile,
            action=Action.login
        )
        instance = await self.db.scalar(query)
        if instance is None:
            raise HTTPException(
                400,
                "请先发送验证码"
            )
        if instance.code != code:
            raise HTTPException(
                400,
                '验证码错误'
            )
        query = select(models.User).where(models.User.mobile == mobile)
        instance = await self.db.scalar(query)
        if instance is None:
            instance = await self.do_register(mobile)
        token = utils.create_access_token({
            "id": instance.id
        })
        return {
            'access_token': token, 'token_type': "bearer"
        }
