# Motor de Cálculo de Reembolso de Despesas — SDD

Motor determinístico para avaliação e cálculo de reembolso de despesas corporativas, desenvolvido com **Spec-Driven Development (SDD)**.

Dado um arquivo JSON contendo as despesas de um colaborador em um período de competência, o sistema avalia cada lançamento contra a política de reembolso desambiguada, gerando um JSON com o resumo financeiro consolidado, o status, o valor reembolsado, o valor glosado e a justificativa auditável item a item.

---

## Pré-requisitos

- **Python 3.12+** (o motor de produção utiliza exclusivamente a biblioteca padrão do Python — zero dependências externas para rodar a CLI).
- **`pytest`** (apenas para execução da suíte de testes automatizados).

---

## Como rodar a CLI

Na raiz do repositório, execute:

```bash
python -m src.cli calcular --input exemplos/despesas-exemplo.json --output resultado.json
```

O arquivo `resultado.json` será gerado com a avaliação completa dos 14 lançamentos de referência.

---

## Como rodar os testes automatizados

Instale o `pytest` (caso ainda não esteja instalado no seu ambiente/venv) e execute a suíte:

```bash
python -m pip install pytest
python -m pytest -v
```

---

## Estrutura do Projeto e Rastreabilidade SDD

```text
├── CLAUDE.md                                   # Convenções e regras de trabalho para o agente
├── README.md                                   # Instruções de execução e testes deste projeto
├── exemplos/
│   └── despesas-exemplo.json                   # Lote de entrada de referência (14 casos)
├── specs/
│   └── 001-motor-reembolso/
│       ├── spec.md                             # Especificação funcional (RN-001..RN-008, AMB-001..AMB-010, CA-001..CA-008)
│       ├── plan.md                             # Plano técnico e decisões arquiteturais (DT-001..DT-003)
│       ├── tasks.md                            # Tasks executáveis (T-001..T-007) e matriz de cobertura
│       └── DECISIONS.md                        # Histórico vivo de decisões e evoluções da spec (D-001..D-003)
├── src/
│   ├── models.py                               # Modelos de domínio imutáveis e normalização/arredondamento (RN-001)
│   ├── policy.py                               # Parâmetros isolados da política de reembolso
│   ├── engine.py                               # Núcleo funcional puro de avaliação em duas passagens (RN-002..RN-008)
│   ├── io_handler.py                           # Leitura e escrita JSON preservando precisão Decimal
│   └── cli.py                                  # Interface de linha de comando (`calcular --input ... --output ...`)
├── tests/
│   ├── test_engine.py                          # Testes unitários por regra de negócio e ambiguidade
│   ├── test_edge_cases.py                      # Testes dos casos de borda (Seções 7 e 8) e lote de referência (CA-001)
│   └── test_cli.py                             # Testes ponta a ponta da CLI
└── docs/
    ├── sessions/                               # Histórico exportado das sessões de trabalho com o agente
    └── RELATORIO.md                            # Relatório final estruturado pelos 4 Ds do AI Fluency
```
