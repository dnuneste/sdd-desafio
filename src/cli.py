"""Interface de linha de comando (CLI) do Motor de Cálculo de Reembolso (T-007, T-010)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from src.engine import avaliar_relatorio
from src.io_handler import (
    CAMINHO_CAMBIO_PADRAO,
    CAMINHO_POLITICA_V4_PADRAO,
    carregar_cambio_json,
    carregar_entrada_json,
    carregar_politica_json,
    salvar_saida_json,
)


def construir_parser() -> argparse.ArgumentParser:
    """Constrói o parser de argumentos da CLI conforme interface fixa do desafio."""
    parser = argparse.ArgumentParser(
        prog="motor-reembolso",
        description="Motor de calculo de reembolso de despesas corporativas (Politica v4).",
    )
    subparsers = parser.add_subparsers(dest="comando", required=True)

    calc_parser = subparsers.add_parser(
        "calcular",
        help="Lê um arquivo JSON de despesas e escreve o resultado da avaliação em JSON.",
    )
    calc_parser.add_argument(
        "--input",
        "-i",
        required=True,
        help="Caminho do arquivo JSON de entrada (ex: exemplos/Envelope/despesas-envelope.json).",
    )
    calc_parser.add_argument(
        "--output",
        "-o",
        required=True,
        help="Caminho do arquivo JSON de saída (ex: resultado.json).",
    )
    calc_parser.add_argument(
        "--politica",
        "-p",
        default=str(CAMINHO_POLITICA_V4_PADRAO),
        help="Caminho do arquivo JSON de política externa por centro de custo (padrão: exemplos/Envelope/politica-v4.json).",
    )
    calc_parser.add_argument(
        "--cambio",
        "-c",
        default=str(CAMINHO_CAMBIO_PADRAO),
        help="Caminho do arquivo JSON de taxas de câmbio por data (padrão: exemplos/Envelope/cambio.json).",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Ponto de entrada principal da CLI."""
    parser = construir_parser()
    args = parser.parse_args(argv)

    if args.comando == "calcular":
        colaborador, periodo, despesas = carregar_entrada_json(args.input)
        politica = carregar_politica_json(args.politica) if Path(args.politica).exists() else None
        cambio = carregar_cambio_json(args.cambio) if Path(args.cambio).exists() else None
        relatorio = avaliar_relatorio(
            colaborador,
            periodo,
            despesas,
            politica=politica,
            cambio=cambio,
        )
        salvar_saida_json(relatorio, args.output)
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
