from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class AuthenticationTests(APITestCase):
    def setUp(self):
        self.register_url = reverse("user_register")
        self.login_url = reverse("user_login")
        self.logout_url = reverse("user_logout")
        self.user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123",
            "password_confirm": "testpassword123",
        }

    def test_register_auto_login(self):
        """Test that registration returns user data and tokens (auto-login)."""
        response = self.client.post(self.register_url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check structure
        self.assertIn("user", response.data)
        self.assertIn("tokens", response.data)
        self.assertIn("access", response.data["tokens"])
        self.assertIn("refresh", response.data["tokens"])

        # Verify custom claims in token
        token = RefreshToken(response.data["tokens"]["refresh"])
        self.assertEqual(token["username"], self.user_data["username"])

    def test_login(self):
        """Test explicit login flow."""
        User.objects.create_user(  # type: ignore
            username=self.user_data["username"], email=self.user_data["email"], password=self.user_data["password"]
        )

        data = {"username": self.user_data["username"], "password": self.user_data["password"]}
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

        # Verify claims
        token = RefreshToken(response.data["refresh"])
        self.assertEqual(token["username"], self.user_data["username"])

    def test_logout(self):
        """Test that logout blacklists the refresh token."""
        # Create user and get tokens
        user = User.objects.create_user(  # type: ignore
            username=self.user_data["username"], email=self.user_data["email"], password=self.user_data["password"]
        )
        refresh = RefreshToken.for_user(user)
        refresh_token = str(refresh)

        # Logout
        self.client.force_authenticate(user=user)
        response = self.client.post(self.logout_url, {"refresh": refresh_token})
        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)

        # Verify token is blacklisted
        with self.assertRaises(TokenError):
            # Attempting to use blacklisted token should fail
            # Note: SimpleJWT raises TokenError, but for test simplicity we expect failure
            RefreshToken(refresh_token).check_blacklist()

    def test_logout_invalid_token(self):
        """Test logout with invalid token."""
        user = User.objects.create_user(  # type: ignore
            username=self.user_data["username"], email=self.user_data["email"], password=self.user_data["password"]
        )
        self.client.force_authenticate(user=user)
        response = self.client.post(self.logout_url, {"refresh": "invalid_token"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
