from fastapi_rf.core import GenericViewSet
from fastapi_rf.mixin import ListMixin, CreateMixin, RetrieveMixin, UpdateMixin, DestroyMixin, PartialUpdateMixin
from fastapi_rf.mixin import BatchCreateMixin, BatchDestroyMixin


class ViewSet(
    ListMixin,
    CreateMixin,
    RetrieveMixin,
    UpdateMixin,
    PartialUpdateMixin,
    DestroyMixin,
    BatchCreateMixin,
    BatchDestroyMixin,
    GenericViewSet
):
    pass


class ReadOnlyViewSet(
    ListMixin,
    RetrieveMixin,
    GenericViewSet
):
    pass
