"""Testes de integração dos casos de borda da Seção 7 da spec e critérios de aceite CA-001 a CA-008 (T-006)."""

from datetime import date
from decimal import Decimal

import pytest

from src.engine import avaliar_relatorio
from src.io_handler import carregar_entrada_json
from src.models import (
    CodigoMotivo,
    Colaborador,
    DespesaInput,
    Periodo,
    StatusDespesa,
)


def test_ca_001_lote_referencia_despesas_exemplo() -> None:
    """Valida todos os 14 itens e o resumo consolidado de exemplos/despesas-exemplo.json (CA-001 a CA-008)."""
    colaborador, periodo, despesas = carregar_entrada_json("exemplos/despesas-exemplo.json")
    relatorio = avaliar_relatorio(colaborador, periodo, despesas)

    assert relatorio.em_viagem is True
    assert relatorio.resumo.quantidade_despesas == 14
    assert relatorio.resumo.quantidade_aprovadas == 4
    assert relatorio.resumo.quantidade_aprovadas_parcialmente == 4
    assert relatorio.resumo.quantidade_recusadas == 6

    assert relatorio.resumo.total_solicitado == Decimal("1962.84")
    assert relatorio.resumo.total_reembolsado == Decimal("585.43")
    assert relatorio.resumo.total_glosado == Decimal("1377.41")

    esperado = {
        "d-001": (StatusDespesa.APROVADA_PARCIALMENTE, CodigoMotivo.LIMITE_DIARIO_EXCEDIDO, Decimal("60.00"), Decimal("12.50")),
        "d-002": (StatusDespesa.RECUSADA, CodigoMotivo.LIMITE_DIARIO_EXCEDIDO, Decimal("0.00"), Decimal("38.00")),
        "d-003": (StatusDespesa.APROVADA_PARCIALMENTE, CodigoMotivo.LIMITE_DIARIO_EXCEDIDO, Decimal("80.00"), Decimal("20.00")),
        "d-004": (StatusDespesa.RECUSADA, CodigoMotivo.SEM_NOTA_FISCAL, Decimal("0.00"), Decimal("100.01")),
        "d-005": (StatusDespesa.RECUSADA, CodigoMotivo.CATEGORIA_NAO_REEMBOLSAVEL, Decimal("0.00"), Decimal("89.00")),
        "d-006": (StatusDespesa.APROVADA, CodigoMotivo.OK, Decimal("54.90"), Decimal("0.00")),
        "d-007": (StatusDespesa.RECUSADA, CodigoMotivo.DESPESA_DUPLICADA, Decimal("0.00"), Decimal("54.90")),
        "d-008": (StatusDespesa.RECUSADA, CodigoMotivo.FORA_PERIODO_COMPETENCIA, Decimal("0.00"), Decimal("41.00")),
        "d-009": (StatusDespesa.RECUSADA, CodigoMotivo.VALOR_INVALIDO, Decimal("0.00"), Decimal("0.00")),
        "d-010": (StatusDespesa.APROVADA_PARCIALMENTE, CodigoMotivo.LIMITE_DIARIO_EXCEDIDO, Decimal("250.00"), Decimal("230.00")),
        "d-011": (StatusDespesa.APROVADA, CodigoMotivo.OK, Decimal("33.33"), Decimal("0.00")),
        "d-012": (StatusDespesa.APROVADA, CodigoMotivo.OK, Decimal("47.20"), Decimal("0.00")),
        "d-013": (StatusDespesa.RECUSADA, CodigoMotivo.SEM_NOTA_FISCAL, Decimal("0.00"), Decimal("690.00")),
        "d-014": (StatusDespesa.APROVADA_PARCIALMENTE, CodigoMotivo.LIMITE_DIARIO_EXCEDIDO, Decimal("60.00"), Decimal("1.00")),
    }

    assert [r.id for r in relatorio.resultados] == list(esperado.keys())

    for res in relatorio.resultados:
        st_esp, cod_esp, reemb_esp, glosa_esp = esperado[res.id]
        assert res.status == st_esp, f"Falha de status em {res.id}"
        assert res.codigo_motivo == cod_esp, f"Falha de codigo_motivo em {res.id}"
        assert res.valor_reembolsado == reemb_esp, f"Falha de valor_reembolsado em {res.id}"
        assert res.valor_glosado == glosa_esp, f"Falha de valor_glosado em {res.id}"


def test_secao_8_precedencia_duplicata_nao_consome_saldo_diario() -> None:
    """Garante que uma duplicata recusada (RN-006) não consome o saldo diário restante para outra despesa legítima no mesmo dia."""
    colaborador = Colaborador(id="c-1", nome="Teste", centro_custo="CC-1")
    periodo = Periodo(competencia="2026-07", inicio=date(2026, 7, 1), fim=date(2026, 7, 31))

    despesas = [
        DespesaInput.criar("d-1", "2026-07-09", "alimentacao", "Almoco", "Bistro", "54.90", True),
        DespesaInput.criar("d-2", "2026-07-09", "alimentacao", "Almoco", "Bistro", "54.90", True),
        DespesaInput.criar("d-3", "2026-07-09", "alimentacao", "Cafe", "Padaria", "5.10", False),
    ]
    relatorio = avaliar_relatorio(colaborador, periodo, despesas)

    assert relatorio.resultados[0].status == StatusDespesa.APROVADA
    assert relatorio.resultados[0].valor_reembolsado == Decimal("54.90")

    assert relatorio.resultados[1].status == StatusDespesa.RECUSADA
    assert relatorio.resultados[1].codigo_motivo == CodigoMotivo.DESPESA_DUPLICADA
    assert relatorio.resultados[1].valor_reembolsado == Decimal("0.00")

    # Os R$ 5,10 restantes do limite de R$ 60,00 ainda estão disponíveis para d-3
    assert relatorio.resultados[2].status == StatusDespesa.APROVADA
    assert relatorio.resultados[2].valor_reembolsado == Decimal("5.10")


def test_secao_8_ordem_hospedagem_depois_de_alimentacao_no_mesmo_dia() -> None:
    """DT-001 / RN-007: Verifica que uma hospedagem válida lançada depois de alimentação no mesmo dia D ainda ativa o limite de viagem (+50%) para D."""
    colaborador = Colaborador(id="c-1", nome="Teste", centro_custo="CC-1")
    periodo = Periodo(competencia="2026-07", inicio=date(2026, 7, 1), fim=date(2026, 7, 31))

    despesas = [
        DespesaInput.criar("d-alim", "2026-07-14", "alimentacao", "Almoco viagem", "Restaurante", "85.00", True),
        DespesaInput.criar("d-hosp", "2026-07-14", "hospedagem", "Diaria hotel", "Hotel", "200.00", True),
    ]
    relatorio = avaliar_relatorio(colaborador, periodo, despesas)

    assert relatorio.em_viagem is True
    assert relatorio.resultados[0].status == StatusDespesa.APROVADA
    assert relatorio.resultados[0].valor_reembolsado == Decimal("85.00")
    assert relatorio.resultados[1].status == StatusDespesa.APROVADA
    assert relatorio.resultados[1].valor_reembolsado == Decimal("200.00")
