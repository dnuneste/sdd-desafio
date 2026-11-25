# Spec — Motor de Cálculo de Reembolso

**Versão:** 2.0 · **Status:** aprovada · **Última alteração:** `2026-11-25`

> **Regra de ouro deste arquivo:** ele descreve o QUÊ e o PORQUÊ. Nenhuma linha
> aqui pode citar linguagem, biblioteca, classe, função ou estrutura de pasta.
> Se apareceu solução, o lugar dela é o `plan.md`.
>
> **Teste de aceitação da própria spec:** uma pessoa que nunca viu o projeto
> consegue, lendo só este arquivo, verificar se o sistema está correto?

---

## 1. Problema

A conferência de reembolso de despesas corporativas é feita manualmente pelo time financeiro em planilhas, analisando lançamento por lançamento contra uma política de RH textual e ambígua, que na versão v4 passou também a variar por centro de custo e a incluir despesas internacionais em moeda estrangeira. Esse processo manual é lento, sujeito a interpretações divergentes entre analistas e gera erros financeiros em conversões cambiais, aplicação de tetos por centro de custo, glosas indevidas e retrabalho de auditoria.

## 2. Objetivo

Avaliar automaticamente o lote de despesas (nacionais e internacionais) de um colaborador em um período de competência contra a tabela externa de política por centro de custo e a tabela oficial de taxas de câmbio por data, determinando de forma determinística e auditável o status, a conversão para BRL, o valor reembolsável e a justificativa de cada item, bem como o resumo financeiro consolidado do período.

## 3. Fora de escopo

- Não realiza leitura ou extração de dados de texto livre no campo `descricao` (como tentar adivinhar número de diárias ou contexto por palavras-chave).
- Não processa múltiplos colaboradores ou múltiplos períodos de competência em uma mesma execução.
- Não consulta cotações de câmbio na internet em tempo real (opera exclusivamente sobre o documento de taxas de câmbio fornecido como entrada do motor).
- Não implementa fila de aprovação manual nem estado de pendência para aprovação de gestor em despesas acima de R$ 500,00 (Item C opcional do comunicado da Política v4 explicitamente fora de escopo para preservar o contrato determinístico de 3 status: `APROVADA`, `APROVADA_PARCIALMENTE`, `RECUSADA`).
- Não valida autenticidade fiscal de notas junto a órgãos governamentais (confia exclusivamente no campo booleano `tem_nota_fiscal`).
- Não persiste histórico entre execuções distintas nem consulta bases de dados externas.
- Não altera, reordena nem remove itens da lista de despesas na saída (toda despesa de entrada produz exatamente um item avaliado na saída, na mesma ordem).

## 4. Entrada e saída

**Entradas do sistema:**
1. **Lote de despesas** (conforme `exemplos/despesas-exemplo.json`, `exemplos/Envelope/despesas-envelope.json` e `exemplos/Envelope/despesas-envelope-cc-desconhecido.json`):

| Campo | Tipo | Significado | Obrigatório |
|---|---|---|---|
| `colaborador` | Objeto | Dados cadastrais do colaborador solicitante | Sim |
| `colaborador.id` | Texto | Identificador único do colaborador | Sim |
| `colaborador.nome` | Texto | Nome completo do colaborador | Sim |
| `colaborador.centro_custo` | Texto | Código do centro de custo do colaborador | Sim |
| `periodo` | Objeto | Período de apuração do relatório de despesas | Sim |
| `periodo.competencia` | Texto (`AAAA-MM`) | Mês/ano de referência da competência | Sim |
| `periodo.inicio` | Texto (`AAAA-MM-DD`) | Data inicial inclusiva do período válido | Sim |
| `periodo.fim` | Texto (`AAAA-MM-DD`) | Data final inclusiva do período válido | Sim |
| `despesas` | Lista de Objetos | Conjunto de despesas submetidas para avaliação | Sim |
| `despesas[].id` | Texto | Identificador único do lançamento | Sim |
| `despesas[].data` | Texto (`AAAA-MM-DD`) | Data de ocorrência da despesa | Sim |
| `despesas[].categoria` | Texto | Categoria informada pelo colaborador | Sim |
| `despesas[].descricao` | Texto | Descrição livre do gasto | Sim |
| `despesas[].fornecedor` | Texto | Nome do estabelecimento ou prestador | Sim |
| `despesas[].valor` | Número | Valor monetário na moeda informada | Sim |
| `despesas[].moeda` | Texto (ISO 4217) | Código da moeda da despesa (quando ausente, assume-se `"BRL"`) | Não (padrão `"BRL"`) |
| `despesas[].tem_nota_fiscal` | Booleano | Indica se há comprovante fiscal anexado (`true`/`false`) | Sim |

2. **Política externa por centro de custo** (`exemplos/Envelope/politica-v4.json`):
   - `moeda_base`: Moeda dos limites da política (`"BRL"`).
   - `padrao`: Mapa de categorias e limites diários aplicável quando o centro de custo do colaborador não consta em `centros_custo`.
   - `centros_custo`: Mapa de códigos de centro de custo para suas respectivas categorias e limites diários.
   - `nota_fiscal_obrigatoria_acima_de`: Valor em `BRL` acima do qual a nota fiscal é obrigatória (`100.00`).
   - `acrescimo_em_viagem_percentual`: Percentual de ampliação dos limites diários em regime de viagem (`50`).

3. **Tabela externa de câmbio** (`exemplos/Envelope/cambio.json`):
   - `moeda_base`: `"BRL"`.
   - `taxas`: Mapa de datas (`AAAA-MM-DD`) para pares `{ "<MOEDA_ISO>": <taxa_para_BRL> }`.

**Saída:** documento JSON contendo a identificação do colaborador, o período, o resumo consolidado em BRL e a lista de resultados por despesa:

