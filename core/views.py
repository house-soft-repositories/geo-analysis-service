from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import BasicAuthentication
from rest_framework.permissions import AllowAny


class HealthCheckView(APIView):
    """
    Endpoint público de health check — sem autenticação.
    GET /api/v1/health/
    """

    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"status": "ok", "servico": "geo-analysis-service"})
