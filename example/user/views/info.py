from fastapi import APIRouter
from fastapi_rf.core import GenericViewSet, register, action
from user.authorization import JWTAuthorization
from user.mixin import AuthorizationMixin
from user import serializers

router = APIRouter()


@register(router, 'info')
class UserViewSet(AuthorizationMixin, GenericViewSet):
    _authorization_classes = [JWTAuthorization]

    @action('get',detail=False)
    async def info(self) -> serializers.UserRead:
        return self.user
