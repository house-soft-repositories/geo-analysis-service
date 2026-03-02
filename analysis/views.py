from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from layers.importers.kml_importer import extract_single_geometry
from .serializers import AnaliseOverlapSerializer
from .services.overlap_service import executar_analise, AnaliseParams


class AnaliseOverlapView(APIView):
    """
    POST /api/v1/analysis/overlap/

    Executa análise de sobreposição espacial de uma área de intervenção
    contra camadas de referência cadastradas no banco PostGIS.

    Body: multipart/form-data
      - kml_area  (file, obrigatório): KML/KMZ/GeoJSON/Shapefile da área
      - kml_imovel (file, opcional): KML do imóvel
      - uf        (str, opcional):  Sigla do estado (ex: SC)
      - checks    (list, opcional): Subset de checks a executar
      - slugs_camadas (list, opcional): Slugs de CamadasGenericas
      - tipos_ambientais (list, opcional): Subtipos ambientais (APP, etc.)

    Response 200:
    {
      "aprovado_geral": bool,
      "total_checks": int,
      "checks_reprovados": int,
      "checks": [
        {
          "nome": str,
          "aprovado": bool,
          "mensagem": str,
          "detalhes": object | null
        }
      ]
    }
    """

    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = AnaliseOverlapSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Parse KML da área de intervenção
        arquivo_area = request.FILES["kml_area"]
        geometria_area = extract_single_geometry(
            arquivo_area.read(),
            arquivo_area.name,
        )

        # Parse KML do imóvel (opcional)
        geometria_imovel = None
        if "kml_imovel" in request.FILES:
            arquivo_imovel = request.FILES["kml_imovel"]
            geometria_imovel = extract_single_geometry(
                arquivo_imovel.read(),
                arquivo_imovel.name,
            )

        params = AnaliseParams(
            geometria_area=geometria_area,
            geometria_imovel=geometria_imovel,
            uf=data.get("uf", ""),
            codigo_ibge=data.get("codigo_ibge", ""),
            checks=data.get("checks", []),
            slugs_camadas=data.get("slugs_camadas", []),
            tipos_ambientais=data.get("tipos_ambientais", []),
        )

        resultado = executar_analise(params)

        return Response(resultado.to_dict(), status=status.HTTP_200_OK)
