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


def apurar_datas_em_viagem(
    colaborador: "Colaborador",
    despesas_elegiveis: list[DespesaInput],
    politica: "PoliticaReembolso",
) -> set["date"]:
    """RN-007 / AMB-007 / AMB-008: Determina as datas cobertas pelo regime de viagem."""
    from datetime import timedelta

    datas_viagem: set["date"] = set()
    if colaborador.em_viagem:
        for d in despesas_elegiveis:
            datas_viagem.add(d.data)

    for d in despesas_elegiveis:
        if d.em_viagem:
            datas_viagem.add(d.data)
        if d.categoria_normalizada == "hospedagem":
            for offset in range(politica.dias_extensao_viagem_hospedagem + 1):
                datas_viagem.add(d.data + timedelta(days=offset))

    return datas_viagem


def aplicar_limite_diario(
    despesa: DespesaInput,
    saldos_diarios: dict[tuple["date", str], Decimal],
    em_viagem_na_data: bool,
    politica: "PoliticaReembolso",
) -> ResultadoDespesa:
    """RN-008 / AMB-001: Consome o saldo diário cumulativo e calcula reembolso total, parcial ou recusa."""
    chave_saldo = (despesa.data, despesa.categoria_normalizada)
    limite_dia = politica.obter_limite_diario(despesa.categoria_normalizada, em_viagem_na_data)
    if chave_saldo not in saldos_diarios:
        saldos_diarios[chave_saldo] = limite_dia

    saldo_atual = saldos_diarios[chave_saldo]

    if despesa.valor_original <= saldo_atual:
        saldos_diarios[chave_saldo] = saldo_atual - despesa.valor_original
        return ResultadoDespesa(
            id=despesa.id,
            data=despesa.data.isoformat(),
            categoria_original=despesa.categoria_original,
            categoria_normalizada=despesa.categoria_normalizada,
            valor_original=despesa.valor_original,
            valor_reembolsado=despesa.valor_original,
            valor_glosado=Decimal("0.00"),
            status=StatusDespesa.APROVADA,
            codigo_motivo=CodigoMotivo.OK,
            justificativa=(
                f"Despesa aprovada integralmente dentro do limite diario de "
                f"R$ {limite_dia:.2f} da categoria '{despesa.categoria_normalizada}' (RN-008)."
            ),
        )

    if saldo_atual > Decimal("0.00"):
        reembolsado = saldo_atual
        glosado = despesa.valor_original - reembolsado
        saldos_diarios[chave_saldo] = Decimal("0.00")
        return ResultadoDespesa(
            id=despesa.id,
            data=despesa.data.isoformat(),
            categoria_original=despesa.categoria_original,
            categoria_normalizada=despesa.categoria_normalizada,
            valor_original=despesa.valor_original,
            valor_reembolsado=reembolsado,
            valor_glosado=glosado,
            status=StatusDespesa.APROVADA_PARCIALMENTE,
            codigo_motivo=CodigoMotivo.LIMITE_DIARIO_EXCEDIDO,
            justificativa=(
                f"Despesa excede o saldo diario da categoria '{despesa.categoria_normalizada}' "
                f"(limite R$ {limite_dia:.2f}). Reembolso parcial de R$ {reembolsado:.2f}; "
                f"excedente glosado de R$ {glosado:.2f} (RN-008)."
            ),
        )

    return ResultadoDespesa(
        id=despesa.id,
        data=despesa.data.isoformat(),
        categoria_original=despesa.categoria_original,
        categoria_normalizada=despesa.categoria_normalizada,
        valor_original=despesa.valor_original,
        valor_reembolsado=Decimal("0.00"),
        valor_glosado=despesa.valor_original,
        status=StatusDespesa.RECUSADA,
        codigo_motivo=CodigoMotivo.LIMITE_DIARIO_EXCEDIDO,
        justificativa=(
            f"Limite diario da categoria '{despesa.categoria_normalizada}' "
            f"(R$ {limite_dia:.2f}) ja totalmente consumido na data {despesa.data.isoformat()} (RN-008)."
        ),
    )


def avaliar_relatorio(
    colaborador: "Colaborador",
    periodo: Periodo,
    despesas: list[DespesaInput],
    politica: "PoliticaReembolso | None" = None,
) -> "RelatorioReembolso":
    """Executa o pipeline completo de avaliação em duas passagens conforme Seção 8 da spec e DT-001."""
    from datetime import date
    from src.models import RelatorioReembolso, ResumoProcessamento
    from src.policy import PoliticaReembolso as PoliticaPadrao

    pol = politica or PoliticaPadrao()

    resultados_parciais: dict[int, ResultadoDespesa] = {}
    despesas_elegiveis: list[tuple[int, DespesaInput]] = []
    chaves_vistas: set[tuple[str, str, str, str, Decimal]] = set()

    # Passagem 1 — Validação de elegibilidade individual na ordem estrita da Seção 8 da spec
    for idx, despesa in enumerate(despesas):
        res = (
            validar_valor_positivo(despesa)
            or validar_periodo_competencia(despesa, periodo)
            or validar_categoria_politica(despesa, pol)
            or validar_duplicidade(despesa, chaves_vistas)
            or validar_nota_fiscal(despesa, pol)
        )
        if res is not None:
            resultados_parciais[idx] = res
        else:
            despesas_elegiveis.append((idx, despesa))

    # Passagem 2 — Apuração de datas em viagem (RN-007) e aplicação de limites diários (RN-008)
    datas_viagem = apurar_datas_em_viagem(
        colaborador=colaborador,
        despesas_elegiveis=[d for _, d in despesas_elegiveis],
        politica=pol,
    )

    saldos_diarios: dict[tuple[date, str], Decimal] = {}
    for idx, despesa in despesas_elegiveis:
        em_viagem_na_data = colaborador.em_viagem or despesa.em_viagem or (despesa.data in datas_viagem)
        resultados_parciais[idx] = aplicar_limite_diario(
            despesa=despesa,
            saldos_diarios=saldos_diarios,
            em_viagem_na_data=em_viagem_na_data,
            politica=pol,
        )

    resultados_finais = [resultados_parciais[i] for i in range(len(despesas))]

    total_solicitado = sum(
        (d.valor_original for d in despesas if d.valor_original > Decimal("0.00")),
        start=Decimal("0.00"),
    )
    total_reembolsado = sum(
        (r.valor_reembolsado for r in resultados_finais),
        start=Decimal("0.00"),
    )
    total_glosado = total_solicitado - total_reembolsado

    qtd_aprovadas = sum(1 for r in resultados_finais if r.status == StatusDespesa.APROVADA)
    qtd_parciais = sum(
        1 for r in resultados_finais if r.status == StatusDespesa.APROVADA_PARCIALMENTE
    )
    qtd_recusadas = sum(1 for r in resultados_finais if r.status == StatusDespesa.RECUSADA)

    resumo = ResumoProcessamento(
        total_solicitado=total_solicitado,
        total_reembolsado=total_reembolsado,
        total_glosado=total_glosado,
        quantidade_despesas=len(despesas),
        quantidade_aprovadas=qtd_aprovadas,
        quantidade_aprovadas_parcialmente=qtd_parciais,
        quantidade_recusadas=qtd_recusadas,
    )

    return RelatorioReembolso(
        colaborador=colaborador,
        periodo=periodo,
        em_viagem=bool(datas_viagem) or colaborador.em_viagem,
        resumo=resumo,
        resultados=resultados_finais,
    )