| Campo | Tipo | Significado |
|---|---|---|
| `colaborador` | Objeto | Eco dos dados do colaborador da entrada (`id`, `nome`, `centro_custo`) |
| `periodo` | Objeto | Eco dos dados do período da entrada (`competencia`, `inicio`, `fim`) |
| `em_viagem` | Booleano | Indica se ao menos uma data no lote teve o regime de viagem ativado (`true`/`false`) |
| `resumo` | Objeto | Totais consolidados do processamento (sempre em `BRL`) |
| `resumo.total_solicitado` | Número (2 casas) | Soma dos valores em `BRL` (`valor_original`) das despesas com valor positivo (`> 0`) e câmbio conhecido |
| `resumo.total_reembolsado` | Número (2 casas) | Soma final em `BRL` dos valores efetivamente aprovados para reembolso |
| `resumo.total_glosado` | Número (2 casas) | Diferença `total_solicitado - total_reembolsado` |
| `resumo.quantidade_despesas` | Inteiro | Total de itens recebidos na entrada |
| `resumo.quantidade_aprovadas` | Inteiro | Quantidade de itens com status `APROVADA` |
| `resumo.quantidade_aprovadas_parcialmente` | Inteiro | Quantidade de itens com status `APROVADA_PARCIALMENTE` |
| `resumo.quantidade_recusadas` | Inteiro | Quantidade de itens com status `RECUSADA` |
| `resultados` | Lista de Objetos | Avaliação individual de cada despesa, na mesma ordem da entrada |
| `resultados[].id` | Texto | Identificador original da despesa |
| `resultados[].data` | Texto (`AAAA-MM-DD`) | Data original da despesa |
| `resultados[].categoria_original` | Texto | Categoria exatamente como recebida na entrada |
| `resultados[].categoria_normalizada` | Texto | Categoria normalizada em letras minúsculas e sem espaços nas bordas |
| `resultados[].moeda_original` | Texto (ISO 4217) | Moeda normalizada em maiúsculas (`"BRL"`, `"EUR"`, `"USD"`, etc.) |
| `resultados[].valor_moeda_original` | Número (2 casas) | Valor solicitado na moeda original arredondado para 2 casas decimais |
| `resultados[].taxa_cambio_aplicada` | Número ou Nulo | Taxa usada na conversão para `BRL` (`1.0` para `BRL`, taxa PTAX para moeda estrangeira, ou `null` quando a moeda/taxa não existir) |
| `resultados[].valor_original` | Número (2 casas) | Valor convertido para `BRL` (arredondado para 2 casas), usado como base para todas as regras financeiras (`0.00` se a moeda não for suportada) |
| `resultados[].valor_reembolsado` | Número (2 casas) | Valor aprovado em `BRL` após aplicação das regras (`0.00` quando recusada) |
| `resultados[].valor_glosado` | Número (2 casas) | Valor cortado em `BRL` (`valor_original - valor_reembolsado` para valores positivos, ou `0.00` se `valor_original <= 0`) |
| `resultados[].status` | Texto | Um entre: `APROVADA`, `APROVADA_PARCIALMENTE`, `RECUSADA` |
| `resultados[].codigo_motivo` | Texto | Código padronizado da decisão (`OK`, `LIMITE_DIARIO_EXCEDIDO`, `SEM_NOTA_FISCAL`, `CATEGORIA_NAO_REEMBOLSAVEL`, `FORA_PERIODO_COMPETENCIA`, `DESPESA_DUPLICADA`, `VALOR_INVALIDO`, `MOEDA_NAO_SUPORTADA`, `CAMBIO_INDISPONIVEL`) |
| `resultados[].justificativa` | Texto | Explicação legível por humanos detalhando a regra aplicada |

---

## 5. Regras de negócio

### RN-001 — Normalização e arredondamento monetário na entrada

**Regra:** Todo valor monetário de entrada (`valor`) é arredondado para 2 casas decimais (`valor_moeda_original`) utilizando a regra de arredondamento "meio para cima" (half-up: `0.005` arredonda para `0.01`). Todo texto de `categoria` é normalizado removendo espaços nas extremidades e convertendo para letras minúsculas (`"ALIMENTACAO"` torna-se `"alimentacao"`). O campo opcional `moeda`, quando ausente ou vazio, assume o valor padrão `"BRL"`; quando presente, é normalizado removendo espaços e convertendo para letras maiúsculas (`"eur"` → `"EUR"`).
**Origem:** política do RH v3/v4 (item B do envelope e higiene de dados financeiros: `AMB-003`, `AMB-009`).
**Aceite:** Uma despesa sem campo `moeda`, com `valor: 33.333` e `categoria: "ALIMENTACAO"` resulta em `moeda_original: "BRL"`, `valor_moeda_original: 33.33`, `valor_original: 33.33` e `categoria_normalizada: "alimentacao"`.

### RN-002 — Rejeição de valores não positivos (estornos, negativos ou zero)

**Regra:** Despesas com `valor_moeda_original <= 0.00` não são reembolsáveis. Recebem status `RECUSADA`, `codigo_motivo: "VALOR_INVALIDO"`, `valor_reembolsado: 0.00` e `valor_glosado: 0.00`. Tais itens não somam no `total_solicitado` do resumo e não abatem nem recompõem o saldo diário de nenhuma categoria.
**Origem:** política do RH (implícita) e item `d-009` da entrada de referência (`AMB-006`).
**Aceite:** A despesa `d-009` (`valor: -45.00`) resulta em `status: "RECUSADA"`, `codigo_motivo: "VALOR_INVALIDO"`, `valor_reembolsado: 0.00`, `valor_glosado: 0.00`.

### RN-003 — Validação do período de competência

**Regra:** A data da despesa (`data`) deve estar contida no intervalo fechado `[periodo.inicio, periodo.fim]` (`periodo.inicio <= data <= periodo.fim`), independentemente do dia da semana (sábados, domingos e feriados dentro do intervalo são válidos). Despesas fora desse intervalo recebem status `RECUSADA`, `codigo_motivo: "FORA_PERIODO_COMPETENCIA"` e `valor_reembolsado: 0.00`.
**Origem:** política do RH, item 7 (`AMB-005`, `AMB-010`).
**Aceite:** Em um período `2026-07-01` a `2026-07-31`, `d-008` (`2026-04-15`) é `RECUSADA` com `FORA_PERIODO_COMPETENCIA`, enquanto `d-012` e `e-004` (`2026-07-18`, sábado) prosseguem normalmente para avaliação.

### RN-004 — Elegibilidade de categorias por centro de custo (Política Externa v4)

**Regra:** A tabela de categorias e limites aplicável ao colaborador é determinada pelo seu `colaborador.centro_custo` no documento externo de política (`politica-v4.json`):
1. Se `colaborador.centro_custo` existir na chave `centros_custo` da política, utiliza-se **exclusivamente** o mapa de categorias definido para aquele centro de custo.
2. Se `colaborador.centro_custo` **não** existir em `centros_custo`, utiliza-se o mapa de categorias definido na chave `padrao` da política.
3. Uma categoria é considerada **elegível** para aquele centro de custo se e somente se `categoria_normalizada` constar no mapa aplicável **E** seu `limite` configurado for estritamente maior que zero (`limite > 0.00`).
4. Caso a categoria não conste no mapa aplicável (ex.: `coworking` em qualquer CC, ou `representacao` fora de `CC-COMERCIAL`, ou `hospedagem` em `CC-ADM`) **ou** possua `limite == 0.00` (ex.: `hospedagem` em `CC-ENG-PLATAFORMA`), a despesa é recusada imediatamente na validação de elegibilidade com status `RECUSADA`, `codigo_motivo: "CATEGORIA_NAO_REEMBOLSAVEL"` e `valor_reembolsado: 0.00`, não ativando regime de viagem.
**Origem:** comunicado da Política v4, item A (`AMB-003`, `AMB-014`, `AMB-016`).
**Aceite:**
- Para `CC-COMERCIAL` (`despesas-envelope.json`), `e-001` (`representacao`, R$ 340,00) é elegível (limite R$ 300,00), enquanto `e-009` (`coworking`) é `RECUSADA` (`CATEGORIA_NAO_REEMBOLSAVEL`).
- Para `CC-SUPORTE-N2` (`despesas-envelope-cc-desconhecido.json`, ausente da tabela), aplica-se a política `padrao`, de modo que `f-003` (`representacao`, R$ 190,00) é `RECUSADA` (`CATEGORIA_NAO_REEMBOLSAVEL`).
- Para `CC-ENG-PLATAFORMA` (`despesas-exemplo.json` sob a v4), `d-010` (`hospedagem`) tem `limite: 0.00` ("não reembolsável") e é `RECUSADA` com `CATEGORIA_NAO_REEMBOLSAVEL`.

