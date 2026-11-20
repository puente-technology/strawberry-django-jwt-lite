class VerifyMixin:
    def test_verify(self):
        response = self.execute(
            {
                "token": self.token,
            }
        )

        payload = response.data["verifyToken"]["payload"]

        self.assertIsNone(response.errors)
        self.assertUsernameIn(payload)

    def test_verify_invalid_token(self):
        response = self.execute(
            {
                "token": "invalid",
            }
        )

        self.assertIsNotNone(response.errors)
