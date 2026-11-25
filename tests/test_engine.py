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


def test_rn_007_amb_007_amb_008_regime_viagem_hospedagem_valida() -> None:
    """Verifica ativação do regime de viagem em D e D+1 por hospedagem válida e manutenção do teto de R$ 250 para hospedagem (RN-007, AMB-007, AMB-008, D-002)."""
    from datetime import date
    from src.engine import avaliar_relatorio
    from src.models import CodigoMotivo, Colaborador, Periodo, StatusDespesa

    colaborador = Colaborador(id="c-0417", nome="Marina Volpi", centro_custo="CC-ENG-PLATAFORMA")
    periodo = Periodo(competencia="2026-07", inicio=date(2026, 7, 1), fim=date(2026, 7, 31))

    despesas = [
        DespesaInput.criar(
            id="d-010",
            data="2026-07-14",
            categoria="hospedagem",
            descricao="Hotel Rio - 2 diarias",
            fornecedor="Hotel Copa Sul",
            valor=Decimal("480.00"),
            tem_nota_fiscal=True,
        ),
        DespesaInput.criar(
            id="d-011",
            data="2026-07-15",
            categoria="alimentacao",
            descricao="Cafe da manha hotel",
            fornecedor="Hotel Copa Sul",
            valor=Decimal("85.00"),
            tem_nota_fiscal=True,
        ),
        DespesaInput.criar(
            id="d-013",
            data="2026-07-22",
            categoria="hospedagem",
            descricao="Airbnb 3 noites",
            fornecedor="Airbnb",
            valor=Decimal("690.00"),
            tem_nota_fiscal=False,
        ),
        DespesaInput.criar(
            id="d-alim-22",
            data="2026-07-22",
            categoria="alimentacao",
            descricao="Jantar no dia do Airbnb sem NF",
            fornecedor="Restaurante",
            valor=Decimal("75.00"),
            tem_nota_fiscal=True,
        ),
    ]

    relatorio = avaliar_relatorio(colaborador, periodo, despesas)
    assert relatorio.em_viagem is True

    # d-010 (hospedagem válida): teto R$ 250.00 (D-002)
    r_d010 = relatorio.resultados[0]
    assert r_d010.status == StatusDespesa.APROVADA_PARCIALMENTE
    assert r_d010.codigo_motivo == CodigoMotivo.LIMITE_DIARIO_EXCEDIDO
    assert r_d010.valor_reembolsado == Decimal("250.00")
    assert r_d010.valor_glosado == Decimal("230.00")

    # d-011 em D+1 (2026-07-15): alimentação com limite ampliado em +50% (R$ 90.00), logo R$ 85.00 é APROVADA
    r_d011 = relatorio.resultados[1]
    assert r_d011.status == StatusDespesa.APROVADA
    assert r_d011.codigo_motivo == CodigoMotivo.OK
    assert r_d011.valor_reembolsado == Decimal("85.00")

    # d-013 (hospedagem sem NF acima de R$ 100): RECUSADA por SEM_NOTA_FISCAL e NÃO ativa viagem em 2026-07-22
    r_d013 = relatorio.resultados[2]
    assert r_d013.status == StatusDespesa.RECUSADA
    assert r_d013.codigo_motivo == CodigoMotivo.SEM_NOTA_FISCAL

    # d-alim-22 em 2026-07-22 opera no limite normal de R$ 60.00 (não R$ 90.00)
    r_alim22 = relatorio.resultados[3]
    assert r_alim22.status == StatusDespesa.APROVADA_PARCIALMENTE
    assert r_alim22.valor_reembolsado == Decimal("60.00")
    assert r_alim22.valor_glosado == Decimal("15.00")


