from keto.models import KetoRelationTuples
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import delete, select


class WriteApi(object):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def delete_relation_tuples(self, namespace: str = None, object: str = None, relation: str = None, subject_id: str = None,
                                     subject_set_namespace: str = None, subject_set_object: str = None,
                                     subject_set_relation: str = None, **kwargs):
        args = []
        if namespace:
            args.append(KetoRelationTuples.namespace == namespace)
        if object:
            args.append(KetoRelationTuples.object == object)
        if relation:
            args.append(KetoRelationTuples.relation == relation)
        if subject_id:
            args.append(KetoRelationTuples.subject_id == subject_id)
        if subject_set_namespace:
            args.append(KetoRelationTuples.subject_set_namespace == subject_set_namespace)
        if subject_set_object:
            args.append(KetoRelationTuples.subject_set_object == subject_set_object)
        if subject_set_relation:
            args.append(KetoRelationTuples.subject_set_relation == subject_set_relation)
        query = delete(KetoRelationTuples).where(*args)
        await self.session.execute(query)

    async def patch_multiple_relation_tuples(self, array):
        for item in array:
            await self.patch_relation_tuples(**item)

    async def patch_relation_tuples(self, action: str, namespace: str, object: str, relation: str, subject_id: str = None,
                                    subject_set_namespace: str = None, subject_set_object: str = None,
                                    subject_set_relation: str = None):
        if subject_id is None:
            assert subject_set_namespace is not None and \
                subject_set_object is not None and \
                subject_set_relation is not None, "subject_set_namespace, subject_set_object, and " \
                "subject_set_relation are required when subject_id is not specified"
        if action == 'insert':
            query = select(KetoRelationTuples).filter_by(
                namespace=namespace,
                object=object,
                relation=relation,
                subject_id=subject_id,
                subject_set_namespace=subject_set_namespace,
                subject_set_object=subject_set_object,
                subject_set_relation=subject_set_relation
            ).exists()
            if not await self.session.scalar(query):
                instance = KetoRelationTuples(
                    namespace=namespace,
                    object=object,
                    relation=relation,
                    subject_id=subject_id,
                    subject_set_namespace=subject_set_namespace,
                    subject_set_object=subject_set_object,
                    subject_set_relation=subject_set_relation
                )
                self.session.add(instance)
        elif action == 'delete':
            query = delete(KetoRelationTuples).filter_by(
                namespace=namespace,
                object=object,
                relation=relation,
                subject_id=subject_id,
                subject_set_namespace=subject_set_namespace,
                subject_set_object=subject_set_object,
                subject_set_relation=subject_set_relation
            )
            await self.session.execute(query)
        else:
            raise Exception(detail={'msg': 'action must be insert or delete'})

    async def create_relation_tuple(self, namespace: str, object: str, relation: str, subject_id: str = None,
                                    subject_set_namespace: str = None, subject_set_object: str = None,
                                    subject_set_relation: str = None):
        if subject_id is None:
            assert subject_set_namespace is not None and \
                subject_set_object is not None and \
                subject_set_relation is not None, "subject_set_namespace, subject_set_object, and " \
                "subject_set_relation are required when subject_id is not specified"
        try:
            query = select(KetoRelationTuples).filter_by(
                namespace=namespace,
                object=object,
                relation=relation,
                subject_id=subject_id,
                subject_set_namespace=subject_set_namespace,
                subject_set_object=subject_set_object,
                subject_set_relation=subject_set_relation
            ).exists()
            if not await self.session.scalar(query):
                instance = KetoRelationTuples(
                    namespace=namespace,
                    object=object,
                    relation=relation,
                    subject_id=subject_id,
                    subject_set_namespace=subject_set_namespace,
                    subject_set_object=subject_set_object,
                    subject_set_relation=subject_set_relation
                )
                self.session.add(instance)
        except Exception as e:
            raise e
        return instance
