# Sessão 02 — Implementação Guiada por Tasks (`T-001` a `T-007`), Detecção de Erro Aritmético em `CA-001` (`D-003`) e Testes Automatizados (Dia 1 - Tarde)

**Data:** 2026-11-25  
**Fase SDD:** `T-001` → `T-002` → `T-003` → `T-004` → `T-005` → `T-006` (`D-003`) → `T-007`  
**Nota de privacidade:** Caminhos locais foram sanitizados para `<workspace>` conforme instruções do `FAQ.md`.

---

## Interação 1 — Verificação da Frequência e Granularidade de Commits

**Usuário:**
> Onde aplicou o comit ?

**Agente:**
- Executou `git status`, `git remote -v` e `git log -n 6 --oneline`.
- Explicou que os 5 commits de documentação estavam aplicados na branch local `main`, prontos para `git push` ao fork remoto `origin`.

**Usuário:**
> O desafio especifica algo em relação a frequencia de commits ?

**Agente:**
- Citou a `RUBRICA.md` (Critério 2 — Rastreabilidade, linhas 44–48 e Penalidades transversais, linha 107) e o `DESAFIO.md` (Regra 1):
  - Granularidade compatível com as tasks (1 commit por task concluída, marcando `[x]` em `tasks.md` progressivamente ao longo do caminho, não tudo no fim);
  - Ordem temporal no `git log` respeitando `spec` → `plan` → `tasks` → `código`.

**Usuário:**
> Sim

---

## Interação 2 — Execução Sequencial das Tasks `T-001` a `T-005`

**Usuário:**
> Podemos seguir ?

**Agente:**
1. **Task `T-001` (Fundação — Modelos e Política):**
   - Implementou `<workspace>/src/models.py` (`arredondar_moeda` com `Decimal` e `ROUND_HALF_UP`, `normalizar_texto`, `DespesaInput`, `ResultadoDespesa`, `ResumoProcessamento`, `RelatorioReembolso`) e `<workspace>/src/policy.py` (`PoliticaReembolso`).
   - Criou os testes `test_rn_001_amb_009_arredondamento_half_up` e `test_rn_001_amb_003_normalizacao_categoria` em `<workspace>/tests/test_engine.py`.
   - Executou `python -m pytest -v` (2 passed), marcou `[x]` em `T-001` no `tasks.md` e realizou o commit `48afcd5` (`feat(T-001): estrutura modelos de dominio, politica e normalizacao RN-001`).

2. **Task `T-002` (Fundação — Parser e Serializador JSON com `Decimal`):**
   - Implementou `<workspace>/src/io_handler.py` utilizando `json.loads(..., parse_float=Decimal)` (conforme `DT-002` do `plan.md`).
   - Adicionou `test_rn_001_io_parsing_e_serializacao_json` em `<workspace>/tests/test_engine.py`.
   - Executou `python -m pytest -v` (3 passed), marcou `[x]` em `T-002` no `tasks.md` e realizou o commit `98de944` (`feat(T-002): implementa parser e serializador JSON com precisao Decimal`).

3. **Task `T-003` (Regras de Negócio — Valores não positivos e Período de competência):**
   - Implementou `validar_valor_positivo` (`RN-002`, `AMB-006`) e `validar_periodo_competencia` (`RN-003`, `AMB-005`, `AMB-010`) em `<workspace>/src/engine.py`.
   - Adicionou os testes `test_rn_002_amb_006_recusa_valor_negativo_ou_zero` e `test_rn_003_amb_005_amb_010_periodo_competencia_e_fim_de_semana`.
   - Executou `python -m pytest -v` (5 passed), marcou `[x]` em `T-003` no `tasks.md` e realizou o commit `eb730db` (`feat(T-003): implementa validacao de valores nao positivos e periodo de competencia`).

4. **Task `T-004` (Regras de Negócio — Categorias, Duplicatas e Nota Fiscal):**
   - Implementou `validar_categoria_politica` (`RN-004`, `AMB-003`), `validar_duplicidade` (`RN-006`, `AMB-004`) e `validar_nota_fiscal` (`RN-005`, `AMB-002`) em `<workspace>/src/engine.py`.
   - Adicionou os testes correspondentes em `<workspace>/tests/test_engine.py`.
   - Executou `python -m pytest -v` (8 passed), marcou `[x]` em `T-004` no `tasks.md` e realizou o commit `d0a9dba` (`feat(T-004): implementa elegibilidade de categoria, duplicatas e nota fiscal acima de 100`).

