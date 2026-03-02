from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


class GeoAnalysisException(Exception):
    """Base exception for domain errors in this service."""

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class KMLParseError(GeoAnalysisException):
    """Raised when a KML file cannot be parsed into a valid geometry."""

    def __init__(self, detail: str = "Arquivo KML inválido ou geometria não reconhecida."):
        super().__init__(detail, 422)


class EmptyGeometryError(GeoAnalysisException):
    """Raised when a parsed KML results in an empty geometry."""

    def __init__(self):
        super().__init__("O KML não contém feições geométricas.", 422)


class LayerNotFoundError(GeoAnalysisException):
    """Raised when a reference layer slug does not exist."""

    def __init__(self, slug: str):
        super().__init__(f"Camada de referência não encontrada: '{slug}'.", 404)


def custom_exception_handler(exc, context):
    """
    Extends DRF's default handler to also handle GeoAnalysisException subclasses.
    Returns JSON envelope: { "erro": "...", "detalhe": "..." }
    """
    response = exception_handler(exc, context)

    if response is not None:
        # Normalize DRF errors to our envelope
        data = response.data
        if isinstance(data, dict) and "detail" in data:
            response.data = {"erro": str(data["detail"]), "detalhe": None}
        else:
            response.data = {"erro": "Erro de validação.", "detalhe": data}
        return response

    if isinstance(exc, GeoAnalysisException):
        return Response(
            {"erro": exc.message, "detalhe": None},
            status=exc.status_code,
        )

    # Unexpected errors → 500
    return Response(
        {"erro": "Erro interno no servidor.", "detalhe": str(exc)},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
