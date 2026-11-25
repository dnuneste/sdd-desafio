# Log de Decisões e Mudanças de Spec

> Uma entrada **toda vez** que a spec mudar. Este arquivo é a prova de que a spec
> foi tratada como artefato vivo e não como cerimônia de abertura.
>
> Spec que não muda em dois dias é spec que ninguém consultou. Mudança não é
> demérito — mudança não registrada é.

Ordem cronológica inversa: a mais recente primeiro.

---

## D-005 — Reincidência do erro aritmético do agente nos totais agregados de `CA-001` (v4) e `CA-009` · `2026-11-25`

**Gatilho:** Execução de `python -m pytest` na `T-010`. Os testes `test_ca_001_lote_referencia_despesas_exemplo` e `test_ca_009_lote_envelope_cc_comercial_e_cambio` falharam **apenas nos totais agregados** — as contagens por status e os resultados item a item estavam corretos. `CA-010` passou.

**O que mudou na spec (`spec.md` v2.0, Seção 9):**
- **`CA-001`:** `total_reembolsado` de `373.93` → **`351.43`**; `total_glosado` de `1487.91` → **`1510.41`**. Conferência: `72.50 + 2.50 + 80.00 + 54.90 + 33.33 + 47.20 + 61.00 = 351.43`.
- **`CA-009`:** `total_solicitado` de `2517.52` → **`2457.52`**; `total_glosado` de `1283.80` → **`1223.80`**. Conferência: `340.00 + 130.46 + 85.26 + 178.80 + 220.00 + 0.00 (GBP) + 1200.00 + 95.00 + 120.00 + 88.00 = 2457.52`; glosas `40.00 + 43.80 + 220.00 + 800.00 + 120.00 = 1223.80`.

**Por quê:** Nenhuma regra de negócio mudou. É a **segunda ocorrência do mesmo padrão já registrado em `D-003`**: o agente acerta a decisão de cada item, mas erra a soma mental de colunas ao redigir critérios de aceite agregados. A lição de `D-003` foi registrada no relatório, mas não virou uma salvaguarda de processo — e por isso o erro se repetiu.

**O que isso invalidou:** Os totais de `CA-001` e `CA-009` em `spec.md` v2.0 (commit `3e68e54`) e as asserções correspondentes em `tests/test_edge_cases.py` e `tests/test_cli.py`.

**Tasks afetadas:** `T-010`.

**Custo:** 4 arquivos (`spec.md`, `DECISIONS.md`, `tests/test_edge_cases.py`, `tests/test_cli.py`), ~5 minutos.

**Ação de processo:** Totais agregados de critérios de aceite passam a ser conferidos somando os valores item a item da tabela de casos de borda **antes** de congelar a spec, e não por soma mental do agente.

---

## D-004 — Absorção do Envelope Lacrado (Política de Reembolso v4: Limites por Centro de Custo e Câmbio Internacional) · `2026-11-25`

**Gatilho:** Recebimento do Envelope Lacrado do Dia 2 (`exemplos/Envelope/00-ENVELOPE-LACRADO.md`) acompanhado de `politica-v4.json`, `cambio.json`, `despesas-envelope.json` e `despesas-envelope-cc-desconhecido.json`.

**O que mudou na spec (`spec.md` v1.2 → v2.0):**
1. **Fora de escopo (Seção 3) e O que fica em aberto (Seção 10):**
   - Removida a restrição contra conversão de moedas estrangeiras (agora parte obrigatória do Item B).
   - Declarado explicitamente fora de escopo o Item C opcional ("Fila de aprovação manual acima de R$ 500"), inclusive porque o maior teto diário possível em `politica-v4.json` é R$ 400,00 (`hospedagem` em `CC-COMERCIAL`).
2. **Contrato de Entrada e Saída (Seção 4):**
   - Adicionado o campo opcional `moeda` (ISO 4217, padrão `"BRL"`) em `despesas[]` e os documentos externos `politica-v4.json` e `cambio.json`.
   - Adicionados em `resultados[]` os campos `moeda_original`, `valor_moeda_original` e `taxa_cambio_aplicada`, além dos novos códigos de motivo `MOEDA_NAO_SUPORTADA` e `CAMBIO_INDISPONIVEL`.
