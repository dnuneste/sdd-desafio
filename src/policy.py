"""Parâmetros da política de reembolso v3/v4 e tabela de câmbio (RN-004, RN-005, RN-007, RN-008, RN-009)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any, Mapping

from src.models import arredondar_moeda, normalizar_moeda, normalizar_texto


@dataclass(frozen=True)
class PoliticaReembolso:
    """Representação parametrizada da Política de Reembolso de Despesas (suporta v3 e v4 por centro de custo)."""

    limites_diarios_base: Mapping[str, Decimal] = field(
        default_factory=lambda: {
            "alimentacao": Decimal("60.00"),
            "transporte_urbano": Decimal("80.00"),
            "hospedagem": Decimal("250.00"),
        }
    )
    limites_por_centro_custo: Mapping[str, Mapping[str, Decimal]] = field(
        default_factory=dict
    )
    categorias_ampliadas_em_viagem: frozenset[str] = field(
        default_factory=lambda: frozenset({"alimentacao", "transporte_urbano"})
    )
    fator_multiplicador_viagem: Decimal = Decimal("1.50")
    limite_isencao_nota_fiscal: Decimal = Decimal("100.00")
    dias_extensao_viagem_hospedagem: int = 1

    @classmethod
    def de_dict(cls, dados: Mapping[str, Any]) -> PoliticaReembolso:
        """Constrói uma PoliticaReembolso a partir do dicionário de `politica-v4.json`."""
        padrao_raw = dados.get("padrao", {})
        limites_padrao: dict[str, Decimal] = {}
        for cat, info in padrao_raw.items():
            valor_lim = info["limite"] if isinstance(info, Mapping) else info
            limites_padrao[normalizar_texto(cat)] = arredondar_moeda(Decimal(str(valor_lim)))

        cc_raw = dados.get("centros_custo", {})
        limites_cc: dict[str, dict[str, Decimal]] = {}
        for cc_nome, mapa_cat in cc_raw.items():
            limites_cc[str(cc_nome).strip()] = {}
            for cat, info in mapa_cat.items():
                valor_lim = info["limite"] if isinstance(info, Mapping) else info
                limites_cc[str(cc_nome).strip()][normalizar_texto(cat)] = arredondar_moeda(
                    Decimal(str(valor_lim))
                )

        nf_acima = Decimal(str(dados.get("nota_fiscal_obrigatoria_acima_de", "100.00")))
        perc_viagem = Decimal(str(dados.get("acrescimo_em_viagem_percentual", "50")))
        fator_viagem = Decimal("1.00") + (perc_viagem / Decimal("100"))

        return cls(
            limites_diarios_base=limites_padrao or {
                "alimentacao": Decimal("60.00"),
                "transporte_urbano": Decimal("80.00"),
                "hospedagem": Decimal("250.00"),
            },
            limites_por_centro_custo=limites_cc,
            fator_multiplicador_viagem=fator_viagem,
            limite_isencao_nota_fiscal=arredondar_moeda(nf_acima),
        )

    def obter_mapa_centro_custo(self, centro_custo: str | None = None) -> Mapping[str, Decimal]:
        """Retorna a tabela específica do centro de custo ou a tabela padrão se o CC não estiver cadastrado (RN-004, AMB-014)."""
        if centro_custo and centro_custo in self.limites_por_centro_custo:
            return self.limites_por_centro_custo[centro_custo]
        return self.limites_diarios_base

    def categoria_elegivel(
        self,
        categoria_normalizada: str,
        centro_custo: str | None = None,
    ) -> bool:
        """Verifica se a categoria existe na tabela aplicável ao CC e possui limite > 0.00 (RN-004, AMB-014)."""
        mapa = self.obter_mapa_centro_custo(centro_custo)
        if categoria_normalizada not in mapa:
            return False
        return mapa[categoria_normalizada] > Decimal("0.00")

    def obter_limite_diario(
        self,
        categoria_normalizada: str,
        em_viagem: bool,
        centro_custo: str | None = None,
    ) -> Decimal:
        """Retorna o limite diário da categoria para o centro de custo considerando o regime de viagem (RN-007, RN-008)."""
        mapa = self.obter_mapa_centro_custo(centro_custo)
        limite_base = mapa[categoria_normalizada]
        if em_viagem and categoria_normalizada in self.categorias_ampliadas_em_viagem:
            return arredondar_moeda(limite_base * self.fator_multiplicador_viagem)
        return limite_base


@dataclass(frozen=True)
class TabelaCambio:
    """Tabela de taxas de câmbio PTAX de fechamento por data (RN-009, AMB-011, AMB-012)."""

    moeda_base: str = "BRL"
    taxas_por_data: Mapping[date, Mapping[str, Decimal]] = field(default_factory=dict)

    @classmethod
    def de_dict(cls, dados: Mapping[str, Any]) -> TabelaCambio:
        """Constrói uma TabelaCambio a partir do dicionário de `cambio.json`."""
        moeda_base = normalizar_moeda(str(dados.get("moeda_base", "BRL")))
        taxas_raw = dados.get("taxas", {})
        taxas_parsed: dict[date, dict[str, Decimal]] = {}
        for data_str, mapa_moedas in taxas_raw.items():
            dt = date.fromisoformat(str(data_str))
            taxas_parsed[dt] = {
                normalizar_moeda(m): Decimal(str(taxa))
                for m, taxa in mapa_moedas.items()
            }
        return cls(moeda_base=moeda_base, taxas_por_data=taxas_parsed)

    def obter_data_cotacao_aplicavel(self, data_despesa: date) -> date | None:
        """Retorna a data exata ou a maior data disponível estritamente anterior (<= data_despesa) (AMB-011)."""
        if data_despesa in self.taxas_por_data:
            return data_despesa
        datas_anteriores = [d for d in self.taxas_por_data if d <= data_despesa]
        if not datas_anteriores:
            return None
        return max(datas_anteriores)

    def obter_taxa(self, data_despesa: date, moeda: str) -> tuple[Decimal | None, str | None]:
        """
        Retorna `(taxa, codigo_erro)`.
        - Para `moeda == moeda_base` ("BRL"), retorna `(Decimal("1.00"), None)`.
        - Se não houver nenhuma data `<= data_despesa`, retorna `(None, "CAMBIO_INDISPONIVEL")`.
        - Se a moeda não constar na data aplicável, retorna `(None, "MOEDA_NAO_SUPORTADA")`.
        """
        moeda_norm = normalizar_moeda(moeda)
        if moeda_norm == self.moeda_base:
            return Decimal("1.00"), None

        data_cotacao = self.obter_data_cotacao_aplicavel(data_despesa)
        if data_cotacao is None:
            return None, "CAMBIO_INDISPONIVEL"

        mapa_moedas = self.taxas_por_data[data_cotacao]
        if moeda_norm not in mapa_moedas:
            return None, "MOEDA_NAO_SUPORTADA"

        return mapa_moedas[moeda_norm], None
