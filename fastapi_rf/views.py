from fastapi_rf.core import GenericViewSet
from fastapi_rf.mixin import ListMixin, CreateMixin, RetrieveMixin, UpdateMixin, DestroyMixin


class ViewSet(
    ListMixin,
    CreateMixin,
    RetrieveMixin,
    UpdateMixin,
    DestroyMixin,
    GenericViewSet
):
    pass


class ReadOnlyViewSet(
    ListMixin,
    RetrieveMixin,
    GenericViewSet
):
    pass
