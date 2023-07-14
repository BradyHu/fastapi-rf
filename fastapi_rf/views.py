from fastapi_rf.pagination import BasePagination
import inspect
import typing as t
from functools import wraps
from typing import Any, Callable

import fastapi.params
from fastapi import APIRouter, HTTPException, Response, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import select, Select

from fastapi_rf.dependency import get_db


class action:
    # class decorator
    def __init__(self, method='get', url="", detail=True, **kwargs) -> None:
        self.method = method
        self.url = url
        self.kwargs = kwargs
        self.detail = detail

    def __call__(self, func) -> Any:
        func.is_endpoint = True
        func.url = self.url or func.__name__
        if not func.url.startswith('/'):
            func.url = '/'+func.url
        if not func.url.endswith('/'):
            func.url += '/'
        func.method = self.method
        func.kwargs = self.kwargs
        return func


class ViewSetMetaClass(type):
    def __new__(cls, name, bases, attrs):
        old_init: Callable[..., Any] = attrs.get("__init__", lambda self: None)
        old_signature = inspect.signature(old_init)
        old_parameters = list(old_signature.parameters.values())[1:]  # drop `self` parameter
        new_parameters = [
            x for x in old_parameters if x.kind not in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
        ]
        dependencies = {}
        for base in bases:
            base_dependencies = getattr(base, '_dependencies', None)
            if base_dependencies:
                dependencies.update(base_dependencies)

        # dependencies
        for _name, default in attrs.items():
            if isinstance(default, fastapi.params.Depends):
                dependencies.setdefault(_name, {})
                dependencies[_name]['default'] = default
        # other annotate
        for _name, hint in attrs.get("__annotations__", {}).items():
            # 不在全局引入主键
            if _name in ['pk_field', 'pk_type'] or _name.startswith("_"):
                continue
            dependencies.setdefault(_name, {})
            dependencies[_name]['hint'] = hint

        for _name, info in dependencies.items():
            parameter_kwargs = {"default": info.get('default')}
            new_parameters.append(
                inspect.Parameter(name=_name, kind=inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=info.get('hint'), **parameter_kwargs)
            )
        new_signature = old_signature.replace(parameters=new_parameters)

        def new_init(self: Any, *args: Any, **kwargs: Any) -> None:
            for dep_name in dependencies.keys():
                dep_value = kwargs.pop(dep_name, None)
                if dep_value:
                    setattr(self, dep_name, dep_value)
            old_init(self, *args, **kwargs)
        new_cls = type.__new__(cls, name, bases, attrs)
        setattr(new_cls, "__signature__", new_signature)
        setattr(new_cls, "__init__", new_init)
        setattr(new_cls, '_dependencies', dependencies)
        return new_cls

    def __getattribute__(self, __name: str) -> Any:
        if __name.startswith('_'):
            return super().__getattribute__(__name)
        ret = super().__getattribute__(__name)
        if ret is None:
            ret = getattr(self, "_dependencies", {}).get(__name, None)
        return ret


T = t.TypeVar("T")
R = t.TypeVar("R")
W = t.TypeVar("W")


def add_dependency_to_self(name, func, default=inspect._empty, annotation=inspect._empty, ):
    old_signature = inspect.signature(func)
    old_parameters: list[inspect.Parameter] = list(old_signature.parameters.values())
    first_parameter = old_parameters[0]

    @wraps(func)
    async def new_func(self, *args, **kwargs):
        setattr(self, name, kwargs.pop(name, None))
        return await func(self, *args, **kwargs)
    new_parameters = [first_parameter, inspect.Parameter(
        name=name,
        kind=inspect.Parameter.KEYWORD_ONLY,
        default=default,
        annotation=annotation
    )] + old_parameters[1:]
    new_signature = old_signature.replace(parameters=new_parameters, return_annotation=old_signature.return_annotation)
    setattr(new_func, "__signature__", new_signature)
    return new_func


class BaseViewSet(t.Generic[T, R, W], metaclass=ViewSetMetaClass):
    if t.TYPE_CHECKING:
        _dependencies: dict = {}
    pk_field = 'id'
    pk_type = int

    @classmethod
    def discover_endpoint(cls):
        for func_name, func in inspect.getmembers(cls, inspect.isfunction):
            if getattr(func, 'is_endpoint', False):
                yield func_name, cls.update_endpoint_signature(func)

    @classmethod
    def update_endpoint_signature(cls, func):
        old_signature = inspect.signature(func)
        old_parameters: list[inspect.Parameter] = list(old_signature.parameters.values())
        old_first_parameter = old_parameters[0]
        new_first_parameter = old_first_parameter.replace(default=Depends(cls), kind=inspect.Parameter.POSITIONAL_ONLY)
        if func.__name__ in ['retrieve', 'update', 'partial_update', 'destroy']:
            func.detail = True
        elif func.__name__ in ['list', "create"]:
            func.detail = False

        new_parameters = [new_first_parameter] + [
            parameter.replace(
                kind=inspect.Parameter.KEYWORD_ONLY,
                default=parameter.default if parameter.default != inspect._empty else None
            ) for parameter in old_parameters[1:]
        ]
        new_signature = old_signature.replace(parameters=new_parameters)
        setattr(func, "__signature__", new_signature)
        if getattr(func, 'detail', False):
            func = add_dependency_to_self(cls.pk_field, func, annotation=cls.pk_type, )
        return func

    @classmethod
    def register(cls, router: APIRouter, path):
        for _, func in cls.discover_endpoint():
            getattr(router, func.method)(f"/{path}{func.url}")(func)