3. **Regras de Negócio alteradas e criadas:**
   - **`RN-001`:** Passa a normalizar também o campo `moeda` (`"BRL"` quando omitido, uppercase).
   - **`RN-004` (De lista fixa de 3 categorias → Para tabela externa por Centro de Custo):** Resolve a tabela de `colaborador.centro_custo` em `politica-v4.json` (ou fallback para `padrao` se o CC não estiver cadastrado). Categorias ausentes da tabela do CC ou com `limite <= 0.00` (ex.: `hospedagem` em `CC-ENG-PLATAFORMA`) são recusadas com `CATEGORIA_NAO_REEMBOLSAVEL`.
   - **`RN-005`:** Especificado que a comparação `> 100.00` para exigência de nota fiscal incide sobre o valor já convertido para `BRL` (`valor_original`).
   - **`RN-006`:** A chave de duplicidade passa a incluir `moeda_original` e `valor_moeda_original`.
   - **`RN-007`:** Além de flag `em_viagem` e datas `D`/`D+1` de `hospedagem` válida, qualquer despesa válida em moeda estrangeira (`moeda_original != "BRL"`) ativa o regime de viagem na sua `data`. O bônus de +50% continua aplicando-se às categorias cotidianas (`alimentacao` e `transporte_urbano`), mantendo `hospedagem` e `representacao` em seus tetos próprios da tabela.
   - **`RN-009` (Nova):** Conversão cambial para `BRL` usando a taxa da data da despesa em `cambio.json`, com fallback para o último dia útil bancário anterior (`data_cotacao <= data`) em finais de semana/feriados e recusa com `MOEDA_NAO_SUPORTADA` quando a moeda não existir na tabela (ex.: `GBP`).
4. **Novas Ambiguidades Resolvidas (`AMB-011` a `AMB-016`) e Critérios de Aceite (`CA-001` atualizado para v4, `CA-009` e `CA-010` criados):**
   - `AMB-011`: Fallback de cotação em sábado (`e-004` em `18/07` usa cotação de sexta `17/07`).
   - `AMB-012`: Moeda não cadastrada (`e-006` em `GBP` → `MOEDA_NAO_SUPORTADA`).
   - `AMB-013`: Nota fiscal avaliada sobre o valor convertido em `BRL` (`e-005`: `40 USD = R$ 220` sem NF → `SEM_NOTA_FISCAL`).
   - `AMB-014`: Fallback para `padrao` apenas quando o CC não existe na tabela (`CC-SUPORTE-N2`), e `limite: 0.00` em `CC-ENG-PLATAFORMA` tratado como `CATEGORIA_NAO_REEMBOLSAVEL`.
   - `AMB-015`: Moeda estrangeira válida ativa regime de viagem na data `D`; `representacao` mantém teto fixo de R$ 300,00.
   - `AMB-016`: Vigência retroativa da Política v4 sobre `exemplos/despesas-exemplo.json` (`CC-ENG-PLATAFORMA`).

**Por quê:** Exigência obrigatória do Envelope Lacrado do Dia 2 (Política de Reembolso v4 com vigência imediata e retroativa à competência `2026-07`).

**O que isso invalidou:**
- Os limites fixos em código da Política v3 (`src/policy.py` precisa carregar `politica-v4.json` e resolver por `centro_custo`).
- O critério `CA-001` sob a v3 para `CC-ENG-PLATAFORMA` (que agora tem `alimentacao` = R$ 75,00 e `hospedagem` não reembolsável sob a v4).

**Tasks afetadas:**
- Tasks antigas `T-001` a `T-007` permanecem no histórico como Fase 1 a 4.
- Criadas na **Fase 5 — Envelope** em `tasks.md`: `T-008`, `T-009`, `T-010` e `T-011`.

**Custo:** 4 arquivos de documentação atualizados antes do código (`spec.md`, `DECISIONS.md`, `plan.md`, `tasks.md`), seguidos da implementação cirúrgica em `src/` e `tests/`.

---

## D-003 — Correção de erro aritmético de soma manual do agente no critério de aceite `CA-001` · `2026-11-25`

**Gatilho:** Ao executar o teste automatizado `test_ca_001_lote_referencia_despesas_exemplo` na `T-006`, o motor com `Decimal` revelou que a soma manual feita pelo agente ao redigir `CA-001` na `spec.md` estava errada (`1962.84` vs `1861.84` e contagem `4 aprovadas / 6 recusadas` vs `3 aprovadas / 7 recusadas`).

**O que mudou na spec:**
- **`CA-001` (Seção 9 da `spec.md`, v1.2):**
  - **De:** `total_solicitado: 1962.84`, `total_reembolsado: 585.43`, `total_glosado: 1377.41`, `quantidade_aprovadas: 4`, `quantidade_aprovadas_parcialmente: 4` e `quantidade_recusadas: 6`.
  - **Para:** `total_solicitado: 1861.84`, `total_reembolsado: 585.43`, `total_glosado: 1276.41`, `quantidade_aprovadas: 3`, `quantidade_aprovadas_parcialmente: 4` e `quantidade_recusadas: 7`.

