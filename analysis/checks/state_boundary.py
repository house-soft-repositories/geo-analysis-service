"""
Check: Limite estadual/municipal.

Verifica se a geometria analisada está completamente contida dentro do
limite de um estado ou município. Se ultrapassar o limite, o check falha.
"""
from django.contrib.gis.geos import GEOSGeometry

from layers.models import CamadaEstadual
from .base_check import BaseCheck, CheckResult


class LimiteEstadualCheck(BaseCheck):
    """
    Verifica se a geometria está dentro do limite do estado.

    Parâmetros:
        uf (str): Sigla do estado (ex: 'SC'). Obrigatório.
        tipo_limite (str): 'ESTADO' ou 'MUNICIPIO'. Padrão: 'ESTADO'.
        nome_municipio (str): Nome do município (somente quando tipo_limite='MUNICIPIO').
    """

    NOME = "limite_estadual"

    def run(self, geometry: GEOSGeometry, uf: str = "", tipo_limite: str = "ESTADO", nome_municipio: str = "", **kwargs) -> CheckResult:
        if not uf:
            return CheckResult(
                nome=self.NOME,
                aprovado=False,
                mensagem="Parâmetro 'uf' não informado para verificação de limite estadual.",
            )

        filtros = {"uf__iexact": uf, "tipo": tipo_limite}
        if tipo_limite == "MUNICIPIO" and nome_municipio:
            filtros["nome__icontains"] = nome_municipio

        camadas = CamadaEstadual.objects.filter(**filtros)

        if not camadas.exists():
            return CheckResult(
                nome=self.NOME,
                aprovado=False,
                mensagem=f"Camada de limite não encontrada para UF='{uf}' tipo='{tipo_limite}'.",
            )

        # Une todos os polígonos do estado (pode haver múltiplos registros)
        limite = camadas.first().geometry
        for c in camadas[1:]:
            limite = limite.union(c.geometry)

        dentro = geometry.within(limite)

        if dentro:
            return CheckResult(
                nome=self.NOME,
                aprovado=True,
                mensagem=f"Geometria está dentro do limite do {'estado' if tipo_limite == 'ESTADO' else 'município'} {uf}.",
            )

        # Calcula área fora (em graus²; para area real usar projeção + área)
        area_fora = geometry.difference(limite)
        return CheckResult(
            nome=self.NOME,
            aprovado=False,
            mensagem=f"Geometria ultrapassa o limite do {'estado' if tipo_limite == 'ESTADO' else 'município'} {uf}.",
            detalhes={
                "area_fora_graus2": round(area_fora.area, 8) if not area_fora.empty else 0,
                "wkt_area_fora": area_fora.wkt if not area_fora.empty else None,
            },
        )
