# Log de Decisões e Mudanças de Spec

> Uma entrada **toda vez** que a spec mudar. Este arquivo é a prova de que a spec
> foi tratada como artefato vivo e não como cerimônia de abertura.
>
> Spec que não muda em dois dias é spec que ninguém consultou. Mudança não é
> demérito — mudança não registrada é.

Ordem cronológica inversa: a mais recente primeiro.

---

## D-001 — Consolidação inicial da Spec v1.0 e resolução das 10 ambiguidades da política v3 · `2026-11-25`

**Gatilho:** Análise cruzada entre a "Política de Reembolso de Despesas — v3" enviada pelo RH e os 14 itens do arquivo `exemplos/despesas-exemplo.json` antes do início da implementação.

**O que mudou na spec:** Criação das regras `RN-001` a `RN-008`, definição da ordem estrita de precedência (Seção 8), contrato de entrada/saída (Seção 4) e formalização das decisões para as 10 ambiguidades (`AMB-001` a `AMB-010`).

**Por quê:** A política textual do RH omitia a unidade de aplicação (teto cumulativo diário vs. individual), fronteiras numéricas (`> 100.00` vs `>= 100.00`, arredondamento de 3 casas decimais, valores negativos/estornos) e dados ausentes no JSON (`em_viagem` e `quantidade_diarias`).

**O que isso invalidou:** O esqueleto inicial em branco de `spec.md`.

**Tasks afetadas:** Criadas `T-001` a `T-007` em `specs/001-motor-reembolso/tasks.md`.

**Custo:** 1 arquivo de especificação (`spec.md`), 0 linhas de código alteradas (decisão tomada na fase de especificação, antes da escrita de código).
