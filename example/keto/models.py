from sqlalchemy import Column, Integer, String


from . import definitions
from fastapi_rf.models import CoreModel, Base


class KetoRelationTuples(CoreModel, Base):

    id = Column(Integer(), primary_key=True, index=True)
    namespace = Column(String(length=255))
    object = Column(String(length=255))
    relation = Column(String(length=64))
    subject_id = Column(String(length=255), nullable=True)
    subject_set_namespace = Column(String(length=255), nullable=True)
    subject_set_object = Column(String(length=255), nullable=True)
    subject_set_relation = Column(String(length=255), nullable=True)

    def to_relation_tuple(self) -> definitions.RelationTuple:
        if self.subject_id:
            subject = definitions.SubjectID(id=self.subject_id)
        else:
            subject = definitions.SubjectSet(
                namespace=self.subject_set_namespace,
                object=self.subject_set_object,
                relation=self.subject_set_relation
            )
        relation_tuple = definitions.RelationTuple(
            namespace=self.namespace,
            object=self.object,
            relation=self.relation,
            subject=subject
        )
        return relation_tuple
