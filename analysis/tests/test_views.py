"""
Testes de integração para o endpoint POST /api/v1/analysis/overlap/.

Executar: python manage.py test analysis.tests.test_views
"""
from io import BytesIO

from django.contrib.gis.geos import MultiPolygon, Polygon
from django.test import TestCase, override_settings
from django.urls import reverse

from layers.models import CamadaEstadual


VALID_KML = b"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <Placemark>
      <Polygon>
        <outerBoundaryIs>
          <LinearRing>
            <coordinates>
              -49.5,-26.5,0 -49.0,-26.5,0 -49.0,-26.0,0
              -49.5,-26.0,0 -49.5,-26.5,0
            </coordinates>
          </LinearRing>
        </outerBoundaryIs>
      </Polygon>
    </Placemark>
  </Document>
</kml>"""


@override_settings(
    REST_FRAMEWORK={
        "DEFAULT_AUTHENTICATION_CLASSES": ["core.authentication.ApiKeyAuthentication"],
        "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
        "EXCEPTION_HANDLER": "core.exceptions.custom_exception_handler",
    },
    GEO_API_KEY="test-api-key",
)
class AnalyzeOverlapViewTest(TestCase):
    def setUp(self):
        self.headers = {"HTTP_X_API_KEY": "test-api-key"}
        # Cadastra estado de teste
        CamadaEstadual.objects.create(
            nome="Estado Teste",
            uf="XX",
            tipo="ESTADO",
            geometry=MultiPolygon(
                Polygon([
                    (-50.0, -27.0), (-48.0, -27.0),
                    (-48.0, -25.0), (-50.0, -25.0), (-50.0, -27.0),
                ], srid=4326),
                srid=4326,
            ),
        )

    def test_sem_api_key_retorna_401(self):
        response = self.client.post("/api/v1/analysis/overlap/")
        self.assertEqual(response.status_code, 401)

    def test_sem_kml_area_retorna_400(self):
        response = self.client.post(
            "/api/v1/analysis/overlap/",
            data={},
            **self.headers,
        )
        self.assertIn(response.status_code, [400, 422])

    def test_resultado_com_kml_valido(self):
        response = self.client.post(
            "/api/v1/analysis/overlap/",
            data={
                "kml_area": BytesIO(VALID_KML),
                "uf": "XX",
                "checks": ["limite_estadual"],
            },
            format="multipart",
            **self.headers,
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("aprovado_geral", data)
        self.assertIn("checks", data)
        self.assertTrue(isinstance(data["checks"], list))

    def test_health_sem_autenticacao(self):
        response = self.client.get("/api/v1/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")
