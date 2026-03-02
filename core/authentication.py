from django.conf import settings
from rest_framework import authentication, exceptions


class ApiKeyUser:
    """
    Objeto mínimo que satisfaz a verificação rest_framework.permissions.IsAuthenticated.
    Não há modelo de usuário — a identidade é a própria API Key.
    """

    is_authenticated = True
    is_active = True

    def __init__(self, api_key: str):
        self.api_key = api_key

    def __str__(self):
        return f"ApiKeyUser({self.api_key[:8]}...)"


class ApiKeyAuthentication(authentication.BaseAuthentication):
    """
    Autentica requisições via header X-API-Key.

    Uso: X-API-Key: <valor configurado em GEO_API_KEY>
    """

    HEADER_NAME = "HTTP_X_API_KEY"

    def authenticate(self, request):
        api_key = request.META.get(self.HEADER_NAME)

        if not api_key:
            raise exceptions.NotAuthenticated("Header X-API-Key ausente.")

        expected = getattr(settings, "GEO_API_KEY", None)
        if not expected or api_key != expected:
            raise exceptions.AuthenticationFailed("API Key inválida.")

        return (ApiKeyUser(api_key), api_key)

    def authenticate_header(self, request):
        return "ApiKey"
