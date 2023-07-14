from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import select, delete
from sqlalchemy.orm import selectinload
from wechatpy import WeChatClient
from wechatpy import WeChatClientException

from fastapi_rf.dependency import get_db
from fastapi_rf.views import BaseViewSet, register, action
from fastapi_rf.serializers import BaseSchemaModel
from config.settings import WXAPP_KEYS
import enum

from user import serializers
from user import models
from user import utils
from user.authorization import JWTAuthorization
from config.redis import get_redis, Redis

import requests

router = APIRouter()

wx_client_cache = {}


class WxAPPViewSet(BaseViewSet):
    """微信小程序注册登录"""
    # redis: Redis = Depends(get_redis)
    # _redis_prefix = 'wxapp:'
    db: AsyncSession = Depends(get_db)

    @action('post')
    async def login(
            self,
            wxapp_origin_id: str,
            code: str
    ) -> serializers.Token:
        """登录
        可以通过code 获取用户的openid， union id
        """
        wxapp_key = WXAPP_KEYS[wxapp_origin_id]['wxapp_key']
        wxapp_secret = WXAPP_KEYS[wxapp_origin_id]['wxapp_secret']
        if wx_client_cache.get(wxapp_key + wxapp_secret):
            wx_client = wx_client_cache.get(wxapp_key + wxapp_secret)
        else:
            wx_client = WeChatClient(wxapp_key, wxapp_secret)
            wx_client_cache.setdefault(wxapp_key + wxapp_secret, wx_client)
        json_data = wx_client.wxa.code_to_session(code)
        unionid = json_data.get('unionid')
        query = select(models.UserSocialAuth).where(
            models.UserSocialAuth.provider == 'wxapp',
            models.UserSocialAuth.uid == unionid
        ).options(selectinload(models.UserSocialAuth.user))
        instance: models.UserSocialAuth = await self.db.scalar(query)
        if instance is None:
            raise HTTPException(
                400,
                detail={
                    'message': "找不到用户，请先注册",
                    'unionid': unionid
                }
            )
        user = instance.user
        return {
            'access_token': utils.create_access_token({'id': user.id}),
            'token_type': 'bearer'
        }

    @action('post', 'register')
    async def _register(
            self,
            wxapp_origin_id: str,
            mobile_code: str,
            code: str = "",
            union_id: str = ""
    ) -> serializers.Token:
        """小程序注册接口"""

        if code:
            wxapp_key = WXAPP_KEYS[wxapp_origin_id]['wxapp_key']
            wxapp_secret = WXAPP_KEYS[wxapp_origin_id]['wxapp_secret']
            if wx_client_cache.get(wxapp_key + wxapp_secret):
                wx_client = wx_client_cache.get(wxapp_key + wxapp_secret)
            else:
                wx_client = WeChatClient(wxapp_key, wxapp_secret)
                wx_client_cache.setdefault(wxapp_key + wxapp_secret, wx_client)
            json_data = wx_client.wxa.code_to_session(code)
            union_id = json_data.get('unionid')
        # session_key = json_data.get('session_key')
        mobile_json_data = requests.post(
            "https://api.weixin.qq.com/wxa/business/getuserphonenumber",
            params={
                'access_token': wx_client.access_token,
                "code": mobile_code
            },
            timeout=5
        ).json()
        mobile = f"+{mobile_json_data['phone_info']['countryCode']}{mobile_json_data['phone_info']['purePhoneNumber']}"
        # 注册用户
        user_instance = models.User(
            nickname=mobile,
            mobile=mobile
        )
        self.db.add(user_instance)
        await self.db.flush()
        social_auth_instance = models.UserSocialAuth(
            user=user_instance,
            provider='wxapp',
            uid=union_id
        )
        self.db.add(social_auth_instance)
        await self.db.flush()
        token = utils.create_access_token({
            "id": user_instance.id
        })
        return {"access_token": token, 'token_type': "bearer"}
