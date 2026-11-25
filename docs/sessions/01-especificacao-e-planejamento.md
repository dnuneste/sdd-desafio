# Sessão 01 — Especificação, Resolução de Ambiguidades e Planejamento (Dia 1 - Manhã)

**Data:** 2026-11-25  
**Fase SDD:** `CLAUDE.md` → `spec.md` → `plan.md` → `tasks.md` → `DECISIONS.md`  
**Nota de privacidade:** Caminhos locais foram sanitizados para `<workspace>` conforme instruções do `FAQ.md`.

---

## Interação 1 — Leitura Inicial do Desafio e Análise dos Dados

**Usuário:**
> Precisamos cumprir alguns desafios referentes a um curso de trilha da anthropic, Leia o arquivo README.md e DESAFIO.md do diretorio para iniciarmos a implementação do desafio

**Agente:**
- Realizou a leitura de `<workspace>/README.md`, `<workspace>/DESAFIO.md`, `<workspace>/RUBRICA.md`, `<workspace>/FAQ.md`, `<workspace>/exemplos/despesas-exemplo.json` e dos arquivos base em `<workspace>/specs/001-motor-reembolso/`.
- Mapeou as 3 regras de ouro do desafio:
  1. Nenhum commit sem task (`docs(spec)`, `docs(plan)`, `docs(tasks)`, `feat(T-XXX)`, `test(T-XXX)`).
  2. Explicação no chat que não está na spec é bug de spec.
  3. Interações exportadas e commitadas em `docs/sessions/`.
- Cruzou os 9 itens da Política de Reembolso v3 do RH com os 14 lançamentos de `exemplos/despesas-exemplo.json`, identificando as ambiguidades de unidade de aplicação, fronteira e dado ausente (`d-001` a `d-014`).
- Perguntou ao usuário a definição da stack e diretrizes sobre as decisões de ambiguidade.

---

## Interação 2 — Definição da Stack e Elaboração da Spec, Plan e Tasks

**Usuário:**
> 1 - Utilizaremos python com pytest  2 - Proponha decisões e posteriormente farei a revisão, lembre-se de verificar as politicas do curso para seguirmos todos os padrões exigidos.

**Agente:**
- Verificou a versão do Python instalada (`Python 3.12.10`).
- Preencheu `<workspace>/CLAUDE.md` com as convenções do projeto, stack Python 3.12+ com `pytest`, uso estrito de `decimal.Decimal` (`ROUND_HALF_UP`) e escopo negativo.
- Escreveu `<workspace>/specs/001-motor-reembolso/spec.md` (v1.0) sem qualquer vazamento técnico, contendo:
  - Problema, Objetivo e Fora de Escopo;
  - Contrato de Entrada e Saída com exemplo JSON completo;
  - Regras de Negócio `RN-001` a `RN-008`;
  - 10 Ambiguidades identificadas, decididas e justificadas (`AMB-001` a `AMB-010`);
  - Tabela com 11 Casos de Borda mapeados para `d-001`..`d-014`;
  - Ordem determinística de aplicação das regras (Passo 0 a Passo 3);
  - Critérios de Aceite verificáveis (`CA-001` a `CA-008`) e seção "O que fica em aberto".
- Escreveu `<workspace>/specs/001-motor-reembolso/plan.md` (v1.0) definindo a arquitetura *Functional Core, Imperative Shell* (`src/models.py`, `src/policy.py`, `src/engine.py`, `src/io_handler.py`, `src/cli.py`), decisões técnicas (`DT-001` a `DT-003`) e estratégia de testes.
- Escreveu `<workspace>/specs/001-motor-reembolso/tasks.md` com as tasks `T-001` a `T-007` e matriz de cobertura completa.
- Registrou a decisão inicial `D-001` em `<workspace>/specs/001-motor-reembolso/DECISIONS.md`.

---

## Interação 3 — Estratégia de Exportação de Sessões e Governança do `CLAUDE.md`

**Usuário:**
> Oque sugere em relação ao comando /export

**Agente:**
- Consultou o `FAQ.md` (linhas 74–77) e a `RUBRICA.md` (linha 82) sobre alternativas ao `/export` e a exigência de múltiplos arquivos por sessão (`docs/sessions/NN-descricao-curta.md`) ao longo do desafio.
- Propôs gerar e commitar um arquivo de sessão a cada etapa concluída do fluxo SDD, sanitizando dados pessoais do diretório local.

**Usuário:**
> Antes de responder sua pergunta, você respeita todas as regras do claude.md antes de executar qualquer ação ?

**Agente:**
- Confirmou a adesão estrita a todas as regras do `CLAUDE.md` (fonte da verdade na spec, bloqueio de regra de negócio não especificada, verificação prévia de task em `tasks.md`, padrão de commits e testes obrigatórios) e sugeriu incluir a regra de exportação periódica no próprio `CLAUDE.md`.

**Usuário:**
> Sim, podemos anexar essa regra no claude.md para criar arquivos periodicos para popular docs/sessions

**Agente:**
- Atualizou `<workspace>/CLAUDE.md` adicionando a regra de exportação periódica em `docs/sessions/NN-descricao-curta.md` ao final de cada etapa.

**Usuário:**
> Pode commitar respeitando as regras do desafio, depois vamos para os proximos passos

---

## Interação 4 — Revisão de Negócio da Spec v1.1 e Registro de Decisão D-002

**Usuário:**
> Vamos azer uma revisão de negócio na spec.md

**Agente:**
- Analisou o efeito da regra `RN-007` / `AMB-008` proposta na `spec.md` v1.0 (`0ba5346`).
- Explicou a falha lógica de domínio detectada na revisão: na v1.0, uma despesa de `hospedagem` válida ativava o regime de viagem (+50%) para sua data `D` e `D + 1` e aplicava o multiplicador de +50% inclusive sobre a própria categoria `hospedagem` (elevando o limite de R$ 250,00 para R$ 375,00). Como toda hospedagem válida ativaria o regime de viagem na data `D`, o limite de R$ 250,00 do item 3 da política do RH jamais seria aplicado (tornando-se regra morta).
- Propôs a correção para a `spec.md` v1.1 (`D-002`): manter o bônus de +50% em viagem apenas para as categorias cotidianas (`alimentacao`: R$ 60 → R$ 90; `transporte_urbano`: R$ 80 → R$ 120), preservando o teto próprio de `hospedagem` em R$ 250,00 por diária.

**Usuário:**
> Pode aplicar a revisão

**Agente:**
- Atualizou `<workspace>/specs/001-motor-reembolso/spec.md` para a versão 1.1 (`RN-007`, `RN-008`, `AMB-007`, `AMB-008`, `CA-001` e `CA-008`).
- Registrou a entrada `D-002` em `<workspace>/specs/001-motor-reembolso/DECISIONS.md` detalhando o gatilho, o antes/depois, a justificativa de negócio e os critérios afetados.
