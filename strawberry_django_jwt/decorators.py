from calendar import timegm
from datetime import datetime
from functools import wraps
import inspect

from django.middleware.csrf import rotate_token
from django.utils.translation import gettext as _
from strawberry.types import Info

from strawberry_django_jwt import exceptions
from strawberry_django_jwt.settings import jwt_settings
from strawberry_django_jwt.utils import (
    delete_cookie,
    get_context,
    maybe_thenable,
    set_cookie,
)

__all__ = [
    "refresh_expiration",
    "csrf_rotation",
    "setup_jwt_cookie",
    "jwt_cookie",
    "ensure_token",
]


def refresh_expiration(f):
    @wraps(f)
    def wrapper(cls, *args, **kwargs):
        def on_resolve(payload):
            if jwt_settings.JWT_ALLOW_REFRESH:
                payload.refresh_expires_in = timegm(datetime.utcnow().utctimetuple()) + jwt_settings.JWT_REFRESH_EXPIRATION_DELTA.total_seconds()
            return payload

        result = f(cls, *args, **kwargs)
        return maybe_thenable(result, on_resolve)

    return wrapper


def csrf_rotation(f):
    @wraps(f)
    def wrapper(cls, info: Info, *args, **kwargs):
        if jwt_settings.JWT_CSRF_ROTATION:
            rotate_token(info.context)
        return f(cls, info, **kwargs)

    return wrapper


def setup_jwt_cookie(f):
    async def set_token(ctx, result):
        res = await result
        ctx.jwt_token = res.token
        return res

    @wraps(f)
    def wrapper(cls, info: Info, *args, **kwargs):
        result = f(cls, info, **kwargs)
        ctx = get_context(info)
        if getattr(ctx, "jwt_cookie", False):
            if inspect.isawaitable(result):
                return set_token(ctx, result)
            else:
                ctx.jwt_token = result.token
        return result

    return wrapper


def jwt_cookie(view_func):
    async def finish_response(request, response):
        res = await response
        return finish_response_sync(request, res)

    def finish_response_sync(request, response):
        if hasattr(request, "jwt_token"):
            expires = datetime.utcnow() + jwt_settings.JWT_EXPIRATION_DELTA

            set_cookie(
                response,
                jwt_settings.JWT_COOKIE_NAME,
                request.jwt_token,
                expires=expires,
            )
            if hasattr(request, "jwt_refresh_token"):
                refresh_token = request.jwt_refresh_token
                expires = refresh_token.created + jwt_settings.JWT_REFRESH_EXPIRATION_DELTA

                set_cookie(
                    response,
                    jwt_settings.JWT_REFRESH_TOKEN_COOKIE_NAME,
                    refresh_token.token,
                    expires=expires,
                )

        if hasattr(request, "delete_jwt_cookie"):
            delete_cookie(response, jwt_settings.JWT_COOKIE_NAME)

        if hasattr(request, "delete_refresh_token_cookie"):
            delete_cookie(response, jwt_settings.JWT_REFRESH_TOKEN_COOKIE_NAME)

        return response

    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        request.jwt_cookie = True
        response = view_func(request, *args, **kwargs)

        if inspect.isawaitable(response):
            return finish_response(request, response)

        return finish_response_sync(request, response)

    return wrapped_view


def ensure_token(f):
    @wraps(f)
    def wrapper(cls, info: Info, token=None, *args, **kwargs):
        if token is None:
            cookies = get_context(info).COOKIES
            token = cookies.get(jwt_settings.JWT_COOKIE_NAME)

            if token is None:
                raise exceptions.JSONWebTokenError(_("Token is required"))
        return f(cls, info, token, *args, **kwargs)

    return wrapper
