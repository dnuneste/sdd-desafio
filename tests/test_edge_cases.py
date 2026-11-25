"""Testes de integração dos casos de borda da Seção 7 da spec e critérios de aceite CA-001 a CA-010 (T-006, T-010)."""

from datetime import date
from decimal import Decimal

from src.engine import avaliar_relatorio
from src.io_handler import carregar_cambio_json, carregar_entrada_json, carregar_politica_json
from src.models import (
    CodigoMotivo,
    Colaborador,
    DespesaInput,
    Periodo,
    StatusDespesa,
)


def test_ca_001_lote_referencia_despesas_exemplo() -> None:
    """Valida exemplos/despesas-exemplo.json (CC-ENG-PLATAFORMA) sob vigência retroativa da Política v4 (CA-001, AMB-016)."""
    colaborador, periodo, despesas = carregar_entrada_json("exemplos/despesas-exemplo.json")
    politica = carregar_politica_json("exemplos/Envelope/politica-v4.json")
    cambio = carregar_cambio_json("exemplos/Envelope/cambio.json")

    relatorio = avaliar_relatorio(colaborador, periodo, despesas, politica=politica, cambio=cambio)

    # Em CC-ENG-PLATAFORMA sob a v4, hospedagem (d-010) tem limite 0.00 (CATEGORIA_NAO_REEMBOLSAVEL), logo não ativa viagem
    assert relatorio.em_viagem is False
    assert relatorio.resumo.quantidade_despesas == 14
    assert relatorio.resumo.quantidade_aprovadas == 5
    assert relatorio.resumo.quantidade_aprovadas_parcialmente == 2
    assert relatorio.resumo.quantidade_recusadas == 7

    assert relatorio.resumo.total_solicitado == Decimal("1861.84")
    assert relatorio.resumo.total_reembolsado == Decimal("351.43")
    assert relatorio.resumo.total_glosado == Decimal("1510.41")

    esperado = {
        "d-001": (StatusDespesa.APROVADA, CodigoMotivo.OK, Decimal("72.50"), Decimal("0.00")),
        "d-002": (StatusDespesa.APROVADA_PARCIALMENTE, CodigoMotivo.LIMITE_DIARIO_EXCEDIDO, Decimal("2.50"), Decimal("35.50")),
        "d-003": (StatusDespesa.APROVADA_PARCIALMENTE, CodigoMotivo.LIMITE_DIARIO_EXCEDIDO, Decimal("80.00"), Decimal("20.00")),
        "d-004": (StatusDespesa.RECUSADA, CodigoMotivo.SEM_NOTA_FISCAL, Decimal("0.00"), Decimal("100.01")),
        "d-005": (StatusDespesa.RECUSADA, CodigoMotivo.CATEGORIA_NAO_REEMBOLSAVEL, Decimal("0.00"), Decimal("89.00")),
        "d-006": (StatusDespesa.APROVADA, CodigoMotivo.OK, Decimal("54.90"), Decimal("0.00")),
        "d-007": (StatusDespesa.RECUSADA, CodigoMotivo.DESPESA_DUPLICADA, Decimal("0.00"), Decimal("54.90")),
        "d-008": (StatusDespesa.RECUSADA, CodigoMotivo.FORA_PERIODO_COMPETENCIA, Decimal("0.00"), Decimal("41.00")),
        "d-009": (StatusDespesa.RECUSADA, CodigoMotivo.VALOR_INVALIDO, Decimal("0.00"), Decimal("0.00")),
        "d-010": (StatusDespesa.RECUSADA, CodigoMotivo.CATEGORIA_NAO_REEMBOLSAVEL, Decimal("0.00"), Decimal("480.00")),
        "d-011": (StatusDespesa.APROVADA, CodigoMotivo.OK, Decimal("33.33"), Decimal("0.00")),
        "d-012": (StatusDespesa.APROVADA, CodigoMotivo.OK, Decimal("47.20"), Decimal("0.00")),
        "d-013": (StatusDespesa.RECUSADA, CodigoMotivo.CATEGORIA_NAO_REEMBOLSAVEL, Decimal("0.00"), Decimal("690.00")),
        "d-014": (StatusDespesa.APROVADA, CodigoMotivo.OK, Decimal("61.00"), Decimal("0.00")),
    }

    assert [r.id for r in relatorio.resultados] == list(esperado.keys())

    for res in relatorio.resultados:
        st_esp, cod_esp, reemb_esp, glosa_esp = esperado[res.id]
        assert res.status == st_esp, f"Falha de status em {res.id}"
        assert res.codigo_motivo == cod_esp, f"Falha de codigo_motivo em {res.id}"
        assert res.valor_reembolsado == reemb_esp, f"Falha de valor_reembolsado em {res.id}"
        assert res.valor_glosado == glosa_esp, f"Falha de valor_glosado em {res.id}"


