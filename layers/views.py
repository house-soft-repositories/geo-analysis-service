from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from .models import CamadaEstadual, CamadaAmbiental, CamadaGenerica
from .serializers import (
    CamadaEstadualSerializer,
    CamadaAmbientalSerializer,
    CamadaGenericaSerializer,
    ImportarCamadaSerializer,
)
from .importers.kml_importer import extract_multipolygon, extract_single_geometry
from django.contrib.gis.geos import GeometryCollection


class ListarCamadasView(APIView):
    """
    GET /api/v1/layers/
    Retorna todas as camadas registradas agrupadas por tipo.
    """

    def get(self, request):
        return Response({
            "estaduais": CamadaEstadualSerializer(CamadaEstadual.objects.all(), many=True).data,
            "ambientais": CamadaAmbientalSerializer(CamadaAmbiental.objects.all(), many=True).data,
            "genericas": CamadaGenericaSerializer(CamadaGenerica.objects.all(), many=True).data,
        })


class ImportarCamadaView(APIView):
    """
    POST /api/v1/layers/import/
    Importa uma camada de referência a partir de arquivo KML/KMZ/GeoJSON/Shapefile (ZIP).

    Corpo da requisição: multipart/form-data
      - arquivo: arquivo geoespacial
      - tipo: ESTADUAL | AMBIENTAL | GENERICA
      - (demais campos conforme tipo)
    """

    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = ImportarCamadaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        arquivo = request.FILES["arquivo"]
        file_content = arquivo.read()
        filename = arquivo.name
        tipo = data["tipo"]

        if tipo == "ESTADUAL":
            geom = extract_multipolygon(file_content, filename)
            camada = CamadaEstadual.objects.create(
                nome=data["nome"],
                uf=data["uf"].upper(),
                tipo=data.get("tipo_camada", "ESTADO"),
                geometry=geom,
                fonte=data.get("fonte", ""),
            )
            return Response(CamadaEstadualSerializer(camada).data, status=status.HTTP_201_CREATED)

        elif tipo == "AMBIENTAL":
            geom = extract_multipolygon(file_content, filename)
            camada = CamadaAmbiental.objects.create(
                nome=data["nome"],
                tipo=data.get("tipo_ambiental", "OUTRO"),
                codigo=data.get("codigo", ""),
                geometry=geom,
                fonte=data.get("fonte", ""),
                uf=data.get("uf", "").upper(),
            )
            return Response(CamadaAmbientalSerializer(camada).data, status=status.HTTP_201_CREATED)

        else:  # GENERICA
            geom = extract_single_geometry(file_content, filename)
            # Normalizar para GeometryCollection
            if geom.geom_type not in ("GeometryCollection",):
                geom = GeometryCollection(geom, srid=4326)

            camada, created = CamadaGenerica.objects.update_or_create(
                slug=data["slug"],
                defaults={
                    "descricao": data.get("descricao", data["slug"]),
                    "geometry": geom,
                },
            )
            return Response(
                CamadaGenericaSerializer(camada).data,
                status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
            )


class RemoverCamadaView(APIView):
    """
    DELETE /api/v1/layers/<tipo>/<id>/
    Remove uma camada de referência pelo tipo e ID.
    tipo: estadual | ambiental | generica
    """

    TIPO_MAP = {
        "estadual": CamadaEstadual,
        "ambiental": CamadaAmbiental,
        "generica": CamadaGenerica,
    }

    def delete(self, request, tipo: str, pk: int):
        model = self.TIPO_MAP.get(tipo.lower())
        if model is None:
            return Response({"erro": f"Tipo de camada inválido: '{tipo}'."}, status=404)

        try:
            camada = model.objects.get(pk=pk)
        except model.DoesNotExist:
            return Response({"erro": "Camada não encontrada."}, status=404)

        camada.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
