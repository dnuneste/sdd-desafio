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


def validar_categoria_politica(
    despesa: DespesaInput,
    politica: "PoliticaReembolso",
) -> ResultadoDespesa | None:
    """RN-004 / AMB-003: Recusa categorias fora da política."""
    if not politica.categoria_elegivel(despesa.categoria_normalizada):
        return ResultadoDespesa(
            id=despesa.id,
            data=despesa.data.isoformat(),
            categoria_original=despesa.categoria_original,
            categoria_normalizada=despesa.categoria_normalizada,
            valor_original=despesa.valor_original,
            valor_reembolsado=Decimal("0.00"),
            valor_glosado=despesa.valor_original,
            status=StatusDespesa.RECUSADA,
            codigo_motivo=CodigoMotivo.CATEGORIA_NAO_REEMBOLSAVEL,
            justificativa=(
                f"Categoria '{despesa.categoria_original}' (normalizada: "
                f"'{despesa.categoria_normalizada}') nao faz parte da politica de reembolso (RN-004)."
            ),
        )
    return None


def obter_chave_duplicidade(despesa: DespesaInput) -> tuple[str, str, str, str, Decimal]:
    """Retorna a tupla de negócio para detecção de duplicatas (RN-006, AMB-004)."""
    return (
        despesa.data.isoformat(),
        despesa.categoria_normalizada,
        despesa.descricao_normalizada,
        despesa.fornecedor_normalizado,
        despesa.valor_original,
    )


def validar_duplicidade(
    despesa: DespesaInput,
    chaves_vistas: set[tuple[str, str, str, str, Decimal]],
) -> ResultadoDespesa | None:
    """RN-006 / AMB-004: Recusa ocorrências subsequentes de mesma tupla de negócio."""
    chave = obter_chave_duplicidade(despesa)
    if chave in chaves_vistas:
        return ResultadoDespesa(
            id=despesa.id,
            data=despesa.data.isoformat(),
            categoria_original=despesa.categoria_original,
            categoria_normalizada=despesa.categoria_normalizada,
            valor_original=despesa.valor_original,
            valor_reembolsado=Decimal("0.00"),
            valor_glosado=despesa.valor_original,
            status=StatusDespesa.RECUSADA,
            codigo_motivo=CodigoMotivo.DESPESA_DUPLICADA,
            justificativa=(
                f"Despesa duplicada detectada para data {despesa.data.isoformat()}, "
                f"categoria '{despesa.categoria_normalizada}', fornecedor '{despesa.fornecedor}' "
                f"e valor R$ {despesa.valor_original:.2f} (RN-006)."
            ),
        )
    chaves_vistas.add(chave)
    return None


def validar_nota_fiscal(
    despesa: DespesaInput,
    politica: "PoliticaReembolso",
) -> ResultadoDespesa | None:
    """RN-005 / AMB-002: Exige nota fiscal estritamente acima de R$ 100,00 (valor_original > 100.00)."""
    if despesa.valor_original > politica.limite_isencao_nota_fiscal and not despesa.tem_nota_fiscal:
        return ResultadoDespesa(
            id=despesa.id,
            data=despesa.data.isoformat(),
            categoria_original=despesa.categoria_original,
            categoria_normalizada=despesa.categoria_normalizada,
            valor_original=despesa.valor_original,
            valor_reembolsado=Decimal("0.00"),
            valor_glosado=despesa.valor_original,
            status=StatusDespesa.RECUSADA,
            codigo_motivo=CodigoMotivo.SEM_NOTA_FISCAL,
            justificativa=(
                f"Nota fiscal obrigatoria para despesas acima de "
                f"R$ {politica.limite_isencao_nota_fiscal:.2f} "
                f"(valor solicitado: R$ {despesa.valor_original:.2f}) (RN-005)."
            ),
        )
    return None
