"""
Testes unitários para o KML importer.

Executar: python manage.py test analysis.tests.test_importer
"""
from django.test import TestCase

from core.exceptions import KMLParseError, EmptyGeometryError


VALID_KML = b"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <Placemark>
      <name>Teste</name>
      <Polygon>
        <outerBoundaryIs>
          <LinearRing>
            <coordinates>
              -49.5,-26.5,0
              -49.0,-26.5,0
              -49.0,-26.0,0
              -49.5,-26.0,0
              -49.5,-26.5,0
            </coordinates>
          </LinearRing>
        </outerBoundaryIs>
      </Polygon>
    </Placemark>
  </Document>
</kml>"""

EMPTY_KML = b"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
  </Document>
</kml>"""

INVALID_CONTENT = b"isso nao e um kml valido"


class KMLImporterTest(TestCase):
    def test_kml_valido_retorna_geometria(self):
        from layers.importers.kml_importer import extract_single_geometry
        geom = extract_single_geometry(VALID_KML, "test.kml")
        self.assertIsNotNone(geom)
        self.assertFalse(geom.empty)
        self.assertEqual(geom.srid, 4326)

    def test_kml_vazio_lanca_empty_geometry_error(self):
        from layers.importers.kml_importer import extract_single_geometry
        with self.assertRaises(EmptyGeometryError):
            extract_single_geometry(EMPTY_KML, "empty.kml")

    def test_conteudo_invalido_lanca_kml_parse_error(self):
        from layers.importers.kml_importer import extract_single_geometry
        with self.assertRaises(KMLParseError):
            extract_single_geometry(INVALID_CONTENT, "invalid.txt")

    def test_kml_valido_retorna_multipolygon(self):
        from layers.importers.kml_importer import extract_multipolygon
        from django.contrib.gis.geos import MultiPolygon
        geom = extract_multipolygon(VALID_KML, "test.kml")
        self.assertIsInstance(geom, MultiPolygon)