def test_ca_009_lote_envelope_cc_comercial_e_cambio() -> None:
    """Valida todos os 10 itens de exemplos/Envelope/despesas-envelope.json (CA-009, AMB-011 a AMB-015)."""
    colaborador, periodo, despesas = carregar_entrada_json("exemplos/Envelope/despesas-envelope.json")
    politica = carregar_politica_json("exemplos/Envelope/politica-v4.json")
    cambio = carregar_cambio_json("exemplos/Envelope/cambio.json")

    relatorio = avaliar_relatorio(colaborador, periodo, despesas, politica=politica, cambio=cambio)

    assert relatorio.em_viagem is True
    assert relatorio.resumo.quantidade_despesas == 10
    assert relatorio.resumo.quantidade_aprovadas == 4
    assert relatorio.resumo.quantidade_aprovadas_parcialmente == 3
    assert relatorio.resumo.quantidade_recusadas == 3

    assert relatorio.resumo.total_solicitado == Decimal("2457.52")
    assert relatorio.resumo.total_reembolsado == Decimal("1233.72")
    assert relatorio.resumo.total_glosado == Decimal("1223.80")

    esperado = {
        "e-001": (StatusDespesa.APROVADA_PARCIALMENTE, CodigoMotivo.LIMITE_DIARIO_EXCEDIDO, Decimal("340.00"), Decimal("300.00"), Decimal("40.00")),
        "e-002": (StatusDespesa.APROVADA, CodigoMotivo.OK, Decimal("130.46"), Decimal("130.46"), Decimal("0.00")),
        "e-003": (StatusDespesa.APROVADA, CodigoMotivo.OK, Decimal("85.26"), Decimal("85.26"), Decimal("0.00")),
        "e-004": (StatusDespesa.APROVADA_PARCIALMENTE, CodigoMotivo.LIMITE_DIARIO_EXCEDIDO, Decimal("178.80"), Decimal("135.00"), Decimal("43.80")),
        "e-005": (StatusDespesa.RECUSADA, CodigoMotivo.SEM_NOTA_FISCAL, Decimal("220.00"), Decimal("0.00"), Decimal("220.00")),
        "e-006": (StatusDespesa.RECUSADA, CodigoMotivo.MOEDA_NAO_SUPORTADA, Decimal("0.00"), Decimal("0.00"), Decimal("0.00")),
        "e-007": (StatusDespesa.APROVADA_PARCIALMENTE, CodigoMotivo.LIMITE_DIARIO_EXCEDIDO, Decimal("1200.00"), Decimal("400.00"), Decimal("800.00")),
        "e-008": (StatusDespesa.APROVADA, CodigoMotivo.OK, Decimal("95.00"), Decimal("95.00"), Decimal("0.00")),
        "e-009": (StatusDespesa.RECUSADA, CodigoMotivo.CATEGORIA_NAO_REEMBOLSAVEL, Decimal("120.00"), Decimal("0.00"), Decimal("120.00")),
        "e-010": (StatusDespesa.APROVADA, CodigoMotivo.OK, Decimal("88.00"), Decimal("88.00"), Decimal("0.00")),
    }

    for res in relatorio.resultados:
        st_esp, cod_esp, orig_brl, reemb_esp, glosa_esp = esperado[res.id]
        assert res.status == st_esp, f"Falha de status em {res.id}"
        assert res.codigo_motivo == cod_esp, f"Falha de codigo_motivo em {res.id}"
        assert res.valor_original == orig_brl, f"Falha de valor_original BRL em {res.id}"
        assert res.valor_reembolsado == reemb_esp, f"Falha de valor_reembolsado em {res.id}"
        assert res.valor_glosado == glosa_esp, f"Falha de valor_glosado em {res.id}"


def test_ca_010_lote_envelope_cc_desconhecido_fallback_padrao() -> None:
    """Valida todos os 4 itens de exemplos/Envelope/despesas-envelope-cc-desconhecido.json (CA-010, AMB-014)."""
    colaborador, periodo, despesas = carregar_entrada_json(
        "exemplos/Envelope/despesas-envelope-cc-desconhecido.json"
    )
    politica = carregar_politica_json("exemplos/Envelope/politica-v4.json")
    cambio = carregar_cambio_json("exemplos/Envelope/cambio.json")

    relatorio = avaliar_relatorio(colaborador, periodo, despesas, politica=politica, cambio=cambio)

    assert relatorio.em_viagem is True
    assert relatorio.resumo.quantidade_despesas == 4
    assert relatorio.resumo.quantidade_aprovadas == 2
    assert relatorio.resumo.quantidade_aprovadas_parcialmente == 1
    assert relatorio.resumo.quantidade_recusadas == 1

    assert relatorio.resumo.total_solicitado == Decimal("623.76")
    assert relatorio.resumo.total_reembolsado == Decimal("373.76")
    assert relatorio.resumo.total_glosado == Decimal("250.00")

    esperado = {
        "f-001": (StatusDespesa.APROVADA, CodigoMotivo.OK, Decimal("58.00"), Decimal("58.00"), Decimal("0.00")),
        "f-002": (StatusDespesa.APROVADA_PARCIALMENTE, CodigoMotivo.LIMITE_DIARIO_EXCEDIDO, Decimal("310.00"), Decimal("250.00"), Decimal("60.00")),
        "f-003": (StatusDespesa.RECUSADA, CodigoMotivo.CATEGORIA_NAO_REEMBOLSAVEL, Decimal("190.00"), Decimal("0.00"), Decimal("190.00")),
        "f-004": (StatusDespesa.APROVADA, CodigoMotivo.OK, Decimal("65.76"), Decimal("65.76"), Decimal("0.00")),
    }

    for res in relatorio.resultados:
        st_esp, cod_esp, orig_brl, reemb_esp, glosa_esp = esperado[res.id]
        assert res.status == st_esp, f"Falha de status em {res.id}"
        assert res.codigo_motivo == cod_esp, f"Falha de codigo_motivo em {res.id}"
        assert res.valor_original == orig_brl, f"Falha de valor_original BRL em {res.id}"
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
