# Motor de Cálculo de Reembolso de Despesas — SDD (Política v4)

Motor determinístico para avaliação e cálculo de reembolso de despesas corporativas (nacionais e internacionais), desenvolvido com **Spec-Driven Development (SDD)**.

Dado um arquivo JSON contendo as despesas de um colaborador em um período de competência, o sistema carrega a tabela externa de política por centro de custo (`exemplos/Envelope/politica-v4.json`) e a tabela de taxas de câmbio por data (`exemplos/Envelope/cambio.json`), convertendo despesas em moeda estrangeira para `BRL` e gerando um JSON com o resumo financeiro consolidado, o status, o valor reembolsado, o valor glosado e a justificativa auditável item a item.

---

## Pré-requisitos

- **Python 3.12+** (o motor de produção utiliza exclusivamente a biblioteca padrão do Python — zero dependências externas para rodar a CLI).
- **`pytest`** (apenas para execução da suíte de testes automatizados).

---

## Como rodar a CLI

Na raiz do repositório, execute qualquer um dos lotes de referência:

```bash
# 1. Lote original (Marina Volpi — CC-ENG-PLATAFORMA sob vigência retroativa da Política v4)
python -m src.cli calcular --input exemplos/despesas-exemplo.json --output resultado.json

# 2. Lote do Envelope Dia 2 (Rafael Nkemelu — CC-COMERCIAL + despesas internacionais EUR/USD/GBP)
python -m src.cli calcular --input exemplos/Envelope/despesas-envelope.json --output resultado-envelope.json

# 3. Lote do Envelope com Centro de Custo fora da tabela (Dani Okonkwo — CC-SUPORTE-N2 -> fallback padrão)
python -m src.cli calcular --input exemplos/Envelope/despesas-envelope-cc-desconhecido.json --output resultado-cc-desconhecido.json
```

*(Opcionalmente, é possível informar caminhos customizados de política e câmbio via `--politica <arquivo.json>` e `--cambio <arquivo.json>`).*

---

## Como rodar os testes automatizados

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
│   ├── despesas-exemplo.json                   # Lote de entrada do Dia 1 (14 casos)
│   └── Envelope/                               # Arquivos do Envelope Lacrado do Dia 2 (Política v4)
│       ├── 00-ENVELOPE-LACRADO.md
│       ├── politica-v4.json                    # Limites externos por centro de custo
│       ├── cambio.json                         # Cotações PTAX de fechamento por data
│       ├── despesas-envelope.json              # Lote CC-COMERCIAL e moedas estrangeiras
│       └── despesas-envelope-cc-desconhecido.json
├── specs/
│   └── 001-motor-reembolso/
│       ├── spec.md                             # Especificação funcional v2.0 (RN-001..RN-009, AMB-001..AMB-016, CA-001..CA-010)
│       ├── plan.md                             # Plano técnico v2.0 e decisões arquiteturais (DT-001..DT-004)
│       ├── tasks.md                            # Tasks executáveis (T-001..T-010) e matriz de cobertura
│       └── DECISIONS.md                        # Histórico vivo de decisões e evoluções da spec (D-001..D-004)
├── src/
│   ├── models.py                               # Modelos de domínio imutáveis e normalização/arredondamento (RN-001)
│   ├── policy.py                               # Política externa por centro de custo e TabelaCambio com fallback de dia útil
│   ├── engine.py                               # Núcleo funcional puro de avaliação em duas passagens (RN-002..RN-009)
│   ├── io_handler.py                           # Leitura e escrita JSON preservando precisão Decimal
│   └── cli.py                                  # Interface de linha de comando (`calcular --input ... --output ...`)
├── tests/
│   ├── test_engine.py                          # Testes unitários por regra de negócio e ambiguidade
│   ├── test_edge_cases.py                      # Testes dos 3 lotes completos (CA-001, CA-009, CA-010) e casos de borda
│   └── test_cli.py                             # Testes ponta a ponta da CLI
└── docs/
    ├── sessions/                               # Histórico exportado das sessões de trabalho com o agente
    └── RELATORIO.md                            # Relatório final estruturado pelos 4 Ds + O Envelope
```
