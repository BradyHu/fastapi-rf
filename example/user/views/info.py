from fastapi import APIRouter
from fastapi_rf.views import GenericViewSet, register, action
from user.authorization import JWTAuthorization
from user import serializers

router = APIRouter()


@register(router, 'info')
class UserViewSet(GenericViewSet):
    _authorization_classes = [JWTAuthorization]

    @action('get')
    async def info(self) -> serializers.UserRead:
        return self.user
