# Log de Decisões e Mudanças de Spec

> Uma entrada **toda vez** que a spec mudar. Este arquivo é a prova de que a spec
> foi tratada como artefato vivo e não como cerimônia de abertura.
>
> Spec que não muda em dois dias é spec que ninguém consultou. Mudança não é
> demérito — mudança não registrada é.

Ordem cronológica inversa: a mais recente primeiro.

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
