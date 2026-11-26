# Sessão 03 — Absorção do Envelope Lacrado do Dia 2 (Política v4 por Centro de Custo e Câmbio Internacional)

**Data:** 2026-11-25 / 2026-11-26  
**Fase SDD:** `spec.md` v2.0 (`D-004`) → `plan.md` v2.0 / `tasks.md` Fase 5 (`T-008`..`T-010`) → `D-005` → `RELATORIO.md`  
**Nota de privacidade:** Caminhos locais foram sanitizados para `<workspace>` conforme instruções do `FAQ.md`.

---

## Interação 1 — Auditoria Final da Parte 1 e Abertura do Envelope Lacrado

**Usuário:**
> Faça um double check para ter certeza que concluimos todas as exigencias propostas na parte 1 do desafio, para que então possamos dar andamento a segunda parte

**Agente:**
- Executou `git status`, `git log --oneline`, `python -m pytest -v` (15 passed) e validou a CLI, confirmando que todos os critérios do Dia 1 estavam 100% atendidos e sincronizados com `origin/main` (`5584cf6`).

**Usuário:**
> A parte 2 do desafio esta no caminho sdd-desafio\exemplos\Envelope, leia o arquivo 00-ENVELOPE-LACRADO.md

**Agente:**
- Leu `<workspace>/exemplos/Envelope/00-ENVELOPE-LACRADO.md`, `politica-v4.json`, `cambio.json`, `despesas-envelope.json` e `despesas-envelope-cc-desconhecido.json`.
- Identificou as **6 novas ambiguidades (`AMB-011` a `AMB-016`)** trazidas pela Política v4 e pelos dados do envelope:
  - **`AMB-011`:** Despesa em moeda estrangeira realizada em fim de semana (`e-004` no sábado `2026-07-18`, `30.00 EUR`) sem cotação publicada na data exata em `cambio.json` → decisão de usar o fechamento PTAX do último dia útil bancário imediatamente anterior (`2026-07-17`, `EUR = 5.96`).
  - **`AMB-012`:** Despesa em moeda estrangeira ausente da tabela de câmbio (`e-006`, `55.00 GBP`) → decisão de recusar o item com `MOEDA_NAO_SUPORTADA` sem abortar o lote.
  - **`AMB-013`:** Fronteira de obrigatoriedade de nota fiscal (`> R$ 100,00`) para despesas em moeda estrangeira (`e-003`: `14.50 EUR = R$ 85,26` sem NF vs. `e-005`: `40.00 USD = R$ 220,00` sem NF) → decisão de converter para `BRL` antes de avaliar a exigência de nota fiscal.
  - **`AMB-014`:** Alcance de "aplica-se a política padrão" e categorias com `limite: 0.00` (`hospedagem` em `CC-ENG-PLATAFORMA`) ou omitidas (`hospedagem` em `CC-ADM`) → decisão de aplicar `padrao` apenas quando o `centro_custo` não existe em `centros_custo` (`CC-SUPORTE-N2`), e tratar categorias ausentes do CC ou com `limite <= 0.00` como `CATEGORIA_NAO_REEMBOLSAVEL` (não ativando regime de viagem).
  - **`AMB-015`:** Ativação do regime de viagem (+50%) por despesas válidas em moeda estrangeira (`moeda != "BRL"`) na data `D`, mantendo `hospedagem` e `representacao` em seus limites próprios da tabela.
  - **`AMB-016`:** Vigência imediata e retroativa da Política v4 sobre o lote `exemplos/despesas-exemplo.json` (`CC-ENG-PLATAFORMA`).
- Recomendou manter o Item C opcional explicitamente fora de escopo na Seção 3 e Seção 10 da `spec.md` (já que o maior limite diário possível na `politica-v4.json` é R$ 400,00, abaixo de R$ 500,00, e o enunciado orienta priorizar a consistência da spec).

**Usuário:**
> Estou de acordo, pode seguir com o plano

---

## Interação 2 — Atualização da Spec v2.0 (`D-004`), Plan v2.0, Tasks Fase 5 (`T-008` a `T-010`) e Implementação

