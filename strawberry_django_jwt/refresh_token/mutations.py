import strawberry
from strawberry.types import Info

from strawberry_django_jwt.refresh_token.decorators import ensure_refresh_token
from strawberry_django_jwt.refresh_token.object_types import RevokeType
from strawberry_django_jwt.refresh_token.shortcuts import get_refresh_token


class Revoke:
    @strawberry.mutation
    @ensure_refresh_token
    def revoke(self, info: Info, refresh_token: str) -> RevokeType:
        context = info.context
        refresh_token_obj = get_refresh_token(refresh_token, context)
        refresh_token_obj.revoke(context)
        return RevokeType(revoked=refresh_token_obj.revoked)
