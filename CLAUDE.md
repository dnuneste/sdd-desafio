# CLAUDE.md

## O projeto

Motor de cálculo de reembolso de despesas corporativas. CLI que lê um JSON de
despesas e emite um JSON com o valor reembolsável e a justificativa de cada item.

## Fonte da verdade

`specs/001-motor-reembolso/spec.md` define **o que** o sistema faz.
`specs/001-motor-reembolso/plan.md` define **como**.
`specs/001-motor-reembolso/tasks.md` define **em que ordem**.

Quando o código e a spec discordarem, a spec está certa e o código é o bug —
a menos que a spec esteja errada, e nesse caso corrigimos a spec primeiro e
registramos em `DECISIONS.md`.

**Antes de implementar qualquer coisa, leia a task correspondente em `tasks.md`.**
Se o que eu pedi não está coberto por nenhuma task, me avise em vez de implementar.

## Regras de trabalho

- Toda regra de negócio vive na spec, não no chat e não em comentário de código.
- Se eu te explicar uma regra que não está na spec, **pare e me diga isso** antes
  de escrever código. Isso é um bug de spec.
- Todo commit referencia uma task: `feat(T-003): <descrição>`, `test(T-003): <descrição>`.
  Mudanças de documentação: `docs(spec):`, `docs(plan):`, `docs(tasks):`, `docs(decisions):`.
- Nenhuma regra de negócio entra sem teste.
- Marque `[x]` e preencha o hash/referência em `tasks.md` conforme cada task for concluída.
- Ao final de cada etapa/sessão de trabalho (especificação, implementação, revisão, mudança de requisito), exporte o histórico de interações para `docs/sessions/NN-descricao-curta.md` (ocultando dados pessoais do caminho local) e faça o commit correspondente.

## Stack e comandos

- Linguagem: Python 3.12+
- Rodar CLI: `python -m src.cli calcular --input exemplos/despesas-exemplo.json --output resultado.json`
- Testes: `python -m pytest -v`
- Lint/format: `python -m compileall src tests`

## Convenções de código

- Estrutura de diretórios: código-fonte em `src/` e testes automatizados em `tests/`.
- Nomenclatura: `snake_case` para módulos, funções e variáveis; `PascalCase` para classes/modelos; nomes de testes no formato `test_rn_XXX_<cenario>` ou `test_amb_XXX_<cenario>` para rastreabilidade direta com a spec.
- Valores monetários: representados internamente exclusivamente com `decimal.Decimal` (duas casas decimais, arredondamento `ROUND_HALF_UP`), nunca `float` em cálculos.
- Arquitetura: separação estrita entre núcleo puro de avaliação das regras e camada de I/O (leitura/escrita de arquivos e CLI).

## Fora de escopo

- Interface gráfica, API HTTP/REST ou banco de dados.
- Autenticação, controle de acesso ou integração com sistemas externos (ERP/RH).
- Processamento em lote de múltiplos colaboradores em um mesmo arquivo de entrada.
- Conversão de moedas estrangeiras ou cálculo de impostos.
- Inferência por linguagem natural/IA sobre o campo livre `descricao`.
