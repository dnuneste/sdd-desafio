"""Interface de linha de comando (CLI) do Motor de Cálculo de Reembolso (T-007)."""

from __future__ import annotations

import argparse
import sys
from typing import Sequence

from src.engine import avaliar_relatorio
from src.io_handler import carregar_entrada_json, salvar_saida_json


def construir_parser() -> argparse.ArgumentParser:
    """Constrói o parser de argumentos da CLI conforme interface fixa do desafio."""
    parser = argparse.ArgumentParser(
        prog="motor-reembolso",
        description="Motor de calculo de reembolso de despesas corporativas.",
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
        help="Caminho do arquivo JSON de entrada (ex: exemplos/despesas-exemplo.json).",
    )
    calc_parser.add_argument(
        "--output",
        "-o",
        required=True,
        help="Caminho do arquivo JSON de saída (ex: resultado.json).",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Ponto de entrada principal da CLI."""
    parser = construir_parser()
    args = parser.parse_args(argv)

    if args.comando == "calcular":
        colaborador, periodo, despesas = carregar_entrada_json(args.input)
        relatorio = avaliar_relatorio(colaborador, periodo, despesas)
        salvar_saida_json(relatorio, args.output)
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