def test_rn_008_amb_001_limite_diario_cumulativo_e_reembolso_parcial() -> None:
    """Verifica consumo cumulativo do saldo diário na mesma data e categoria (RN-008, AMB-001)."""
    from datetime import date
    from src.engine import avaliar_relatorio
    from src.models import CodigoMotivo, Colaborador, Periodo, StatusDespesa

    colaborador = Colaborador(id="c-0417", nome="Marina Volpi", centro_custo="CC-ENG-PLATAFORMA")
    periodo = Periodo(competencia="2026-07", inicio=date(2026, 7, 1), fim=date(2026, 7, 31))

    despesas = [
        DespesaInput.criar(
            id="d-001",
            data="2026-07-03",
            categoria="alimentacao",
            descricao="Almoco com cliente",
            fornecedor="Restaurante Tavola",
            valor=Decimal("72.50"),
            tem_nota_fiscal=True,
        ),
        DespesaInput.criar(
            id="d-002",
            data="2026-07-03",
            categoria="alimentacao",
            descricao="Jantar apos reuniao",
            fornecedor="Cantina do Porto",
            valor=Decimal("38.00"),
            tem_nota_fiscal=True,
        ),
    ]

    relatorio = avaliar_relatorio(colaborador, periodo, despesas)
    assert relatorio.em_viagem is False

    r1, r2 = relatorio.resultados
    assert r1.status == StatusDespesa.APROVADA_PARCIALMENTE
    assert r1.codigo_motivo == CodigoMotivo.LIMITE_DIARIO_EXCEDIDO
    assert r1.valor_reembolsado == Decimal("60.00")
    assert r1.valor_glosado == Decimal("12.50")

    assert r2.status == StatusDespesa.RECUSADA
    assert r2.codigo_motivo == CodigoMotivo.LIMITE_DIARIO_EXCEDIDO
    assert r2.valor_reembolsado == Decimal("0.00")
    assert r2.valor_glosado == Decimal("38.00")

    assert relatorio.resumo.total_solicitado == Decimal("110.50")
    assert relatorio.resumo.total_reembolsado == Decimal("60.00")
    assert relatorio.resumo.total_glosado == Decimal("50.50")


def test_rn_004_amb_014_politica_v4_por_centro_custo_e_fallback_padrao() -> None:
    """Verifica leitura de politica-v4.json, limites por CC, limite 0.00 em CC-ENG-PLATAFORMA e fallback padrão (T-008, RN-004, AMB-014)."""
    from src.io_handler import carregar_politica_json

    politica = carregar_politica_json("exemplos/Envelope/politica-v4.json")

    # CC-COMERCIAL possui representacao (300.00) e alimentacao (90.00, em viagem 135.00)
    assert politica.categoria_elegivel("representacao", "CC-COMERCIAL") is True
    assert politica.obter_limite_diario("representacao", False, "CC-COMERCIAL") == Decimal("300.00")
    assert politica.obter_limite_diario("representacao", True, "CC-COMERCIAL") == Decimal("300.00")
    assert politica.obter_limite_diario("alimentacao", False, "CC-COMERCIAL") == Decimal("90.00")
    assert politica.obter_limite_diario("alimentacao", True, "CC-COMERCIAL") == Decimal("135.00")

    # CC-ENG-PLATAFORMA tem hospedagem com limite 0.00 ("nao reembolsavel") e alimentacao 75.00
    assert politica.categoria_elegivel("hospedagem", "CC-ENG-PLATAFORMA") is False
    assert politica.categoria_elegivel("alimentacao", "CC-ENG-PLATAFORMA") is True
    assert politica.obter_limite_diario("alimentacao", False, "CC-ENG-PLATAFORMA") == Decimal("75.00")

    # CC-ADM não lista hospedagem -> não elegível
    assert politica.categoria_elegivel("hospedagem", "CC-ADM") is False

    # CC-SUPORTE-N2 não existe na tabela -> usa fallback padrão (alimentacao 60, hospedagem 250, sem representacao)
    assert politica.categoria_elegivel("alimentacao", "CC-SUPORTE-N2") is True
    assert politica.obter_limite_diario("alimentacao", False, "CC-SUPORTE-N2") == Decimal("60.00")
    assert politica.categoria_elegivel("hospedagem", "CC-SUPORTE-N2") is True
    assert politica.obter_limite_diario("hospedagem", False, "CC-SUPORTE-N2") == Decimal("250.00")
    assert politica.categoria_elegivel("representacao", "CC-SUPORTE-N2") is False


