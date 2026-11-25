# Plano Técnico — Motor de Cálculo de Reembolso

**Versão:** 2.0 · **Baseado na spec:** 2.0

> Aqui mora o COMO. Este arquivo pode e deve falar de linguagem, biblioteca e
> arquitetura. O que ele **não** pode é introduzir regra de negócio nova — se
> apareceu uma, ela pertence à `spec.md`.

---

## 1. Stack

| Escolha | O quê | Por quê | O que descartei e por quê |
|---|---|---|---|
| Linguagem | Python 3.12+ | Domínio da stack, biblioteca padrão rica (`decimal`, `dataclasses`, `datetime`, `argparse`, `json`) e zero atrito de compilação. | Node.js / Go — exigiriam bibliotecas externas para decimal exato ou setup adicional desnecessário para uma CLI local. |
| Testes | `pytest` (com fallback compatível com `unittest`) | Sintaxe enxuta com `assert`, parametrização simples e excelente legibilidade de falhas por requisito (`test_rn_XXX`). | Apenas `unittest` puro sem runner `pytest` — mais verboso para asserções e fixtures. |
| Parsing/validação | Biblioteca padrão (`json`, `datetime.date.fromisoformat`, `dataclasses`) | Zero dependências externas de runtime, mantendo o projeto executável em qualquer ambiente Python 3.12 limpo conforme exigido pela rubrica. | `pydantic` — adicionaria dependência externa para um contrato JSON simples e bem definido. |
| Aritmética monetária | `decimal.Decimal` com `ROUND_HALF_UP` e quantização `Decimal("0.01")` | Evita erros de representação binária IEEE 754 (`float`) tanto nos valores em BRL quanto na multiplicação por taxas de câmbio (`RN-001`, `RN-009`). | `float` nativo (descartado por erro de precisão em centavos) e inteiros em centavos (descartado porque taxas de câmbio e entradas com 3 casas exigem `Decimal`). |

## 2. Arquitetura

A arquitetura segue o padrão **Functional Core, Imperative Shell** (Núcleo Funcional Puro e Casca Imperativa de I/O):

```
[CLI: src/cli.py]
   │  (lê arquivos JSON: --input, e opcionalmente --politica e --cambio)
   ▼
[Parser/Serializer: src/io_handler.py]
   │  (converte JSONs → DespesaInput, PoliticaReembolso e TabelaCambio com Decimal)
   ▼
[Núcleo de Domínio: src/engine.py + src/policy.py + src/models.py]
   │  1. Normalização (RN-001)
   │  2. Validação de elegibilidade individual e conversão cambial (RN-002, RN-003, RN-004, RN-006, RN-009, RN-005)
   │  3. Apuração de datas em viagem: hospedagem válida D/D+1 ou moeda != BRL (RN-007)
   │  4. Consumo de saldo diário por centro de custo e reembolso parcial (RN-008)
   │  5. Consolidação do resumo financeiro em BRL
   ▼
[Parser/Serializer: src/io_handler.py]
   │  (converte RelatorioReembolso → dict JSON com números formatados)
   ▼
[CLI: src/cli.py]
      (escreve arquivo JSON de saída)
```

**Fronteiras:**
- **Núcleo puro (`src/models.py`, `src/policy.py`, `src/engine.py`):** Recebe estruturas tipadas em memória (`Colaborador`, `Periodo`, `list[DespesaInput]`, `PoliticaReembolso`, `TabelaCambio`) e devolve `RelatorioReembolso`.
- **Casca de I/O (`src/io_handler.py`, `src/cli.py`):** Carrega `exemplos/Envelope/politica-v4.json` e `exemplos/Envelope/cambio.json` por padrão (ou caminhos customizados via flags `--politica` e `--cambio`).

## 3. Modelo de dados

Estruturas internas em `src/models.py`:

- `Colaborador`: `id: str`, `nome: str`, `centro_custo: str`, `em_viagem: bool = False`
- `Periodo`: `competencia: str`, `inicio: date`, `fim: date`
- `DespesaInput`:
  - `id: str`, `data: date`, `categoria_original: str`, `categoria_normalizada: str`
  - `descricao: str`, `descricao_normalizada: str`, `fornecedor: str`, `fornecedor_normalizado: str`
  - `moeda_original: str` (ISO 4217 normalizada em uppercase, padrão `"BRL"`)
  - `valor_bruto: Decimal`
  - `valor_moeda_original: Decimal` (quantizado em `0.01` na moeda original)
  - `valor_original: Decimal` (para `"BRL"` é igual a `valor_moeda_original`; para moeda estrangeira é atualizado após conversão cambial `RN-009`)
  - `tem_nota_fiscal: bool`, `em_viagem: bool = False`
- `CodigoMotivo` (Enum `str`):
  - `OK`, `LIMITE_DIARIO_EXCEDIDO`, `SEM_NOTA_FISCAL`, `CATEGORIA_NAO_REEMBOLSAVEL`, `FORA_PERIODO_COMPETENCIA`, `DESPESA_DUPLICADA`, `VALOR_INVALIDO`, `MOEDA_NAO_SUPORTADA`, `CAMBIO_INDISPONIVEL`
