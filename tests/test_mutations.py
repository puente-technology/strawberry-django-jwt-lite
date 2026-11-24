import strawberry

import strawberry_django_jwt.mutations
from tests import mixins
from tests.testcases import SchemaTestCase


class VerifyTests(mixins.VerifyMixin, SchemaTestCase):
    query = """
    mutation VerifyToken($token: String!) {
      verifyToken(token: $token) {
        payload {
            username
        }
      }
    }"""

    @strawberry.type
    class Mutation:
        verify_token = strawberry_django_jwt.mutations.Verify.verify
