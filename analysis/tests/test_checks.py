"""
Testes unitários para os checks de sobreposição espacial.

Executar: python manage.py test analysis.tests.test_checks
"""
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon, Polygon, Point
from django.test import TestCase

from analysis.checks.base_check import CheckResult
from analysis.checks.state_boundary import LimiteEstadualCheck
from analysis.checks.property_containment import ContencaoImovelCheck
from analysis.checks.legal_reserve import ReservaLegalCheck
from analysis.checks.generic_layer import CamadaGenericaCheck, TipoAmbientalCheck
from layers.models import CamadaEstadual, CamadaAmbiental, CamadaGenerica, TipoCamadaAmbiental


def make_polygon(coords) -> GEOSGeometry:
    """Cria um Polygon a partir de lista de (lon, lat)."""
    return GEOSGeometry(
        Polygon(coords, srid=4326).wkt,
        srid=4326,
    )


def make_multipolygon(coords) -> MultiPolygon:
    return MultiPolygon(Polygon(coords, srid=4326), srid=4326)


# Polígono "estado" fictício cobrindo área ampla
ESTADO_COORDS = [
    (-50.0, -27.0),
    (-48.0, -27.0),
    (-48.0, -25.0),
    (-50.0, -25.0),
    (-50.0, -27.0),
]

# Polígono dentro do estado
DENTRO_COORDS = [
    (-49.5, -26.5),
    (-49.0, -26.5),
    (-49.0, -26.0),
    (-49.5, -26.0),
    (-49.5, -26.5),
]

# Polígono fora do estado
FORA_COORDS = [
    (-55.0, -30.0),
    (-54.0, -30.0),
    (-54.0, -29.0),
    (-55.0, -29.0),
    (-55.0, -30.0),
]

# Polígono imóvel
IMOVEL_COORDS = [
    (-49.4, -26.4),
    (-49.1, -26.4),
    (-49.1, -26.1),
    (-49.4, -26.1),
    (-49.4, -26.4),
]

# Polígono menor que o imóvel (dentro)
DENTRO_IMOVEL_COORDS = [
    (-49.35, -26.35),
    (-49.15, -26.35),
    (-49.15, -26.15),
    (-49.35, -26.15),
    (-49.35, -26.35),
]

# Polígono que extrapola o imóvel
FORA_IMOVEL_COORDS = [
    (-49.6, -26.6),
    (-49.0, -26.6),
    (-49.0, -26.0),
    (-49.6, -26.0),
    (-49.6, -26.6),
]


class LimiteEstadualCheckTest(TestCase):
    def setUp(self):
        self.estado = CamadaEstadual.objects.create(
            nome="Estado Fictício",
            uf="XX",
            tipo="ESTADO",
            geometry=make_multipolygon(ESTADO_COORDS),
            fonte="Teste",
        )
        self.check = LimiteEstadualCheck()

    def test_geometria_dentro_do_estado_aprovado(self):
        geom = make_polygon(DENTRO_COORDS)
        resultado = self.check.run(geom, uf="XX")
        self.assertTrue(resultado.aprovado)
        self.assertEqual(resultado.nome, "limite_estadual")

    def test_geometria_fora_do_estado_reprovado(self):
        geom = make_polygon(FORA_COORDS)
        resultado = self.check.run(geom, uf="XX")
        self.assertFalse(resultado.aprovado)
        self.assertIsNotNone(resultado.detalhes)

    def test_sem_uf_reprovado(self):
        geom = make_polygon(DENTRO_COORDS)
        resultado = self.check.run(geom, uf="")
        self.assertFalse(resultado.aprovado)

    def test_uf_inexistente_reprovado(self):
        geom = make_polygon(DENTRO_COORDS)
        resultado = self.check.run(geom, uf="ZZ")
        self.assertFalse(resultado.aprovado)


