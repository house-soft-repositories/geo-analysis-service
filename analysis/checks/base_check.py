"""
Interface base para todos os checks de sobreposição espacial.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from django.contrib.gis.geos import GEOSGeometry


@dataclass
class CheckResult:
    """
    Resultado de um check de análise espacial.

    Atributos:
        nome:         Identificador do check (snake_case).
        aprovado:     True se a geometria passou no critério (não viola a regra).
        mensagem:     Descrição humana do resultado.
        detalhes:     Dados extras opcionais (área de sobreposição, IDs de camadas, etc.).
    """

    nome: str
    aprovado: bool
    mensagem: str
    detalhes: Optional[Any] = field(default=None)

    def to_dict(self) -> dict:
        return {
            "nome": self.nome,
            "aprovado": self.aprovado,
            "mensagem": self.mensagem,
            "detalhes": self.detalhes,
        }


class BaseCheck:
    """
    Classe base abstrata para checks de análise espacial.

    Subclasses devem implementar o método `run(geometry)` e definir `NOME`.
    """

    NOME: str = "base_check"

    def run(self, geometry: GEOSGeometry, **kwargs) -> CheckResult:
        """
        Executa o check para a geometria fornecida.

        Args:
            geometry: GEOSGeometry (SRID 4326) a ser analisada.
            **kwargs: Parâmetros adicionais específicos do check.

        Returns:
            CheckResult com o resultado da análise.
        """
        raise NotImplementedError(f"O check '{self.__class__.__name__}' deve implementar o método run().")
