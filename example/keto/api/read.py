from keto.engine import CheckEngine, ExpandEngine, PermissionEngine
from keto.definitions import SubjectID, SubjectSet, RelationTuple
from keto.models import KetoRelationTuples
import typing as t
from sqlalchemy.ext.asyncio import AsyncSession
from config.database import DATABASE
from sqlalchemy.future import select


class ReadApi(object):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def check(self, namespace: str, object: str, relation: str = None, subject_id: str = None, subject_set_namespace: str = None,
                    subject_set_object: str = None, subject_set_relation: str = None, max_depth=-1, ):
        """
        Use: check <subject> <relation> <namespace> <object>
        Check whether a subject has a relation on an object.
        """
        if subject_id:
            subject = SubjectID(id=subject_id)
        else:
            assert subject_set_namespace and \
                subject_set_object and \
                subject_set_relation, "must provide subject_id or subject_set"
            subject = SubjectSet(namespace=subject_set_namespace, object=subject_set_object, relation=subject_set_relation)
        relation_tuple = RelationTuple(namespace=namespace, object=object, relation=relation)
        engine = CheckEngine(self.session)
        allowed = await engine.subject_is_allowed(subject, relation_tuple, max_depth)
        return allowed

    async def expand(self, namespace: str, object: str, relation: str = None, max_depth=-1):
        """
        Use: expand <relation> <namespace> <object>
        """
        subject = SubjectSet(namespace=namespace, object=object, relation=relation)
        engine = ExpandEngine(self.session)
        tree = await engine.build_tree(subject, max_depth)
        return tree

    async def query_permission_tree(self, namespace: str, domain: str, subject_id: str, max_depth=-1):
        subject = SubjectID(id=subject_id)
        engine = PermissionEngine(self.session)
        tree = await engine.build_tree(namespace, domain, subject, max_depth)
        return tree

    # # 这部分是定制为自己的项目写的，其实应该移到项目中去，因此注释，作为示例展示
    # def query_permission(namespace: str, domain: str, subject_id: str, max_depth=-1) -> t.List[str]:
    #     tree = query_permission_tree(namespace, domain, subject_id, max_depth)
    #     if tree is None:
    #         return []
    #     ret = []
    #     queue = tree.children
    #     while queue:
    #         node = queue.pop(0)
    #         if node.relation == 'menu_owner':
    #             ret.append(re.compile(r'^/\d+/groups/(.*?)/menus/(.*?)$').findall(node.object)[0])
    #         queue.extend(node.children)
    #     return ret

    # 根据指定条件，快速筛选满足条件的relation_tuples

    async def get_relation_tuples(self, namespace: str = None, object: str = None, relation: str = None, subject_id: str = None,
                                  subject_set_namespace: str = None,
                                  subject_set_object: str = None, subject_set_relation: str = None) -> t.List[RelationTuple]:
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
        query = select(KetoRelationTuples).where(*args)
        rels = await self.session.execute(query)
        return rels
