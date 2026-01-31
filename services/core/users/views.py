from django.conf import settings
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .models import User
from .serializers import (
    ChangePasswordSerializer,
    MyTokenObtainPairSerializer,
    RegisterSerializer,
    UserSerializer,
    UserUpdateSerializer,
)
from .utils import set_auth_cookies


class MeAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(UserSerializer(request.user).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(generics.UpdateAPIView):
    """
    An endpoint for changing password.
    """

    serializer_class = ChangePasswordSerializer
    model = User
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self, queryset=None):
        return self.request.user

    def post(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        self.object = self.get_object()
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            # Check old password
            if not self.object.check_password(serializer.data.get("old_password")):
                return Response({"old_password": ["Wrong password."]}, status=status.HTTP_400_BAD_REQUEST)

            # set_password also hashes the password that the user will get
            self.object.set_password(serializer.data.get("new_password"))
            self.object.save()

            response = {
                "status": "success",
                "code": status.HTTP_200_OK,
                "message": "Password updated successfully",
            }

            return Response(response)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(TokenObtainPairView):
    """
    Takes a set of user credentials and returns an access and refresh JSON web
    token to prove the authentication of those credentials.
    """

    serializer_class = MyTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        if response.status_code == status.HTTP_200_OK:
            access = response.data.get("access")
            refresh = response.data.get("refresh")

            set_auth_cookies(response, access, refresh)

            # Return simple success message instead of tokens or user data
            response.data = {"detail": "Login successful"}

        return response


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate tokens for the new user
        refresh = MyTokenObtainPairSerializer.get_token(user)
        access = str(refresh.access_token)

        response = Response(
            {"detail": "Registration successful"},
            status=status.HTTP_201_CREATED,
        )

        set_auth_cookies(response, access, str(refresh))

        return response


class LogoutView(APIView):
    # permission_classes = [permissions.IsAuthenticated]
    # Optional: If you want to allow logout even if token expired, remove IsAuthenticate.
    # But usually logout needs authentication.

    def post(self, request):
        try:
            refresh_token = request.COOKIES.get(settings.AUTH_COOKIE_REFRESH)
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()

            response = Response(status=status.HTTP_205_RESET_CONTENT)
            response.delete_cookie(settings.AUTH_COOKIE)
            response.delete_cookie(settings.AUTH_COOKIE_REFRESH)
            return response
        except Exception:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class CookieTokenRefreshView(TokenRefreshView):
    """
    Custom Refresh View that reads refresh token from cookie
    and sets new access token in cookie.
    """

    def post(self, request, *args, **kwargs):
        # Inject refresh token from cookie into data if not present
        if "refresh" not in request.data:
            refresh_token = request.COOKIES.get(settings.AUTH_COOKIE_REFRESH)
            if refresh_token:
                request.data["refresh"] = refresh_token

        try:
            response = super().post(request, *args, **kwargs)

            if response.status_code == 200:
                access = response.data.get("access")
                refresh = response.data.get("refresh") or request.COOKIES.get(settings.AUTH_COOKIE_REFRESH)

                set_auth_cookies(response, access, refresh)

                del response.data["access"]
                if "refresh" in response.data:
                    del response.data["refresh"]

            return response
        except (InvalidToken, TokenError) as e:
            return Response({"detail": str(e)}, status=status.HTTP_401_UNAUTHORIZED)