### RN-005 — Obrigatoriedade de nota fiscal acima de R$ 100,00 (em BRL)

**Regra:** Toda despesa cujo valor convertido em Reais (`valor_original` em `BRL`) seja estritamente maior que o limite de isenção da política (`valor_original > 100.00`) exige `tem_nota_fiscal: true`. Se `valor_original > 100.00` e `tem_nota_fiscal` for `false`, a despesa recebe status `RECUSADA`, `codigo_motivo: "SEM_NOTA_FISCAL"` e `valor_reembolsado: 0.00`, sem consumir limite diário da categoria. Despesas com `valor_original <= 100.00` estão dispensadas de nota fiscal.
**Origem:** política do RH v3/v4, item 5 e item B (`AMB-002`, `AMB-013`).
**Aceite:**
- `d-003` (`100.00 BRL`, `tem_nota_fiscal: false`) é isenta de NF; `d-004` (`100.01 BRL`, `tem_nota_fiscal: false`) é `RECUSADA` (`SEM_NOTA_FISCAL`).
- `e-003` (`14.50 EUR` em `2026-07-15` × `5.88` = `85.26 BRL`, `tem_nota_fiscal: false`) tem valor em BRL `<= 100.00`, logo é dispensada de NF e aprovada.
- `e-005` (`40.00 USD` em `2026-07-20` × `5.50` = `220.00 BRL`, `tem_nota_fiscal: false`) tem valor em BRL `> 100.00`, logo é `RECUSADA` com `SEM_NOTA_FISCAL`.

### RN-006 — Detecção e recusa de despesas duplicadas

**Regra:** Duas ou mais despesas são consideradas duplicatas quando possuem exatamente a mesma tupla de negócio: `(data, categoria_normalizada, descricao_normalizada, fornecedor_normalizado, moeda_original, valor_moeda_original)`. A primeira ocorrência na ordem de entrada é processada normalmente; todas as ocorrências subsequentes idênticas recebem status `RECUSADA`, `codigo_motivo: "DESPESA_DUPLICADA"` e `valor_reembolsado: 0.00`, sem consumir limite diário.
**Origem:** política do RH, item 8 (`AMB-004`).
**Aceite:** Entre `d-006` e `d-007` (ambas em `2026-07-09`, `alimentacao`, `"Almoco"`, `"Bistro Central"`, `BRL`, `54.90`), `d-006` é `APROVADA` (`54.90`) e `d-007` é `RECUSADA` com `codigo_motivo: "DESPESA_DUPLICADA"` (`0.00`).

### RN-007 — Caracterização de colaborador em viagem e ampliação de limites em 50%

**Regra:** Considera-se que uma data `D` opera em regime de **colaborador em viagem** quando:
1. O objeto `colaborador` ou uma despesa da data `D` contiver o campo booleano opcional `em_viagem: true`; **OU**
2. A data `D` coincidir com a data de estadia (`D_hosp`) ou o dia imediatamente seguinte de check-out (`D_hosp + 1 dia`) de uma despesa de `hospedagem` válida (que sobreviveu a todas as validações de elegibilidade individual, incluindo `RN-004` e `RN-005`); **OU**
3. A data `D` possuir uma despesa válida lançada em **moeda estrangeira** (`moeda_original != "BRL"`), caracterizando deslocamento em viagem internacional naquela data (`AMB-015`).

Nas datas caracterizadas como em viagem, os limites diários das despesas cotidianas (`alimentacao` e `transporte_urbano`) do centro de custo do colaborador são ampliados no percentual definido pela política (`acrescimo_em_viagem_percentual`: **+50%**), enquanto `hospedagem` e `representacao` mantêm seus respectivos limites diários da tabela do centro de custo:
- Em `padrao` (ex.: `CC-SUPORTE-N2`): `alimentacao` passa de R$ 60,00 para **R$ 90,00/dia**; `transporte_urbano` passa de R$ 80,00 para **R$ 120,00/dia**; `hospedagem` mantém **R$ 250,00/diária**.
- Em `CC-COMERCIAL`: `alimentacao` passa de R$ 90,00 para **R$ 135,00/dia**; `transporte_urbano` passa de R$ 150,00 para **R$ 225,00/dia**; `hospedagem` mantém **R$ 400,00/diária** e `representacao` mantém **R$ 300,00/dia**.
- Em `CC-ENG-PLATAFORMA`: `alimentacao` é R$ 75,00/dia (ou **R$ 112,50/dia** se em viagem) e `transporte_urbano` é R$ 80,00/dia (ou **R$ 120,00/dia** se em viagem); porém, como `hospedagem` não é reembolsável nesse centro de custo (`limite: 0.00`), lançamentos de hospedagem são recusados na `RN-004` e não ativam viagem.

O campo de saída de nível superior `em_viagem` será `true` se ao menos uma data no período tiver o regime de viagem ativado.
**Origem:** política do RH v3/v4, item 6 e itens A/B do envelope (`AMB-007`, `AMB-008`, `AMB-015`, `AMB-016`).
**Aceite:**
- Em `despesas-envelope.json` (`CC-COMERCIAL`, limite base de `alimentacao` = R$ 90,00):
  - `e-002` (`2026-07-14`, `22.00 EUR` = R$ 130,46) está em moeda estrangeira, logo `2026-07-14` opera em viagem (limite de `alimentacao` = R$ 135,00) e `e-002` é `APROVADA` integralmente (`130.46`).
  - `e-004` (`2026-07-18`, `30.00 EUR` = R$ 178,80) está em moeda estrangeira, opera com limite de viagem de R$ 135,00 e é `APROVADA_PARCIALMENTE` (reembolsa `135.00`, glosa `43.80`).
  - `e-007` (`2026-07-22`, `hospedagem`, R$ 1.200,00) é uma hospedagem válida: reembolsa o teto de hospedagem de `CC-COMERCIAL` (`400.00`, glosa `800.00`) e ativa viagem em `2026-07-22` e `2026-07-23`. Por isso, `e-008` (`2026-07-23`, `alimentacao`, `95.00 BRL`) opera sob o limite ampliado de R$ 135,00 e é `APROVADA` integralmente (`95.00`).
  - Já `e-010` (`2026-07-27`, `alimentacao`, `88.00 BRL`), em dia sem viagem, opera sob o limite base de R$ 90,00 de `CC-COMERCIAL` e é `APROVADA` (`88.00`).

### RN-008 — Limites diários por categoria e reembolso parcial por corte de excedente

