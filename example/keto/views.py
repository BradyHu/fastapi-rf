from . import models
from . import serializers
from fastapi import APIRouter, HTTPException
from fastapi_rf.core import register, action, GenericViewSet
from fastapi_rf.pagination import LimitOffsetPagination
from .api import read
from config.views import ViewSet

router = APIRouter(
    prefix='/keto'
)


@register(router, "relation_tuples")
class KetoViewSet(ViewSet):
    _model = models.KetoRelationTuples
    _serializer_read = serializers.KetoRelationTuplesRead
    _serializer_write = serializers.KetoRelationTuplesWrite
    _pagination_class = LimitOffsetPagination


@register(router, 'read')
class ReadViewSet(GenericViewSet):
    @action(detail=False)
    async def check(self,
                    namespace: str,
                    object: str,
                    relation: str = None,
                    subject_id: str = None,
                    subject_set_namespace: str = None,
                    subject_set_object: str = None,
                    subject_set_relation: str = None,
                    max_depth: int = -1,
                    ) -> bool:
        """
        Use: check subject  relation namespace object
        Check whether a subject has a relation on an object.
        """
        try:
            return await read.ReadApi(self.db).check(
                namespace=namespace,
                object=object,
                relation=relation,
                subject_id=subject_id,
                subject_set_namespace=subject_set_namespace,
                subject_set_object=subject_set_object,
                subject_set_relation=subject_set_relation,
                max_depth=max_depth
            )
        except AssertionError as e:
            raise HTTPException(
                400, detail=e.args
            )

    @action(detail=False)
    async def expand(self,
                     namespace: str,
                     object: str,
                     relation: str = None,
                     max_depth: int = -1
                     ) -> serializers.Tree:
        try:
            return await read.ReadApi(self.db).expand(
                namespace=namespace,
                object=object,
                relation=relation,
                max_depth=max_depth
            )
        except AssertionError as e:
            raise HTTPException(
                400, detail=e.args
            )

    @action(detail=False)
    async def query_permission_tree(self,
                                    namespace: str,
                                    domain: str,
                                    subject_id: str,
                                    max_depth: int = -1,
                                    ) -> serializers.Tree:
        try:
            return await read.ReadApi(self.db).query_permission_tree(
                namespace=namespace,
                domain=domain,
                subject_id=subject_id,
                max_depth=max_depth
            )
        except AssertionError as e:
            raise HTTPException(
                400, detail=e.args
            )
