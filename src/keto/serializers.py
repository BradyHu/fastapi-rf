from __future__ import annotations
from core.serializers import BaseSchemaModel
from pydantic import constr


class KetoRelationTuplesBase(BaseSchemaModel):
    namespace: constr(max_length=255)
    object: constr(max_length=255)
    relation: constr(max_length=255)
    subject_id: constr(max_length=255) | None
    subject_set_namespace:  constr(max_length=255) | None
    subject_set_object:  constr(max_length=255) | None
    subject_set_relation:  constr(max_length=255) | None


class KetoRelationTuplesRead(KetoRelationTuplesBase):
    id: int | None


class KetoRelationTuplesWrite(KetoRelationTuplesBase):
    pass


class Subject(BaseSchemaModel):
    id: str | None = None
    namespace: str | None = None
    object: str | None = None
    relation: str | None = None


class Tree(BaseSchemaModel):
    type: str
    subject: Subject | None = None
    namespace: str | None = None
    object: str | None = None
    relation: str | None = None
    subject_id: str | None = None
    children: list[Tree] = []