**Regra:** Os limites diários aplicáveis ao centro de custo (já considerado o regime de viagem da `RN-007`) são controlados **por dia (`data`) e por categoria (`categoria_normalizada`)**, somando-se os valores em `BRL` (`valor_original`) de todas as despesas elegíveis daquela categoria naquela data na ordem em que aparecem na entrada.
Para cada despesa elegível, dado o `saldo_diario` restante daquela `(data, categoria_normalizada)`:
1. Se `valor_original <= saldo_diario`: `status: "APROVADA"`, `codigo_motivo: "OK"`, `valor_reembolsado = valor_original`, `valor_glosado = 0.00`, e `saldo_diario` diminui em `valor_original`.
2. Se `saldo_diario > 0.00` e `valor_original > saldo_diario`: `status: "APROVADA_PARCIALMENTE"`, `codigo_motivo: "LIMITE_DIARIO_EXCEDIDO"`, `valor_reembolsado = saldo_diario`, `valor_glosado = valor_original - saldo_diario`, e `saldo_diario` passa a `0.00`.
3. Se `saldo_diario == 0.00`: `status: "RECUSADA"`, `codigo_motivo: "LIMITE_DIARIO_EXCEDIDO"`, `valor_reembolsado = 0.00`, `valor_glosado = valor_original`.
**Origem:** política do RH v3/v4, itens 1, 2, 3, 4 e item A (`AMB-001`, `AMB-007`).
**Aceite:** Na data `2026-07-03` em `CC-ENG-PLATAFORMA` sob a v4 (limite de `alimentacao` = R$ 75,00), `d-001` (`72.50`) é `APROVADA` integralmente (`72.50`, restando saldo de `2.50`) e `d-002` (`38.00`) é `APROVADA_PARCIALMENTE` (reembolsa os `2.50` restantes e glosa `35.50`).

### RN-009 — Conversão cambial de despesas em moeda estrangeira para BRL

**Regra:** Toda despesa cuja `moeda_original` seja diferente de `"BRL"` deve ser convertida para `BRL` antes da verificação de nota fiscal (`RN-005`) e da aplicação dos limites diários (`RN-008`), seguindo as regras:
1. **Busca de data da cotação (fallback de dia útil anterior — `AMB-011`):** Consulta-se a tabela de `taxas` em `cambio.json` na data exata da despesa (`data`). Caso a data exata não conste na tabela (por ser sábado, domingo ou feriado bancário), utiliza-se a tabela da **maior data disponível em `cambio.json` que seja estritamente anterior à data da despesa (`data_cotacao <= despesa.data`)**. Se não existir nenhuma data `<= despesa.data` na tabela de câmbio, a despesa recebe status `RECUSADA`, `codigo_motivo: "CAMBIO_INDISPONIVEL"`, `taxa_cambio_aplicada: null`, `valor_original: 0.00`, `valor_reembolsado: 0.00` e `valor_glosado: 0.00`.
2. **Suporte à moeda (`AMB-012`):** Na data de cotação selecionada, verifica-se se o código `moeda_original` consta no mapa de moedas. Se a moeda não estiver cadastrada (ex.: `"GBP"`), a despesa recebe status `RECUSADA`, `codigo_motivo: "MOEDA_NAO_SUPORTADA"`, `taxa_cambio_aplicada: null`, `valor_original: 0.00`, `valor_reembolsado: 0.00` e `valor_glosado: 0.00` (não somando no `total_solicitado` em BRL por impossibilidade de conversão).
3. **Cálculo e arredondamento:** Existindo a `taxa`, define-se `taxa_cambio_aplicada = taxa` e calcula-se `valor_original = arredondar_half_up(valor_moeda_original * taxa, 2 casas)`. Para despesas em `"BRL"`, `taxa_cambio_aplicada = 1.00` e `valor_original = valor_moeda_original`.
**Origem:** comunicado da Política v4, item B (`AMB-011`, `AMB-012`, `AMB-013`).
**Aceite:**
- `e-002` (`2026-07-14`, `22.00 EUR`): taxa exata de `2026-07-14` (`5.93`) → `valor_original = 130.46 BRL`.
- `e-004` (`2026-07-18`, sábado, `30.00 EUR`): sem cotação em `18/07`, usa cotação do último dia útil anterior `2026-07-17` (`5.96`) → `valor_original = 178.80 BRL`.
- `e-006` (`2026-07-21`, `55.00 GBP`): moeda `"GBP"` ausente em `cambio.json` → `RECUSADA` com `codigo_motivo: "MOEDA_NAO_SUPORTADA"`.
- `f-004` (`2026-07-21`, `12.00 USD`): taxa exata de `2026-07-21` (`5.48`) → `valor_original = 65.76 BRL`.

---

## 6. Ambiguidades identificadas e decisões

*(As ambiguidades `AMB-001` a `AMB-010` da Política v3 permanecem registradas abaixo, seguidas pelas novas ambiguidades `AMB-011` a `AMB-016` introduzidas pelo Envelope da Política v4).*

### AMB-001 — Unidade de aplicação do limite ("por dia" vs. "por despesa") e mecânica de reembolso parcial

**Texto original do RH:** "1. Alimentação tem limite de R$ 60 por dia. 2. Transporte urbano tem limite de R$ 80 por dia. [...] 4. Despesas acima do limite são reembolsadas parcialmente."
**O que não está claro:** (a) Se houver mais de uma despesa da mesma categoria no mesmo dia, o teto vale para a soma do dia ou para cada comprovante individual? (b) Quando a soma do dia já atingiu o teto na primeira despesa, a segunda despesa do dia tem reembolso R$ 0,00 com status `RECUSADA` ou `APROVADA_PARCIALMENTE`?
**Decisão:** O limite é um saldo diário cumulativo por `(data, categoria_normalizada)` consumido na ordem da entrada. Quando uma despesa recebe valor entre `0.01` e `valor_original - 0.01`, o status é `APROVADA_PARCIALMENTE`; quando o saldo diário restante já é `0.00`, o reembolso é `0.00` e o status é `RECUSADA` com motivo `LIMITE_DIARIO_EXCEDIDO`.
**Justificativa:** Impede o fracionamento artificial de notas no mesmo dia para burlar o teto diário e evita rotular como "aprovada parcialmente" uma despesa cujo reembolso efetivo foi R$ 0,00.
**Regra afetada:** RN-008

### AMB-002 — Fronteira de obrigatoriedade da nota fiscal ("acima de R$ 100") e base de comparação

**Texto original do RH:** "5. Nota fiscal é obrigatória acima de R$ 100."
**O que não está claro:** (a) O valor exato de R$ 100,00 (`d-003`) exige nota fiscal (`>= 100`) ou apenas valores a partir de R$ 100,01 (`> 100`, como `d-004`)? (b) A exigência de nota fiscal incide sobre o valor original da despesa ou sobre o valor após o corte pelo teto da categoria?
**Decisão:** A comparação é estritamente maior que R$ 100,00 (`valor_original > 100.00`) e é avaliada sobre o `valor_original` (em BRL) da despesa antes da aplicação do teto diário.
**Justificativa:** "Acima de 100" em português e no campo `nota_fiscal_obrigatoria_acima_de: 100.00` define desigualdade estrita (`> 100.00`), e a obrigação fiscal decorre do valor da transação comercial original, não do teto interno de reembolso.
**Regra afetada:** RN-005

### AMB-003 — Sensibilidade a maiúsculas/minúsculas nas categorias e categorias não listadas

