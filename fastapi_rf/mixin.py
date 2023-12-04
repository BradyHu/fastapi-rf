from datetime import datetime

from fastapi import HTTPException, Response, Body
from pydantic import BaseModel
from sqlalchemy import delete
from sqlalchemy.sql.expression import select
from starlette.requests import Request

from fastapi_rf.core import GenericViewSet, action, W, R
from fastapi_rf.pagination import PaginationMixin


class ListMixin(PaginationMixin, GenericViewSet):
    async def list(self):
        if self.pagination_class:
            return await self.pagination_class.paginate(await self.get_queryset())
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
        # query = select(self.model).filter_by(**body.dict())
        # if await self.db.scalar(query):
        #     raise HTTPException(
        #         400,
        #         "record already exists"
        #     )
        data = body.dict()
        data.update(await self.get_create_extra_info())
        instance = self.model(**data)
        self.db.add(instance)
        await self.db.flush()
        # query = select(self.model).where(getattr(self.model, self.pk_field) == getattr(instance, self.pk_field))
        # instance = await self.db.scalar(query)
        return instance

    async def get_create_extra_info(self) -> dict:
        return {}

    @classmethod
    def discover_endpoint(cls):
        cls.create = action('post', '/', detail=False)(cls.create)
        return super().discover_endpoint()


class BatchCreateMixin(GenericViewSet):
    async def batch_create(self, body: list[W]) -> list[R]:
        # query = select(self.model).filter_by(**body.dict())
        # if await self.db.scalar(query):
        #     raise HTTPException(
        #         400,
        #         "record already exists"
        #     )
        rels = []
        for _body in body:
            data = _body.dict()
            data.update(await self.get_create_extra_info())
            instance = self.model(**data)
            self.db.add(instance)
            await self.db.flush()
            rels.append(instance)
        return rels

    async def get_create_extra_info(self) -> dict:
        return {}

    @classmethod
    def discover_endpoint(cls):
        cls.batch_create = action('post', '/batch_create', detail=False)(cls.batch_create)
        return super().discover_endpoint()


class RetrieveMixin(GenericViewSet):
    async def retrieve(self) -> R:
        return await self.get_object()

    @classmethod
    def discover_endpoint(cls):
        cls.retrieve = action('get', f"/")(cls.retrieve)
        return super().discover_endpoint()


class UpdateMixin(GenericViewSet):
    async def update(self, body: W) -> R:
        if body is None:
            raise HTTPException(400, "body required")
        instance = await self.get_object()
        for k, v in body.dict().items():
            setattr(instance, k, v)
        if hasattr(instance, 'updated_at'):
            instance.updated_at = datetime.utcnow()
        self.db.add(instance)
        await self.db.flush()
        return instance

    @classmethod
    def discover_endpoint(cls):
        cls.update = action('put', f"/")(cls.update)
        return super().discover_endpoint()


class PartialUpdateMixin(GenericViewSet):
    async def partial_update(self, body: W, request: Request) -> R:
        raw_body = await request.json()
        if body is None:
            raise HTTPException(400, 'body required')
        instance = await self.get_object()
        for k, v in body.dict().items():
            # 部分更新，如果request中没放东西，就不更新
            if k in raw_body.keys():
                setattr(instance, k, v)
        if hasattr(instance, 'updated_at'):
            instance.updated_at = datetime.utcnow()
        self.db.add(instance)
        await self.db.flush()
        return instance

    @classmethod
    def discover_endpoint(cls):
        cls.partial_update = action('patch', f'/')(cls.partial_update)
        return super().discover_endpoint()


class DestroyMixin(GenericViewSet):
    async def destroy(self):
        instance = await self.get_object()
        await self.db.delete(instance)
        return Response(status_code=204)

    @classmethod
    def discover_endpoint(cls):
        cls.destroy = action('delete', f"/")(cls.destroy)
        return super().discover_endpoint()


class BatchDestroyMixin(GenericViewSet):
    class BatchDestroy(BaseModel):
        pks: list

    async def batch_destroy(self, data: BatchDestroy):
        await self.db.execute(delete(self.model).where(
            getattr(self.model, self.pk_field).in_(data.pks)
        ))
        return Response(status_code=204)

    @classmethod
    def discover_endpoint(cls):
        cls.batch_destroy = action('post', f"/batch_destroy", detail=False)(cls.batch_destroy)
        return super().discover_endpoint()
