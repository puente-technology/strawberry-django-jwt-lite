# Strawberry Django JWT Lite

[JSON Web Token](https://jwt.io/) authentication for
[Strawberry Django GraphQL](https://strawberry.rocks/docs/integrations/django), with long-running refresh tokens.

This is a stripped-down fork of [strawberry-django-jwt](https://github.com/KundaPanda/strawberry-django-jwt), which is
no longer maintained. That project is itself a port of [Django GraphQL JWT](https://github.com/flavors/django-graphql-jwt)
from Graphene to Strawberry. This fork keeps only the synchronous, refresh-token feature set and updates it to run on
current Python, Django and Strawberry releases.

The import name is unchanged (`strawberry_django_jwt`), so projects using the original library only need to swap the
dependency, as long as they use the features listed below.

---

## What's included

- `JSONWebTokenMiddleware` schema extension: authenticates requests from the `Authorization: JWT <token>` header, falling
  back to the `JWT` cookie
- `JSONWebTokenBackend` authentication backend
- `Verify`, `Refresh` and `Revoke` mutations
- Long-running refresh tokens stored in the database (`strawberry_django_jwt.refresh_token`), with a Django admin page
- `jwt_cookie` view decorator for setting and deleting the `JWT` and `JWT-refresh-token` cookies
- `get_token` and `create_refresh_token` shortcuts for issuing tokens from your own login mutation
- Signals, CSRF rotation, and the configurable handler settings from the original library

### Removed from the original library

- All async support (`AsyncJSONWebTokenMiddleware`, `*Async` mutations, async backend and shortcuts)
- `ObtainJSONWebToken` (`tokenAuth`); issue tokens from your own mutation instead (see below)
- Permission decorators (`login_required`, `login_field`, `permission_required`, `staff_member_required`,
  `superuser_required`, `user_passes_test`)
- Keep-alive refresh (refreshing with the access token instead of a refresh token)
- `DeleteJSONWebTokenCookie` and `DeleteRefreshTokenCookie` mutations
- Passing the token as a GraphQL argument (`JWT_ALLOW_ARGUMENT`, `JWT_ARGUMENT_NAME`)
- `StatusHandlingGraphQLView` and the other custom views
- The `cleartokens` management command
- Integration with strawberry-graphql-django and Django REST Framework

## Requirements

- Python 3.10+
- Django 4.2 to 6.1 (tested with 4.2, 5.2, 6.0 and 6.1; Django 6 needs Python 3.12+)
- strawberry-graphql 0.215.1+
- PyJWT 2.x

---

## Installation

1. Install from a git tag. With pip:

   ```shell
   pip install "strawberry-django-jwt-lite @ git+https://github.com/puente-technology/strawberry-django-jwt-lite.git@v0.1.1"
   ```

   or with Poetry:

   ```toml
   [tool.poetry.dependencies]
   strawberry-django-jwt-lite = { git = "https://github.com/puente-technology/strawberry-django-jwt-lite.git", tag = "v0.1.1" }
   ```

   Don't install it alongside the original `strawberry-django-jwt` package: both provide the `strawberry_django_jwt`
   module.

2. Add `AuthenticationMiddleware` to **MIDDLEWARE**:

   ```python
   MIDDLEWARE = [
       ...,
       "django.contrib.auth.middleware.AuthenticationMiddleware",
       ...,
   ]
   ```

3. Add the refresh token app to **INSTALLED_APPS**:

   ```python
   INSTALLED_APPS = [
       "django.contrib.auth",
       "django.contrib.contenttypes",
       "django.contrib.sessions",
       ...,
       "strawberry_django_jwt.refresh_token.apps.RefreshTokenConfig",
   ]
   ```

   Its app label and migrations are the same as the original library's, so existing refresh tokens are kept.

4. Add `JSONWebTokenBackend` to **AUTHENTICATION_BACKENDS**:

   ```python
   AUTHENTICATION_BACKENDS = [
       "strawberry_django_jwt.backends.JSONWebTokenBackend",
       "django.contrib.auth.backends.ModelBackend",
   ]
   ```

5. Configure the library. Long-running refresh tokens are the only supported refresh mode, so turn them on:

   ```python
   from datetime import timedelta

   GRAPHQL_JWT = {
       "JWT_LONG_RUNNING_REFRESH_TOKEN": True,
       "JWT_VERIFY_EXPIRATION": True,
       "JWT_EXPIRATION_DELTA": timedelta(minutes=5),
       "JWT_REFRESH_EXPIRATION_DELTA": timedelta(days=7),
   }
   ```

6. Add the middleware and mutations to your schema, plus your own login mutation:

   ```python
   import strawberry
   from strawberry_django_jwt.middleware import JSONWebTokenMiddleware
   import strawberry_django_jwt.mutations as jwt_mutations
   from strawberry_django_jwt.shortcuts import create_refresh_token, get_token


   @strawberry.type
   class LogInPayload:
       token: str
       refresh_token: str


   @strawberry.mutation
   def log_in(self, info: strawberry.Info, email: str, password: str) -> LogInPayload:
       user = ...  # check the credentials yourself
       token = get_token(user)
       refresh_token = create_refresh_token(user)

       # Only needed if you use the jwt_cookie decorator (step 7)
       info.context.jwt_token = token
       info.context.jwt_refresh_token = refresh_token

       return LogInPayload(token=token, refresh_token=refresh_token.token)


   @strawberry.type
   class Mutation:
       log_in = log_in
       verify_token = jwt_mutations.Verify.verify
       refresh_token = jwt_mutations.Refresh.refresh
       revoke_token = jwt_mutations.Revoke.revoke


   schema = strawberry.Schema(query=..., mutation=Mutation, extensions=[JSONWebTokenMiddleware])
   ```

   The `info.context.jwt_token` lines assume your view's context is the Django request, as in the boilerplate's
   `CustomGraphQLView`. With Strawberry's default context, set them on `info.context.request` instead.

7. \[OPTIONAL\] Wrap the GraphQL view with `jwt_cookie` to set the `JWT` and `JWT-refresh-token` cookies on login and
   refresh:

   ```python
   from django.urls import path
   from strawberry.django.views import GraphQLView
   from strawberry_django_jwt.decorators import jwt_cookie

   urlpatterns = [
       path("graphql", jwt_cookie(GraphQLView.as_view(schema=schema))),
   ]
   ```

   To delete the cookies, for example on logout, set `request.delete_jwt_cookie = True` and
   `request.delete_refresh_token_cookie = True` in your resolver.

---

## Behaviour to be aware of

These are unchanged from the original library:

- **Refreshing doesn't revoke the old refresh token.** `refreshToken` issues a new refresh token, and the old one stays
  valid until it expires or is revoked with `revokeToken`. Set `JWT_REUSE_REFRESH_TOKENS` to reuse the same token
  instead.
- **An expired access token fails every field**, with the message `Signature has expired`, until the client stops
  sending it. Clients can use that message as the signal to refresh.
- **`refreshExpiresIn` is a Unix timestamp** (when the refresh token expires), not a number of seconds.
- **Cookies are not `Secure` and have no `SameSite` attribute by default.** Set `JWT_COOKIE_SECURE` and
  `JWT_COOKIE_SAMESITE` in production.
- The introspection query requires authentication unless `JWT_AUTHENTICATE_INTROSPECTION` is `False`.

## Known issues

- `JWT_ALLOW_ANY_CLASSES` only supports return-type based filtering, because Strawberry doesn't keep class-based field
  definitions (so superclasses are dropped).

---

## Development

```shell
poetry install --extras dev   # dev dependencies, plus uvicorn for the example app
poetry run pytest
pre-commit run --all-files    # pre-commit is installed separately, not via Poetry
poetry run mypy strawberry_django_jwt tests
```

To start the example application, run `poetry run uvicorn tests.example_app.asgi:application`.

## License

MIT. See [LICENSE](LICENSE). The original copyright notice from Django GraphQL JWT is kept, as the licence requires.
