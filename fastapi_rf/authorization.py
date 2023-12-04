import inspect
import typing as t

from fastapi import Depends

from fastapi_rf.core import BaseViewSet, add_dependency_to_self


class AuthorizationMixin(BaseViewSet, ignores=['authorization_classes']):
    authorization_classes = []
    if t.TYPE_CHECKING:
        user: t.Any = None

    @classmethod
    def update_endpoint_signature(cls, func):
        func = super().update_endpoint_signature(func)

        def get_user(**kwargs):
            for user_ret in kwargs.values():
                if user_ret:
                    return user_ret

        old_signature = inspect.signature(get_user)
        params = [
            inspect.Parameter(
                name=backend.__name__,
                kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
                default=Depends(backend())
            )
            for backend in cls.authorization_classes
        ]
        new_signature = old_signature.replace(parameters=params)
        setattr(get_user, '__signature__', new_signature)
        new_func = add_dependency_to_self('user', func, default=Depends(get_user))
        return new_func

class BaseAuthorization:
    async def __call__(self, *args, **kwargs):
        raise NotImplementedError

