from django.test import TestCase

from users.models import User
from users.serializers import MyTokenObtainPairSerializer


class JWTCustomClaimsTest(TestCase):
    def test_token_contains_username(self):
        user = User.objects.create_user(username="testuser", password="testpassword", email="test@example.com")
        refresh = MyTokenObtainPairSerializer.get_token(user)
        access_token = refresh.access_token

        # Decode the token
        payload = access_token.payload

        self.assertIn("username", payload)
        self.assertEqual(payload["username"], "testuser")
