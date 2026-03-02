"""
Serviço orquestrador de análise de sobreposição.

Recebe uma GEOSGeometry (área de intervenção) e os parâmetros de análise,
executa os checks selecionados e retorna um OverlapResult agregado.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from django.contrib.gis.geos import GEOSGeometry

from analysis.checks.base_check import CheckResult
from analysis.checks.state_boundary import LimiteEstadualCheck
from analysis.checks.property_containment import ContencaoImovelCheck
from analysis.checks.legal_reserve import ReservaLegalCheck
from analysis.checks.generic_layer import CamadaGenericaCheck, TipoAmbientalCheck


# Identificadores dos checks disponíveis
CHECK_LIMITE_ESTADUAL = "limite_estadual"
CHECK_CONTENCAO_IMOVEL = "contencao_imovel"
CHECK_RESERVA_LEGAL = "reserva_legal"
CHECK_CAMADA_GENERICA = "camada_generica"
CHECK_TIPO_AMBIENTAL = "tipo_ambiental"

ALL_CHECKS = [
    CHECK_LIMITE_ESTADUAL,
    CHECK_CONTENCAO_IMOVEL,
    CHECK_RESERVA_LEGAL,
    CHECK_CAMADA_GENERICA,
    CHECK_TIPO_AMBIENTAL,
]


@dataclass
class AnaliseParams:
    """Parâmetros de entrada para a análise de sobreposição."""

    geometria_area: GEOSGeometry
    geometria_imovel: Optional[GEOSGeometry] = None
    uf: str = ""
    checks: List[str] = field(default_factory=lambda: list(ALL_CHECKS))
    slugs_camadas: List[str] = field(default_factory=list)
    tipos_ambientais: List[str] = field(default_factory=list)


@dataclass
class OverlapResult:
    """Resultado agregado da análise de sobreposição."""

    checks: List[CheckResult]
    aprovado_geral: bool

    def to_dict(self) -> dict:
        return {
            "aprovado_geral": self.aprovado_geral,
            "total_checks": len(self.checks),
            "checks_reprovados": sum(1 for c in self.checks if not c.aprovado),
            "checks": [c.to_dict() for c in self.checks],
        }


def executar_analise(params: AnaliseParams) -> OverlapResult:
    """
    Executa todos os checks selecionados e retorna OverlapResult.

    Ordem de execução:
    1. Limite estadual/municipal
    2. Contenção no imóvel
    3. Reserva Legal
    4. Camadas genéricas (uma por slug)
    5. Tipos ambientais (um por tipo)
    """
    resultados: List[CheckResult] = []
    checks_solicitados = set(params.checks)

    # 1. Limite estadual
    if CHECK_LIMITE_ESTADUAL in checks_solicitados and params.uf:
        check = LimiteEstadualCheck()
        resultados.append(check.run(params.geometria_area, uf=params.uf))

    # 2. Contenção no imóvel
    if CHECK_CONTENCAO_IMOVEL in checks_solicitados:
        if params.geometria_imovel is not None:
            check = ContencaoImovelCheck()
            resultados.append(check.run(params.geometria_area, geometria_imovel=params.geometria_imovel))

    # 3. Reserva Legal
    if CHECK_RESERVA_LEGAL in checks_solicitados:
        check = ReservaLegalCheck()
        resultados.append(check.run(params.geometria_area, uf=params.uf))

    # 4. Camadas genéricas — uma execução por slug
    if CHECK_CAMADA_GENERICA in checks_solicitados:
        for slug in params.slugs_camadas:
            check = CamadaGenericaCheck()
            resultados.append(check.run(params.geometria_area, slug=slug))

    # 5. Tipos ambientais (APP, UNIDADE_CONSERVACAO, etc.)
    if CHECK_TIPO_AMBIENTAL in checks_solicitados:
        for tipo in params.tipos_ambientais:
            check = TipoAmbientalCheck()
            resultados.append(check.run(params.geometria_area, tipo_ambiental=tipo, uf=params.uf))

    aprovado_geral = all(r.aprovado for r in resultados)

    return OverlapResult(checks=resultados, aprovado_geral=aprovado_geral)
