# Plano Técnico — Motor de Cálculo de Reembolso

**Versão:** 1.0 · **Baseado na spec:** 1.0

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
| Aritmética monetária | `decimal.Decimal` com `ROUND_HALF_UP` e quantização `Decimal("0.01")` | Evita erros de representação binária IEEE 754 (`float`, onde `0.1 + 0.2 != 0.3` e `100.01` pode sofrer imprecisão) e implementa fielmente `RN-001`. | `float` nativo (descartado por erro de precisão em centavos) e inteiros em centavos (descartado porque a entrada pode vir com 3 casas decimais como `33.333`, exigindo `Decimal` antes da conversão). |

## 2. Arquitetura

A arquitetura segue o padrão **Functional Core, Imperative Shell** (Núcleo Funcional Puro e Casca Imperativa de I/O):

```
[CLI: src/cli.py]
   │  (lê arquivo JSON / valida argumentos CLI --input e --output)
   ▼
[Parser/Serializer: src/io_handler.py]
   │  (converte dict JSON → dataclasses tipadas com Decimal e date)
   ▼
[Núcleo de Domínio: src/engine.py + src/policy.py + src/models.py]
   │  1. Normalização (RN-001)
   │  2. Validação de elegibilidade individual (RN-002, RN-003, RN-004, RN-006, RN-005)
   │  3. Apuração de datas em viagem (RN-007)
   │  4. Consumo de saldo diário e reembolso parcial (RN-008)
   │  5. Consolidação do resumo financeiro
   ▼
[Parser/Serializer: src/io_handler.py]
   │  (converte ResultadoProcessamento → dict JSON com números formatados em 2 casas)
   ▼
[CLI: src/cli.py]
      (escreve arquivo JSON de saída)
```

**Fronteiras:**
- **Núcleo puro (`src/models.py`, `src/policy.py`, `src/engine.py`):** Não realiza leitura de disco, não acessa variáveis de ambiente, não usa `print` e não conhece `argparse`. Recebe estruturas de dados em memória e devolve estruturas de dados avaliadas.
- **Casca de I/O (`src/io_handler.py`, `src/cli.py`):** Trata caminhos de arquivos, codificação UTF-8, serialização JSON e interface de linha de comando (`calcular --input ... --output ...`).

## 3. Modelo de dados

Estruturas internas em `src/models.py` (usando `@dataclass(frozen=True)` sempre que aplicável):

- `Colaborador`:
  - `id: str`
  - `nome: str`
  - `centro_custo: str`
  - `em_viagem: bool = False`
- `Periodo`:
  - `competencia: str`
  - `inicio: date`
  - `fim: date`
- `DespesaInput`:
  - `id: str`
  - `data: date`
  - `categoria_original: str`
  - `categoria_normalizada: str`
  - `descricao: str`
  - `descricao_normalizada: str`
  - `fornecedor: str`
  - `fornecedor_normalizado: str`
  - `valor_bruto: Decimal`
  - `valor_original: Decimal` (quantizado em `0.01` via `ROUND_HALF_UP`)
  - `tem_nota_fiscal: bool`
  - `em_viagem: bool = False`
- `StatusDespesa` (Enum `str`):
  - `APROVADA`
  - `APROVADA_PARCIALMENTE`
  - `RECUSADA`
- `CodigoMotivo` (Enum `str`):
  - `OK`
  - `LIMITE_DIARIO_EXCEDIDO`
  - `SEM_NOTA_FISCAL`
  - `CATEGORIA_NAO_REEMBOLSAVEL`
  - `FORA_PERIODO_COMPETENCIA`
  - `DESPESA_DUPLICADA`
  - `VALOR_INVALIDO`
- `ResultadoDespesa`:
  - `id: str`
  - `data: str` (`YYYY-MM-DD`)
  - `categoria_original: str`
  - `categoria_normalizada: str`
  - `valor_original: Decimal`
  - `valor_reembolsado: Decimal`
  - `valor_glosado: Decimal`
  - `status: StatusDespesa`
  - `codigo_motivo: CodigoMotivo`
  - `justificativa: str`
- `ResumoProcessamento`:
  - `total_solicitado: Decimal`
  - `total_reembolsado: Decimal`
  - `total_glosado: Decimal`
  - `quantidade_despesas: int`
  - `quantidade_aprovadas: int`
  - `quantidade_aprovadas_parcialmente: int`
  - `quantidade_recusadas: int`
- `RelatorioReembolso`:
  - `colaborador: Colaborador`
  - `periodo: Periodo`
  - `em_viagem: bool`
  - `resumo: ResumoProcessamento`
  - `resultados: list[ResultadoDespesa]`

## 4. Como a política é representada

Toda a parametrização da política vive isolada em `src/policy.py` através de uma estrutura imutável `PoliticaReembolso`:

```python
@dataclass(frozen=True)
class PoliticaReembolso:
    limites_diarios_base: Mapping[str, Decimal] = field(default_factory=lambda: {
        "alimentacao": Decimal("60.00"),
        "transporte_urbano": Decimal("80.00"),
        "hospedagem": Decimal("250.00"),
    })
    fator_multiplicador_viagem: Decimal = Decimal("1.50")
    limite_isencao_nota_fiscal: Decimal = Decimal("100.00")
    dias_extensao_viagem_hospedagem: int = 1
```

