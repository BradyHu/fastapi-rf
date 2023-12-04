import inspect
import typing as t
from functools import wraps

from fastapi import HTTPException

from fastapi_rf.core import BaseViewSet, add_dependency_to_self
from .permission import BasePermission


class PermissionMixin(BaseViewSet, ignores=['permission_classes']):
    permission_classes: list[t.Type[BasePermission]] = []

    @classmethod
    def update_endpoint_signature(cls, func):
        func = super().update_endpoint_signature(func)

        @wraps(func)
        def check_permission(self, *args, **kwargs):
            for backend in self.permission_classes:
                if not backend().has_permission(self):
                    raise HTTPException(403, '暂无权限')
            return func(self, *args, **kwargs)

        return check_permission
