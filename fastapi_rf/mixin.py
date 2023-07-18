from fastapi import HTTPException, Response
from sqlalchemy.sql.expression import select

from fastapi_rf.core import GenericViewSet, action, W, R
from fastapi_rf.pagination import PaginationMixin


class ListMixin(PaginationMixin, GenericViewSet):
    async def list(self):
        if self._pagination_class:
            return await self._pagination_class.paginate(await self.get_queryset())
        ret = await self.db.scalars(
            await self.get_queryset()
        )
        return ret.all()

    @classmethod
    def discover_endpoint(cls):
        cls.list = action('get', '/', detail=False)(cls.list)
        return super().discover_endpoint()


class CreateMixin(GenericViewSet):
    async def create(self, body: W) -> R:
        query = select(self._model).filter_by(**body.dict())
        if await self.db.scalar(query):
            raise HTTPException(
                400,
                "record already exists"
            )
        instance = self._model(**body.dict())
        self.db.add(instance)
        await self.db.flush()
        return instance

    @classmethod
    def discover_endpoint(cls):
        cls.create = action('post', '/', detail=False)(cls.create)
        return super().discover_endpoint()


class RetrieveMixin(GenericViewSet):
    async def retrieve(self) -> R:
        return await self.get_object()

    @classmethod
    def discover_endpoint(cls):
        cls.retrieve = action('get', f"/{{{cls._pk_field}}}/")(cls.retrieve)
        return super().discover_endpoint()


class UpdateMixin(GenericViewSet):
    async def update(self, body: W) -> R:
        instance = await self.get_object()
        for k, v in body.dict().items():
            setattr(instance, k, v)
        await self.db.flush()
        return instance

    @classmethod
    def discover_endpoint(cls):
        cls.update = action('put', f"/{{{cls._pk_field}}}/")(cls.update)
        return super().discover_endpoint()


class DestroyMixin(GenericViewSet):
    async def destroy(self):
        instance = await self.get_object()
        await self.db.delete(instance)
        return Response(status_code=204)

    @classmethod
    def discover_endpoint(cls):
        cls.destroy = action('delete', f"/{{{cls._pk_field}}}/")(cls.destroy)
        return super().discover_endpoint()