**Texto original do RH:** "9. Categorias fora da política não são reembolsáveis."
**O que não está claro:** Uma diferença apenas de caixa (`"ALIMENTACAO"` vs `"alimentacao"`) deve ser recusada como categoria fora da política ou normalizada?
**Decisão:** O nome da categoria é normalizado (trim + lowercase) antes da validação; portanto `"ALIMENTACAO"` é aceita como `"alimentacao"`, enquanto `"coworking"` é recusada com `CATEGORIA_NAO_REEMBOLSAVEL`.
**Justificativa:** Diferença de capitalização é variação de formatação de sistemas de origem, não uma categoria contábil distinta.
**Regra afetada:** RN-001, RN-004

### AMB-004 — Definição de duplicata e efeito sobre o saldo diário

**Texto original do RH:** "8. Duplicatas devem ser tratadas."
**O que não está claro:** O que define uma duplicata quando os itens têm `id` diferentes (`d-006` e `d-007`) e como tratá-la sem distorcer o saldo diário?
**Decisão:** Duplicata é todo item que repete `(data, categoria_normalizada, descricao_normalizada, fornecedor_normalizado, moeda_original, valor_moeda_original)` de um item anterior do mesmo lote; a primeira ocorrência é avaliada normalmente e as subsequentes são mantidas na saída com status `RECUSADA` (`DESPESA_DUPLICADA`) sem consumir saldo diário.
**Justificativa:** Preserva a rastreabilidade de auditoria na saída sem penalizar o lançamento original legítimo.
**Regra afetada:** RN-006

### AMB-005 — Definição de período de competência (`competencia` vs `inicio`/`fim`)

**Texto original do RH:** "7. Despesas devem ser lançadas dentro do período de competência."
**O que não está claro:** Validar pelo prefixo `AAAA-MM` de `competencia` ou pelo intervalo `[inicio, fim]`?
**Decisão:** Uma despesa está dentro do período de competência se e somente se `periodo.inicio <= despesa.data <= periodo.fim`.
**Justificativa:** Os campos `inicio` e `fim` definem explicitamente as fronteiras exatas da janela de apuração.
**Regra afetada:** RN-003

### AMB-006 — Tratamento de valores negativos / estornos

**Texto original do RH:** (Omisso sobre valores negativos; a entrada traz `d-009` com `valor: -45.00`).
**O que não está claro:** Um valor negativo ou zero deve recompor saldo diário, abater de outras despesas ou ser recusado?
**Decisão:** Despesas com `valor_moeda_original <= 0.00` são recusadas com `codigo_motivo: "VALOR_INVALIDO"`, `valor_reembolsado: 0.00` e `valor_glosado: 0.00`, sem alterar o saldo diário nem o `total_solicitado`.
**Justificativa:** Um estorno de corrida cancelada cujo débito original não consta no relatório não representa desembolso do colaborador.
**Regra afetada:** RN-002

### AMB-007 — Limite de hospedagem "por diária" diante da ausência do campo de quantidade de diárias

**Texto original do RH:** "3. Hospedagem tem limite de R$ 250 por diária."
**O que não está claro:** `d-010` (`"Hotel Rio - 2 diarias"`), `d-013` (`"Airbnb 3 noites"`) e `e-007` (`"Hotel Londres - 3 noites"`) mencionam múltiplas diárias apenas no texto livre `descricao`. O sistema deve fazer parsing de texto livre ou aplicar o teto de 1 diária da categoria `hospedagem` por lançamento/data?
**Decisão:** O sistema não extrai números do texto livre `descricao`; cada lançamento de hospedagem é submetido ao limite diário da categoria `hospedagem` do respectivo centro de custo na sua `data`.
**Justificativa:** Extrair regras financeiras de texto livre não estruturado é frágil e vulnerável a manipulação; a política opera apenas sobre campos estruturados do schema.
**Regra afetada:** RN-007, RN-008

### AMB-008 — Critério de ativação do regime "Colaborador em viagem" (+50% nos limites) e categorias elegíveis ao bônus

**Texto original do RH:** "6. Colaborador em viagem tem limites ampliados em 50%."
**O que não está claro:** Como inferir viagem sem campo explícito e quais categorias recebem +50%?
**Decisão:** O regime de viagem aplica-se por data: é ativado por flag `em_viagem: true`, pelas datas `D` e `D + 1 dia` de uma `hospedagem` válida, ou na data `D` de uma despesa válida em moeda estrangeira (`moeda_original != "BRL"`). Nas datas em viagem, apenas os limites cotidianos de `alimentacao` e `transporte_urbano` são ampliados em +50%, mantendo `hospedagem` e `representacao` em seus tetos próprios da tabela.
**Justificativa:** Toda hospedagem já ocorre em viagem; se o acréscimo de +50% incidisse sobre `hospedagem`, o teto de hospedagem da tabela jamais seria utilizado.
**Regra afetada:** RN-007

### AMB-009 — Casas decimais excedentes em valores monetários

**Texto original do RH:** (Omisso sobre precisão decimal; `d-011` traz `valor: 33.333` e conversões cambiais geram mais de 2 casas).
**O que não está claro:** Truncar ou arredondar valores com mais de 2 casas decimais?
**Decisão:** Todos os valores monetários são arredondados para 2 casas decimais pelo método half-up (`0.005` → `0.01`) na entrada e após a multiplicação pela taxa de câmbio.
**Justificativa:** Garante consistência contábil exata em centavos (`valor_reembolsado + valor_glosado == valor_original`).
**Regra afetada:** RN-001, RN-009

### AMB-010 — Despesas realizadas em finais de semana (sábado/domingo)

**Texto original do RH:** "7. Despesas devem ser lançadas dentro do período de competência."
**O que não está claro:** Despesas em sábado (`d-012` e `e-004` em `2026-07-18`) são permitidas?
**Decisão:** Despesas em finais de semana são permitidas sob as mesmas regras, desde que dentro de `[periodo.inicio, periodo.fim]`.
**Justificativa:** A política restringe apenas o período de competência, sem vedar trabalho em plantão ou viagem no fim de semana.
**Regra afetada:** RN-003

### AMB-011 — Taxa de câmbio da "data da despesa" quando a despesa ocorre em fim de semana ou dia sem cotação bancária

**Texto original do RH (Envelope v4, Item B):** "A conversão usa a taxa da data da despesa, não a taxa de hoje. As taxas estão em `cambio.json`." (E em `cambio.json`: `"observacao": "Cotacoes publicadas apenas em dias uteis bancarios."`).
**O que não está claro:** A despesa `e-004` ocorre no sábado `2026-07-18` (`30.00 EUR`), data que não existe em `cambio.json` (que salta de sexta `2026-07-17` para segunda `2026-07-20`). O sistema deve recusar a despesa de sábado por falta de câmbio, usar a cotação da sexta-feira anterior (`17/07`) ou usar a cotação da segunda-feira seguinte (`20/07`)?
**Decisão:** Quando a data exata `D` da despesa não constar em `cambio.json`, utiliza-se a cotação da **data disponível mais recente anterior a `D` (`data_cotacao <= D`)** — no caso de `2026-07-18`, a PTAX de fechamento de sexta-feira `2026-07-17` (`EUR = 5.96`). Apenas se não houver nenhuma data `<= D` na tabela é que a despesa é recusada com `CAMBIO_INDISPONIVEL`.
**Justificativa:** Segue a convenção contábil e cambial oficial do Banco Central (PTAX): em dias não úteis bancários, a taxa vigente é o fechamento do último dia útil imediatamente anterior.
**Regra afetada:** RN-009

