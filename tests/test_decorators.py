import django
from django.contrib.auth.models import AnonymousUser

from strawberry_django_jwt import decorators
from tests.decorators import OverrideJwtSettings
from tests.testcases import TestCase


class CSRFRotationTests(TestCase):
    @OverrideJwtSettings(JWT_CSRF_ROTATION=True)
    def test_csrf_rotation(self):
        info_mock = self.info(AnonymousUser())
        decorators.csrf_rotation(
            lambda cls, info, *args, **kwargs: None,
        )(self, info_mock)
        if django.VERSION >= (4, 0):
            self.assertTrue(info_mock.context.META["CSRF_COOKIE_NEEDS_UPDATE"])
        else:
            self.assertTrue(info_mock.context.csrf_cookie_needs_reset)
