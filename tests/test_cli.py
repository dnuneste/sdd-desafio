"""Testes ponta a ponta da CLI do motor de reembolso (T-007)."""

import json
import subprocess
import sys
from pathlib import Path

from src.cli import main


def test_cli_calcular_gera_arquivo_saida_valido(tmp_path: Path) -> None:
    """Verifica execução da CLI via função main() e estrutura completa do JSON gerado (CA-001)."""
    saida = tmp_path / "resultado.json"
    codigo = main(
        [
            "calcular",
            "--input",
            "exemplos/despesas-exemplo.json",
            "--output",
            str(saida),
        ]
    )
    assert codigo == 0
    assert saida.exists()

    dados = json.loads(saida.read_text(encoding="utf-8"))
    assert dados["colaborador"]["id"] == "c-0417"
    assert dados["periodo"]["competencia"] == "2026-07"
    assert dados["em_viagem"] is True
    assert dados["resumo"] == {
        "total_solicitado": 1861.84,
        "total_reembolsado": 585.43,
        "total_glosado": 1276.41,
        "quantidade_despesas": 14,
        "quantidade_aprovadas": 3,
        "quantidade_aprovadas_parcialmente": 4,
        "quantidade_recusadas": 7,
    }
    assert len(dados["resultados"]) == 14


def test_cli_subprocess_modulo_python(tmp_path: Path) -> None:
    """Verifica execução real via subprocesso `python -m src.cli calcular ...` conforme README.md."""
    saida = tmp_path / "resultado_sub.json"
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "src.cli",
            "calcular",
            "--input",
            "exemplos/despesas-exemplo.json",
            "--output",
            str(saida),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, f"Erro na CLI: {proc.stderr}"
    assert saida.exists()
