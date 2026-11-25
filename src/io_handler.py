"""Parser de entrada JSON e serializador de saída JSON com precisão Decimal (T-002)."""

from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

from src.models import (
    Colaborador,
    DespesaInput,
    Periodo,
    RelatorioReembolso,
    arredondar_moeda,
)


def parse_entrada_dict(dados: dict[str, Any]) -> tuple[Colaborador, Periodo, list[DespesaInput]]:
    """Converte um dicionário deserializado do JSON em objetos de domínio normalizados (RN-001)."""
    col_raw = dados["colaborador"]
    colaborador = Colaborador(
        id=str(col_raw["id"]),
        nome=str(col_raw["nome"]),
        centro_custo=str(col_raw["centro_custo"]),
        em_viagem=bool(col_raw.get("em_viagem", False)),
    )

    per_raw = dados["periodo"]
    periodo = Periodo(
        competencia=str(per_raw["competencia"]),
        inicio=date.fromisoformat(str(per_raw["inicio"])),
        fim=date.fromisoformat(str(per_raw["fim"])),
    )

    despesas: list[DespesaInput] = []
    for item in dados.get("despesas", []):
        despesas.append(
            DespesaInput.criar(
                id=str(item["id"]),
                data=str(item["data"]),
                categoria=str(item["categoria"]),
                descricao=str(item["descricao"]),
                fornecedor=str(item["fornecedor"]),
                valor=item["valor"],
                tem_nota_fiscal=bool(item["tem_nota_fiscal"]),
                em_viagem=bool(item.get("em_viagem", False)),
            )
        )

    return colaborador, periodo, despesas


def carregar_entrada_json(caminho: str | Path) -> tuple[Colaborador, Periodo, list[DespesaInput]]:
    """Lê um arquivo JSON do disco preservando precisão Decimal para todos os números (DT-002)."""
    conteudo = Path(caminho).read_text(encoding="utf-8")
    dados = json.loads(conteudo, parse_float=Decimal)
    return parse_entrada_dict(dados)


def _decimal_para_float_2_casas(valor: Decimal) -> float:
    """Converte Decimal quantizado em 2 casas para número JSON sem perda de representação."""
    quantizado = arredondar_moeda(valor)
    return float(str(quantizado))


def serializar_relatorio_dict(relatorio: RelatorioReembolso) -> dict[str, Any]:
    """Converte o RelatorioReembolso para o dicionário do schema de saída (Seção 4 da spec)."""
    return {
        "colaborador": {
            "id": relatorio.colaborador.id,
            "nome": relatorio.colaborador.nome,
            "centro_custo": relatorio.colaborador.centro_custo,
        },
        "periodo": {
            "competencia": relatorio.periodo.competencia,
            "inicio": relatorio.periodo.inicio.isoformat(),
            "fim": relatorio.periodo.fim.isoformat(),
        },
        "em_viagem": relatorio.em_viagem,
        "resumo": {
            "total_solicitado": _decimal_para_float_2_casas(relatorio.resumo.total_solicitado),
            "total_reembolsado": _decimal_para_float_2_casas(relatorio.resumo.total_reembolsado),
            "total_glosado": _decimal_para_float_2_casas(relatorio.resumo.total_glosado),
            "quantidade_despesas": relatorio.resumo.quantidade_despesas,
            "quantidade_aprovadas": relatorio.resumo.quantidade_aprovadas,
            "quantidade_aprovadas_parcialmente": relatorio.resumo.quantidade_aprovadas_parcialmente,
            "quantidade_recusadas": relatorio.resumo.quantidade_recusadas,
        },
        "resultados": [
            {
                "id": r.id,
                "data": r.data,
                "categoria_original": r.categoria_original,
                "categoria_normalizada": r.categoria_normalizada,
                "valor_original": _decimal_para_float_2_casas(r.valor_original),
                "valor_reembolsado": _decimal_para_float_2_casas(r.valor_reembolsado),
                "valor_glosado": _decimal_para_float_2_casas(r.valor_glosado),
                "status": r.status.value,
                "codigo_motivo": r.codigo_motivo.value,
                "justificativa": r.justificativa,
            }
            for r in relatorio.resultados
        ],
    }


def salvar_saida_json(relatorio: RelatorioReembolso, caminho: str | Path) -> None:
    """Serializa e grava o RelatorioReembolso em arquivo JSON formatado em UTF-8."""
    dados = serializar_relatorio_dict(relatorio)
    destino = Path(caminho)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(
        json.dumps(dados, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