### AMB-012 — Despesa em moeda estrangeira ausente da tabela de câmbio (`GBP`)

**Texto original do RH (Envelope v4, Item B):** "Colaboradores em viagem internacional lançam despesas em moeda estrangeira. A entrada agora pode trazer um campo `moeda` (ISO 4217). [...] As taxas estão em `cambio.json`."
**O que não está claro:** A despesa `e-006` (`2026-07-21`) foi lançada em libras esterlinas (`"moeda": "GBP"`, `valor: 55.00`), mas `cambio.json` contém apenas cotações para `USD` e `EUR`. O sistema deve abortar com erro de execução ou recusar o item com motivo específico?
**Decisão:** O sistema não interrompe o processamento do lote; a despesa cuja moeda não existe na tabela de câmbio recebe status `RECUSADA` com `codigo_motivo: "MOEDA_NAO_SUPORTADA"`, `taxa_cambio_aplicada: null`, `valor_original: 0.00`, `valor_reembolsado: 0.00` e `valor_glosado: 0.00`.
**Justificativa:** Um lançamento com moeda sem cotação cadastrada não pode impedir o reembolso das demais despesas válidas do colaborador no período.
**Regra afetada:** RN-009

### AMB-013 — Verificação de obrigatoriedade de nota fiscal ("acima de R$ 100") antes ou depois da conversão cambial

**Texto original do RH (Envelope v4, Item B):** "Os limites da política são sempre em BRL. Uma despesa em EUR é convertida antes de ser comparada ao limite." (E em `politica-v4.json`: `"nota_fiscal_obrigatoria_acima_de": 100.00`).
**O que não está claro:** A despesa `e-005` (`2026-07-20`, `transporte_urbano`, `tem_nota_fiscal: false`) tem `valor: 40.00` em `USD` (que é numericamente `<= 100`), mas após conversão pela taxa de `20/07` (`5.50`) passa a valer **`R$ 220,00`** (`> R$ 100,00`). A exigência de nota fiscal acima de 100 compara o número na moeda estrangeira (`40.00 <= 100`) ou o valor convertido em `BRL` (`220.00 > 100.00`)?
**Decisão:** A conversão cambial para `BRL` ocorre antes da validação de nota fiscal; portanto, o patamar de `R$ 100,00` (`nota_fiscal_obrigatoria_acima_de`) é comparado contra o `valor_original` já convertido em `BRL`. Assim, `e-005` (`40.00 USD` = `R$ 220,00` sem NF) é `RECUSADA` por `SEM_NOTA_FISCAL`, enquanto `e-003` (`14.50 EUR` = `R$ 85,26` sem NF) é isenta de NF.
**Justificativa:** O parâmetro `100.00` da política está expresso na `moeda_base: "BRL"`; comparar 100 unidades de moeda estrangeira (ex.: 100 EUR ≈ R$ 600) com 100 Reais violaria a regra de que todos os parâmetros da política estão em BRL.
**Regra afetada:** RN-005, RN-009

### AMB-014 — Significado de "aplica-se a política padrão" e categorias com `limite: 0.00` ou omitidas em um centro de custo

**Texto original do RH (Envelope v4, Item A):** "- `CC-ENG-PLATAFORMA` não reembolsa `hospedagem` de forma alguma. - Alguns centros de custo não têm entrada na tabela. Nesse caso, aplica-se a política padrão."
**O que não está claro:** (a) Quando um centro de custo está cadastrado em `centros_custo`, mas uma categoria tem `"limite": 0.00` (como `hospedagem` em `CC-ENG-PLATAFORMA`) ou foi omitida (como `hospedagem` em `CC-ADM`), deve-se fazer fallback para o limite de `padrao` (R$ 250,00) ou recusar a categoria como `CATEGORIA_NAO_REEMBOLSAVEL`? (b) Quando a despesa é recusada porque `hospedagem` tem `limite: 0.00`, o código de motivo é `CATEGORIA_NAO_REEMBOLSAVEL` ou `LIMITE_DIARIO_EXCEDIDO`, e ela ativa ou não o regime de viagem?
**Decisão:** A política `padrao` aplica-se exclusivamente quando o código `colaborador.centro_custo` **não existe** em `centros_custo` (ex.: `CC-SUPORTE-N2`). Se o centro de custo existe em `centros_custo`, vale estritamente o seu próprio mapa: categorias ausentes desse mapa ou configuradas com `limite <= 0.00` são recusadas na validação de elegibilidade (`RN-004`) com `codigo_motivo: "CATEGORIA_NAO_REEMBOLSAVEL"` e **não** ativam o regime de viagem (`RN-007`).
**Justificativa:** O comunicado afirma expressamente que "`CC-ENG-PLATAFORMA` não reembolsa `hospedagem` de forma alguma"; tratá-la como `CATEGORIA_NAO_REEMBOLSAVEL` na Passagem 1 impede que uma hospedagem proibida para aquele CC ative indevidamente bônus de viagem (+50%) no dia.
**Regra afetada:** RN-004, RN-007

### AMB-015 — Ativação do regime de viagem (+50%) por despesas em moeda estrangeira e incidência sobre a nova categoria `representacao`

**Texto original do RH (Envelope v4, Itens A e B):** "`CC-COMERCIAL` tem uma categoria nova, `representacao`, que não existia na v3 — limite de R$ 300 por dia. [...] Colaboradores em viagem internacional lançam despesas em moeda estrangeira."
**O que não está claro:** (a) Em `despesas-envelope.json`, o colaborador lança almoços em Lisboa em `EUR` nos dias `14/07`, `15/07` e `18/07` (`e-002`, `e-003`, `e-004`), mas não há lançamento de hospedagem nessas datas (só há hospedagem em Londres no dia `22/07`, `e-007`). Despesas válidas em moeda estrangeira (`moeda != "BRL"`) caracterizam por si sós que o colaborador está em viagem naquela data? (b) O bônus de +50% em viagem amplia a categoria `representacao` ou apenas as categorias cotidianas (`alimentacao` e `transporte_urbano`)?
**Decisão:** Toda despesa válida com `moeda_original != "BRL"` ativa o regime de viagem na sua própria `data` (além da ativação em `D` e `D + 1` por `hospedagem` válida). O acréscimo de +50% em viagem continua aplicando-se apenas às despesas cotidianas do colaborador (`alimentacao` e `transporte_urbano`), mantendo `hospedagem` e `representacao` nos seus limites fixos da tabela.
**Justificativa:** O próprio comunicado define que despesas em moeda estrangeira decorrem de "colaboradores em viagem internacional"; logo, um gasto válido em `EUR` ou `USD` comprova que o colaborador estava em viagem naquela data, enquanto `representacao` (jantar de negócios com clientes/parceiros) já possui teto específico elevado (R$ 300,00).
**Regra afetada:** RN-007

### AMB-016 — Vigência retroativa da Política v4 sobre o lote de referência da competência `2026-07` (`CC-ENG-PLATAFORMA`)