Isso garante que nenhuma constante mágica (`60`, `80`, `250`, `100`, `1.5`) fique espalhada pelo motor (`src/engine.py`). Se o envelope do Dia 2 alterar limites, categorias, multiplicadores ou tetos por centro de custo, basta ajustar ou estender `PoliticaReembolso` e o pipeline em `src/engine.py`.

## 5. Decisões técnicas

### DT-001 — Avaliação em duas passagens no motor (`src/engine.py`)

**Contexto:** Segundo `RN-007` e a Seção 8 da `spec.md`, uma despesa de `hospedagem` válida na data `D` ativa o regime de viagem (+50% nos limites) para todas as categorias nas datas `D` e `D + 1`, independentemente da ordem em que as despesas da data `D` apareçam na lista JSON.
**Decisão:** O motor executa em duas passagens sobre a lista de despesas:
- **Passagem 1:** Executa a normalização (`RN-001`) e as validações de elegibilidade individual (`RN-002`, `RN-003`, `RN-004`, `RN-006`, `RN-005`). Ao final da Passagem 1, todas as despesas inválidas já estão marcadas como `RECUSADA` e as despesas de `hospedagem` válidas determinam o conjunto `datas_em_viagem`.
- **Passagem 2:** Percorre as despesas elegíveis na ordem original da entrada, inicializando o saldo diário de `(data, categoria_normalizada)` com o limite base ou ampliado (+50% se `data in datas_em_viagem`) e aplicando o corte de limite diário (`RN-008`).
**Alternativa descartada:** Passagem única com avaliação imediata de limite diário — falharia caso uma despesa de alimentação na data `D` aparecesse no JSON antes da despesa de hospedagem da mesma data `D`.
**Consequência:** Comportamento 100% determinístico e independente da ordem relativa entre alimentação/transporte e hospedagem no mesmo dia.

### DT-002 — Conversão de valores JSON para `Decimal` via `str`

**Contexto:** Em Python, `json.loads` converte números JSON para `float` por padrão, o que pode introduzir artefatos binários (`float(100.01)` → `100.0100000000000051159...`).
**Decisão:** Usar `parse_float=Decimal` no `json.loads` (na camada de I/O) e converter `str(valor)` para `Decimal` nos construtores de modelo, seguido de `.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)`.
**Alternativa descartada:** Converter `float` diretamente para `Decimal(valor_float)`.
**Consequência:** Precisão decimal exata desde a leitura do JSON até a escrita do resultado.

### DT-003 — Zero dependências externas de runtime

**Contexto:** O critério 5 da `RUBRICA.md` especifica que o avaliador vai rodar o projeto pelo `README.md` sem intervenção manual para processar `despesas-exemplo.json` e o conjunto oculto do instrutor.
**Decisão:** O código de produção (`src/`) utiliza exclusivamente a biblioteca padrão do Python 3.12+. Apenas os testes utilizam `pytest`.
**Alternativa descartada:** Uso de `click`, `typer` ou `pydantic`.
**Consequência:** A CLI roda imediatamente com `python -m src.cli calcular --input ... --output ...` mesmo sem instalar pacotes de terceiros.

## 6. Estratégia de testes

- **Nível:**
  - **Unitários (~80%):** Testam isoladamente cada regra de negócio (`RN-001` a `RN-008`) e cada ambiguidade (`AMB-001` a `AMB-010`) invocando diretamente o núcleo puro (`avaliar_relatorio`).
  - **Integração / Ponta a ponta (~20%):** Testam a CLI (`src/cli.py`) e a leitura/escrita real do arquivo `exemplos/despesas-exemplo.json`, validando o critério de aceite `CA-001`.
- **Cada `RN-NNN` da spec tem teste?** Sim. Haverá pelo menos um teste dedicado para cada `RN-001`..`RN-008` e para cada caso da tabela de Casos de Borda (Seção 7 da `spec.md`).
- **Casos de borda da seção 7 da spec:** Todos os 11 casos da tabela da Seção 7 terão testes explícitos verificando `status`, `codigo_motivo`, `valor_reembolsado` e `valor_glosado`.
- **Nomenclatura:** Os testes seguem o padrão `test_rn_XXX_<descricao>` e `test_amb_XXX_<descricao>` (ex.: `test_rn_005_amb_002_fronteira_nota_fiscal_100_reais`), permitindo rastrear diretamente `spec.md` ↔ `tasks.md` ↔ `tests/`.

## 7. Riscos

| Risco | Probabilidade | O que faço se acontecer |
|---|---|---|
| Mudança de requisito do Dia 2 alterar limites por centro de custo, categoria ou regra de viagem | Alta (é a natureza do envelope do Dia 2) | Como `PoliticaReembolso` e o pipeline em 2 passagens (`src/engine.py`) estão desacoplados, atualizo primeiro a `spec.md`, registro em `DECISIONS.md`, crio as tasks da Fase 5 em `tasks.md` e ajusto apenas `policy.py`/`engine.py`. |
| Mudança do Dia 2 exigir leitura de novos campos opcionais no JSON de entrada | Média | O parser em `src/io_handler.py` usará `.get()` com valores padrão seguros, facilitando adicionar campos sem quebrar testes existentes. |
| Ambiente de correção não ter `pytest` instalado globalmente | Baixa | Documentar no `README.md` a instalação em `venv` (`pip install pytest`) e garantir que a CLI de produção (`src/`) não dependa de nenhum pacote externo. |
