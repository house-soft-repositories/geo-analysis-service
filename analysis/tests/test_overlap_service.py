"""
Testes unitários para o serviço orquestrador de análise.

Executar: python manage.py test analysis.tests.test_overlap_service
"""
from unittest.mock import patch, MagicMock

from django.contrib.gis.geos import GEOSGeometry, MultiPolygon, Polygon
from django.test import TestCase

from analysis.services.overlap_service import (
    AnaliseParams,
    executar_analise,
    CHECK_LIMITE_ESTADUAL,
    CHECK_CONTENCAO_IMOVEL,
    CHECK_RESERVA_LEGAL,
)
from analysis.checks.base_check import CheckResult


def make_polygon(coords):
    return GEOSGeometry(Polygon(coords, srid=4326).wkt, srid=4326)


DENTRO_COORDS = [
    (-49.5, -26.5), (-49.0, -26.5), (-49.0, -26.0),
    (-49.5, -26.0), (-49.5, -26.5),
]


class OverlapServiceTest(TestCase):
    def test_sem_checks_retorna_aprovado_geral_true(self):
        geom = make_polygon(DENTRO_COORDS)
        params = AnaliseParams(
            geometria_area=geom,
            checks=[],
        )
        resultado = executar_analise(params)
        self.assertTrue(resultado.aprovado_geral)
        self.assertEqual(len(resultado.checks), 0)

    def test_to_dict_estrutura_correta(self):
        geom = make_polygon(DENTRO_COORDS)
        params = AnaliseParams(
            geometria_area=geom,
            checks=[],
        )
        resultado = executar_analise(params)
        d = resultado.to_dict()
        self.assertIn("aprovado_geral", d)
        self.assertIn("total_checks", d)
        self.assertIn("checks_reprovados", d)
        self.assertIn("checks", d)

    @patch("analysis.services.overlap_service.LimiteEstadualCheck")
    def test_limite_estadual_check_chamado_com_uf(self, MockCheck):
        mock_instance = MagicMock()
        mock_instance.run.return_value = CheckResult(
            nome=CHECK_LIMITE_ESTADUAL,
            aprovado=True,
            mensagem="OK",
        )
        MockCheck.return_value = mock_instance

        geom = make_polygon(DENTRO_COORDS)
        params = AnaliseParams(
            geometria_area=geom,
            checks=[CHECK_LIMITE_ESTADUAL],
            uf="SC",
        )
        resultado = executar_analise(params)

        mock_instance.run.assert_called_once_with(geom, uf="SC")
        self.assertEqual(len(resultado.checks), 1)
        self.assertTrue(resultado.aprovado_geral)

    @patch("analysis.services.overlap_service.ContencaoImovelCheck")
    def test_contencao_ignorada_sem_imovel(self, MockCheck):
        """Se geometria_imovel é None, o check de contenção não deve ser executado."""
        mock_instance = MagicMock()
        MockCheck.return_value = mock_instance

        geom = make_polygon(DENTRO_COORDS)
        params = AnaliseParams(
            geometria_area=geom,
            checks=[CHECK_CONTENCAO_IMOVEL],
            geometria_imovel=None,
        )
        resultado = executar_analise(params)

        mock_instance.run.assert_not_called()
        self.assertEqual(len(resultado.checks), 0)

    def test_aprovado_geral_false_quando_algum_check_reprova(self):
        """aprovado_geral deve ser False se pelo menos um check falhar."""
        from analysis.services.overlap_service import OverlapResult

        checks = [
            CheckResult(nome="a", aprovado=True, mensagem=""),
            CheckResult(nome="b", aprovado=False, mensagem=""),
        ]
        resultado = OverlapResult(checks=checks, aprovado_geral=False)
        d = resultado.to_dict()
        self.assertFalse(d["aprovado_geral"])
        self.assertEqual(d["checks_reprovados"], 1)
