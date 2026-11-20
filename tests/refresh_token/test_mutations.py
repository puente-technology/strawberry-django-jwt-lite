import strawberry

import strawberry_django_jwt.mutations
from tests.refresh_token import mixins
from tests.refresh_token.testcases import CookieTestCase
from tests.testcases import SchemaTestCase


class RefreshTests(mixins.RefreshMixin, SchemaTestCase):
    query = """
    mutation RefreshToken($refreshToken: String) {
      refreshToken(refreshToken: $refreshToken) {
        token
        payload {
            username
            origIat
            exp
        }
        refreshToken
        refreshExpiresIn
      }
    }"""

    refresh_token_mutations = {
        "refresh_token": strawberry_django_jwt.mutations.Refresh.refresh,
    }


class RevokeTests(mixins.RevokeMixin, SchemaTestCase):
    query = """
    mutation RevokeToken($refreshToken: String!) {
      revokeToken(refreshToken: $refreshToken) {
        revoked
      }
    }"""

    @strawberry.type
    class Mutation:
        revoke_token = strawberry_django_jwt.mutations.Revoke.revoke


class CookieRefreshTests(mixins.CookieRefreshMixin, CookieTestCase):
    query = """
    mutation {
      refreshToken {
        token
        payload {
          username
        }
        refreshToken
        refreshExpiresIn
      }
    }"""

    refresh_token_mutations = {
        "refresh_token": strawberry_django_jwt.mutations.Refresh.refresh,
    }
