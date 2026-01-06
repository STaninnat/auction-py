from django.conf import settings


def set_auth_cookies(response, access, refresh):
    """Helper to set auth cookies on the response."""
    response.set_cookie(
        key=settings.AUTH_COOKIE,
        value=access,
        expires=settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"],
        secure=settings.AUTH_COOKIE_SECURE,
        httponly=settings.AUTH_COOKIE_HTTP_ONLY,
        samesite=settings.AUTH_COOKIE_SAMESITE,
    )
    response.set_cookie(
        key=settings.AUTH_COOKIE_REFRESH,
        value=refresh,
        expires=settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"],
        secure=settings.AUTH_COOKIE_SECURE,
        httponly=settings.AUTH_COOKIE_HTTP_ONLY,
        samesite=settings.AUTH_COOKIE_SAMESITE,
    )
