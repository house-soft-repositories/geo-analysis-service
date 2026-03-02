"""
Checks de limite geográfico.

Verificam se a geometria analisada está completamente contida dentro
do limite de um estado ou município. Se ultrapassar o limite, o check falha.
"""
from django.contrib.gis.geos import GEOSGeometry

from layers.models import CamadaEstadual, CamadaMunicipal
from .base_check import BaseCheck, CheckResult


class LimiteEstadualCheck(BaseCheck):
    """
    Verifica se a geometria está dentro do limite estadual.

    Parâmetros:
        uf (str): Sigla do estado (ex: 'SC'). Obrigatório.
    """

    NOME = "limite_estadual"

    def run(self, geometry: GEOSGeometry, uf: str = "", **kwargs) -> CheckResult:
        if not uf:
            return CheckResult(
                nome=self.NOME,
                aprovado=False,
                mensagem="Parâmetro 'uf' não informado para verificação de limite estadual.",
            )

        try:
            camada = CamadaEstadual.objects.get(uf__iexact=uf)
        except CamadaEstadual.DoesNotExist:
            return CheckResult(
                nome=self.NOME,
                aprovado=False,
                mensagem=f"Camada estadual não encontrada para UF='{uf}'.",
            )

        dentro = geometry.within(camada.geometry)

        if dentro:
            return CheckResult(
                nome=self.NOME,
                aprovado=True,
                mensagem=f"Geometria está dentro do limite do estado {uf}.",
            )

        area_fora = geometry.difference(camada.geometry)
        return CheckResult(
            nome=self.NOME,
            aprovado=False,
            mensagem=f"Geometria ultrapassa o limite do estado {uf}.",
            detalhes={
                "area_fora_graus2": round(area_fora.area, 8) if not area_fora.empty else 0,
                "wkt_area_fora": area_fora.wkt if not area_fora.empty else None,
            },
        )


class LimiteMunicipalCheck(BaseCheck):
    """
    Verifica se a geometria está dentro do limite municipal.

    Parâmetros:
        codigo_ibge (str): Código IBGE do município com 7 dígitos. Obrigatório.
        uf (str): Sigla do estado. Usado apenas para mensagens de contexto.
    """

    NOME = "limite_municipal"

    def run(self, geometry: GEOSGeometry, codigo_ibge: str = "", uf: str = "", **kwargs) -> CheckResult:
        if not codigo_ibge:
            return CheckResult(
                nome=self.NOME,
                aprovado=False,
                mensagem="Parâmetro 'codigo_ibge' não informado para verificação de limite municipal.",
            )

        try:
            camada = CamadaMunicipal.objects.get(codigo_ibge=codigo_ibge)
        except CamadaMunicipal.DoesNotExist:
            return CheckResult(
                nome=self.NOME,
                aprovado=False,
                mensagem=f"Camada municipal não encontrada para código IBGE='{codigo_ibge}'.",
            )

        dentro = geometry.within(camada.geometry)

        if dentro:
            return CheckResult(
                nome=self.NOME,
                aprovado=True,
                mensagem=f"Geometria está dentro do limite do município {camada.nome}/{camada.uf} (IBGE: {codigo_ibge}).",
            )

        area_fora = geometry.difference(camada.geometry)
        return CheckResult(
            nome=self.NOME,
            aprovado=False,
            mensagem=f"Geometria ultrapassa o limite do município {camada.nome}/{camada.uf} (IBGE: {codigo_ibge}).",
            detalhes={
                "codigo_ibge": codigo_ibge,
                "nome_municipio": camada.nome,
                "uf": camada.uf,
                "area_fora_graus2": round(area_fora.area, 8) if not area_fora.empty else 0,
                "wkt_area_fora": area_fora.wkt if not area_fora.empty else None,
            },
        )
