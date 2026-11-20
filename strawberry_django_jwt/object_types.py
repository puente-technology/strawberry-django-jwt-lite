from typing import Any, TypeVar

from django.contrib.auth import get_user_model
import strawberry

from strawberry_django_jwt.settings import jwt_settings

X = TypeVar("X", Any, Any)


def inject_fields(fields: dict[str, tuple[type[X], X]]):
    def inject(cls):
        for field, data in fields.items():
            setattr(cls, field, data[1])
            cls.__annotations__[field] = data[0]
        return cls

    return inject


@strawberry.type
@inject_fields(
    {
        **{get_user_model().USERNAME_FIELD: (str, "")},
        **({"origIat": (int, 0)} if jwt_settings.JWT_ALLOW_REFRESH else {}),
        **({"aud": (str, "")} if jwt_settings.JWT_AUDIENCE else {}),
        **({"iss": (str, "")} if jwt_settings.JWT_ISSUER else {}),
    }
)
class TokenPayloadType:
    exp: int = 0
    origIat: int = 0


@strawberry.type
class PayloadType:
    payload: TokenPayloadType
