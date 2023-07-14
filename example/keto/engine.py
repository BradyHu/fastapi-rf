from .models import KetoRelationTuples
from . import definitions
import typing as t
from config import settings
from sqlalchemy.ext.asyncio import AsyncSession
from config.database import DATABASE
from sqlalchemy import text
from sqlalchemy import func, select


class GraphMixin:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.visited = set()

    def check_and_add_visited(self, id: str):
        if id in self.visited:
            return True
        else:
            self.visited.add(id)
            return False


class CheckEngine(GraphMixin):
    async def _subject_is_allowed(self, requested: definitions.Subject, rels: t.List[definitions.RelationTuple],
                                  rest_depth: int) -> bool:
        for sr in rels[:]:
            was_already_visited = self.check_and_add_visited(sr.subject.unique_id())

            if was_already_visited:
                continue

            if requested == sr.subject:
                return True
            sub = sr.subject
            if not isinstance(sub, definitions.SubjectSet):
                continue

            allowed = await self.check_one_indirection_further(requested, definitions.RelationTuple(
                object=sub.object,
                relation=sub.relation,
                namespace=sub.namespace
            ), rest_depth - 1)

            if allowed:
                return True

        return False

    async def check_one_indirection_further(self, requested: definitions.Subject, expand_query: definitions.RelationTuple,
                                            rest_depth: int) -> bool:
        if rest_depth == 0:
            return False
        query = select(KetoRelationTuples).where(
            KetoRelationTuples.namespace == expand_query.namespace,
            KetoRelationTuples.object == expand_query.object,
            KetoRelationTuples.relation == expand_query.relation
        )
        next_rels: t.List[KetoRelationTuples] = await self.session.execute(query)
        next_rels: t.List[definitions.RelationTuple] = [i.to_relation_tuple() for i in next_rels]

        allowed = self._subject_is_allowed(requested, next_rels, rest_depth)
        if allowed:
            return allowed

        return False

    async def subject_is_allowed(self, subject: definitions.Subject, r: definitions.RelationTuple, rest_depth=-1) -> bool:
        global_max_depth = getattr(settings, 'KETO_MAX_INDIRECTION_DEPTH', 32)
        if rest_depth <= 0 or rest_depth > global_max_depth:
            rest_depth = global_max_depth
        return await self.check_one_indirection_further(subject, r, rest_depth)


class CheckEngineCTE(CheckEngine):
    async def check_one_indirection_further(self, requested: definitions.Subject, expand_query: definitions.RelationTuple,
                                            rest_depth: int) -> bool:
        """新版本函数，采用rte方式进行快速查询，提升查询效率"""
        cnt = await self.session.scalar(
            text("""
        with RECURSIVE rt as (
            select 1 as level, * from ketorelationtuples
            where namespace=:namespace
            and object=:object
            and relation=:relation
            union all
            select rt.level+1 as level, ketorelationtuples.* from rt, ketorelationtuples
            where ketorelationtuples.namespace = rt.subject_set_namespace
            and ketorelationtuples.object = rt.subject_set_object
            and ketorelationtuples.relation = rt.subject_set_relation
        )
        select count(*) as count from rt
        where level < :level
            and (subject_id =:subject_id
            or (
                subject_set_namespace=:subject_set_namespace
                and subject_set_object =:subject_set_object
                and subject_set_relation =:subject_set_relation
            )
        )
        """).bindparams(namespace=expand_query.namespace,
                        object=expand_query.object,
                        relation=expand_query.relation,
                        subject_id=getattr(requested, 'id', None),
                        subject_set_namespace=getattr(requested, 'namespace', None),
                        subject_set_object=getattr(requested, 'object', None),
                        subject_set_relation=getattr(requested, 'relation', None),
                        level=rest_depth)
        )
        return cnt > 0


class ExpandEngine(GraphMixin):
    async def build_tree(self, subject: definitions.Subject, rest_depth) -> t.Optional[definitions.Tree]:
        global_max_depth = getattr(settings, 'KETO_MAX_INDIRECTION_DEPTH', 32)
        if rest_depth <= 0 or rest_depth > global_max_depth:
            rest_depth = global_max_depth
        is_user_set = isinstance(subject, definitions.SubjectSet)
        if is_user_set:
            was_already_visited = self.check_and_add_visited(subject.unique_id())
            if was_already_visited:
                return
            subTree = definitions.Tree(
                type=definitions.ExpandNodeType.ExpandNodeUnion.value,
                subject=subject
            )
            query = select(KetoRelationTuples).where(
                KetoRelationTuples.relation == subject.relation,
                KetoRelationTuples.namespace == subject.namespace,
                KetoRelationTuples.object == subject.object
            )
            rels: t.List[KetoRelationTuples] = await self.session.execute(query)
            if len(rels) == 0:
                return
            rels: t.List[definitions.RelationTuple] = [i.to_relation_tuple() for i in rels]
            if rest_depth <= 1:
                subTree.type = definitions.ExpandNodeType.ExpandNodeLeaf.value
                return subTree
            children = []
            for r in rels:
                child = self.build_tree(r.subject, rest_depth - 1)
                if child is None:
                    child = definitions.Tree(
                        type=definitions.ExpandNodeType.ExpandNodeLeaf.value,
                        subject=r.subject
                    )
                children.append(child)
            subTree.children = children
            return subTree


