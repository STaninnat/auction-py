from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import LoginView, LogoutView, MeAPIView, RegisterView

urlpatterns = [
    path("login/", LoginView.as_view(), name="user_login"),
    path("register/", RegisterView.as_view(), name="user_register"),
    path("logout/", LogoutView.as_view(), name="user_logout"),
    path("me/", MeAPIView.as_view(), name="user_me"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
