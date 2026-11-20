import strawberry
from strawberry.types import Info

from strawberry_django_jwt import mixins
from strawberry_django_jwt.decorators import ensure_token
from strawberry_django_jwt.object_types import PayloadType
from strawberry_django_jwt.refresh_token.mutations import Revoke

__all__ = [
    "Verify",
    "Refresh",
    "Revoke",
]

from strawberry_django_jwt.utils import get_payload


class Verify:
    @strawberry.mutation
    @ensure_token
    def verify(self, info: Info, token: str) -> PayloadType:
        return PayloadType(payload=get_payload(token, info.context))


class Refresh(mixins.RefreshMixin):
    pass