- `ResultadoDespesa`:
  - `id: str`, `data: str`, `categoria_original: str`, `categoria_normalizada: str`
  - `moeda_original: str = "BRL"`
  - `valor_moeda_original: Decimal`
  - `taxa_cambio_aplicada: Decimal | None = Decimal("1.00")`
  - `valor_original: Decimal`, `valor_reembolsado: Decimal`, `valor_glosado: Decimal`
  - `status: StatusDespesa`, `codigo_motivo: CodigoMotivo`, `justificativa: str`

## 4. Como a política e o câmbio são representados

Em `src/policy.py`:
1. **`PoliticaReembolso`:**
   - Mantém `limites_padrao: Mapping[str, Decimal]` e `limites_por_centro_custo: Mapping[str, Mapping[str, Decimal]]`.
   - Método `obter_mapa_centro_custo(centro_custo: str)` retorna `limites_por_centro_custo[centro_custo]` se o centro de custo estiver cadastrado, ou `limites_padrao` caso contrário (`RN-004`, `AMB-014`).
   - Método `categoria_elegivel(categoria_normalizada: str, centro_custo: str | None = None)` verifica se a categoria existe no mapa do centro de custo **e** possui `limite > Decimal("0.00")`.
   - Método `obter_limite_diario(categoria_normalizada: str, em_viagem: bool, centro_custo: str | None = None)` aplica `+50%` quando `em_viagem` for `True` e a categoria pertencer a `categorias_ampliadas_em_viagem` (`{"alimentacao", "transporte_urbano"}`).
   - Construtor `PoliticaReembolso.de_dict(dados)` carrega diretamente a estrutura de `politica-v4.json`.
2. **`TabelaCambio`:**
   - Representa as taxas de `cambio.json` (`taxas_por_data: Mapping[date, Mapping[str, Decimal]]`).
   - Método `obter_taxa(data_despesa: date, moeda: str)` implementa o fallback de dia útil anterior (`max(d for d in taxas_por_data if d <= data_despesa)`) conforme `RN-009` / `AMB-011`.

## 5. Decisões técnicas

### DT-001 — Avaliação em duas passagens no motor (`src/engine.py`)
Mantida da v1.0 e estendida na v2.0: na Passagem 1 ocorrem as validações de elegibilidade individual e a conversão cambial (`RN-009`) antes da checagem de nota fiscal (`RN-005`). Na Passagem 2, apuram-se as datas em viagem (incluindo datas com despesas válidas em `moeda != "BRL"`) e consome-se o saldo diário do respectivo centro de custo.

### DT-002 — Conversão de valores JSON para `Decimal` via `str`
Mantida da v1.0 e estendida para `politica-v4.json` e `cambio.json`.

### DT-003 — Zero dependências externas de runtime
Mantida da v1.0.

### DT-004 — Retrocompatibilidade da assinatura do motor e carregamento padrão da Política v4 na CLI
**Contexto:** Os testes unitários das regras base (`tests/test_engine.py`) instanciam `PoliticaReembolso()` sem argumentos para testar as regras isoladas, enquanto a CLI e os lotes da v4 usam `politica-v4.json` e `cambio.json`.
**Decisão:** `PoliticaReembolso()` mantém defaults compatíveis com a tabela `padrao`, e `carregar_politica_json` / `carregar_cambio_json` carregam os arquivos externos `exemplos/Envelope/politica-v4.json` e `exemplos/Envelope/cambio.json` por padrão na CLI (com flags opcionais `--politica` e `--cambio`).
**Alternativa descartada:** Hardcodar os centros de custo dentro do código Python — violaria diretamente a exigência do Item A do envelope ("O motor precisa ler a política de fora, não de dentro do código").
**Consequência:** Testes unitários existentes continuam funcionando sem acoplamento a disco, e o motor em produção lê 100% da política e do câmbio de arquivos JSON externos.

## 6. Estratégia de testes

- **Unitários (`tests/test_engine.py`):** Testam `RN-001` a `RN-009` e `AMB-001` a `AMB-016`, incluindo resolução por centro de custo, fallback para `padrao`, limite `0.00` em `CC-ENG-PLATAFORMA`, conversão cambial com fallback de sábado para sexta e recusa de `GBP`.
- **Integração / Casos de borda (`tests/test_edge_cases.py`):** Testam os 3 lotes completos:
  1. `exemplos/despesas-exemplo.json` (`CA-001` sob Política v4);
  2. `exemplos/Envelope/despesas-envelope.json` (`CA-009` — `CC-COMERCIAL` + câmbio);
  3. `exemplos/Envelope/despesas-envelope-cc-desconhecido.json` (`CA-010` — `CC-SUPORTE-N2` fallback `padrao`).
- **CLI Ponta a Ponta (`tests/test_cli.py`):** Testa a CLI processando tanto o lote original quanto os lotes do envelope.

## 7. Riscos

| Risco | Probabilidade | O que faço se acontecer |
|---|---|---|
| Avaliador rodar `python -m src.cli calcular --input ... --output ...` sem passar flags `--politica` e `--cambio` | Alta (a interface fixa do enunciado só tem `--input` e `--output`) | Configurar `--politica` com default `"exemplos/Envelope/politica-v4.json"` e `--cambio` com default `"exemplos/Envelope/cambio.json"`, mantendo a interface fixa 100% funcional. |