class ContencaoImovelCheckTest(TestCase):
    def setUp(self):
        self.check = ContencaoImovelCheck()
        self.imovel = make_polygon(IMOVEL_COORDS)

    def test_area_dentro_do_imovel_aprovado(self):
        area = make_polygon(DENTRO_IMOVEL_COORDS)
        resultado = self.check.run(area, geometria_imovel=self.imovel)
        self.assertTrue(resultado.aprovado)

    def test_area_fora_do_imovel_reprovado(self):
        area = make_polygon(FORA_IMOVEL_COORDS)
        resultado = self.check.run(area, geometria_imovel=self.imovel)
        self.assertFalse(resultado.aprovado)
        self.assertIn("percentual_fora", resultado.detalhes)

    def test_sem_imovel_reprovado(self):
        area = make_polygon(DENTRO_IMOVEL_COORDS)
        resultado = self.check.run(area, geometria_imovel=None)
        self.assertFalse(resultado.aprovado)


class ReservaLegalCheckTest(TestCase):
    def setUp(self):
        self.check = ReservaLegalCheck()
        # Reserva dentro da área de intervenção
        self.reserva = CamadaAmbiental.objects.create(
            nome="Reserva Legal Teste",
            tipo=TipoCamadaAmbiental.RESERVA_LEGAL,
            codigo="RL-TEST",
            geometry=make_multipolygon(DENTRO_COORDS),
            uf="XX",
        )

    def test_sem_sobreposicao_aprovado(self):
        area = make_polygon(FORA_COORDS)
        resultado = self.check.run(area, uf="XX")
        self.assertTrue(resultado.aprovado)

    def test_com_sobreposicao_reprovado(self):
        area = make_polygon(DENTRO_COORDS)
        resultado = self.check.run(area, uf="XX")
        self.assertFalse(resultado.aprovado)
        self.assertIn("sobreposicoes", resultado.detalhes)
        self.assertEqual(len(resultado.detalhes["sobreposicoes"]), 1)
        self.assertEqual(resultado.detalhes["sobreposicoes"][0]["codigo"], "RL-TEST")

    def test_sem_reservas_cadastradas_aprovado(self):
        CamadaAmbiental.objects.all().delete()
        area = make_polygon(DENTRO_COORDS)
        resultado = self.check.run(area, uf="XX")
        self.assertTrue(resultado.aprovado)


class CamadaGenericaCheckTest(TestCase):
    def setUp(self):
        from django.contrib.gis.geos import GeometryCollection
        self.check = CamadaGenericaCheck()
        self.camada = CamadaGenerica.objects.create(
            slug="apa-teste",
            descricao="APA de Teste",
            geometry=GeometryCollection(
                Polygon(DENTRO_COORDS, srid=4326),
                srid=4326,
            ),
        )

    def test_sem_sobreposicao_aprovado(self):
        area = make_polygon(FORA_COORDS)
        resultado = self.check.run(area, slug="apa-teste")
        self.assertTrue(resultado.aprovado)

    def test_com_sobreposicao_reprovado(self):
        area = make_polygon(DENTRO_COORDS)
        resultado = self.check.run(area, slug="apa-teste")
        self.assertFalse(resultado.aprovado)
        self.assertIn("percentual_sobreposicao", resultado.detalhes)

    def test_slug_inexistente_lanca_excecao(self):
        from core.exceptions import LayerNotFoundError
        area = make_polygon(DENTRO_COORDS)
        with self.assertRaises(LayerNotFoundError):
            self.check.run(area, slug="nao-existe")

    def test_sem_slug_reprovado(self):
        area = make_polygon(DENTRO_COORDS)
        resultado = self.check.run(area, slug="")
        self.assertFalse(resultado.aprovado)


class CheckResultTest(TestCase):
    def test_to_dict(self):
        result = CheckResult(
            nome="test_check",
            aprovado=True,
            mensagem="OK",
            detalhes={"extra": 1},
        )
        d = result.to_dict()
        self.assertIn("nome", d)
        self.assertIn("aprovado", d)
        self.assertIn("mensagem", d)
        self.assertIn("detalhes", d)
        self.assertTrue(d["aprovado"])
