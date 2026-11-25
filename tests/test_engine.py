"""Testes unitários das regras de negócio do motor de reembolso."""

from decimal import Decimal

from src.models import DespesaInput, arredondar_moeda, normalizar_texto
from src.policy import PoliticaReembolso


def test_rn_001_amb_009_arredondamento_half_up() -> None:
    """Verifica arredondamento half-up para 2 casas decimais na entrada (RN-001, AMB-009)."""
    assert arredondar_moeda(Decimal("33.333")) == Decimal("33.33")
    assert arredondar_moeda(Decimal("33.335")) == Decimal("33.34")
    assert arredondar_moeda("100.004") == Decimal("100.00")
    assert arredondar_moeda("100.005") == Decimal("100.01")

    despesa = DespesaInput.criar(
        id="d-011",
        data="2026-07-15",
        categoria="alimentacao",
        descricao="Cafe da manha hotel",
        fornecedor="Hotel Copa Sul",
        valor=Decimal("33.333"),
        tem_nota_fiscal=True,
    )
    assert despesa.valor_bruto == Decimal("33.333")
    assert despesa.valor_original == Decimal("33.33")


def test_rn_001_amb_003_normalizacao_categoria() -> None:
    """Verifica normalização case-insensitive e remoção de espaços em categorias (RN-001, AMB-003)."""
    assert normalizar_texto("  ALIMENTACAO ") == "alimentacao"
    assert normalizar_texto("Transporte_Urbano") == "transporte_urbano"

    despesa = DespesaInput.criar(
        id="d-014",
        data="2026-07-31",
        categoria="ALIMENTACAO",
        descricao="Jantar de encerramento",
        fornecedor="Restaurante Tavola",
        valor=Decimal("61.00"),
        tem_nota_fiscal=True,
    )
    assert despesa.categoria_original == "ALIMENTACAO"
    assert despesa.categoria_normalizada == "alimentacao"

    politica = PoliticaReembolso()
    assert politica.categoria_elegivel(despesa.categoria_normalizada) is True
    assert politica.categoria_elegivel("coworking") is False


def test_rn_001_io_parsing_e_serializacao_json(tmp_path) -> None:
    """Verifica parsing de JSON com parse_float=Decimal e serialização do schema de saída (T-002)."""
    from datetime import date
    from src.io_handler import carregar_entrada_json, salvar_saida_json, serializar_relatorio_dict
    from src.models import (
        CodigoMotivo,
        Colaborador,
        Periodo,
        RelatorioReembolso,
        ResultadoDespesa,
        ResumoProcessamento,
        StatusDespesa,
    )

    colaborador, periodo, despesas = carregar_entrada_json("exemplos/despesas-exemplo.json")
    assert colaborador.id == "c-0417"
    assert colaborador.nome == "Marina Volpi"
    assert periodo.competencia == "2026-07"
    assert periodo.inicio == date(2026, 7, 1)
    assert periodo.fim == date(2026, 7, 31)
    assert len(despesas) == 14

    # d-011 possui 33.333 no JSON e deve ser normalizada para Decimal("33.33")
    d011 = next(d for d in despesas if d.id == "d-011")
    assert d011.valor_bruto == Decimal("33.333")
    assert d011.valor_original == Decimal("33.33")

    # d-014 possui categoria "ALIMENTACAO" e deve ser normalizada para "alimentacao"
    d014 = next(d for d in despesas if d.id == "d-014")
    assert d014.categoria_original == "ALIMENTACAO"
    assert d014.categoria_normalizada == "alimentacao"

    relatorio = RelatorioReembolso(
        colaborador=colaborador,
        periodo=periodo,
        em_viagem=False,
        resumo=ResumoProcessamento(
            total_solicitado=Decimal("33.33"),
            total_reembolsado=Decimal("33.33"),
            total_glosado=Decimal("0.00"),
            quantidade_despesas=1,
            quantidade_aprovadas=1,
            quantidade_aprovadas_parcialmente=0,
            quantidade_recusadas=0,
        ),
        resultados=[
            ResultadoDespesa(
                id="d-011",
                data="2026-07-15",
                categoria_original="alimentacao",
                categoria_normalizada="alimentacao",
                valor_original=Decimal("33.33"),
                valor_reembolsado=Decimal("33.33"),
                valor_glosado=Decimal("0.00"),
                status=StatusDespesa.APROVADA,
                codigo_motivo=CodigoMotivo.OK,
                justificativa="Despesa aprovada integralmente.",
            )
        ],
    )
    saida_dict = serializar_relatorio_dict(relatorio)
    assert saida_dict["resumo"]["total_solicitado"] == 33.33
    assert saida_dict["resultados"][0]["status"] == "APROVADA"
    assert saida_dict["resultados"][0]["codigo_motivo"] == "OK"

    arquivo_saida = tmp_path / "saida_teste.json"
    salvar_saida_json(relatorio, arquivo_saida)
    assert arquivo_saida.exists()
