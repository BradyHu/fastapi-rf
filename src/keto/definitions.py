from dataclasses import dataclass, field
import typing as t
from enum import Enum


@dataclass
class Subject:
    def unique_id(self):
        raise NotImplementedError

    def __eq__(self, other):
        raise NotImplementedError


@dataclass
class SubjectID(Subject):
    id: str

    def unique_id(self):
        return self.id

    def __eq__(self, other):
        if type(other) != SubjectID:
            return False
        return self.id == other.id


@dataclass
class SubjectSet:
    namespace: str
    object: str
    relation: str

    def unique_id(self):
        return f'{self.namespace}{self.object}{self.relation}'

    def __eq__(self, other):
        if type(other) != SubjectSet:
            return False
        return self.namespace == other.namespace and self.object == other.object and self.relation == other.relation


@dataclass
class RelationQuery:
    namespace: str
    object: str
    relation: str
    subject: Subject


@dataclass
class RelationTuple:
    namespace: str
    object: str
    relation: str
    subject: Subject = None


class ExpandNodeType(str, Enum):
    ExpandNodeUnion = 'union'
    ExpandNodeExclusion = 'exclusion'
    ExpandNodeIntersection = 'intersection'
    ExpandNodeLeaf = 'leaf'
    ExpandNodeUnspecified = 'unspecified'


@dataclass
class Tree:
    type: str
    subject: Subject = None
    namespace: str = None
    object: str = None
    relation: str = None
    subject_id: str = None
    children: t.List['Tree'] = field(default_factory=list)