5. **Task `T-005` (Regras de Negócio — Regime de Viagem e Limite Diário Cumulativo):**
   - Implementou `apurar_datas_em_viagem` (`RN-007`, `AMB-007`, `AMB-008`, respeitando `D-002`), `aplicar_limite_diario` (`RN-008`, `AMB-001`) e o pipeline em duas passagens `avaliar_relatorio` (`DT-001`) em `<workspace>/src/engine.py`.
   - Adicionou `test_rn_007_amb_007_amb_008_regime_viagem_hospedagem_valida` e `test_rn_008_amb_001_limite_diario_cumulativo_e_reembolso_parcial`.
   - Executou `python -m pytest -v` (10 passed), marcou `[x]` em `T-005` no `tasks.md` e realizou o commit `1bf9600` (`feat(T-005): implementa regime de viagem RN-007 e limite diario com reembolso parcial RN-008`).

---

## Interação 3 — Task `T-006`: Detecção de Erro Aritmético em `CA-001` e Registro `D-003`

- Ao implementar `<workspace>/tests/test_edge_cases.py` (`test_ca_001_lote_referencia_despesas_exemplo`) para a **`T-006`**, todas as 14 decisões individuais de `d-001` a `d-014` bateram com a tabela esperada, mas a asserção do resumo falhou (`AssertionError: assert 3 == 4` em `quantidade_aprovadas` e `Decimal('1861.84')` em `total_solicitado`).
- **Diagnóstico:** Ao escrever `CA-001` na `spec.md` v1.0/v1.1, o agente havia cometido um erro de soma manual:
  - As 13 despesas positivas de `exemplos/despesas-exemplo.json` somam exatamente `72.50 + 38.00 + 100.00 + 100.01 + 89.00 + 54.90 + 54.90 + 41.00 + 480.00 + 33.33 + 47.20 + 690.00 + 61.00 = 1861.84` (e não `1962.84`, que tinha R$ 101,00 a mais).
  - As despesas `APROVADA` são 3 (`d-006`, `d-011`, `d-012`), as `APROVADA_PARCIALMENTE` são 4 (`d-001`, `d-003`, `d-010`, `d-014`) e as `RECUSADA` são 7 (`d-002`, `d-004`, `d-005`, `d-007`, `d-008`, `d-009`, `d-013`).
- **Correção via Spec (`D-003`):**
  - Atualizada `<workspace>/specs/001-motor-reembolso/spec.md` para a versão 1.2 corrigindo os totais de `CA-001`.
  - Registrada a decisão `D-003` em `<workspace>/specs/001-motor-reembolso/DECISIONS.md`.
  - Atualizado `tests/test_edge_cases.py`, com todos os 13 testes passando (`06dadda`).

---

## Interação 4 — Task `T-007`: Interface CLI, Testes E2E e Documentação no `README.md`

- Implementou `<workspace>/src/cli.py` com o subcomando `calcular --input <arquivo> --output <arquivo>`.
- Implementou `<workspace>/tests/test_cli.py` testando tanto a função `main()` quanto a invocação real via subprocesso `python -m src.cli calcular ...`.
- Substituiu `<workspace>/README.md` pelas instruções completas de execução e testes do projeto conforme exigido pelo enunciado.
- Marcou `[x]` em `T-007` no `tasks.md` e `[x]` em `CA-001`..`CA-008` na `spec.md`.

---

## Interação 5 — Preenchimento do Relatório (`docs/RELATORIO.md`) com Evidências dos 4 Ds

**Usuário:**
> Já deixe o relatorio.mds preenchido

**Agente:**
- Preencheu `<workspace>/docs/RELATORIO.md` com evidências verificáveis (hashes de commit `0ba5346`, `6e4fb09`, `cabadd2`, `053b90a`, `48afcd5`, `98de944`, `eb730db`, `d0a9dba`, `1bf9600`, `5fe5c5b`, `06dadda`, `9f52c16` e referências às sessões `01` e `02`) cobrindo:
  - **Delegação:** Tabela completa de divisão de responsabilidades, arrependimento sobre a soma manual delegada em `CA-001` e governança via `CLAUDE.md`.
  - **Descrição:** Antes (commit `0ba5346`) e Depois (commit `053b90a`, `D-002`) da regra `RN-007` / `AMB-008`.
  - **Discernimento:** Dois casos concretos e auditáveis onde o agente errou e foi corrigido (`Caso 1: D-002` — regra morta do limite de R$ 250 de hospedagem ao aplicar +50% sobre si mesma; `Caso 2: D-003` — erro aritmético de R$ 101,00 na soma mental de `CA-001` detectado na execução de `test_ca_001_lote_referencia_despesas_exemplo` no commit `5fe5c5b`).
  - **Diligência:** Procedimento real de verificação, percentual de leitura de diff (85%) e análise crítica da suíte de testes.
  - **Fechamento:** Reflexão crítica sobre SDD e armadilhas de fluência textual da IA, deixando a seção **O envelope** pronta para ser preenchida após a mudança de requisito do Dia 2.
