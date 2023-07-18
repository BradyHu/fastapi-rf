from fastapi import APIRouter
from sqlalchemy import Select
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.expression import select

from config.views import ViewSet
from fastapi_rf.core import register, action
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

    async def get_queryset(self) -> Select:
        qs = await super().get_queryset()
        if self.user.is_superuser:
            return qs
        qs = select(models.Organization).join(models.OrganizationMember).join(models.User).where(
            models.User.id == self.user.id
        )
        return qs

    @action('get', detail=False)
    async def current_organization(self) -> serializers.OrganizationRead | None:
        query = select(models.UserCurrentOrganization).where(
            models.UserCurrentOrganization.user == self.user
        ).options(selectinload(models.UserCurrentOrganization.organization))
        instance: models.UserCurrentOrganization = await self.db.scalar(query)
        return instance.organization
