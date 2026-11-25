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


def test_rn_002_amb_006_recusa_valor_negativo_ou_zero() -> None:
    """Verifica recusa de estornos/valores negativos e zero sem glosa positiva (RN-002, AMB-006)."""
    from src.engine import validar_valor_positivo
    from src.models import CodigoMotivo, StatusDespesa

    estorno = DespesaInput.criar(
        id="d-009",
        data="2026-07-11",
        categoria="transporte_urbano",
        descricao="Estorno de corrida cancelada",
        fornecedor="TaxiApp",
        valor=Decimal("-45.00"),
        tem_nota_fiscal=False,
    )
    res_estorno = validar_valor_positivo(estorno)
    assert res_estorno is not None
    assert res_estorno.status == StatusDespesa.RECUSADA
    assert res_estorno.codigo_motivo == CodigoMotivo.VALOR_INVALIDO
    assert res_estorno.valor_reembolsado == Decimal("0.00")
    assert res_estorno.valor_glosado == Decimal("0.00")

    zero = DespesaInput.criar(
        id="d-zero",
        data="2026-07-11",
        categoria="alimentacao",
        descricao="Cortesia",
        fornecedor="Bistro",
        valor=Decimal("0.00"),
        tem_nota_fiscal=True,
    )
    res_zero = validar_valor_positivo(zero)
    assert res_zero is not None
    assert res_zero.status == StatusDespesa.RECUSADA
    assert res_zero.codigo_motivo == CodigoMotivo.VALOR_INVALIDO


def test_rn_003_amb_005_amb_010_periodo_competencia_e_fim_de_semana() -> None:
    """Verifica recusa fora do período [inicio, fim] e permissão em sábado dentro do período (RN-003, AMB-005, AMB-010)."""
    from datetime import date
    from src.engine import validar_periodo_competencia
    from src.models import CodigoMotivo, Periodo, StatusDespesa

    periodo = Periodo(
        competencia="2026-07",
        inicio=date(2026, 7, 1),
        fim=date(2026, 7, 31),
    )

    fora = DespesaInput.criar(
        id="d-008",
        data="2026-04-15",
        categoria="alimentacao",
        descricao="Almoco de abril lancado com atraso",
        fornecedor="Restaurante Tavola",
        valor=Decimal("41.00"),
        tem_nota_fiscal=True,
    )
    res_fora = validar_periodo_competencia(fora, periodo)
    assert res_fora is not None
    assert res_fora.status == StatusDespesa.RECUSADA
    assert res_fora.codigo_motivo == CodigoMotivo.FORA_PERIODO_COMPETENCIA
    assert res_fora.valor_reembolsado == Decimal("0.00")
    assert res_fora.valor_glosado == Decimal("41.00")

    sabado = DespesaInput.criar(
        id="d-012",
        data="2026-07-18",
        categoria="alimentacao",
        descricao="Almoco de sabado - plantao",
        fornecedor="Padaria Uniao",
        valor=Decimal("47.20"),
        tem_nota_fiscal=True,
    )
    assert validar_periodo_competencia(sabado, periodo) is None


def test_rn_004_amb_003_categoria_fora_da_politica() -> None:
    """Verifica recusa de categoria fora da política (coworking) e aceite de categoria normalizada (RN-004, AMB-003)."""
    from src.engine import validar_categoria_politica
    from src.models import CodigoMotivo, StatusDespesa

    politica = PoliticaReembolso()

    coworking = DespesaInput.criar(
        id="d-005",
        data="2026-07-07",
        categoria="coworking",
        descricao="Diaria em espaco compartilhado",
        fornecedor="HubOffice",
        valor=Decimal("89.00"),
        tem_nota_fiscal=True,
    )
    res_coworking = validar_categoria_politica(coworking, politica)
    assert res_coworking is not None
    assert res_coworking.status == StatusDespesa.RECUSADA
    assert res_coworking.codigo_motivo == CodigoMotivo.CATEGORIA_NAO_REEMBOLSAVEL
    assert res_coworking.valor_reembolsado == Decimal("0.00")
    assert res_coworking.valor_glosado == Decimal("89.00")

    maiuscula = DespesaInput.criar(
        id="d-014",
        data="2026-07-31",
        categoria="ALIMENTACAO",
        descricao="Jantar de encerramento",
        fornecedor="Restaurante Tavola",
        valor=Decimal("61.00"),
        tem_nota_fiscal=True,
    )
    assert validar_categoria_politica(maiuscula, politica) is None


def test_rn_005_amb_002_fronteira_nota_fiscal_100_reais() -> None:
    """Verifica fronteira estrita > 100.00 para exigência de nota fiscal (RN-005, AMB-002)."""
    from src.engine import validar_nota_fiscal
    from src.models import CodigoMotivo, StatusDespesa

    politica = PoliticaReembolso()

    d003 = DespesaInput.criar(
        id="d-003",
        data="2026-07-06",
        categoria="transporte_urbano",
        descricao="Corrida aeroporto",
        fornecedor="TaxiApp",
        valor=Decimal("100.00"),
        tem_nota_fiscal=False,
    )
    assert validar_nota_fiscal(d003, politica) is None

    d004 = DespesaInput.criar(
        id="d-004",
        data="2026-07-06",
        categoria="transporte_urbano",
        descricao="Corrida hotel",
        fornecedor="TaxiApp",
        valor=Decimal("100.01"),
        tem_nota_fiscal=False,
    )
    res_d004 = validar_nota_fiscal(d004, politica)
    assert res_d004 is not None
    assert res_d004.status == StatusDespesa.RECUSADA
    assert res_d004.codigo_motivo == CodigoMotivo.SEM_NOTA_FISCAL
    assert res_d004.valor_reembolsado == Decimal("0.00")
    assert res_d004.valor_glosado == Decimal("100.01")


def test_rn_006_amb_004_deteccao_duplicatas() -> None:
    """Verifica aprovação da 1ª ocorrência e recusa da 2ª ocorrência idêntica com ID diferente (RN-006, AMB-004)."""
    from src.engine import validar_duplicidade
    from src.models import CodigoMotivo, StatusDespesa

    chaves_vistas: set = set()

    d006 = DespesaInput.criar(
        id="d-006",
        data="2026-07-09",
        categoria="alimentacao",
        descricao="Almoco",
        fornecedor="Bistro Central",
        valor=Decimal("54.90"),
        tem_nota_fiscal=True,
    )
    d007 = DespesaInput.criar(
        id="d-007",
        data="2026-07-09",
        categoria="alimentacao",
        descricao="Almoco",
        fornecedor="Bistro Central",
        valor=Decimal("54.90"),
        tem_nota_fiscal=True,
    )

    assert validar_duplicidade(d006, chaves_vistas) is None
    res_d007 = validar_duplicidade(d007, chaves_vistas)
    assert res_d007 is not None
    assert res_d007.status == StatusDespesa.RECUSADA
    assert res_d007.codigo_motivo == CodigoMotivo.DESPESA_DUPLICADA
    assert res_d007.valor_reembolsado == Decimal("0.00")
    assert res_d007.valor_glosado == Decimal("54.90")