**Texto original do RH (Envelope v4):** "O RH revisou a política. Vigência imediata, retroativa à competência atual (`2026-07`)."
**O que não está claro:** O arquivo de exemplo do Dia 1 (`exemplos/despesas-exemplo.json`) pertence justamente à competência `2026-07` e ao centro de custo `CC-ENG-PLATAFORMA`. Sob a Política v4, `CC-ENG-PLATAFORMA` passa a ter limite de `alimentacao` de R$ 75,00 (em vez de R$ 60,00) e `hospedagem` com limite R$ 0,00 (não reembolsável).
**Decisão:** Como a Política v4 tem vigência imediata e retroativa a `2026-07-01`, o motor passa a utilizar `politica-v4.json` e `cambio.json` como configuração padrão da versão 2.0, atualizando o resultado esperado de `CC-ENG-PLATAFORMA` (`CA-001`) para refletir as regras da v4 (enquanto o comportamento legado da v3 continua podendo ser testado unitariamente se instanciada a política v3).
**Justificativa:** Cumpre literalmente a determinação do comunicado ("Vigência imediata, retroativa à competência atual") sem manter duas verdades conflitantes para a competência `2026-07`.
**Regra afetada:** RN-004, RN-007, RN-008, CA-001

---

## 7. Casos de borda

| Caso | Entrada | Comportamento esperado | Regra |
|---|---|---|---|
| Múltiplas despesas em `CC-ENG-PLATAFORMA` sob v4 (limite `alimentacao` R$ 75,00) | `d-001` (R$ 72,50) e `d-002` (R$ 38,00) em `2026-07-03` | `d-001` é `APROVADA` (reembolsa R$ 72,50, saldo resta R$ 2,50); `d-002` é `APROVADA_PARCIALMENTE` (reembolsa R$ 2,50, glosa R$ 35,50) | RN-004, RN-008, AMB-001, AMB-016 |
| Hospedagem em `CC-ENG-PLATAFORMA` sob v4 (`limite: 0.00`) | `d-010` (`2026-07-14`, `hospedagem`, R$ 480,00, NF `true`) | `RECUSADA` por `CATEGORIA_NAO_REEMBOLSAVEL` (reembolsa R$ 0,00, glosa R$ 480,00) e **não** ativa regime de viagem em `14/07` e `15/07` | RN-004, RN-007, AMB-014, AMB-016 |
| Categoria `representacao` em `CC-COMERCIAL` | `e-001` (`2026-07-13`, `representacao`, R$ 340,00, NF `true`) | `APROVADA_PARCIALMENTE` até o limite de R$ 300,00 de `CC-COMERCIAL` (reembolsa R$ 300,00, glosa R$ 40,00) | RN-004, RN-008 |
| Despesa em `EUR` em dia útil ativando viagem (+50%) em `CC-COMERCIAL` | `e-002` (`2026-07-14`, `alimentacao`, `22.00 EUR`, NF `true`) | Convertida pela taxa de `14/07` (`5.93`) → `R$ 130,46`. Como é moeda estrangeira, ativa viagem no dia (limite `alimentacao` de `CC-COMERCIAL` sobe de R$ 90 para R$ 135) → `APROVADA` (`130.46`) | RN-007, RN-009, AMB-015 |
| Despesa em `EUR` sem NF cujo valor convertido em BRL fica `<= R$ 100,00` | `e-003` (`2026-07-15`, `alimentacao`, `14.50 EUR`, NF `false`) | Convertida pela taxa de `15/07` (`5.88`) → `R$ 85,26` (`<= 100.00`, isenta de NF) → `APROVADA` (`85.26`) | RN-005, RN-009, AMB-013 |
| Despesa em `EUR` no sábado (sem cotação na data exata) | `e-004` (`2026-07-18`, sábado, `alimentacao`, `30.00 EUR`, NF `true`) | Usa cotação do último dia útil anterior `2026-07-17` (`5.96`) → `R$ 178,80`. Em viagem (limite R$ 135,00) → `APROVADA_PARCIALMENTE` (reembolsa `135.00`, glosa `43.80`) | RN-007, RN-008, RN-009, AMB-011 |
| Despesa em `USD` sem NF cujo valor nominal é `<= 100` mas em BRL é `> R$ 100,00` | `e-005` (`2026-07-20`, `transporte_urbano`, `40.00 USD`, NF `false`) | Convertida pela taxa de `20/07` (`5.50`) → `R$ 220,00` (`> 100.00` sem NF) → `RECUSADA` por `SEM_NOTA_FISCAL` (glosa `220.00`) | RN-005, RN-009, AMB-013 |
| Moeda estrangeira não existente em `cambio.json` (`GBP`) | `e-006` (`2026-07-21`, `representacao`, `55.00 GBP`, NF `true`) | `RECUSADA` por `MOEDA_NAO_SUPORTADA` (`taxa_cambio_aplicada: null`, `valor_original: 0.00`, `valor_reembolsado: 0.00`, `valor_glosado: 0.00`) | RN-009, AMB-012 |
| Hospedagem válida em `CC-COMERCIAL` ativando viagem para o dia seguinte (`D+1`) | `e-007` (`2026-07-22`, `hospedagem`, `1200.00 BRL`, NF `true`) e `e-008` (`2026-07-23`, `alimentacao`, `95.00 BRL`, NF `true`) | `e-007` é `APROVADA_PARCIALMENTE` no limite de R$ 400,00 (glosa `800.00`) e ativa viagem em `22/07` e `23/07`; `e-008` em `23/07` tem limite de `alimentacao` ampliado para R$ 135,00 e é `APROVADA` (`95.00`) | RN-007, RN-008, AMB-008 |
| Centro de custo desconhecido (`CC-SUPORTE-N2`) tentando usar `representacao` | `f-003` (`2026-07-17`, `representacao`, `190.00 BRL`) em `despesas-envelope-cc-desconhecido.json` | Fallback para tabela `padrao` (que não inclui `representacao`) → `RECUSADA` por `CATEGORIA_NAO_REEMBOLSAVEL` | RN-004, AMB-014 |

## 8. Ordem de aplicação das regras

A ordem de precedência é determinística e obrigatória:

1. **Passo 0 — Normalização Básica (RN-001):** Arredondar `valor` para 2 casas decimais (`valor_moeda_original`), normalizar `moeda_original` (padrão `"BRL"`, uppercase) e normalizar textos (`categoria_normalizada`, `descricao_normalizada`, `fornecedor_normalizado`).
2. **Passo 1 — Validação de Elegibilidade Individual e Conversão Cambial (nesta ordem estrita de curto-circuito):**
   - **1.1. Valor positivo (RN-002):** Se `valor_moeda_original <= 0.00` → `RECUSADA` (`VALOR_INVALIDO`). Para aqui.
   - **1.2. Período de competência (RN-003):** Se `data < periodo.inicio` ou `data > periodo.fim` → `RECUSADA` (`FORA_PERIODO_COMPETENCIA`). Para aqui.
   - **1.3. Categoria elegível no Centro de Custo (RN-004):** Resolver a tabela do `colaborador.centro_custo` (ou `padrao` se o CC não existir). Se `categoria_normalizada` não existir nessa tabela ou tiver `limite <= 0.00` → `RECUSADA` (`CATEGORIA_NAO_REEMBOLSAVEL`). Para aqui.
   - **1.4. Duplicidade (RN-006):** Se a tupla `(data, categoria_normalizada, descricao_normalizada, fornecedor_normalizado, moeda_original, valor_moeda_original)` já tiver sido vista anteriormente no lote → `RECUSADA` (`DESPESA_DUPLICADA`). Para aqui.
   - **1.5. Conversão cambial para BRL (RN-009):** Se `moeda_original != "BRL"`, buscar a data de cotação `<= data` em `cambio.json` (se inexistente → `RECUSADA` / `CAMBIO_INDISPONIVEL`) e a taxa da `moeda_original` (se inexistente → `RECUSADA` / `MOEDA_NAO_SUPORTADA`). Calcular `valor_original = arredondar_half_up(valor_moeda_original * taxa, 2 casas)`.
   - **1.6. Nota fiscal sobre o valor em BRL (RN-005):** Se `valor_original > nota_fiscal_obrigatoria_acima_de` (`100.00 BRL`) e `tem_nota_fiscal == false` → `RECUSADA` (`SEM_NOTA_FISCAL`). Para aqui.
