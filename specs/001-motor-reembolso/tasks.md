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
  - **Commit:** `feat(T-001)` (`48afcd5`)

- [x] **T-002** — Implementar parser de entrada JSON e serializador de saída JSON com precisão `Decimal` (`src/io_handler.py`)
  - **Atende:** RN-001, AMB-009 (Seção 4 da spec — Contrato de Entrada e Saída)
  - **Aceite:** `tests/test_engine.py::test_rn_001_io_parsing_e_serializacao_json` passa
  - **Commit:** `feat(T-002)` (`98de944`)

## Fase 2 — Regras de negócio

- [x] **T-003** — Implementar validação de valores não positivos / estornos e período de competência (`src/engine.py`)
  - **Atende:** RN-002, RN-003, AMB-005, AMB-006, AMB-010, CA-006, CA-007
  - **Aceite:** `tests/test_engine.py::test_rn_002_amb_006_recusa_valor_negativo_ou_zero` e `tests/test_engine.py::test_rn_003_amb_005_amb_010_periodo_competencia_e_fim_de_semana` passam
  - **Commit:** `feat(T-003)` (`eb730db`)

- [x] **T-004** — Implementar validação de categorias elegíveis, detecção de duplicatas e exigência de nota fiscal acima de R$ 100,00 (`src/engine.py`)
  - **Atende:** RN-004, RN-005, RN-006, AMB-002, AMB-003, AMB-004, CA-003, CA-004, CA-005
  - **Aceite:** `tests/test_engine.py::test_rn_004_amb_003_categoria_fora_da_politica`, `tests/test_engine.py::test_rn_005_amb_002_fronteira_nota_fiscal_100_reais` e `tests/test_engine.py::test_rn_006_amb_004_deteccao_duplicatas` passam
  - **Commit:** `feat(T-004)` (`d0a9dba`)

- [x] **T-005** — Implementar apuração de regime de viagem (+50%) e controle de saldo diário com reembolso parcial por categoria (`src/engine.py`)
  - **Atende:** RN-007, RN-008, AMB-001, AMB-007, AMB-008, CA-002, CA-008
  - **Aceite:** `tests/test_engine.py::test_rn_007_amb_007_amb_008_regime_viagem_hospedagem_valida` e `tests/test_engine.py::test_rn_008_amb_001_limite_diario_cumulativo_e_reembolso_parcial` passam
  - **Commit:** `feat(T-005)` (`1bf9600`)

## Fase 3 — Casos de borda

- [x] **T-006** — Adicionar suíte completa de testes dos casos de borda da Seção 7 da spec e validar lote de referência `exemplos/despesas-exemplo.json` (`tests/test_edge_cases.py`)
  - **Atende:** CA-001 a CA-008, RN-001 a RN-008, AMB-001 a AMB-010
  - **Aceite:** `tests/test_edge_cases.py::test_ca_001_lote_referencia_despesas_exemplo` e todos os testes de borda em `tests/test_edge_cases.py` passam
  - **Commit:** `test(T-006)` (`5fe5c5b`, `06dadda`)

## Fase 4 — Saída e CLI

- [x] **T-007** — Implementar interface CLI (`calcular --input ... --output ...`), testes ponta a ponta da CLI e atualizar `README.md` com instruções de execução (`src/cli.py`, `tests/test_cli.py`, `README.md`)
  - **Atende:** CA-001 (Interface CLI fixa do desafio)
  - **Aceite:** `tests/test_cli.py::test_cli_calcular_gera_arquivo_saida_valido` passa e o comando `python -m src.cli calcular --input exemplos/despesas-exemplo.json --output resultado.json` executa com código 0
  - **Commit:** `feat(T-007)` (`9f52c16`)

---

## Fase 5 — Envelope (Dia 2 — Política de Reembolso v4 e Câmbio)

- [ ] **T-008** — Estender modelos, política externa por centro de custo e tabela de câmbio com fallback de dia útil anterior (`src/models.py`, `src/policy.py`, `src/io_handler.py`)
  - **Atende:** RN-001, RN-004, RN-009, AMB-011, AMB-012, AMB-014
  - **Aceite:** `tests/test_engine.py::test_rn_004_amb_014_politica_v4_por_centro_custo_e_fallback_padrao` e `tests/test_engine.py::test_rn_009_amb_011_amb_012_tabela_cambio_e_fallback_fim_de_semana` passam
  - **Commit:** `<pendente>`

