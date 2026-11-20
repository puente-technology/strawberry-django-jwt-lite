from typing import Any, Optional, Set, cast

from django.contrib.auth import authenticate
from django.utils.translation import gettext as _
from graphql import GraphQLResolveInfo, GraphQLType
from strawberry.extensions import SchemaExtension
from strawberry.types import ExecutionContext

from strawberry_django_jwt import exceptions
from strawberry_django_jwt.settings import jwt_settings
from strawberry_django_jwt.utils import get_context, get_http_authorization

__all__ = [
    "allow_any",
    "JSONWebTokenMiddleware",
]


def allow_any(info, **kwargs):
    field = info.parent_type.fields.get(info.field_name)

    if field is None:
        return False

    field_type = getattr(field.type, "of_type", None)

    return field_type is not None and any(
        [issubclass(class_type, GraphQLType) and isinstance(field_type, class_type) for class_type in tuple(jwt_settings.JWT_ALLOW_ANY_CLASSES)]
    )


def _authenticate(request):
    is_anonymous = not hasattr(request, "user") or request.user.is_anonymous
    return is_anonymous and get_http_authorization(request) is not None


class BaseJSONWebTokenMiddleware(SchemaExtension):
    def __init__(self, *, execution_context: Optional[ExecutionContext] = None):
        super().__init__(execution_context=execution_context)
        self.cached_allow_any: Set[Any] = set()

    def authenticate_context(self, info: GraphQLResolveInfo, **kwargs):
        root_path = info.path[0]

        if root_path not in self.cached_allow_any:
            if jwt_settings.JWT_ALLOW_ANY_HANDLER(info, **kwargs):
                self.cached_allow_any.add(root_path)
            else:
                return True
        return False

    def resolve_base(self, info: GraphQLResolveInfo, **kwargs):
        context = get_context(info)

        if _authenticate(context) and self.authenticate_context(info, **kwargs):
            return context
        elif (
            info.field_name == "__schema"
            and cast(GraphQLResolveInfo, info).parent_type.name == "Query"
            and jwt_settings.JWT_AUTHENTICATE_INTROSPECTION
            and self.authenticate_context(info, **kwargs)
        ):

            raise exceptions.PermissionDenied(_("The introspection query requires authentication."))

        return context


class JSONWebTokenMiddleware(BaseJSONWebTokenMiddleware):
    def resolve(self, _next, root, info: GraphQLResolveInfo, *args, **kwargs):
        context = self.resolve_base(info, **kwargs)

        if _authenticate(context) and self.authenticate_context(info, **kwargs):

            user = authenticate(request=context, **kwargs)

            if user is not None:
                context.user = user

        return _next(root, info, **kwargs)
