"""
Check: Contenção no imóvel.

Verifica se a área de intervenção está completamente contida dentro do
polígono do imóvel (passado como segundo KML na requisição).
"""
from typing import Optional

from django.contrib.gis.geos import GEOSGeometry

from .base_check import BaseCheck, CheckResult


class ContencaoImovelCheck(BaseCheck):
    """
    Verifica se a geometria de intervenção está contida no imóvel.

    Parâmetros:
        geometria_imovel (GEOSGeometry): Geometria do imóvel. Obrigatório.
    """

    NOME = "contencao_imovel"

    def run(self, geometry: GEOSGeometry, geometria_imovel: Optional[GEOSGeometry] = None, **kwargs) -> CheckResult:
        if geometria_imovel is None:
            return CheckResult(
                nome=self.NOME,
                aprovado=False,
                mensagem="Geometria do imóvel não fornecida para o check de contenção.",
            )

        contido = geometry.within(geometria_imovel)

        if contido:
            return CheckResult(
                nome=self.NOME,
                aprovado=True,
                mensagem="Área de intervenção está completamente contida no imóvel.",
            )

        area_fora = geometry.difference(geometria_imovel)
        # Área da sobreposição (porção que está fora do imóvel)
        proporcao_fora = (area_fora.area / geometry.area * 100) if geometry.area > 0 else 0

        return CheckResult(
            nome=self.NOME,
            aprovado=False,
            mensagem="Área de intervenção extrapola os limites do imóvel.",
            detalhes={
                "area_total_graus2": round(geometry.area, 8),
                "area_fora_graus2": round(area_fora.area, 8),
                "percentual_fora": round(proporcao_fora, 2),
                "wkt_area_fora": area_fora.wkt if not area_fora.empty else None,
            },
        )