class ExpandEngineCTE(ExpandEngine):
    async def build_tree(self, subject: definitions.Subject, rest_depth) -> t.Optional[definitions.Tree]:
        global_max_depth = getattr(settings, 'KETO_MAX_INDIRECTION_DEPTH', 32)
        if rest_depth <= 0 or rest_depth > global_max_depth:
            rest_depth = global_max_depth
        is_user_set = isinstance(subject, definitions.SubjectSet)
        if is_user_set:
            was_already_visited = self.check_and_add_visited(subject.unique_id())
            if was_already_visited:
                return

            rels = await self.session.scalars(text("""
            with RECURSIVE rt as (
                select 1 as level, * from ketorelationtuples
                where namespace=:namespace
                and object=:object
                and relation=:relation
                union all
                select rt.level+1 as level, ketorelationtuples.* from rt, ketorelationtuples
                where ketorelationtuples.namespace = rt.subject_set_namespace
                and ketorelationtuples.object = rt.subject_set_object
                and ketorelationtuples.relation = rt.subject_set_relation
            )
            select * from ketorelationtuples where id in (
                select distinct id from rt
                where level < :level
            )
            """).bindparams(
                namespace=subject.namespace,
                object=subject.object,
                relation=subject.relation,
                level=rest_depth
            ))

            subTree = definitions.Tree(
                type=definitions.ExpandNodeType.ExpandNodeUnion.value,
                subject=subject
            )
            rels = await self.session.scalars(
                select(KetoRelationTuples).where(KetoRelationTuples.id.in_(rels.all()))
            )
            subTree.children.extend(self.build_children(subTree.subject, rels.all()))
            return subTree

    def build_children(self, subject: definitions.SubjectSet, relation_tuple_list: t.List[KetoRelationTuples]) -> t.List[definitions.Tree]:
        rels = []
        if isinstance(subject, definitions.SubjectSet):
            for instance in relation_tuple_list[:]:
                if instance.object == subject.object \
                        and instance.namespace == subject.namespace \
                        and instance.relation == subject.relation:
                    relation_tuple_list.remove(instance)
                    relation_tuple = instance.to_relation_tuple()
                    if isinstance(relation_tuple.subject, definitions.SubjectSet):
                        subTree = definitions.Tree(
                            type=definitions.ExpandNodeType.ExpandNodeUnion.value,
                            subject=relation_tuple.subject,
                        )
                        subTree.children.extend(self.build_children(subTree.subject, relation_tuple_list))
                        if len(subTree.children) == 0:
                            subTree.type = definitions.ExpandNodeType.ExpandNodeLeaf.value
                    else:
                        subTree = definitions.Tree(
                            type=definitions.ExpandNodeType.ExpandNodeLeaf.value,
                            subject=relation_tuple.subject
                        )
                    rels.append(subTree)
        return rels


class PermissionEngine(GraphMixin):
    """默认是基于域的rbac权限系统，可以带域查询"""

    async def build_tree(self, namespace, domain, subject: definitions.Subject, rest_depth) -> t.Optional[definitions.Tree]:
        global_max_depth = getattr(settings, 'KETO_MAX_INDIRECTION_DEPTH', 32)
        if rest_depth <= 0 or rest_depth > global_max_depth:
            rest_depth = global_max_depth
        is_user_set = isinstance(subject, definitions.SubjectSet)
        was_already_visited = self.check_and_add_visited(subject.unique_id())
        if was_already_visited:
            return
        if is_user_set:
            subTree = definitions.Tree(
                type=definitions.ExpandNodeType.ExpandNodeUnion.value,
                namespace=subject.namespace,
                relation=subject.relation,
                object=subject.object
            )
            query = select(KetoRelationTuples).where(
                KetoRelationTuples.subject_set_namespace == subject.namespace,
                KetoRelationTuples.subject_set_object == subject.object,
                KetoRelationTuples.subject_set_relation == subject.relation,
            )
            if domain:
                query = query.where(KetoRelationTuples.object.startswith(domain))
            rels = await self.session.scalars(query)
        else:
            # user id
            subTree = definitions.Tree(
                type=definitions.ExpandNodeType.ExpandNodeUnion.value,
                subject_id=subject.id,
            )
            # TODO: implement

            query = select(KetoRelationTuples).where(
                KetoRelationTuples.namespace == namespace,
                KetoRelationTuples.subject_id == subject.id,
            )
            if domain:
                query = query.where(KetoRelationTuples.object.startswith(domain))
            rels = await self.session.scalars(query)
        rels: t.List[KetoRelationTuples] = rels.all()
        if len(rels) == 0:
            return
        rels: t.List[definitions.RelationTuple] = [i.to_relation_tuple() for i in rels]
        if rest_depth <= 1:
            subTree.type = definitions.ExpandNodeType.ExpandNodeLeaf.value
            return subTree
        children = []
        for r in rels:
            subject = definitions.SubjectSet(
                object=r.object,
                relation=r.relation,
                namespace=r.namespace
            )
            child = await self.build_tree(r.namespace, domain, subject, rest_depth - 1)
            if child is None:
                child = definitions.Tree(
                    type=definitions.ExpandNodeType.ExpandNodeLeaf.value,
                    object=r.object,
                    relation=r.relation,
                    namespace=r.namespace
                )
            children.append(child)
        subTree.children = children
        return subTree


class PermissionEngineCTE(PermissionEngine):
    pass


if getattr(settings, 'KETO_USING_CTE', True):
    CheckEngine = CheckEngineCTE
    ExpandEngine = ExpandEngineCTE
