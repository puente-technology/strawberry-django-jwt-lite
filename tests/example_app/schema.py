import strawberry
from strawberry import Schema

from strawberry_django_jwt.middleware import JSONWebTokenMiddleware
import strawberry_django_jwt.mutations as jwt_mutations


@strawberry.type
class Query:
    @strawberry.field
    def value(self) -> int:
        return 1


@strawberry.type
class Mutation:
    verify_token = jwt_mutations.Verify.verify
    refresh_token = jwt_mutations.Refresh.refresh
    revoke_token = jwt_mutations.Revoke.revoke


schema = Schema(query=Query, mutation=Mutation, extensions=[JSONWebTokenMiddleware])
