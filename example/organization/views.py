from fastapi import APIRouter, HTTPException
from fastapi_rf.views import ViewSet, register, action
from fastapi_rf.pagination import LimitOffsetPagination
from user.authorization import JWTAuthorization
from sqlalchemy.sql.expression import select
from sqlalchemy.orm import selectinload
from . import models
from . import serializers

router = APIRouter(
    prefix='/organization'
)


@register(router, 'organizations')
class OrganizationViewSet(ViewSet):
    _model = models.Organization
    _serializer_read = serializers.OrganizationRead
    _serializer_write = serializers.OrganizationCreate
    _authorization_classes = [JWTAuthorization]

    @action('get')
    async def current_organization(self) -> serializers.OrganizationRead | None:
        query = select(models.UserCurrentOrganization).where(
            models.UserCurrentOrganization.user == self.user
        ).options(selectinload(models.UserCurrentOrganization.organization))
        instance: models.UserCurrentOrganization = await self.db.scalar(query)
        return instance.organization
