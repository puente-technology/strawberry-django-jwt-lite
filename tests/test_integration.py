from django.contrib.auth import get_user_model
from django.test.testcases import TestCase
from django.urls import reverse


class IntegrationTestCase(TestCase):
    read_query = """
    query ReadQuery {
      value
    }"""

    @classmethod
    def setUpTestData(cls) -> None:
        get_user_model().objects.create_user(
            username="test",
            password="dolphins",
        )


class LoginTestCase(IntegrationTestCase):
    def test_read(self):
        data = {"query": self.read_query}
        response = self.client.post(reverse("graphql"), data=data, content_type="application/json")
        result = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(result["data"]["value"], 1)
