"""Parâmetros da política de reembolso (RN-004, RN-005, RN-007, RN-008)."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Mapping

from src.models import arredondar_moeda


@dataclass(frozen=True)
class PoliticaReembolso:
    """Representação parametrizada da Política de Reembolso de Despesas — v3."""

    limites_diarios_base: Mapping[str, Decimal] = field(
        default_factory=lambda: {
            "alimentacao": Decimal("60.00"),
            "transporte_urbano": Decimal("80.00"),
            "hospedagem": Decimal("250.00"),
        }
    )
    categorias_ampliadas_em_viagem: frozenset[str] = field(
        default_factory=lambda: frozenset({"alimentacao", "transporte_urbano"})
    )
    fator_multiplicador_viagem: Decimal = Decimal("1.50")
    limite_isencao_nota_fiscal: Decimal = Decimal("100.00")
    dias_extensao_viagem_hospedagem: int = 1

    def categoria_elegivel(self, categoria_normalizada: str) -> bool:
        """Verifica se a categoria faz parte da política (RN-004)."""
        return categoria_normalizada in self.limites_diarios_base

    def obter_limite_diario(self, categoria_normalizada: str, em_viagem: bool) -> Decimal:
        """Retorna o limite diário da categoria considerando o regime de viagem (RN-007, RN-008)."""
        limite_base = self.limites_diarios_base[categoria_normalizada]
        if em_viagem and categoria_normalizada in self.categorias_ampliadas_em_viagem:
            return arredondar_moeda(limite_base * self.fator_multiplicador_viagem)
        return limite_base
