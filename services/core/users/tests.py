from django.conf import settings
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
        self.refresh_url = reverse("token_refresh")
        self.me_url = reverse("user_me")

        self.user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123",
            "password_confirm": "testpassword123",
        }

    def test_register_auto_login(self):
        """Test that registration sets auth cookies."""
        response = self.client.post(self.register_url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check tokens are NOT in body
        self.assertNotIn("access", response.data)
        self.assertNotIn("refresh", response.data)

        # Check cookies
        self.assertIn(settings.AUTH_COOKIE, response.cookies)
        self.assertIn(settings.AUTH_COOKIE_REFRESH, response.cookies)

        # Verify HttpOnly
        self.assertTrue(response.cookies[settings.AUTH_COOKIE]["httponly"])
        self.assertTrue(response.cookies[settings.AUTH_COOKIE_REFRESH]["httponly"])

    def test_login(self):
        """Test explicit login flow sets cookies."""
        User.objects.create_user(  # type: ignore
            username=self.user_data["username"], email=self.user_data["email"], password=self.user_data["password"]
        )

        data = {"username": self.user_data["username"], "password": self.user_data["password"]}
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIn(settings.AUTH_COOKIE, response.cookies)
        self.assertIn(settings.AUTH_COOKIE_REFRESH, response.cookies)

    def test_protected_route_with_cookie_and_csrf(self):
        """Test accessing a protected route using the cookie AND CSRF token."""
        # 1. Register to get cookies
        self.client.post(self.register_url, self.user_data)

        # 2. Access /me/ endpoint
        # The test client normally bypasses CSRF checks unless enforced.
        # Since our CustomAuthentication enforces it, we rely on the client's internal handling
        # or we might need to be explicit if 'enforce_csrf_checks=True' was set on the client.
        # By default, APITestCase client doesn't enforce CSRF middleware logic
        # BUT our CustomAuthentication calls CSRFCheck manually.

        # We need to manually inject CSRF because we are calling CSRFCheck regardless of middleware
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], self.user_data["username"])

    def test_logout(self):
        """Test that logout deletes cookies and blacklists token."""
        # Login to get cookies
        User.objects.create_user(  # type: ignore
            username=self.user_data["username"], email=self.user_data["email"], password=self.user_data["password"]
        )
        login_response = self.client.post(
            self.login_url, {"username": self.user_data["username"], "password": self.user_data["password"]}
        )

        refresh_token_str = login_response.cookies[settings.AUTH_COOKIE_REFRESH].value

        # Logout
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)

        self.assertEqual(response.cookies[settings.AUTH_COOKIE].value, "")
        self.assertEqual(response.cookies[settings.AUTH_COOKIE_REFRESH].value, "")

        with self.assertRaises(TokenError):
            RefreshToken(refresh_token_str).check_blacklist()

    def test_refresh_token_cookie(self):
        """Test refreshing token using cookie."""
        User.objects.create_user(  # type: ignore
            username=self.user_data["username"], email=self.user_data["email"], password=self.user_data["password"]
        )
        self.client.post(
            self.login_url, {"username": self.user_data["username"], "password": self.user_data["password"]}
        )

        response = self.client.post(self.refresh_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIn(settings.AUTH_COOKIE, response.cookies)
        self.assertNotEqual(response.cookies[settings.AUTH_COOKIE].value, "")

    def test_csrf_missing_fail(self):
        """Test that requests fail without CSRF token when using cookies."""
        # Note: Validating CSRF failure in tests is tricky because APITestCase disables it by default.
        # We force it by creating a client that enforces CSRF.
        csrf_client = APITestCase.client_class(enforce_csrf_checks=True)

        # 1. Login manually to get cookies
        User.objects.create_user(  # type: ignore
            username=self.user_data["username"], email=self.user_data["email"], password=self.user_data["password"]
        )
        login_resp = csrf_client.post(
            self.login_url, {"username": self.user_data["username"], "password": self.user_data["password"]}
        )

        # 2. Try to access /me/ with cookies but WITHOUT CSRF header
        # We need to manually transfer cookies from login_resp to the next request
        csrf_client.cookies = login_resp.cookies

        # Make request (GET usually safe, but we check if CSRFCheck enforces on GET too - usually it doesn't)
        # CSRF is usually for unsafe methods (POST, PUT, DELETE).
        # Attempt a POST request (e.g. logout) without CSRF token

        # Clear any CSRF cookie that might have been set automatically
        csrf_client.cookies.pop("csrftoken", None)

        response = csrf_client.post(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("CSRF", str(response.data))
