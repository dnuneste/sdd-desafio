# Tasks — Motor de Cálculo de Reembolso

> Cada task é pequena o bastante para virar **um commit**. Se você não consegue
> descrever o critério de aceite como "o teste X passa", a task está grande demais.
>
> Marque `[x]` conforme conclui — ao longo do caminho, não tudo no fim. O histórico
> de quando cada task foi marcada é lido na correção.

**Formato do commit:** `feat(T-003): <descrição>` · `test(T-003): <descrição>`

---

## Fase 1 — Fundação

- [x] **T-001** — Estruturar modelos de domínio, parâmetros da política e normalização monetária/textual de entrada (`src/models.py`, `src/policy.py`)
  - **Atende:** RN-001, AMB-003, AMB-009
  - **Aceite:** `tests/test_engine.py::test_rn_001_amb_009_arredondamento_half_up` e `tests/test_engine.py::test_rn_001_amb_003_normalizacao_categoria` passam
  - **Commit:** `feat(T-001)`

- [x] **T-002** — Implementar parser de entrada JSON e serializador de saída JSON com precisão `Decimal` (`src/io_handler.py`)
  - **Atende:** RN-001, AMB-009 (Seção 4 da spec — Contrato de Entrada e Saída)
  - **Aceite:** `tests/test_engine.py::test_rn_001_io_parsing_e_serializacao_json` passa
  - **Commit:** `feat(T-002)`

## Fase 2 — Regras de negócio

- [ ] **T-003** — Implementar validação de valores não positivos / estornos e período de competência (`src/engine.py`)
  - **Atende:** RN-002, RN-003, AMB-005, AMB-006, AMB-010, CA-006, CA-007
  - **Aceite:** `tests/test_engine.py::test_rn_002_amb_006_recusa_valor_negativo_ou_zero` e `tests/test_engine.py::test_rn_003_amb_005_amb_010_periodo_competencia_e_fim_de_semana` passam
  - **Commit:** `<pendente>`

- [ ] **T-004** — Implementar validação de categorias elegíveis, detecção de duplicatas e exigência de nota fiscal acima de R$ 100,00 (`src/engine.py`)
  - **Atende:** RN-004, RN-005, RN-006, AMB-002, AMB-003, AMB-004, CA-003, CA-004, CA-005
  - **Aceite:** `tests/test_engine.py::test_rn_004_amb_003_categoria_fora_da_politica`, `tests/test_engine.py::test_rn_005_amb_002_fronteira_nota_fiscal_100_reais` e `tests/test_engine.py::test_rn_006_amb_004_deteccao_duplicatas` passam
  - **Commit:** `<pendente>`

- [ ] **T-005** — Implementar apuração de regime de viagem (+50%) e controle de saldo diário com reembolso parcial por categoria (`src/engine.py`)
  - **Atende:** RN-007, RN-008, AMB-001, AMB-007, AMB-008, CA-002, CA-008
  - **Aceite:** `tests/test_engine.py::test_rn_007_amb_007_amb_008_regime_viagem_hospedagem_valida` e `tests/test_engine.py::test_rn_008_amb_001_limite_diario_cumulativo_e_reembolso_parcial` passam
  - **Commit:** `<pendente>`

## Fase 3 — Casos de borda

- [ ] **T-006** — Adicionar suíte completa de testes dos casos de borda da Seção 7 da spec e validar lote de referência `exemplos/despesas-exemplo.json` (`tests/test_edge_cases.py`)
  - **Atende:** CA-001 a CA-008, RN-001 a RN-008, AMB-001 a AMB-010
  - **Aceite:** `tests/test_edge_cases.py::test_ca_001_lote_referencia_despesas_exemplo` e todos os testes de borda em `tests/test_edge_cases.py` passam
  - **Commit:** `<pendente>`

## Fase 4 — Saída e CLI

- [ ] **T-007** — Implementar interface CLI (`calcular --input ... --output ...`), testes ponta a ponta da CLI e atualizar `README.md` com instruções de execução (`src/cli.py`, `tests/test_cli.py`, `README.md`)
  - **Atende:** CA-001 (Interface CLI fixa do desafio)
  - **Aceite:** `tests/test_cli.py::test_cli_calcular_gera_arquivo_saida_valido` passa e o comando `python -m src.cli calcular --input exemplos/despesas-exemplo.json --output resultado.json` executa com código 0
  - **Commit:** `<pendente>`

---

## Fase 5 — Envelope (criar no Dia 2)

<Novas tasks a partir da mudança de requisito. Numeração continua de onde parou —
não reinicie e não renumere as antigas: a numeração é o eixo da rastreabilidade.>

---

## Cobertura

Preencha ao fechar cada fase. É a sua própria checagem de rastreabilidade — e é
exatamente a matriz que a correção vai montar.

| Regra da spec | Task | Teste |
|---|---|---|
| RN-001 | T-001, T-002 | `test_rn_001_amb_009_arredondamento_half_up`, `test_rn_001_amb_003_normalizacao_categoria`, `test_rn_001_io_parsing_e_serializacao_json` |
| RN-002 | T-003, T-006 | `test_rn_002_amb_006_recusa_valor_negativo_ou_zero` |
| RN-003 | T-003, T-006 | `test_rn_003_amb_005_amb_010_periodo_competencia_e_fim_de_semana` |
| RN-004 | T-004, T-006 | `test_rn_004_amb_003_categoria_fora_da_politica` |
| RN-005 | T-004, T-006 | `test_rn_005_amb_002_fronteira_nota_fiscal_100_reais` |
| RN-006 | T-004, T-006 | `test_rn_006_amb_004_deteccao_duplicatas` |
| RN-007 | T-005, T-006 | `test_rn_007_amb_007_amb_008_regime_viagem_hospedagem_valida` |
| RN-008 | T-005, T-006 | `test_rn_008_amb_001_limite_diario_cumulativo_e_reembolso_parcial` |
| AMB-001 | T-005, T-006 | `test_rn_008_amb_001_limite_diario_cumulativo_e_reembolso_parcial` |
| AMB-002 | T-004, T-006 | `test_rn_005_amb_002_fronteira_nota_fiscal_100_reais` |
| AMB-003 | T-001, T-004, T-006 | `test_rn_001_amb_003_normalizacao_categoria`, `test_rn_004_amb_003_categoria_fora_da_politica` |
| AMB-004 | T-004, T-006 | `test_rn_006_amb_004_deteccao_duplicatas` |
| AMB-005 | T-003, T-006 | `test_rn_003_amb_005_amb_010_periodo_competencia_e_fim_de_semana` |
| AMB-006 | T-003, T-006 | `test_rn_002_amb_006_recusa_valor_negativo_ou_zero` |
| AMB-007 | T-005, T-006 | `test_rn_007_amb_007_amb_008_regime_viagem_hospedagem_valida` |
| AMB-008 | T-005, T-006 | `test_rn_007_amb_007_amb_008_regime_viagem_hospedagem_valida` |
| AMB-009 | T-001, T-006 | `test_rn_001_amb_009_arredondamento_half_up` |
| AMB-010 | T-003, T-006 | `test_rn_003_amb_005_amb_010_periodo_competencia_e_fim_de_semana` |
| CA-001..CA-008 | T-006, T-007 | `test_ca_001_lote_referencia_despesas_exemplo`, `test_cli_calcular_gera_arquivo_saida_valido` |
