import asyncio
import inspect
import typing as t
from functools import wraps
from typing import Any, Callable

import fastapi.params
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import select, Select

from fastapi_rf.dependency import get_db
from fastapi_rf.serializers import AllOptional


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
            func.url = '/' + func.url
        if not func.url.endswith('/'):
            func.url += '/'
        func.method = self.method
        func.detail = self.detail
        func.kwargs = self.kwargs
        return func


class ViewSetMetaClass(type):
    def __new__(cls, name, bases, attrs, ignores=None):
        if ignores is None:
            ignores = []
        for base in bases:
            base_ignores = getattr(base, '_ignores', [])
            for i in base_ignores:
                if i not in ignores:
                    ignores.append(i)
        old_init: Callable[..., Any] = attrs.get("__init__", lambda self: None)
        old_signature = inspect.signature(old_init)
        old_parameters = list(old_signature.parameters.values())[
                         1:]  # drop `self` parameter
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
            # 私有变量不做处理
            if _name.startswith("_") or _name in ignores:
                continue
            dependencies.setdefault(_name, {})
            dependencies[_name]['hint'] = hint

        for _name, info in dependencies.items():
            parameter_kwargs = {"default": info.get('default')}
            new_parameters.append(
                inspect.Parameter(name=_name, kind=inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=info.get('hint'),
                                  **parameter_kwargs)
            )
        new_signature = old_signature.replace(parameters=new_parameters)

        def new_init(self: Any, *args: Any, **kwargs: Any) -> None:
            for dep_name in dependencies.keys():
                dep_value = kwargs.pop(dep_name, None)
                if dep_value is not None:
                    setattr(self, dep_name, dep_value)
            old_init(self, *args, **kwargs)

        new_cls = type.__new__(cls, name, bases, attrs)
        setattr(new_cls, "__signature__", new_signature)
        setattr(new_cls, "__init__", new_init)
        setattr(new_cls, '_dependencies', dependencies)
        setattr(new_cls, '_ignores', ignores)
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


def wrap_func(func):
    @wraps(func)
    async def new_func(*args, **kwargs):
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        return func(*args, **kwargs)

    return new_func


def add_dependency_to_self(name, func, default=inspect.Parameter.empty, annotation=inspect.Parameter.empty, ):
    old_signature = inspect.signature(func)
    old_parameters: list[inspect.Parameter] = list(
        old_signature.parameters.values())
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
    new_signature = old_signature.replace(
        parameters=new_parameters, return_annotation=old_signature.return_annotation)
    setattr(new_func, "__signature__", new_signature)
    return new_func


class BaseViewSet(t.Generic[T, R, W], metaclass=ViewSetMetaClass, ignores=['pk_field', 'pk_type']):
    if t.TYPE_CHECKING:
        _dependencies: dict = {}
    pk_field = 'id'
    pk_type = int

    @classmethod
    def discover_endpoint(cls):
        for func_name, func in inspect.getmembers(cls, inspect.isfunction):
            if getattr(func, 'is_endpoint', False):
                yield func_name, cls.update_endpoint_signature(wrap_func(func))

    @classmethod
    def update_endpoint_signature(cls, func):
        old_signature = inspect.signature(func)
        old_parameters: list[inspect.Parameter] = list(
            old_signature.parameters.values())
        old_first_parameter = old_parameters[0]
        new_first_parameter = old_first_parameter.replace(
            default=Depends(cls), kind=inspect.Parameter.POSITIONAL_ONLY)

        new_parameters = [new_first_parameter] + [
            parameter.replace(
                kind=inspect.Parameter.KEYWORD_ONLY,
                default=parameter.default if parameter.default != inspect.Parameter.empty else None
            ) for parameter in old_parameters[1:]
        ]
        new_signature = old_signature.replace(parameters=new_parameters)
        setattr(func, "__signature__", new_signature)
        if getattr(func, 'detail', False):
            func = add_dependency_to_self(
                cls.pk_field, func, annotation=cls.pk_type, )
        return func

    @classmethod
    def register(cls, router: APIRouter, path):
        for _, func in cls.discover_endpoint():
            if func.detail:
                getattr(router, func.method)(
                    f"/{path}/{{{cls.pk_field}}}{func.url}")(func)
            else:
                getattr(router, func.method)(f"/{path}{func.url}")(func)


class register:
    def __init__(self, router, path) -> None:
        self.router = router
        self.path = path

    def __call__(self, cls: t.Type[BaseViewSet]) -> Any:
        cls.register(self.router, self.path)
        return cls


class GenericViewSet(BaseViewSet, ignores=['serializer_read', 'serializer_write', 'model']):
    model: T
    db: AsyncSession = Depends(get_db)
    serializer_read: R
    serializer_write: W
    order_by: int = 'id'
    if t.TYPE_CHECKING:
        id: t.Any

    async def get_queryset(self) -> Select:
        return select(self.model).order_by(text(self.order_by))

    async def get_object(self, *options) -> T:
        ret = await self.db.scalar(
            (await self.get_queryset()).filter_by(**{
                self.pk_field: getattr(self, self.pk_field)
            }).options(*options)
        )
        if ret is None:
            raise HTTPException(
                400,
                f"can not find object {self.model} {getattr(self, self.pk_field)}"
            )
        return ret

    @classmethod
    def update_endpoint_signature(cls, func):
        func = super().update_endpoint_signature(func)
        old_signature = inspect.signature(func)
        old_parameters: list[inspect.Parameter] = list(
            old_signature.parameters.values())
        new_parameters = []

        def trans_annotation(annotation, partial=False):
            if annotation == T:
                annotation = cls.model
            elif annotation == R:
                annotation = cls.serializer_read
            elif annotation == W:
                if partial:
                    annotation = AllOptional(f'Optional{cls.serializer_write.__name__}', (cls.serializer_write,), {})
                else:
                    annotation = cls.serializer_write
            elif t.get_origin(annotation) is list:
                annotation = list[trans_annotation(t.get_args(annotation)[0])]
            else:
                annotation = annotation
            return annotation

        partial = func.__name__ == 'partial_update'
        for param in old_parameters:
            annotation = trans_annotation(param.annotation, partial=partial)
            new_parameters.append(
                param.replace(annotation=annotation)
            )
        return_annotation = old_signature.return_annotation
        if return_annotation == T:
            return_annotation = cls.model
        elif return_annotation == R:
            return_annotation = cls.serializer_read
        new_signature = old_signature.replace(
            parameters=new_parameters, return_annotation=return_annotation)
        setattr(func, "__signature__", new_signature)
        return func
