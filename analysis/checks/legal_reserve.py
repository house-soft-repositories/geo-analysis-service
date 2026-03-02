"""
Check: Sobreposição com Reserva Legal.

Verifica se a geometria de intervenção intersecta alguma camada de
Reserva Legal (CamadaAmbiental com tipo=RESERVA_LEGAL) carregadas no banco.
"""
from django.contrib.gis.geos import GEOSGeometry

from layers.models import CamadaAmbiental, TipoCamadaAmbiental
from .base_check import BaseCheck, CheckResult


class ReservaLegalCheck(BaseCheck):
    """
    Verifica sobreposição com Reservas Legais cadastradas.

    Parâmetros:
        uf (str): Filtra somente camadas da UF informada. Opcional.
    """

    NOME = "reserva_legal"

    def run(self, geometry: GEOSGeometry, uf: str = "", **kwargs) -> CheckResult:
        qs = CamadaAmbiental.objects.filter(tipo=TipoCamadaAmbiental.RESERVA_LEGAL)
        if uf:
            qs = qs.filter(uf__iexact=uf)

        # Consulta espacial via PostGIS — muito mais eficiente que iterar em Python
        camadas_sobrepostas = qs.filter(geometry__intersects=geometry)

        if not camadas_sobrepostas.exists():
            return CheckResult(
                nome=self.NOME,
                aprovado=True,
                mensagem="Sem sobreposição com Reservas Legais cadastradas.",
            )

        sobreposicoes = []
        for camada in camadas_sobrepostas:
            intersecao = geometry.intersection(camada.geometry)
            sobreposicoes.append({
                "id": camada.id,
                "nome": camada.nome,
                "codigo": camada.codigo,
                "area_sobreposicao_graus2": round(intersecao.area, 8),
                "wkt_intersecao": intersecao.wkt if not intersecao.empty else None,
            })

        return CheckResult(
            nome=self.NOME,
            aprovado=False,
            mensagem=f"Sobreposição com {len(sobreposicoes)} Reserva(s) Legal(is).",
            detalhes={"sobreposicoes": sobreposicoes},
        )
