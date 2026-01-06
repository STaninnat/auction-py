from django.conf import settings
from rest_framework import exceptions
from rest_framework.authentication import CSRFCheck
from rest_framework_simplejwt.authentication import JWTAuthentication


def enforce_csrf(request):
    """
    Enforce CSRF validation using DRF's CSRFCheck.
    """

    def dummy_view(request):
        return None

    check = CSRFCheck(request)
    check.process_request(request)
    reason = check.process_view(request, dummy_view, (), {})
    if reason:
        raise exceptions.PermissionDenied("CSRF Failed: %s" % reason)


class CustomJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        header = self.get_header(request)

        if header is None:
            raw_token = request.COOKIES.get(settings.AUTH_COOKIE) or None
        else:
            raw_token = self.get_raw_token(header)

        if raw_token is None:
            return None

        # If using cookies, enforce CSRF
        if header is None:
            enforce_csrf(request)

        validated_token = self.get_validated_token(raw_token)
        return self.get_user(validated_token), validated_token
