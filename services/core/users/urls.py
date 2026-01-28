from django.urls import path

from .views import (
    ChangePasswordView,
    CookieTokenRefreshView,
    LoginView,
    LogoutView,
    MeAPIView,
    RegisterView,
)

urlpatterns = [
    path("login/", LoginView.as_view(), name="user_login"),
    path("register/", RegisterView.as_view(), name="user_register"),
    path("logout/", LogoutView.as_view(), name="user_logout"),
    path("me/", MeAPIView.as_view(), name="user_me"),
    path("change-password/", ChangePasswordView.as_view(), name="change_password"),
    path("token/refresh/", CookieTokenRefreshView.as_view(), name="token_refresh"),
]
