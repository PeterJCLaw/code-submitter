import json
import importlib
from typing import cast, Type, Mapping, TypeVar
from typing_extensions import TypedDict

from starlette.config import Config
from starlette.authentication import AuthenticationBackend

T = TypeVar('T')


def load_class(name: str, type_: Type[T]) -> Type[T]:
    module_name, _, class_name = name.rpartition('.')
    module = importlib.import_module(module_name)
    cls = getattr(module, class_name)
    if not issubclass(cls, type_):
        raise ValueError("Invalid class at {!r} was {!r} not a {!r}".format(
            name,
            cls,
            type_,
        ))
    return cast(Type[T], cls)


AuthConfig = TypedDict('AuthConfig', {
    'backend': Type[AuthenticationBackend],
    'kwargs': Mapping[str, object],
})


def load_auth_backend(raw: str) -> AuthConfig:
    data = json.loads(raw)
    return AuthConfig({
        'backend': load_class(data['backend'], AuthenticationBackend),
        'kwargs': data.get('kwargs', {}),
    })


def get_auth_backend() -> AuthenticationBackend:
    backend = AUTH_BACKEND['backend']
    return backend(**AUTH_BACKEND['kwargs'])  # type: ignore[call-arg]


config = Config('.env')

DATABASE_URL: str = config('DATABASE_URL', default='sqlite:///sqlite.db')
TESTING: bool = config('TESTING', cast=bool, default=False)

AUTH_BACKEND: AuthConfig = config(
    'AUTH_BACKEND',
    load_auth_backend,
    json.dumps({'backend': 'code_submitter.auth.DummyBackend'}),
)