3. **Passo 2 — Apuração das Datas em Viagem (RN-007):**
   - Para todas as despesas que sobreviveram ao Passo 1:
     - Se `categoria_normalizada == "hospedagem"`, marcar `data` e `data + 1 dia` como datas em viagem;
     - Se `moeda_original != "BRL"` ou `despesa.em_viagem == true` ou `colaborador.em_viagem == true`, marcar `data` como data em viagem.
4. **Passo 3 — Aplicação de Limites Diários do Centro de Custo e Reembolso Parcial (RN-008):**
   - Para cada despesa que sobreviveu ao Passo 1 (na ordem original da entrada), consultar o saldo diário em `BRL` de `(data, categoria_normalizada)` (inicializado com o limite do centro de custo, ampliado em +50% para `alimentacao` e `transporte_urbano` se a `data` estiver em viagem) e aprovar total (`APROVADA`), parcialmente (`APROVADA_PARCIALMENTE`) ou recusar por limite esgotado (`RECUSADA` / `LIMITE_DIARIO_EXCEDIDO`).

## 9. Critérios de aceite

O sistema está pronto quando:

- [ ] **CA-001 (Lote `despesas-exemplo.json` sob Política v4 — `CC-ENG-PLATAFORMA`):** Ao processar `exemplos/despesas-exemplo.json` com `politica-v4.json`, o sistema aplica o limite de `alimentacao` de R$ 75,00 (`d-001` aprova `72.50` e `d-002` aprova parcialmente `2.50`; `d-014` de `61.00` aprova `61.00`) e recusa `hospedagem` (`d-010`) como `CATEGORIA_NAO_REEMBOLSAVEL` (sem ativar viagem), resultando em `total_solicitado: 1861.84`, `total_reembolsado: 373.93`, `total_glosado: 1487.91`, `quantidade_aprovadas: 5`, `quantidade_aprovadas_parcialmente: 2` e `quantidade_recusadas: 7`.
- [ ] **CA-002:** Despesas de mesma categoria e data acumulam consumo contra um único limite diário do centro de custo.
- [ ] **CA-003:** Despesa com valor em BRL `<= 100.00` sem nota fiscal (`d-003`, `e-003`) é aceita para cálculo de limite, enquanto despesa com valor em BRL `> 100.00` sem nota fiscal (`d-004` `100.01 BRL`, `e-005` `40.00 USD = 220.00 BRL`) é recusada com `SEM_NOTA_FISCAL`.
- [ ] **CA-004:** Categorias são tratadas de forma case-insensitive e validadas contra a tabela do centro de custo do colaborador (ou `padrao` se o centro de custo não estiver na tabela).
- [ ] **CA-005:** Despesas duplicadas (`d-007` idêntica a `d-006` exceto pelo `id`) são recusadas com `DESPESA_DUPLICADA` e não consomem saldo diário.
- [ ] **CA-006:** Despesas fora do intervalo `[periodo.inicio, periodo.fim]` (`d-008`) são recusadas com `FORA_PERIODO_COMPETENCIA`, enquanto despesas em sábado dentro do intervalo (`d-012`, `e-004`) são processadas normalmente.
- [ ] **CA-007:** Despesas com valor negativo ou zero (`d-009`, `-45.00`) são recusadas com `VALOR_INVALIDO`, não entram no `total_solicitado` e não alteram saldos diários.
- [ ] **CA-008:** Hospedagem válida (`e-007`, `f-002`) é limitada ao teto de hospedagem do centro de custo e ativa regime de viagem (+50% em `alimentacao` e `transporte_urbano`) para `D` e `D + 1`; despesas válidas em moeda estrangeira (`e-002`, `e-003`, `e-004`, `f-004`) ativam regime de viagem na data `D`.
- [ ] **CA-009 (Lote `despesas-envelope.json` — `CC-COMERCIAL` e Câmbio):** Ao processar `exemplos/Envelope/despesas-envelope.json`, o sistema converte `EUR` e `USD` pela PTAX da data (com fallback de sábado `2026-07-18` para sexta `2026-07-17` em `e-004`), recusa `e-006` (`GBP`) com `MOEDA_NAO_SUPORTADA`, recusa `e-005` (`40 USD = 220 BRL` sem NF) com `SEM_NOTA_FISCAL`, e gera `total_solicitado: 2517.52`, `total_reembolsado: 1233.72`, `total_glosado: 1283.80`, `quantidade_aprovadas: 4`, `quantidade_aprovadas_parcialmente: 3` e `quantidade_recusadas: 3`.
- [ ] **CA-010 (Lote `despesas-envelope-cc-desconhecido.json` — Fallback `padrao`):** Ao processar `exemplos/Envelope/despesas-envelope-cc-desconhecido.json` (`CC-SUPORTE-N2`), o sistema aplica a política `padrao`, recusa `f-003` (`representacao`) com `CATEGORIA_NAO_REEMBOLSAVEL`, converte `f-004` (`12.00 USD` em `21/07` × `5.48` = `65.76 BRL`), e gera `total_solicitado: 623.76`, `total_reembolsado: 373.76`, `total_glosado: 250.00`, `quantidade_aprovadas: 2`, `quantidade_aprovadas_parcialmente: 1` e `quantidade_recusadas: 1`.

## 10. O que fica em aberto

- **Fila de aprovação manual acima de R$ 500,00 (Item C opcional do Envelope v4):** O comunicado do Dia 2 mencionou como item opcional uma fila de pendência de aprovação de gestor para itens cujo valor reembolsável ultrapasse R$ 500,00. Como na tabela `politica-v4.json` o maior limite diário possível de qualquer categoria (mesmo com bônus de viagem de +50%) é R$ 400,00 (`hospedagem` em `CC-COMERCIAL`), nenhum item individual pode ter `valor_reembolsado > 500.00` sob a `politica-v4.json` atual. Por esse motivo e pela diretriz explícita do desafio de priorizar a consistência da spec sobre o item opcional C, esse estado de pendência foi declarado fora de escopo na Seção 3.
- **Múltiplas diárias em um único lançamento de hospedagem:** Mantida a decisão de `AMB-007` de não fazer parsing do texto livre `descricao` (`"3 noites"`, `"2 diarias"`), aplicando o limite estruturado da categoria na data do lançamento.
