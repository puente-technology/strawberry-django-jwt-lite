import inspect
from typing import Any

from django.utils.translation import gettext as _
import strawberry
from strawberry.types import Info
from strawberry.types.field import StrawberryField

from strawberry_django_jwt import exceptions, settings
from strawberry_django_jwt.decorators import (
    csrf_rotation,
    refresh_expiration,
    setup_jwt_cookie,
)
from strawberry_django_jwt.refresh_token import signals as refresh_signals
from strawberry_django_jwt.refresh_token.decorators import ensure_refresh_token
from strawberry_django_jwt.refresh_token.object_types import RefreshedTokenType
from strawberry_django_jwt.refresh_token.shortcuts import (
    create_refresh_token,
    get_refresh_token,
    refresh_token_lazy,
)
from strawberry_django_jwt.utils import (
    create_strawberry_argument,
    get_context,
)


class BaseJSONWebTokenMixin:
    @staticmethod
    def init_fields(cls, field_options: dict[str, dict[str, Any]]):
        if not settings.jwt_settings.JWT_HIDE_TOKEN_FIELDS:
            for __, field in inspect.getmembers(cls, lambda f: isinstance(f, StrawberryField)):
                field.arguments.append(create_strawberry_argument("token", "token", str, **field_options.get("token", {})))
                if settings.jwt_settings.JWT_LONG_RUNNING_REFRESH_TOKEN:
                    field.arguments.append(create_strawberry_argument("refresh_token", "refreshToken", str, **field_options.get("refresh_token", {})))


class JSONWebTokenMixin(BaseJSONWebTokenMixin):
    def __init_subclass__(cls, **kwargs):
        cls.init_fields(
            cls,
            {"token": {"is_optional": True}, "refresh_token": {"is_optional": True}},
        )


class RefreshTokenMixin(JSONWebTokenMixin):
    @staticmethod
    @setup_jwt_cookie
    @csrf_rotation
    @refresh_expiration
    @ensure_refresh_token
    def _refresh(self, info: Info, refresh_token: str | None) -> RefreshedTokenType:
        context = get_context(info)
        old_refresh_token = get_refresh_token(refresh_token, context)

        if old_refresh_token.is_expired(context):
            raise exceptions.JSONWebTokenError(_("Refresh token is expired"))

        payload = settings.jwt_settings.JWT_PAYLOAD_HANDLER(
            old_refresh_token.user,
            context,
        )
        token = settings.jwt_settings.JWT_ENCODE_HANDLER(payload, context)

        if hasattr(context, "jwt_cookie"):
            context.jwt_refresh_token = create_refresh_token(
                old_refresh_token.user,
                old_refresh_token,
            )
            new_refresh_token = context.jwt_refresh_token.get_token()
        else:
            new_refresh_token = refresh_token_lazy(
                old_refresh_token.user,
                old_refresh_token,
            )

        refresh_signals.refresh_token_rotated.send(
            sender=RefreshMixin,
            request=context,
            refresh_token=old_refresh_token,
            refresh_token_issued=new_refresh_token,
        )
        return RefreshedTokenType(payload=payload, token=token, refresh_token=new_refresh_token, refresh_expires_in=0)

    def refresh(self, info: Info, refresh_token: str | None = None) -> RefreshedTokenType:
        return RefreshTokenMixin._refresh(self, info=info, refresh_token=refresh_token)


class RefreshMixin(RefreshTokenMixin, JSONWebTokenMixin):
    """RefreshMixin"""

    refresh = strawberry.mutation(RefreshTokenMixin.refresh)
