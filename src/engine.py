"""Motor puro de avaliação das regras de reembolso (RN-002 a RN-008)."""

from __future__ import annotations

from decimal import Decimal

from src.models import (
    CodigoMotivo,
    DespesaInput,
    Periodo,
    ResultadoDespesa,
    StatusDespesa,
)


def validar_valor_positivo(despesa: DespesaInput) -> ResultadoDespesa | None:
    """RN-002 / AMB-006: Recusa despesas com valor_original <= 0.00 (estornos, negativos ou zero)."""
    if despesa.valor_original <= Decimal("0.00"):
        return ResultadoDespesa(
            id=despesa.id,
            data=despesa.data.isoformat(),
            categoria_original=despesa.categoria_original,
            categoria_normalizada=despesa.categoria_normalizada,
            valor_original=despesa.valor_original,
            valor_reembolsado=Decimal("0.00"),
            valor_glosado=Decimal("0.00"),
            status=StatusDespesa.RECUSADA,
            codigo_motivo=CodigoMotivo.VALOR_INVALIDO,
            justificativa=(
                f"Despesa com valor nao positivo (R$ {despesa.valor_original:.2f}) "
                "nao e elegivel a reembolso (RN-002)."
            ),
        )
    return None


def validar_periodo_competencia(despesa: DespesaInput, periodo: Periodo) -> ResultadoDespesa | None:
    """RN-003 / AMB-005 / AMB-010: Valida se a data da despesa pertence a [periodo.inicio, periodo.fim]."""
    if despesa.data < periodo.inicio or despesa.data > periodo.fim:
        return ResultadoDespesa(
            id=despesa.id,
            data=despesa.data.isoformat(),
            categoria_original=despesa.categoria_original,
            categoria_normalizada=despesa.categoria_normalizada,
            valor_original=despesa.valor_original,
            valor_reembolsado=Decimal("0.00"),
            valor_glosado=despesa.valor_original,
            status=StatusDespesa.RECUSADA,
            codigo_motivo=CodigoMotivo.FORA_PERIODO_COMPETENCIA,
            justificativa=(
                f"Data da despesa ({despesa.data.isoformat()}) esta fora do periodo de "
                f"competencia [{periodo.inicio.isoformat()} a {periodo.fim.isoformat()}] (RN-003)."
            ),
        )
    return None
