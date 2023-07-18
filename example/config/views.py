from fastapi_rf.views import ViewSet as Base
from user.mixin import AuthorizationMixin
from user.authorization import JWTAuthorization
from fastapi_rf.pagination import LimitOffsetPagination

class ViewSet(
    AuthorizationMixin,
    Base
):
    _authorization_classes = [JWTAuthorization]
    _pagination_class = LimitOffsetPagination