from graphql import get_introspection_query

from strawberry_django_jwt.settings import jwt_settings
from tests.decorators import OverrideJwtSettings
from tests.testcases import SchemaTestCase


class QueriesTests(SchemaTestCase):
    def test_introspection(self):
        headers = {
            jwt_settings.JWT_AUTH_HEADER_NAME: f"{jwt_settings.JWT_AUTH_HEADER_PREFIX} {self.token}",
        }

        response = self.client.execute(get_introspection_query(), **headers)

        self.assertIsNone(response.errors)

    def test_introspection_no_header(self):
        response = self.client.execute(get_introspection_query())

        self.assertIsNotNone(response.errors)

    @OverrideJwtSettings(JWT_AUTHENTICATE_INTROSPECTION=False)
    def test_introspection_no_auth(self):
        headers = {
            jwt_settings.JWT_AUTH_HEADER_NAME: f"{jwt_settings.JWT_AUTH_HEADER_PREFIX} {self.token}",
        }

        response = self.client.execute(get_introspection_query(), **headers)

        self.assertIsNone(response.errors)

    @OverrideJwtSettings(JWT_AUTHENTICATE_INTROSPECTION=False)
    def test_introspection_no_auth_no_header(self):
        response = self.client.execute(get_introspection_query())

        self.assertIsNone(response.errors)