1. **Passo 1 — Spec v2.0 e `DECISIONS.md` (`D-004`):**
   - Atualizou `<workspace>/specs/001-motor-reembolso/spec.md` para a versão 2.0 (`RN-001` a `RN-009`, `AMB-001` a `AMB-016`, `CA-001` a `CA-010`).
   - Registrou a entrada `D-004` em `<workspace>/specs/001-motor-reembolso/DECISIONS.md`.
   - Commit: `3e68e54` (`docs(spec): atualiza spec para v2.0 (Politica v4 e cambio) e registra D-004 no DECISIONS.md`).

2. **Passo 2 — Plan v2.0 e Tasks da Fase 5 (`T-008` a `T-010`):**
   - Atualizou `<workspace>/specs/001-motor-reembolso/plan.md` para a versão 2.0 (`DT-004`, `TabelaCambio` e suporte a `politica-v4.json`).
   - Adicionou a **Fase 5 — Envelope (`T-008`, `T-009`, `T-010`)** e atualizou a matriz de cobertura em `<workspace>/specs/001-motor-reembolso/tasks.md`.
   - Versionou os 5 arquivos de `<workspace>/exemplos/Envelope/`.
   - Commit: `c49f175` (`docs(tasks): cria Fase 5 (T-008..T-010), atualiza plan.md para v2.0 e versiona arquivos do envelope`).

3. **Passo 3 — Task `T-008` (`src/models.py`, `src/policy.py`, `src/io_handler.py`):**
   - Estendeu `DespesaInput`, `ResultadoDespesa` e `CodigoMotivo` (`MOEDA_NAO_SUPORTADA`, `CAMBIO_INDISPONIVEL`).
   - Implementou `PoliticaReembolso.de_dict()` com resolução por `centro_custo` e fallback para `padrao`, além de `TabelaCambio` com fallback de dia útil anterior.
   - Adicionou `test_rn_004_amb_014_politica_v4_por_centro_custo_e_fallback_padrao` e `test_rn_009_amb_011_amb_012_tabela_cambio_e_fallback_fim_de_semana` (17 passed).
   - Commit: `5a6a4b3` (`feat(T-008): estende modelos, politica v4 por centro de custo e tabela de cambio com fallback`).

4. **Passo 4 — Task `T-009` (`src/engine.py`):**
   - Atualizou o pipeline em 2 passagens em `src/engine.py` para executar `converter_moeda_despesa` (`RN-009`) antes de `validar_nota_fiscal` (`RN-005`), ativar viagem por moeda estrangeira (`RN-007` / `AMB-015`) e aplicar os limites do centro de custo (`RN-008`).
   - Adicionou `test_rn_005_rn_009_amb_013_nota_fiscal_apos_conversao_cambial` e `test_rn_007_amb_015_moeda_estrangeira_ativa_viagem` (19 passed).
   - Commit: `c707d5c` (`feat(T-009): atualiza motor para conversao cambial RN-009, viagem por moeda estrangeira e limites por CC`).

---

## Interação 3 — Task `T-010`: Detecção de Reincidência de Erro Aritmético nos Totais (`D-005`) e Fechamento

- Ao rodar `python -m pytest` na **`T-010`** com os testes dos 3 lotes completos (`test_ca_001_lote_referencia_despesas_exemplo`, `test_ca_009_lote_envelope_cc_comercial_e_cambio` e `test_ca_010_lote_envelope_cc_desconhecido_fallback_padrao`), todas as decisões individuais dos 28 itens passaram, mas os totais agregados de `CA-001` e `CA-009` acusaram erro de soma manual na spec:
  - Em `CA-001` (v4): os 7 itens reembolsados somam `72.50 + 2.50 + 80.00 + 54.90 + 33.33 + 47.20 + 61.00 = 351.43` (e não `373.93`).
  - Em `CA-009`: os itens válidos convertidos para BRL somam `340.00 + 130.46 + 85.26 + 178.80 + 220.00 + 1200.00 + 95.00 + 120.00 + 88.00 = 2457.52` (e não `2517.52`).
- **Correção via Spec (`D-005`):**
  - Atualizada `spec.md` v2.0 e registrada a decisão `D-005` em `DECISIONS.md` (commit `467c3b3`).
  - Finalizada a `T-010` com 22/22 testes passando (`aca19ac`).
- **Fechamento do Relatório (`docs/RELATORIO.md`):**
  - Preenchida a seção **"O envelope"** com as métricas exatas do `git diff 5584cf6 aca19ac --stat`, análise do que a arquitetura absorveu de graça vs. o que resistiu, e autocrítica sobre `D-005`.
