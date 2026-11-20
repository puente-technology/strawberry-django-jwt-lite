from django.urls import re_path
from strawberry.django.views import GraphQLView

from strawberry_django_jwt.decorators import jwt_cookie
from tests.example_app.schema import schema

urlpatterns = [
    re_path(r"^graphql/?$", jwt_cookie(GraphQLView.as_view(schema=schema)), name="graphql"),
]