class register:
    def __init__(self, router, path) -> None:
        self.router = router
        self.path = path

    def __call__(self, cls: t.Type[BaseViewSet]) -> Any:
        cls.register(self.router, self.path)
        return cls


class AuthorizationMixin(BaseViewSet):
    _authorization_classes = []

    @classmethod
    def update_endpoint_signature(cls, func):
        func = super().update_endpoint_signature(func)

        def get_user(*args, **kwargs):
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
            for backend in cls._authorization_classes
        ]
        new_signature = old_signature.replace(parameters=params)
        setattr(get_user, '__signature__', new_signature)
        new_func = add_dependency_to_self('user', func, default=Depends(get_user))
        return new_func


class GenericViewSet(
        AuthorizationMixin,
        BaseViewSet):
    _model: T
    db: AsyncSession = Depends(get_db)
    _serializer_read: R
    _serializer_write: W

    def get_queryset(self) -> Select:
        return select(self._model)

    async def get_object(self) -> T:
        ret = await self.db.scalar(
            self.get_queryset().filter_by(**{
                self.pk_field: self.id
            })
        )
        if ret is None:
            raise HTTPException(
                400,
                f"can not find object {self.model} {self.id}"
            )
        return ret

    @classmethod
    def update_endpoint_signature(cls, func):
        func = super().update_endpoint_signature(func)
        old_signature = inspect.signature(func)
        old_parameters: list[inspect.Parameter] = list(old_signature.parameters.values())
        new_parameters = []
        for param in old_parameters:
            if param.annotation == T:
                annotation = cls._model
            elif param.annotation == R:
                annotation = cls._serializer_read
            elif param.annotation == W:
                annotation = cls._serializer_write
            else:
                annotation = param.annotation
            new_parameters.append(
                param.replace(annotation=annotation)
            )
        return_annotation = old_signature.return_annotation
        if return_annotation == T:
            return_annotation = cls._model
        elif return_annotation == R:
            return_annotation = cls._serializer_read
        new_signature = old_signature.replace(parameters=new_parameters, return_annotation=return_annotation)
        setattr(func, "__signature__", new_signature)
        return func


class PaginationMixin(BaseViewSet):
    _pagination_class: t.Type[BasePagination] | None = None

    @classmethod
    def update_endpoint_signature(cls, func):
        func = super().update_endpoint_signature(func)
        if cls._pagination_class is None:
            if func.__name__ == 'list':
                old_signature = inspect.signature(func)
                return_annotation = list[getattr(cls, 'serializer_read', dict)]
                new_signature = old_signature.replace(return_annotation=return_annotation)
                setattr(func, "__signature__", new_signature)
            return func

        if func.__name__ != 'list':
            # remove_dependency_from_self('pagination_class', func)
            return func
        # 处理翻页涉及的list endpoint
        old_signature = inspect.signature(func)
        return_annotation = cls._pagination_class.get_paginated_return_type(getattr(cls, '_serializer_read', dict))
        new_signature = old_signature.replace(return_annotation=return_annotation)
        setattr(func, "__signature__", new_signature)
        new_func = add_dependency_to_self('_pagination_class', func, default=Depends(cls._pagination_class), )
        return new_func


class ListMixin(PaginationMixin, GenericViewSet):
    async def list(self):
        if self._pagination_class:
            return await self._pagination_class.paginate(select(self._model))
        ret = await self.db.scalars(
            select(self._model)
        )
        return ret.all()

    @classmethod
    def discover_endpoint(cls):
        cls.list = action('get', '/', detail=False)(cls.list)
        return super().discover_endpoint()


class CreateMixin(GenericViewSet):
    async def create(self, body: W) -> R:
        query = select(self.model).filter_by(**body.dict())
        if await self.db.scalar(query):
            raise HTTPException(
                400,
                "record already exists"
            )
        instance = self.model(**body.dict())
        self.db.add(instance)
        await self.db.flush()
        return instance

    @classmethod
    def discover_endpoint(cls):
        cls.create = action('post', '/', detail=False)(cls.create)
        return super().discover_endpoint()


class RetrieveMixin(GenericViewSet):
    async def retrieve(self) -> R:
        return await self.get_object()

    @classmethod
    def discover_endpoint(cls):
        cls.retrieve = action('get', f"/{{{cls.pk_field}}}/")(cls.retrieve)
        return super().discover_endpoint()


class UpdateMixin(GenericViewSet):
    async def update(self, body: W) -> R:
        instance = await self.get_object()
        for k, v in body.dict().items():
            setattr(instance, k, v)
        await self.db.flush()
        return instance

    @classmethod
    def discover_endpoint(cls):
        cls.update = action('put', f"/{{{cls.pk_field}}}/")(cls.update)
        return super().discover_endpoint()


class DestroyMixin(GenericViewSet):
    async def destroy(self):
        instance = await self.get_object()
        await self.db.delete(instance)
        return Response(status_code=204)

    @classmethod
    def discover_endpoint(cls):
        cls.destroy = action('delete', f"/{{{cls.pk_field}}}/")(cls.destroy)
        return super().discover_endpoint()


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
