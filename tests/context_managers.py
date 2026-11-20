from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from unittest import mock

from strawberry_django_jwt.settings import jwt_settings


@contextmanager
def catch_signal(signal):
    handler = mock.Mock()
    signal.connect(handler)
    yield handler
    signal.disconnect(handler)


@contextmanager
def back_to_the_future(**kwargs):
    with mock.patch("strawberry_django_jwt.utils.datetime") as datetime_mock:
        datetime_mock.now.return_value = datetime.now(timezone.utc) + timedelta(**kwargs)
        yield datetime_mock


def refresh_expired():
    expires = jwt_settings.JWT_REFRESH_EXPIRATION_DELTA.total_seconds()
    return back_to_the_future(seconds=1 + expires)