def test_rn_009_amb_011_amb_012_tabela_cambio_e_fallback_fim_de_semana() -> None:
    """Verifica leitura de cambio.json, cotação no dia útil, fallback de sábado para sexta e moeda não suportada (T-008, RN-009, AMB-011, AMB-012)."""
    from datetime import date
    from src.io_handler import carregar_cambio_json

    cambio = carregar_cambio_json("exemplos/Envelope/cambio.json")

    # BRL sempre retorna 1.00
    taxa_brl, erro_brl = cambio.obter_taxa(date(2026, 7, 13), "BRL")
    assert taxa_brl == Decimal("1.00")
    assert erro_brl is None

    # Dia útil exato: 2026-07-14 EUR = 5.93
    taxa_eur_14, erro_eur_14 = cambio.obter_taxa(date(2026, 7, 14), "EUR")
    assert taxa_eur_14 == Decimal("5.93")
    assert erro_eur_14 is None

    # Sábado 2026-07-18 -> usa cotação de sexta-feira 2026-07-17 (EUR = 5.96)
    taxa_eur_18, erro_eur_18 = cambio.obter_taxa(date(2026, 7, 18), "EUR")
    assert taxa_eur_18 == Decimal("5.96")
    assert erro_eur_18 is None

    # Moeda não cadastrada: GBP em 2026-07-21 -> MOEDA_NAO_SUPORTADA
    taxa_gbp, erro_gbp = cambio.obter_taxa(date(2026, 7, 21), "GBP")
    assert taxa_gbp is None
    assert erro_gbp == "MOEDA_NAO_SUPORTADA"

    # Data anterior à primeira cotação da tabela (ex.: 2026-07-01) -> CAMBIO_INDISPONIVEL
    taxa_antiga, erro_antiga = cambio.obter_taxa(date(2026, 7, 1), "USD")
    assert taxa_antiga is None
    assert erro_antiga == "CAMBIO_INDISPONIVEL"


def test_rn_005_rn_009_amb_013_nota_fiscal_apos_conversao_cambial() -> None:
    """Verifica que a obrigatoriedade de nota fiscal (> R$ 100,00) é avaliada sobre o valor convertido em BRL (T-009, RN-005, RN-009, AMB-013)."""
    from datetime import date
    from src.engine import avaliar_relatorio
    from src.io_handler import carregar_cambio_json, carregar_politica_json
    from src.models import CodigoMotivo, Colaborador, Periodo, StatusDespesa

    politica = carregar_politica_json("exemplos/Envelope/politica-v4.json")
    cambio = carregar_cambio_json("exemplos/Envelope/cambio.json")
    colaborador = Colaborador(id="c-0912", nome="Rafael Nkemelu", centro_custo="CC-COMERCIAL")
    periodo = Periodo(competencia="2026-07", inicio=date(2026, 7, 1), fim=date(2026, 7, 31))

    despesas = [
        # e-003: 14.50 EUR em 2026-07-15 (taxa 5.88) = R$ 85.26 <= 100.00 -> isenta de NF
        DespesaInput.criar(
            id="e-003",
            data="2026-07-15",
            categoria="alimentacao",
            descricao="Cafe e sanduiche",
            fornecedor="Padaria Lisboa",
            valor=Decimal("14.50"),
            moeda="EUR",
            tem_nota_fiscal=False,
        ),
        # e-005: 40.00 USD em 2026-07-20 (taxa 5.50) = R$ 220.00 > 100.00 -> exige NF, logo RECUSADA
        DespesaInput.criar(
            id="e-005",
            data="2026-07-20",
            categoria="transporte_urbano",
            descricao="Corridas do dia",
            fornecedor="Bolt",
            valor=Decimal("40.00"),
            moeda="USD",
            tem_nota_fiscal=False,
        ),
    ]

    relatorio = avaliar_relatorio(colaborador, periodo, despesas, politica=politica, cambio=cambio)
    r_e003, r_e005 = relatorio.resultados

    assert r_e003.status == StatusDespesa.APROVADA
    assert r_e003.codigo_motivo == CodigoMotivo.OK
    assert r_e003.valor_original == Decimal("85.26")
    assert r_e003.valor_reembolsado == Decimal("85.26")

    assert r_e005.status == StatusDespesa.RECUSADA
    assert r_e005.codigo_motivo == CodigoMotivo.SEM_NOTA_FISCAL
    assert r_e005.valor_original == Decimal("220.00")
    assert r_e005.valor_reembolsado == Decimal("0.00")
    assert r_e005.valor_glosado == Decimal("220.00")


