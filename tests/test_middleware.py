from unittest import mock

from django.contrib.auth.models import AnonymousUser

from strawberry_django_jwt.exceptions import JSONWebTokenError
from strawberry_django_jwt.middleware import JSONWebTokenMiddleware, allow_any
from strawberry_django_jwt.settings import jwt_settings
from tests.decorators import OverrideJwtSettings
from tests.testcases import TestCase


class AuthenticateByHeaderTests(TestCase):
    def setUp(self):
        super().setUp()
        self.middleware = JSONWebTokenMiddleware

    @OverrideJwtSettings(JWT_ALLOW_ANY_HANDLER=lambda *args: False)
    def test_authenticate(self):
        headers = {
            jwt_settings.JWT_AUTH_HEADER_NAME: f"{jwt_settings.JWT_AUTH_HEADER_PREFIX} {self.token}",
        }

        next_mock = mock.Mock()
        info_mock = self.info(AnonymousUser(), **headers)

        middleware = self.middleware(execution_context=info_mock.context)
        middleware.resolve(next_mock, None, info_mock)

        next_mock.assert_called_once_with(None, info_mock)
        self.assertEqual(info_mock.context.user, self.user)

    @OverrideJwtSettings(JWT_ALLOW_ANY_HANDLER=lambda *args: False)
    @mock.patch("strawberry_django_jwt.middleware.authenticate", return_value=None)
    def test_not_authenticate(self, authenticate_mock):
        headers = {
            jwt_settings.JWT_AUTH_HEADER_NAME: f"{jwt_settings.JWT_AUTH_HEADER_PREFIX} {self.token}",
        }

        next_mock = mock.Mock()
        info_mock = self.info(AnonymousUser(), **headers)

        middleware = self.middleware(execution_context=info_mock.context)
        middleware.resolve(next_mock, None, info_mock)

        next_mock.assert_called_once_with(None, info_mock)
        authenticate_mock.assert_called_once_with(request=info_mock.context)
        self.assertIsInstance(info_mock.context.user, AnonymousUser)

    @OverrideJwtSettings(JWT_ALLOW_ANY_HANDLER=lambda *args: False)
    def test_invalid_token(self):
        headers = {
            jwt_settings.JWT_AUTH_HEADER_NAME: f"{jwt_settings.JWT_AUTH_HEADER_PREFIX} invalid",
        }

        next_mock = mock.Mock()
        info_mock = self.info(AnonymousUser(), **headers)

        middleware = self.middleware(execution_context=info_mock.context)
        with self.assertRaises(JSONWebTokenError):
            middleware.resolve(next_mock, None, info_mock)

        next_mock.assert_not_called()

    @mock.patch("strawberry_django_jwt.middleware.authenticate")
    def test_already_authenticated(self, authenticate_mock):
        headers = {
            jwt_settings.JWT_AUTH_HEADER_NAME: f"{jwt_settings.JWT_AUTH_HEADER_PREFIX} {self.token}",
        }

        next_mock = mock.Mock()
        info_mock = self.info(self.user, **headers)

        middleware = self.middleware(execution_context=info_mock.context)
        middleware.resolve(next_mock, None, info_mock)

        next_mock.assert_called_once_with(None, info_mock)
        authenticate_mock.assert_not_called()

    @OverrideJwtSettings(JWT_ALLOW_ANY_HANDLER=lambda *args: True)
    def test_allow_any(self):
        headers = {
            jwt_settings.JWT_AUTH_HEADER_NAME: f"{jwt_settings.JWT_AUTH_HEADER_PREFIX} {self.token}",
        }

        next_mock = mock.Mock()
        info_mock = self.info(AnonymousUser(), **headers)

        middleware = self.middleware(execution_context=info_mock.context)
        middleware.resolve(next_mock, None, info_mock)

        next_mock.assert_called_once_with(None, info_mock)
        self.assertIsInstance(info_mock.context.user, AnonymousUser)

    def test_authenticate_context(self):
        info_mock = self.info()

        middleware = self.middleware(execution_context=info_mock.context)
        middleware.cached_allow_any.add("test")
        authenticate_context = middleware.authenticate_context(info_mock)

        self.assertFalse(authenticate_context)


class AllowAnyTests(TestCase):
    def info(self, user, **headers):
        info_mock = super().info(user, **headers)
        info_mock.field_name = "test"
        info_mock.operation.operation.name = "query"
        return info_mock

    def info_with_field_mock(self, user, field=None):
        info_mock = self.info(user)
        info_mock.schema.query_type = mock.Mock(
            fields={
                "test": field,
            }
        )
        return info_mock

    def info_with_type_mock(self, user, type=None):
        type_mock = mock.Mock(type=mock.Mock(graphene_type=type))
        return self.info_with_field_mock(user, type_mock)

    # TODO: Does not work currently, see Known Issues in README.md
    # @OverrideJwtSettings(JWT_ALLOW_ANY_CLASSES=['tests.testcases.TestCase'])
    # def test_allow_any(self):
    #     info_mock = self.info_with_type_mock(self.user, TestCase)
    #     allowed = allow_any(info_mock)
    #
    #     self.assertTrue(allowed)

    def test_not_allow_any(self):
        info_mock = self.info_with_type_mock(self.user, TestCase)
        allowed = allow_any(info_mock)

        self.assertFalse(allowed)

    def test_unknown_field(self):
        info_mock = self.info_with_field_mock(self.user)
        allowed = allow_any(info_mock)

        self.assertFalse(allowed)

    def test_unknown_type(self):
        info_mock = self.info_with_type_mock(self.user)
        allowed = allow_any(info_mock)

        self.assertFalse(allowed)
