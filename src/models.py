"""Modelos de domínio e funções de normalização (RN-001, AMB-003, AMB-009)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum

CENTAVOS = Decimal("0.01")


def arredondar_moeda(valor: Decimal | int | str | float) -> Decimal:
    """Arredonda um valor monetário para 2 casas decimais usando ROUND_HALF_UP (RN-001, AMB-009)."""
    if isinstance(valor, Decimal):
        decimal_val = valor
    else:
        decimal_val = Decimal(str(valor))
    return decimal_val.quantize(CENTAVOS, rounding=ROUND_HALF_UP)


def normalizar_texto(texto: str) -> str:
    """Remove espaços nas extremidades e converte para letras minúsculas (RN-001, AMB-003)."""
    return texto.strip().lower()


class StatusDespesa(str, Enum):
    """Status final de avaliação de uma despesa (Seção 4 da spec)."""

    APROVADA = "APROVADA"
    APROVADA_PARCIALMENTE = "APROVADA_PARCIALMENTE"
    RECUSADA = "RECUSADA"


class CodigoMotivo(str, Enum):
    """Códigos padronizados de motivo de decisão (Seção 4 da spec)."""

    OK = "OK"
    LIMITE_DIARIO_EXCEDIDO = "LIMITE_DIARIO_EXCEDIDO"
    SEM_NOTA_FISCAL = "SEM_NOTA_FISCAL"
    CATEGORIA_NAO_REEMBOLSAVEL = "CATEGORIA_NAO_REEMBOLSAVEL"
    FORA_PERIODO_COMPETENCIA = "FORA_PERIODO_COMPETENCIA"
    DESPESA_DUPLICADA = "DESPESA_DUPLICADA"
    VALOR_INVALIDO = "VALOR_INVALIDO"


@dataclass(frozen=True)
class Colaborador:
    """Dados cadastrais do colaborador solicitante."""

    id: str
    nome: str
    centro_custo: str
    em_viagem: bool = False


@dataclass(frozen=True)
class Periodo:
    """Período de competência do relatório de despesas."""

    competencia: str
    inicio: date
    fim: date


@dataclass(frozen=True)
class DespesaInput:
    """Despesa normalizada pronta para avaliação pelas regras de negócio."""

    id: str
    data: date
    categoria_original: str
    categoria_normalizada: str
    descricao: str
    descricao_normalizada: str
    fornecedor: str
    fornecedor_normalizado: str
    valor_bruto: Decimal
    valor_original: Decimal
    tem_nota_fiscal: bool
    em_viagem: bool = False

    @classmethod
    def criar(
        cls,
        id: str,
        data: date | str,
        categoria: str,
        descricao: str,
        fornecedor: str,
        valor: Decimal | int | str | float,
        tem_nota_fiscal: bool,
        em_viagem: bool = False,
    ) -> DespesaInput:
        """Cria uma DespesaInput aplicando normalização e arredondamento (RN-001)."""
        data_parsed = date.fromisoformat(data) if isinstance(data, str) else data
        valor_dec = valor if isinstance(valor, Decimal) else Decimal(str(valor))
        return cls(
            id=id,
            data=data_parsed,
            categoria_original=categoria,
            categoria_normalizada=normalizar_texto(categoria),
            descricao=descricao,
            descricao_normalizada=normalizar_texto(descricao),
            fornecedor=fornecedor,
            fornecedor_normalizado=normalizar_texto(fornecedor),
            valor_bruto=valor_dec,
            valor_original=arredondar_moeda(valor_dec),
            tem_nota_fiscal=bool(tem_nota_fiscal),
            em_viagem=bool(em_viagem),
        )


@dataclass(frozen=True)
class ResultadoDespesa:
    """Resultado individual da avaliação de uma despesa."""

    id: str
    data: str
    categoria_original: str
    categoria_normalizada: str
    valor_original: Decimal
    valor_reembolsado: Decimal
    valor_glosado: Decimal
    status: StatusDespesa
    codigo_motivo: CodigoMotivo
    justificativa: str


@dataclass(frozen=True)
class ResumoProcessamento:
    """Totais consolidados do lote de despesas."""

    total_solicitado: Decimal
    total_reembolsado: Decimal
    total_glosado: Decimal
    quantidade_despesas: int
    quantidade_aprovadas: int
    quantidade_aprovadas_parcialmente: int
    quantidade_recusadas: int


@dataclass(frozen=True)
class RelatorioReembolso:
    """Documento final de saída da avaliação de reembolso."""

    colaborador: Colaborador
    periodo: Periodo
    em_viagem: bool
    resumo: ResumoProcessamento
    resultados: list[ResultadoDespesa]