def test_rn_007_amb_015_moeda_estrangeira_ativa_viagem() -> None:
    """Verifica que despesa válida em moeda estrangeira ativa o regime de viagem (+50% em alimentacao) na data D (T-009, RN-007, AMB-015)."""
    from datetime import date
    from src.engine import avaliar_relatorio
    from src.io_handler import carregar_cambio_json, carregar_politica_json
    from src.models import CodigoMotivo, Colaborador, Periodo, StatusDespesa

    politica = carregar_politica_json("exemplos/Envelope/politica-v4.json")
    cambio = carregar_cambio_json("exemplos/Envelope/cambio.json")
    colaborador = Colaborador(id="c-0912", nome="Rafael Nkemelu", centro_custo="CC-COMERCIAL")
    periodo = Periodo(competencia="2026-07", inicio=date(2026, 7, 1), fim=date(2026, 7, 31))

    # Em CC-COMERCIAL, alimentacao base é R$ 90.00 e em viagem (+50%) é R$ 135.00
    despesas = [
        # e-002: 22.00 EUR em 2026-07-14 (taxa 5.93) = R$ 130.46 -> APROVADA porque 130.46 <= 135.00
        DespesaInput.criar(
            id="e-002",
            data="2026-07-14",
            categoria="alimentacao",
            descricao="Almoco - Lisboa",
            fornecedor="Taberna do Chiado",
            valor=Decimal("22.00"),
            moeda="EUR",
            tem_nota_fiscal=True,
        ),
        # e-004: 30.00 EUR no sábado 2026-07-18 (taxa sexta 17/07 = 5.96) = R$ 178.80 -> APROVADA_PARCIALMENTE (135.00)
        DespesaInput.criar(
            id="e-004",
            data="2026-07-18",
            categoria="alimentacao",
            descricao="Jantar de sabado",
            fornecedor="Cervejaria Ramiro",
            valor=Decimal("30.00"),
            moeda="EUR",
            tem_nota_fiscal=True,
        ),
    ]

    relatorio = avaliar_relatorio(colaborador, periodo, despesas, politica=politica, cambio=cambio)
    assert relatorio.em_viagem is True

    r_e002, r_e004 = relatorio.resultados
    assert r_e002.status == StatusDespesa.APROVADA
    assert r_e002.valor_original == Decimal("130.46")
    assert r_e002.valor_reembolsado == Decimal("130.46")

    assert r_e004.status == StatusDespesa.APROVADA_PARCIALMENTE
    assert r_e004.codigo_motivo == CodigoMotivo.LIMITE_DIARIO_EXCEDIDO
    assert r_e004.valor_original == Decimal("178.80")
    assert r_e004.valor_reembolsado == Decimal("135.00")
    assert r_e004.valor_glosado == Decimal("43.80")
