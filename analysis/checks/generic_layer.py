"""
Check: Sobreposição com camada genérica.

Verifica se a geometria de intervenção intersecta uma CamadaGenerica
identificada por slug. Também suporta checagem contra camadas ambientais
por tipo (APP, UNIDADE_CONSERVACAO, etc.).
"""
from typing import List

from django.contrib.gis.geos import GEOSGeometry

from layers.models import CamadaGenerica, CamadaAmbiental
from core.exceptions import LayerNotFoundError
from .base_check import BaseCheck, CheckResult


class CamadaGenericaCheck(BaseCheck):
    """
    Verifica sobreposição com uma CamadaGenerica por slug.

    Parâmetros:
        slug (str): Slug da camada de referência. Obrigatório.
    """

    NOME = "camada_generica"

    def run(self, geometry: GEOSGeometry, slug: str = "", **kwargs) -> CheckResult:
        if not slug:
            return CheckResult(
                nome=self.NOME,
                aprovado=False,
                mensagem="Parâmetro 'slug' não informado para check de camada genérica.",
            )

        try:
            camada = CamadaGenerica.objects.get(slug=slug)
        except CamadaGenerica.DoesNotExist:
            raise LayerNotFoundError(slug)

        intersecta = geometry.intersects(camada.geometry)

        if not intersecta:
            return CheckResult(
                nome=f"{self.NOME}:{slug}",
                aprovado=True,
                mensagem=f"Sem sobreposição com a camada '{slug}'.",
                detalhes={"slug": slug},
            )

        intersecao = geometry.intersection(camada.geometry)
        proporcao = (intersecao.area / geometry.area * 100) if geometry.area > 0 else 0

        return CheckResult(
            nome=f"{self.NOME}:{slug}",
            aprovado=False,
            mensagem=f"Sobreposição detectada com a camada '{slug}'.",
            detalhes={
                "slug": slug,
                "descricao": camada.descricao,
                "area_sobreposicao_graus2": round(intersecao.area, 8),
                "percentual_sobreposicao": round(proporcao, 2),
                "wkt_intersecao": intersecao.wkt if not intersecao.empty else None,
            },
        )


class TipoAmbientalCheck(BaseCheck):
    """
    Verifica sobreposição contra todas as CamadasAmbientais de um determinado tipo.

    Parâmetros:
        tipo_ambiental (str): Ex: 'APP', 'UNIDADE_CONSERVACAO'.
        uf (str): Filtra por UF. Opcional.
    """

    NOME = "tipo_ambiental"

    def run(self, geometry: GEOSGeometry, tipo_ambiental: str = "", uf: str = "", **kwargs) -> CheckResult:
        if not tipo_ambiental:
            return CheckResult(
                nome=self.NOME,
                aprovado=False,
                mensagem="Parâmetro 'tipo_ambiental' não informado.",
            )

        qs = CamadaAmbiental.objects.filter(tipo=tipo_ambiental)
        if uf:
            qs = qs.filter(uf__iexact=uf)

        camadas_sobrepostas = qs.filter(geometry__intersects=geometry)

        nome_check = f"{self.NOME}:{tipo_ambiental}"

        if not camadas_sobrepostas.exists():
            return CheckResult(
                nome=nome_check,
                aprovado=True,
                mensagem=f"Sem sobreposição com camadas do tipo '{tipo_ambiental}'.",
            )

        sobreposicoes = []
        for camada in camadas_sobrepostas:
            intersecao = geometry.intersection(camada.geometry)
            sobreposicoes.append({
                "id": camada.id,
                "nome": camada.nome,
                "codigo": camada.codigo,
                "area_sobreposicao_graus2": round(intersecao.area, 8),
            })

        return CheckResult(
            nome=nome_check,
            aprovado=False,
            mensagem=f"Sobreposição com {len(sobreposicoes)} camada(s) do tipo '{tipo_ambiental}'.",
            detalhes={"sobreposicoes": sobreposicoes},
        )