**Por quê:** As 13 despesas positivas de `exemplos/despesas-exemplo.json` somam exatamente `72.50 + 38.00 + 100.00 + 100.01 + 89.00 + 54.90 + 54.90 + 41.00 + 480.00 + 33.33 + 47.20 + 690.00 + 61.00 = 1861.84`. Além disso, as despesas integralmente aprovadas são 3 (`d-006`, `d-011`, `d-012`), as parcialmente aprovadas são 4 (`d-001`, `d-003`, `d-010`, `d-014`) e as recusadas são 7 (`d-002`, `d-004`, `d-005`, `d-007`, `d-008`, `d-009`, `d-013`). Nenhuma regra de negócio (`RN-001`..`RN-008`) mudou; o erro estava na aritmética mental do agente ao escrever `CA-001`.

**O que isso invalidou:** Os números agregados esperados em `CA-001` na `spec.md` v1.1 e na asserção inicial de `tests/test_edge_cases.py`.

**Tasks afetadas:** `T-006` (`tests/test_edge_cases.py`).

**Custo:** 3 arquivos tocados (`spec.md`, `DECISIONS.md`, `tests/test_edge_cases.py`), ~3 minutos.

---

## D-002 — Correção da incidência do bônus de viagem (+50%) sobre a categoria `hospedagem` · `2026-11-25`

**Gatilho:** Revisão humana de negócio sobre a `spec.md` v1.0 (`0ba5346`) antes do início da implementação. Identificou-se uma contradição lógica na proposta inicial do agente para `RN-007` e `AMB-008`.

**O que mudou na spec:**
- **`RN-007`, `RN-008`, `AMB-007` e `AMB-008`:**
  - **De:** O regime de viagem (+50%) ativado por uma despesa de `hospedagem` válida ampliava os limites de todas as três categorias, inclusive da própria `hospedagem` (de R$ 250,00 para R$ 375,00).
  - **Para:** O regime de viagem (+50%) amplia apenas os limites diários das categorias cotidianas (`alimentacao` de R$ 60,00 para R$ 90,00 e `transporte_urbano` de R$ 80,00 para R$ 120,00), mantendo o limite de `hospedagem` em **R$ 250,00 por diária**.
- **`CA-001` e `CA-008`:** No lote de referência `exemplos/despesas-exemplo.json`, o reembolso de `d-010` passa de `375.00` para `250.00` (glosa `230.00`), atualizando `total_reembolsado` de `710.43` para `585.43` e `total_glosado` de `1252.41` para `1377.41`.

**Por quê:** Toda despesa de `hospedagem` já ocorre em contexto de viagem. Se a presença de uma hospedagem válida sempre ativa o regime de viagem na sua data `D` e o bônus de +50% também incidisse sobre `hospedagem`, o limite de R$ 250,00 do item 3 da política do RH jamais seria aplicado em nenhum cenário possível (tornando-se regra morta).

**O que isso invalidou:** O teto ampliado de R$ 375,00 para `hospedagem` em `RN-007`/`RN-008` e os totais esperados em `CA-001` e `CA-008` da versão 1.0 da spec.

**Tasks afetadas:** `T-005` e `T-006` (ainda não implementadas; os critérios de aceite dessas tasks passam a validar a versão 1.1 da spec).

**Custo:** 2 arquivos de documentação tocados (`spec.md` e `DECISIONS.md`), ~5 minutos, 0 arquivos de código refeitos por ter sido capturado na revisão da spec antes da codificação.

---

## D-001 — Consolidação inicial da Spec v1.0 e resolução das 10 ambiguidades da política v3 · `2026-11-25`

**Gatilho:** Análise cruzada entre a "Política de Reembolso de Despesas — v3" enviada pelo RH e os 14 itens do arquivo `exemplos/despesas-exemplo.json` antes do início da implementação.

**O que mudou na spec:** Criação das regras `RN-001` a `RN-008`, definição da ordem estrita de precedência (Seção 8), contrato de entrada/saída (Seção 4) e formalização das decisões para as 10 ambiguidades (`AMB-001` a `AMB-010`).

**Por quê:** A política textual do RH omitia a unidade de aplicação (teto cumulativo diário vs. individual), fronteiras numéricas (`> 100.00` vs `>= 100.00`, arredondamento de 3 casas decimais, valores negativos/estornos) e dados ausentes no JSON (`em_viagem` e `quantidade_diarias`).

**O que isso invalidou:** O esqueleto inicial em branco de `spec.md`.

**Tasks afetadas:** Criadas `T-001` a `T-007` em `specs/001-motor-reembolso/tasks.md`.

**Custo:** 1 arquivo de especificação (`spec.md`), 0 linhas de código alteradas (decisão tomada na fase de especificação, antes da escrita de código).