- [ ] **T-009** — Atualizar motor de avaliação para conversão cambial antes de nota fiscal, viagem por moeda estrangeira e limites por centro de custo (`src/engine.py`)
  - **Atende:** RN-004, RN-005, RN-007, RN-008, RN-009, AMB-011 a AMB-016
  - **Aceite:** `tests/test_engine.py::test_rn_005_rn_009_amb_013_nota_fiscal_apos_conversao_cambial` e `tests/test_engine.py::test_rn_007_amb_015_moeda_estrangeira_ativa_viagem` passam
  - **Commit:** `<pendente>`

- [ ] **T-010** — Validar lotes do envelope (`despesas-envelope.json`, `despesas-envelope-cc-desconhecido.json`) e vigência retroativa em `despesas-exemplo.json` (`tests/test_edge_cases.py`, `src/cli.py`, `tests/test_cli.py`, `README.md`)
  - **Atende:** CA-001, CA-008, CA-009, CA-010, AMB-016
  - **Aceite:** `tests/test_edge_cases.py::test_ca_001_lote_referencia_despesas_exemplo`, `tests/test_edge_cases.py::test_ca_009_lote_envelope_cc_comercial_e_cambio` e `tests/test_edge_cases.py::test_ca_010_lote_envelope_cc_desconhecido_fallback_padrao` passam
  - **Commit:** `<pendente>`

---

## Cobertura

| Regra da spec | Task | Teste |
|---|---|---|
| RN-001 | T-001, T-002, T-008 | `test_rn_001_amb_009_arredondamento_half_up`, `test_rn_001_amb_003_normalizacao_categoria`, `test_rn_001_io_parsing_e_serializacao_json` |
| RN-002 | T-003, T-006 | `test_rn_002_amb_006_recusa_valor_negativo_ou_zero` |
| RN-003 | T-003, T-006 | `test_rn_003_amb_005_amb_010_periodo_competencia_e_fim_de_semana` |
| RN-004 | T-004, T-008, T-009, T-010 | `test_rn_004_amb_003_categoria_fora_da_politica`, `test_rn_004_amb_014_politica_v4_por_centro_custo_e_fallback_padrao` |
| RN-005 | T-004, T-009, T-010 | `test_rn_005_amb_002_fronteira_nota_fiscal_100_reais`, `test_rn_005_rn_009_amb_013_nota_fiscal_apos_conversao_cambial` |
| RN-006 | T-004, T-006 | `test_rn_006_amb_004_deteccao_duplicatas` |
| RN-007 | T-005, T-009, T-010 | `test_rn_007_amb_007_amb_008_regime_viagem_hospedagem_valida`, `test_rn_007_amb_015_moeda_estrangeira_ativa_viagem` |
| RN-008 | T-005, T-009, T-010 | `test_rn_008_amb_001_limite_diario_cumulativo_e_reembolso_parcial` |
| RN-009 | T-008, T-009, T-010 | `test_rn_009_amb_011_amb_012_tabela_cambio_e_fallback_fim_de_semana`, `test_rn_005_rn_009_amb_013_nota_fiscal_apos_conversao_cambial` |
| AMB-001..AMB-010 | T-001..T-007 | Cobertos na suíte `tests/test_engine.py` e `tests/test_edge_cases.py` |
| AMB-011 | T-008, T-010 | `test_rn_009_amb_011_amb_012_tabela_cambio_e_fallback_fim_de_semana`, `test_ca_009_lote_envelope_cc_comercial_e_cambio` |
| AMB-012 | T-008, T-010 | `test_rn_009_amb_011_amb_012_tabela_cambio_e_fallback_fim_de_semana`, `test_ca_009_lote_envelope_cc_comercial_e_cambio` |
| AMB-013 | T-009, T-010 | `test_rn_005_rn_009_amb_013_nota_fiscal_apos_conversao_cambial`, `test_ca_009_lote_envelope_cc_comercial_e_cambio` |
| AMB-014 | T-008, T-010 | `test_rn_004_amb_014_politica_v4_por_centro_custo_e_fallback_padrao`, `test_ca_010_lote_envelope_cc_desconhecido_fallback_padrao` |
| AMB-015 | T-009, T-010 | `test_rn_007_amb_015_moeda_estrangeira_ativa_viagem`, `test_ca_009_lote_envelope_cc_comercial_e_cambio` |
| AMB-016 | T-010 | `test_ca_001_lote_referencia_despesas_exemplo` |
| CA-001..CA-010 | T-006, T-007, T-010 | `test_ca_001_lote_referencia_despesas_exemplo`, `test_ca_009_lote_envelope_cc_comercial_e_cambio`, `test_ca_010_lote_envelope_cc_desconhecido_fallback_padrao` |
