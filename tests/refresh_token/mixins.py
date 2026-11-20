from importlib import reload
from typing import Any

import strawberry

import strawberry_django_jwt
from strawberry_django_jwt.refresh_token.signals import (
    refresh_token_revoked,
    refresh_token_rotated,
)
from strawberry_django_jwt.shortcuts import create_refresh_token, get_refresh_token
from tests.context_managers import back_to_the_future, catch_signal, refresh_expired
from tests.decorators import OverrideJwtSettings


class RefreshTokenMutationMixin:
    Mutation: Any

    # noinspection PyPep8Naming
    @OverrideJwtSettings(JWT_LONG_RUNNING_REFRESH_TOKEN=True)
    def setUp(self):
        reload(strawberry_django_jwt.mutations)
        m = type(
            "jwt",
            (object,),
            {**{name: mutation for name, mutation in self.refresh_token_mutations.items()}},
        )
        self.Mutation = strawberry.type(m)

        super().setUp()


class RefreshTokenMixin:
    refresh_token: Any

    # noinspection PyPep8Naming
    def setUp(self):
        super().setUp()
        self.refresh_token = create_refresh_token(self.user)


class RefreshMixin(RefreshTokenMutationMixin, RefreshTokenMixin):
    @OverrideJwtSettings(JWT_LONG_RUNNING_REFRESH_TOKEN=True)
    def test_refresh_token(self):
        reload(strawberry_django_jwt.mixins)
        reload(strawberry_django_jwt.mutations)
        self.refresh_token_mutations = {
            "refresh_token": strawberry_django_jwt.mutations.Refresh.refresh,
        }
        m = type(
            "jwt",
            (object,),
            {**{name: mutation for name, mutation in self.refresh_token_mutations.items()}},
        )
        self.Mutation = strawberry.type(m)
        self.client.schema(query=self.Query, mutation=self.Mutation)
        with catch_signal(refresh_token_rotated) as refresh_token_rotated_handler, back_to_the_future(seconds=1):
            response = self.execute(
                {
                    "refreshToken": self.refresh_token.token,
                }
            )

        data = response.data["refreshToken"]
        token = data["token"]
        refresh_token = get_refresh_token(data["refreshToken"])
        payload = data["payload"]

        self.assertIsNone(response.errors)
        self.assertEqual(refresh_token_rotated_handler.call_count, 1)

        self.assertUsernameIn(payload)
        self.assertNotEqual(token, self.token)
        self.assertGreater(payload["exp"], self.payload.exp)

        self.assertNotEqual(refresh_token.token, self.refresh_token.token)
        self.assertEqual(refresh_token.user, self.user)
        self.assertGreater(refresh_token.created, self.refresh_token.created)

    @OverrideJwtSettings(JWT_LONG_RUNNING_REFRESH_TOKEN=True, JWT_REUSE_REFRESH_TOKENS=True)
    def test_reuse_refresh_token(self):
        reload(strawberry_django_jwt.mixins)
        reload(strawberry_django_jwt.mutations)
        self.refresh_token_mutations = {
            "refresh_token": strawberry_django_jwt.mutations.Refresh.refresh,
        }
        m = type(
            "jwt",
            (object,),
            {**{name: mutation for name, mutation in self.refresh_token_mutations.items()}},
        )
        self.Mutation = strawberry.type(m)
        self.client.schema(query=self.Query, mutation=self.Mutation)
        with catch_signal(refresh_token_rotated) as refresh_token_rotated_handler, back_to_the_future(seconds=1):
            response = self.execute(
                {
                    "refreshToken": self.refresh_token.token,
                }
            )

        data = response.data["refreshToken"]
        token = data["token"]
        refresh_token = get_refresh_token(data["refreshToken"])
        payload = data["payload"]

        self.assertIsNone(response.errors)
        self.assertEqual(refresh_token_rotated_handler.call_count, 1)

        self.assertUsernameIn(payload)
        self.assertNotEqual(token, self.token)
        self.assertNotEqual(refresh_token.token, self.refresh_token.token)

    @OverrideJwtSettings(JWT_LONG_RUNNING_REFRESH_TOKEN=True)
    def test_missing_refresh_token(self):
        reload(strawberry_django_jwt.mixins)
        reload(strawberry_django_jwt.mutations)
        self.refresh_token_mutations = {
            "refresh_token": strawberry_django_jwt.mutations.Refresh.refresh,
        }
        m = type(
            "jwt",
            (object,),
            {**{name: mutation for name, mutation in self.refresh_token_mutations.items()}},
        )
        self.Mutation = strawberry.type(m)
        self.client.schema(query=self.Query, mutation=self.Mutation)
        response = self.execute({})
        self.assertIsNotNone(response.errors)

    @OverrideJwtSettings(JWT_LONG_RUNNING_REFRESH_TOKEN=True)
    def test_refresh_token_expired(self):
        reload(strawberry_django_jwt.mixins)
        reload(strawberry_django_jwt.mutations)
        self.refresh_token_mutations = {
            "refresh_token": strawberry_django_jwt.mutations.Refresh.refresh,
        }
        m = type(
            "jwt",
            (object,),
            {**{name: mutation for name, mutation in self.refresh_token_mutations.items()}},
        )
        self.Mutation = strawberry.type(m)
        self.client.schema(query=self.Query, mutation=self.Mutation)
        with refresh_expired():
            response = self.execute(
                {
                    "refreshToken": self.refresh_token.token,
                }
            )

        self.assertIsNotNone(response.errors)


class RevokeMixin(RefreshTokenMixin):
    def test_revoke(self):
        with catch_signal(refresh_token_revoked) as refresh_token_revoked_handler:
            response = self.execute(
                {
                    "refreshToken": self.refresh_token.token,
                }
            )

        self.assertIsNone(response.errors)
        self.assertEqual(refresh_token_revoked_handler.call_count, 1)

        self.refresh_token.refresh_from_db()
        self.assertIsNotNone(self.refresh_token.revoked)
        self.assertIsNotNone(response.data["revokeToken"]["revoked"])


class CookieRefreshMixin(RefreshTokenMutationMixin):
    @OverrideJwtSettings(JWT_LONG_RUNNING_REFRESH_TOKEN=True)
    def test_refresh_token(self):
        reload(strawberry_django_jwt.mixins)
        reload(strawberry_django_jwt.mutations)
        self.refresh_token_mutations = {
            "refresh_token": strawberry_django_jwt.mutations.Refresh.refresh,
        }
        m = type(
            "jwt",
            (object,),
            {**{name: mutation for name, mutation in self.refresh_token_mutations.items()}},
        )
        self.Mutation = strawberry.type(m)
        self.client.schema(query=self.Query, mutation=self.Mutation)
        self.set_refresh_token_cookie()

        with catch_signal(refresh_token_rotated) as refresh_token_rotated_handler, back_to_the_future(seconds=1):
            response = self.execute()

        data = response.data["refreshToken"]
        token = data["token"]

        self.assertIsNone(response.errors)
        self.assertEqual(refresh_token_rotated_handler.call_count, 1)

        self.assertNotEqual(token, self.token)
        self.assertUsernameIn(data["payload"])
