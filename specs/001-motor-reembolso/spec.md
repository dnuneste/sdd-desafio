# Spec — Motor de Cálculo de Reembolso

**Versão:** 1.2 · **Status:** aprovada · **Última alteração:** `2026-11-25`

> **Regra de ouro deste arquivo:** ele descreve o QUÊ e o PORQUÊ. Nenhuma linha
> aqui pode citar linguagem, biblioteca, classe, função ou estrutura de pasta.
> Se apareceu solução, o lugar dela é o `plan.md`.
>
> **Teste de aceitação da própria spec:** uma pessoa que nunca viu o projeto
> consegue, lendo só este arquivo, verificar se o sistema está correto?

---

## 1. Problema

A conferência de reembolso de despesas corporativas é feita manualmente pelo time financeiro em planilhas, analisando lançamento por lançamento contra uma política de RH textual e ambígua. Esse processo manual é lento, sujeito a interpretações divergentes entre analistas e gera erros financeiros em pagamentos, glosas indevidas e retrabalho de auditoria.

## 2. Objetivo

Avaliar automaticamente o lote de despesas de um colaborador em um período de competência, determinando de forma determinística e auditável o status, o valor reembolsável e a justificativa de cada item, bem como o resumo financeiro consolidado do período.

## 3. Fora de escopo

- Não realiza leitura ou extração de dados de texto livre no campo `descricao` (como tentar adivinhar número de diárias ou contexto por palavras-chave).
- Não processa múltiplos colaboradores ou múltiplos períodos de competência em uma mesma execução.
- Não faz conversão cambial (assume-se que todos os valores monetários estão em Reais — BRL).
- Não valida autenticidade fiscal de notas junto a órgãos governamentais (confia exclusivamente no campo booleano `tem_nota_fiscal`).
- Não persiste histórico entre execuções distintas nem consulta bases de dados externas.
- Não altera, reordena nem remove itens da lista de despesas na saída (toda despesa de entrada produz exatamente um item avaliado na saída, na mesma ordem).

## 4. Entrada e saída

**Entrada:** documento JSON conforme `exemplos/despesas-exemplo.json`. Campos e significado:

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
| `despesas[].valor` | Número | Valor monetário solicitado pelo colaborador | Sim |
| `despesas[].tem_nota_fiscal` | Booleano | Indica se há comprovante fiscal anexado (`true`/`false`) | Sim |

**Saída:** documento JSON contendo a identificação do colaborador, o período, o resumo consolidado e a lista de resultados por despesa:

| Campo | Tipo | Significado |
|---|---|---|
| `colaborador` | Objeto | Eco dos dados do colaborador da entrada (`id`, `nome`, `centro_custo`) |
| `periodo` | Objeto | Eco dos dados do período da entrada (`competencia`, `inicio`, `fim`) |
| `em_viagem` | Booleano | Indica se o lote não vazio teve o regime de viagem ativado (`true`/`false`) |
| `resumo` | Objeto | Totais consolidados do processamento |
| `resumo.total_solicitado` | Número (2 casas) | Soma dos valores originais (arredondados para 2 casas) apenas das despesas com valor positivo (`> 0`) |
| `resumo.total_reembolsado` | Número (2 casas) | Soma final dos valores efetivamente aprovados para reembolso |
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
| `resultados[].valor_original` | Número (2 casas) | Valor da entrada normalizado para 2 casas decimais |
| `resultados[].valor_reembolsado` | Número (2 casas) | Valor aprovado após aplicação das regras (`0.00` quando recusada) |
| `resultados[].valor_glosado` | Número (2 casas) | Valor cortado (`valor_original - valor_reembolsado` para valores positivos, ou `0.00` se `valor_original <= 0`) |
| `resultados[].status` | Texto | Um entre: `APROVADA`, `APROVADA_PARCIALMENTE`, `RECUSADA` |
| `resultados[].codigo_motivo` | Texto | Código padronizado da decisão (`OK`, `LIMITE_DIARIO_EXCEDIDO`, `SEM_NOTA_FISCAL`, `CATEGORIA_NAO_REEMBOLSAVEL`, `FORA_PERIODO_COMPETENCIA`, `DESPESA_DUPLICADA`, `VALOR_INVALIDO`) |
| `resultados[].justificativa` | Texto | Explicação legível por humanos detalhando a regra aplicada |

### Exemplo de saída para entrada reduzida

```json
{
  "colaborador": {
    "id": "c-0417",
    "nome": "Marina Volpi",
    "centro_custo": "CC-ENG-PLATAFORMA"
  },
  "periodo": {
    "competencia": "2026-07",
    "inicio": "2026-07-01",
    "fim": "2026-07-31"
  },
  "em_viagem": false,
  "resumo": {
    "total_solicitado": 110.50,
    "total_reembolsado": 60.00,
    "total_glosado": 50.50,
    "quantidade_despesas": 2,
    "quantidade_aprovadas": 0,
    "quantidade_aprovadas_parcialmente": 1,
    "quantidade_recusadas": 1
  },
  "resultados": [
    {
      "id": "d-001",
      "data": "2026-07-03",
      "categoria_original": "alimentacao",
      "categoria_normalizada": "alimentacao",
      "valor_original": 72.50,
      "valor_reembolsado": 60.00,
      "valor_glosado": 12.50,
      "status": "APROVADA_PARCIALMENTE",
      "codigo_motivo": "LIMITE_DIARIO_EXCEDIDO",
      "justificativa": "Despesa excede o saldo diario da categoria alimentacao (limite R$ 60.00). Reembolso parcial de R$ 60.00; excedente glosado de R$ 12.50."
    },
    {
      "id": "d-002",
      "data": "2026-07-03",
      "categoria_original": "alimentacao",
      "categoria_normalizada": "alimentacao",
      "valor_original": 38.00,
      "valor_reembolsado": 0.00,
      "valor_glosado": 38.00,
      "status": "RECUSADA",
      "codigo_motivo": "LIMITE_DIARIO_EXCEDIDO",
      "justificativa": "Limite diario da categoria alimentacao (R$ 60.00) ja totalmente consumido na data 2026-07-03."
    }
  ]
}
```

---

## 5. Regras de negócio

### RN-001 — Normalização e arredondamento monetário na entrada

**Regra:** Todo valor monetário de entrada (`valor`) é arredondado para 2 casas decimais utilizando a regra de arredondamento "meio para cima" (half-up: `0.005` arredonda para `0.01`) antes de qualquer validação ou cálculo. Todo texto de `categoria` é normalizado removendo espaços nas extremidades e convertendo para letras minúsculas (`"ALIMENTACAO"` torna-se `"alimentacao"`).
**Origem:** política do RH (implícita) e higiene de dados financeiros (`AMB-003`, `AMB-009`).
**Aceite:** Uma despesa com `valor: 33.333` e `categoria: "ALIMENTACAO"` é processada com `valor_original: 33.33` e `categoria_normalizada: "alimentacao"`.

### RN-002 — Rejeição de valores não positivos (estornos, negativos ou zero)

**Regra:** Despesas com `valor_original <= 0.00` não são reembolsáveis. Recebem status `RECUSADA`, `codigo_motivo: "VALOR_INVALIDO"`, `valor_reembolsado: 0.00` e `valor_glosado: 0.00`. Tais itens não somam no `total_solicitado` do resumo e não abatem nem recompõem o saldo diário de nenhuma categoria.
**Origem:** política do RH (implícita) e item `d-009` da entrada de referência (`AMB-006`).
**Aceite:** A despesa `d-009` (`valor: -45.00`) resulta em `status: "RECUSADA"`, `codigo_motivo: "VALOR_INVALIDO"`, `valor_reembolsado: 0.00`, `valor_glosado: 0.00`.

### RN-003 — Validação do período de competência

**Regra:** A data da despesa (`data`) deve estar contida no intervalo fechado `[periodo.inicio, periodo.fim]` (`periodo.inicio <= data <= periodo.fim`), independentemente do dia da semana (sábados, domingos e feriados dentro do intervalo são válidos). Despesas fora desse intervalo recebem status `RECUSADA`, `codigo_motivo: "FORA_PERIODO_COMPETENCIA"` e `valor_reembolsado: 0.00`.
**Origem:** política do RH, item 7 (`AMB-005`, `AMB-010`).
**Aceite:** Em um período `2026-07-01` a `2026-07-31`, `d-008` (`2026-04-15`) é `RECUSADA` com `FORA_PERIODO_COMPETENCIA`, enquanto `d-012` (`2026-07-18`, sábado) prossegue normalmente para avaliação.

### RN-004 — Elegibilidade de categorias da política

**Regra:** Apenas as categorias normalizadas `alimentacao`, `transporte_urbano` e `hospedagem` fazem parte da política. Qualquer outra categoria recebe status `RECUSADA`, `codigo_motivo: "CATEGORIA_NAO_REEMBOLSAVEL"` e `valor_reembolsado: 0.00`.
**Origem:** política do RH, itens 1, 2, 3 e 9 (`AMB-003`).
**Aceite:** A despesa `d-005` (`categoria: "coworking"`, `valor: 89.00`) resulta em `status: "RECUSADA"`, `codigo_motivo: "CATEGORIA_NAO_REEMBOLSAVEL"`, `valor_reembolsado: 0.00`; já `d-014` (`categoria: "ALIMENTACAO"`) é reconhecida como categoria válida `alimentacao`.

### RN-005 — Obrigatoriedade de nota fiscal acima de R$ 100,00

**Regra:** Toda despesa cujo `valor_original` seja estritamente maior que `100.00` (`valor_original > 100.00`) exige `tem_nota_fiscal: true`. Se `valor_original > 100.00` e `tem_nota_fiscal` for `false`, a despesa recebe status `RECUSADA`, `codigo_motivo: "SEM_NOTA_FISCAL"` e `valor_reembolsado: 0.00`, sem consumir limite diário da categoria. Despesas com `valor_original <= 100.00` estão dispensadas de nota fiscal.
**Origem:** política do RH, item 5 (`AMB-002`).
**Aceite:** `d-003` (`valor: 100.00`, `tem_nota_fiscal: false`) não é recusada por falta de nota fiscal; `d-004` (`valor: 100.01`, `tem_nota_fiscal: false`) e `d-013` (`valor: 690.00`, `tem_nota_fiscal: false`) são `RECUSADA` com `codigo_motivo: "SEM_NOTA_FISCAL"`.

### RN-006 — Detecção e recusa de despesas duplicadas

**Regra:** Duas ou mais despesas são consideradas duplicatas quando possuem exatamente a mesma tupla de negócio: `(data, categoria_normalizada, descricao_normalizada, fornecedor_normalizado, valor_original)`, onde `descricao_normalizada` e `fornecedor_normalizado` têm espaços nas extremidades removidos e letras convertidas para minúsculas. A primeira ocorrência na ordem de entrada é processada normalmente; todas as ocorrências subsequentes idênticas recebem status `RECUSADA`, `codigo_motivo: "DESPESA_DUPLICADA"` e `valor_reembolsado: 0.00`, sem consumir limite diário.
**Origem:** política do RH, item 8 (`AMB-004`).
**Aceite:** Entre `d-006` e `d-007` (ambas em `2026-07-09`, `alimentacao`, `"Almoco"`, `"Bistro Central"`, `54.90`), `d-006` é `APROVADA` (`54.90`) e `d-007` é `RECUSADA` com `codigo_motivo: "DESPESA_DUPLICADA"` (`0.00`).

### RN-007 — Caracterização de colaborador em viagem e ampliação de limites em 50%

**Regra:** Considera-se que uma despesa ocorreu em regime de **colaborador em viagem** quando:
1. O objeto `colaborador` ou a própria despesa contiver o campo booleano opcional `em_viagem: true`; **OU**
2. A data da despesa (`data`) coincidir com uma data coberta por uma despesa de `hospedagem` válida (isto é, dentro do período de competência, com valor positivo, não duplicada e com nota fiscal quando exigida). Como o schema de entrada não possui campo estruturado de número de diárias nem data de check-out, cada lançamento válido de `hospedagem` na data `D` caracteriza regime de viagem na data `D` e no dia imediatamente seguinte `D + 1 dia` (data de check-out da estadia).

Nas datas caracterizadas como em viagem, os limites diários das despesas cotidianas (`alimentacao` e `transporte_urbano`) são ampliados em 50%, enquanto `hospedagem` mantém seu teto próprio de viagem de R$ 250,00 por diária:
- `alimentacao`: de R$ 60,00 para **R$ 90,00 por dia**
- `transporte_urbano`: de R$ 80,00 para **R$ 120,00 por dia**
- `hospedagem`: **R$ 250,00 por diária** (não sofre acréscimo de +50% sobre si mesma, pois toda hospedagem já pressupõe viagem)

O campo de saída de nível superior `em_viagem` será `true` se ao menos uma data no período tiver o regime de viagem ativado.
**Origem:** política do RH, item 6 (`AMB-007`, `AMB-008`).
**Aceite:** Como `d-010` (`2026-07-14`, `hospedagem`, `480.00`, `tem_nota_fiscal: true`) é uma hospedagem válida, as datas `2026-07-14` e `2026-07-15` operam em regime de viagem. Assim, `d-010` é avaliada contra o limite de diária de hospedagem de R$ 250,00 (reembolsa `250.00`, glosa `230.00`) e `d-011` (`2026-07-15`, `alimentacao`, `33.33`) é avaliada sob o limite ampliado de alimentação em viagem de R$ 90,00. Já `d-013` (`2026-07-22`, `hospedagem`, `tem_nota_fiscal: false`) é inválida por falta de NF, portanto não ativa regime de viagem em `2026-07-22`.

### RN-008 — Limites diários por categoria e reembolso parcial por corte de excedente

**Regra:** Os limites base da política são aplicados **por dia (`data`) e por categoria (`categoria_normalizada`)**, somando-se todas as despesas elegíveis daquela categoria naquela data na ordem em que aparecem na entrada:
- `alimentacao`: **R$ 60,00 / dia** (ou **R$ 90,00 / dia** em data de viagem)
- `transporte_urbano`: **R$ 80,00 / dia** (ou **R$ 120,00 / dia** em data de viagem)
- `hospedagem`: **R$ 250,00 / dia**

Para cada despesa elegível, dado o `saldo_diario` restante daquela `(data, categoria_normalizada)`:
1. Se `valor_original <= saldo_diario`: a despesa é integralmente aprovada (`status: "APROVADA"`, `codigo_motivo: "OK"`, `valor_reembolsado = valor_original`, `valor_glosado = 0.00`) e o `saldo_diario` diminui em `valor_original`.
2. Se `saldo_diario > 0.00` e `valor_original > saldo_diario`: a despesa é parcialmente aprovada até o teto disponível (`status: "APROVADA_PARCIALMENTE"`, `codigo_motivo: "LIMITE_DIARIO_EXCEDIDO"`, `valor_reembolsado = saldo_diario`, `valor_glosado = valor_original - saldo_diario`) e o `saldo_diario` passa a `0.00`.
3. Se `saldo_diario == 0.00`: a despesa é recusada por esgotamento do limite diário (`status: "RECUSADA"`, `codigo_motivo: "LIMITE_DIARIO_EXCEDIDO"`, `valor_reembolsado = 0.00`, `valor_glosado = valor_original`).
**Origem:** política do RH, itens 1, 2, 3 e 4 (`AMB-001`, `AMB-007`).
**Aceite:** Na data `2026-07-03` (sem viagem, limite de `alimentacao` = R$ 60,00), `d-001` (`72.50`) recebe `60.00` (`APROVADA_PARCIALMENTE`, glosa `12.50`, saldo zera) e `d-002` (`38.00`) recebe `0.00` (`RECUSADA` por `LIMITE_DIARIO_EXCEDIDO`, glosa `38.00`).

---

## 6. Ambiguidades identificadas e decisões

### AMB-001 — Unidade de aplicação do limite ("por dia" vs. "por despesa") e mecânica de reembolso parcial

**Texto original do RH:** "1. Alimentação tem limite de R$ 60 por dia. 2. Transporte urbano tem limite de R$ 80 por dia. [...] 4. Despesas acima do limite são reembolsadas parcialmente."
**O que não está claro:** (a) Se houver mais de uma despesa da mesma categoria no mesmo dia (ex.: `d-001` almoço R$ 72,50 e `d-002` jantar R$ 38,00 em `2026-07-03`), o teto vale para a soma do dia ou para cada comprovante individual? (b) Quando a soma do dia já atingiu o teto na primeira despesa, a segunda despesa do dia tem reembolso R$ 0,00 com status `RECUSADA` ou `APROVADA_PARCIALMENTE`?
**Decisão:** O limite é um saldo diário cumulativo por `(data, categoria_normalizada)` consumido na ordem da entrada. Quando uma despesa recebe valor entre `0.01` e `valor_original - 0.01`, o status é `APROVADA_PARCIALMENTE`; quando o saldo diário restante já é `0.00`, o reembolso é `0.00` e o status é `RECUSADA` com motivo `LIMITE_DIARIO_EXCEDIDO`.
**Justificativa:** Impede o fracionamento artificial de notas no mesmo dia para burlar o teto diário e evita rotular como "aprovada parcialmente" uma despesa cujo reembolso efetivo foi R$ 0,00.
**Regra afetada:** RN-008

### AMB-002 — Fronteira de obrigatoriedade da nota fiscal ("acima de R$ 100") e base de comparação

**Texto original do RH:** "5. Nota fiscal é obrigatória acima de R$ 100."
**O que não está claro:** (a) O valor exato de R$ 100,00 (`d-003`) exige nota fiscal (`>= 100`) ou apenas valores a partir de R$ 100,01 (`> 100`, como `d-004`)? (b) A exigência de nota fiscal incide sobre o valor original da despesa ou sobre o valor após o corte pelo teto da categoria (ex.: R$ 100,00 em transporte cujo teto é R$ 80,00)?
**Decisão:** A comparação é estritamente maior que R$ 100,00 (`valor_original > 100.00`) e é avaliada sobre o `valor_original` da despesa antes da aplicação do teto diário.
**Justificativa:** "Acima de 100" em português e em regras contábeis define desigualdade estrita (`> 100.00`), e a obrigação fiscal decorre do valor da transação comercial original, não do teto interno de reembolso.
**Regra afetada:** RN-005

### AMB-003 — Sensibilidade a maiúsculas/minúsculas nas categorias e categorias não listadas

**Texto original do RH:** "9. Categorias fora da política não são reembolsáveis."
**O que não está claro:** A entrada contém `d-005` com `categoria: "coworking"` e `d-014` com `categoria: "ALIMENTACAO"` (em letras maiúsculas). Uma diferença apenas de caixa (`"ALIMENTACAO"` vs `"alimentacao"`) deve ser recusada como categoria fora da política ou normalizada?
**Decisão:** O nome da categoria é normalizado (trim + lowercase) antes da validação; portanto `"ALIMENTACAO"` é aceita como `"alimentacao"`, enquanto `"coworking"` é recusada com `CATEGORIA_NAO_REEMBOLSAVEL`.
**Justificativa:** Diferença de capitalização é variação de formatação de sistemas de origem, não uma categoria contábil distinta, ao passo que coworking não consta no rol taxativo dos itens 1 a 3 da política.
**Regra afetada:** RN-001, RN-004

### AMB-004 — Definição de duplicata e efeito sobre o saldo diário

**Texto original do RH:** "8. Duplicatas devem ser tratadas."
**O que não está claro:** (a) O que define uma duplicata quando os itens têm `id` diferentes (`d-006` e `d-007` têm IDs distintos, mas mesma data, categoria, descrição, fornecedor e valor)? (b) "Tratar" significa excluir silenciosamente da saída, recusar ambas por suspeita de fraude ou aprovar a primeira e recusar as demais?
**Decisão:** Duplicata é todo item que repete `(data, categoria_normalizada, descricao_normalizada, fornecedor_normalizado, valor_original)` de um item anterior do mesmo lote; a primeira ocorrência é avaliada normalmente e as subsequentes são mantidas na saída com status `RECUSADA` (`DESPESA_DUPLICADA`) sem consumir saldo diário.
**Justificativa:** Em sistemas de lançamento de despesas, um clique duplo gera novo `id` para o mesmo fato gerador; manter o item na saída como recusado preserva a rastreabilidade de auditoria sem penalizar o lançamento original legítimo.
**Regra afetada:** RN-006

### AMB-005 — Definição de período de competência (`competencia` vs `inicio`/`fim`)

**Texto original do RH:** "7. Despesas devem ser lançadas dentro do período de competência."
**O que não está claro:** O JSON traz três campos em `periodo`: `competencia: "2026-07"`, `inicio: "2026-07-01"` e `fim: "2026-07-31"`. A validação deve comparar o prefixo `AAAA-MM` da data com `competencia` ou testar se a data está no intervalo `[inicio, fim]`?
**Decisão:** Uma despesa está dentro do período de competência se e somente se `periodo.inicio <= despesa.data <= periodo.fim`.
**Justificativa:** Os campos `inicio` e `fim` permitem janelas de fechamento customizadas (ex.: dia 25 a dia 24), tornando a verificação por intervalo fechado mais precisa e determinística do que apenas o prefixo do mês.
**Regra afetada:** RN-003

### AMB-006 — Tratamento de valores negativos / estornos

**Texto original do RH:** (Omisso sobre valores negativos; a entrada traz `d-009` com `valor: -45.00` e `descricao: "Estorno de corrida cancelada"`).
**O que não está claro:** Um valor negativo ou zero deve (a) ser somado algebricamente ao total e devolver saldo diário à categoria, (b) abater de outras despesas aprovadas do colaborador, ou (c) ser recusado como lançamento não reembolsável?
**Decisão:** Despesas com `valor_original <= 0.00` são recusadas com `codigo_motivo: "VALOR_INVALIDO"`, `valor_reembolsado: 0.00` e `valor_glosado: 0.00`, sem alterar o saldo diário nem o `total_solicitado`.
**Justificativa:** Um estorno de corrida cancelada cujo débito original sequer consta no relatório não representa desembolso do colaborador; deduzi-lo reduziria indevidamente o reembolso de outras despesas legítimas.
**Regra afetada:** RN-002

### AMB-007 — Limite de hospedagem "por diária" diante da ausência do campo de quantidade de diárias

**Texto original do RH:** "3. Hospedagem tem limite de R$ 250 por diária."
**O que não está claro:** As despesas `d-010` (`"Hotel Rio - 2 diarias"`, R$ 480,00) e `d-013` (`"Airbnb 3 noites"`, R$ 690,00) mencionam múltiplas diárias/noites apenas no texto livre `descricao`, pois o schema de entrada não possui campo `quantidade_diarias`. O sistema deve tentar fazer parsing de texto livre em `descricao` ou aplicar o teto diário da categoria `hospedagem` por data de lançamento?
**Decisão:** O sistema não extrai números do texto livre `descricao`; cada lançamento de hospedagem é submetido ao limite diário da categoria `hospedagem` na sua respectiva `data` (R$ 250,00).
**Justificativa:** Extrair regras financeiras de texto livre não estruturado ("2 diarias", "duas noites", "14 a 16/07") é frágil e vulnerável a manipulação pelo solicitante; a política financeira deve operar apenas sobre campos estruturados do contrato de entrada.
**Regra afetada:** RN-007, RN-008

### AMB-008 — Critério de ativação do regime "Colaborador em viagem" (+50% nos limites) e categorias elegíveis ao bônus

**Texto original do RH:** "6. Colaborador em viagem tem limites ampliados em 50%."
**O que não está claro:** Não existe campo `em_viagem` em `exemplos/despesas-exemplo.json`, mas existem despesas de hospedagem (`d-010` em `2026-07-14` e `d-011` café da manhã no mesmo hotel em `2026-07-15`) e despesas ordinárias em outros dias do mês. O bônus de 50% aplica-se (a) ao mês inteiro se houver hospedagem, (b) nunca se não houver flag, ou (c) às datas associadas a uma hospedagem válida (`D` e `D + 1`)? Além disso, o bônus de +50% deve incidir sobre a própria `hospedagem` (elevando-a de R$ 250 para R$ 375) ou apenas sobre as categorias cotidianas (`alimentacao` e `transporte_urbano`)?
**Decisão:** O regime de viagem aplica-se por data: é ativado se houver flag explícita `em_viagem: true` (no colaborador ou na despesa) OU nas datas `D` e `D + 1 dia` de qualquer despesa de `hospedagem` válida (aprovada total ou parcialmente). Nas datas em viagem, apenas os limites de `alimentacao` (R$ 60,00 → R$ 90,00) e `transporte_urbano` (R$ 80,00 → R$ 120,00) são ampliados em 50%, enquanto `hospedagem` mantém seu limite próprio de R$ 250,00 por diária.
**Justificativa:** Toda hospedagem já ocorre em contexto de viagem; se o acréscimo de +50% incidisse sobre a própria categoria `hospedagem`, o limite de R$ 250,00 do item 3 da política jamais seria utilizado em nenhum cenário (tornando-se regra morta).
**Regra afetada:** RN-007

### AMB-009 — Casas decimais excedentes em valores monetários

**Texto original do RH:** (Omisso sobre precisão decimal; a entrada traz `d-011` com `valor: 33.333`).
**O que não está claro:** Quando a entrada apresenta mais de duas casas decimais, o sistema deve rejeitar o JSON como inválido, truncar na segunda casa, ou arredondar? E em qual momento (na entrada ou apenas na exibição final)?
**Decisão:** Todos os valores monetários são arredondados na entrada para 2 casas decimais pelo método half-up (`33.333` → `33.33`) antes da execução de qualquer regra.
**Justificativa:** Sistemas de rateio ou conversão frequentemente exportam dízimas com 3 ou mais casas; arredondar na entrada para centavos de Real garante que `valor_reembolsado + valor_glosado == valor_original` sem resíduos de centavos.
**Regra afetada:** RN-001

### AMB-010 — Despesas realizadas em finais de semana (sábado/domingo)

**Texto original do RH:** "7. Despesas devem ser lançadas dentro do período de competência."
**O que não está claro:** O item `d-012` ocorre em `2026-07-18` (um sábado) com a descrição `"Almoco de sabado - plantao"`. Despesas em finais de semana são permitidas ou bloqueadas?
**Decisão:** Despesas em sábados, domingos ou feriados são permitidas sob as mesmas regras e limites diários, desde que sua data esteja dentro de `[periodo.inicio, periodo.fim]`.
**Justificativa:** A política do RH restringe apenas o período de competência, sem vedar trabalho em regime de plantão ou viagem durante finais de semana.
**Regra afetada:** RN-003

---

## 7. Casos de borda

| Caso | Entrada | Comportamento esperado | Regra |
|---|---|---|---|
| Múltiplas despesas no mesmo dia ultrapassando teto na 1ª | `d-001` (R$ 72,50) e `d-002` (R$ 38,00) em `2026-07-03` (`alimentacao`) | `d-001` é `APROVADA_PARCIALMENTE` (reembolsa R$ 60,00, glosa R$ 12,50); `d-002` é `RECUSADA` por `LIMITE_DIARIO_EXCEDIDO` (reembolsa R$ 0,00, glosa R$ 38,00) | RN-008, AMB-001 |
| Valor exatamente R$ 100,00 sem nota fiscal | `d-003` (`transporte_urbano`, R$ 100,00, `tem_nota_fiscal: false`) | Isenta de NF (`100.00 <= 100.00`); sofre corte pelo limite diário de transporte (reembolsa R$ 80,00, glosa R$ 20,00, `APROVADA_PARCIALMENTE`) | RN-005, RN-008, AMB-002 |
| Valor R$ 100,01 sem nota fiscal | `d-004` (`transporte_urbano`, R$ 100,01, `tem_nota_fiscal: false`) | `RECUSADA` por `SEM_NOTA_FISCAL` (reembolsa R$ 0,00, glosa R$ 100,01) e não consome saldo diário | RN-005, AMB-002 |
| Categoria não prevista na política | `d-005` (`coworking`, R$ 89,00, `tem_nota_fiscal: true`) | `RECUSADA` por `CATEGORIA_NAO_REEMBOLSAVEL` (reembolsa R$ 0,00, glosa R$ 89,00) | RN-004, AMB-003 |
| Lançamento duplicado com IDs distintos | `d-006` e `d-007` (`2026-07-09`, `alimentacao`, R$ 54,90) | `d-006` é `APROVADA` (R$ 54,90); `d-007` é `RECUSADA` por `DESPESA_DUPLICADA` (R$ 0,00) e não consome os R$ 5,10 restantes do dia | RN-006, AMB-004 |
| Despesa fora do período de competência | `d-008` (`2026-04-15` em período `2026-07-01`..`2026-07-31`) | `RECUSADA` por `FORA_PERIODO_COMPETENCIA` (reembolsa R$ 0,00, glosa R$ 41,00) | RN-003, AMB-005 |
| Estorno / valor negativo | `d-009` (`transporte_urbano`, R$ -45,00) | `RECUSADA` por `VALOR_INVALIDO` (`valor_reembolsado: 0.00`, `valor_glosado: 0.00`, não entra no `total_solicitado`) | RN-002, AMB-006 |
| Hospedagem válida ativando regime de viagem em `D` e `D+1` | `d-010` (`2026-07-14`, `hospedagem`, R$ 480,00, NF `true`) e `d-011` (`2026-07-15`, `alimentacao`, R$ 33,333) | `2026-07-14` e `2026-07-15` ficam em viagem: `d-010` é `APROVADA_PARCIALMENTE` com teto de hospedagem de R$ 250,00 (glosa R$ 230,00); `d-011` é arredondada para R$ 33,33 e `APROVADA` (teto do dia em viagem R$ 90,00) | RN-001, RN-007, RN-008, AMB-007, AMB-008, AMB-009 |
| Despesa em fim de semana (sábado) | `d-012` (`2026-07-18`, `alimentacao`, R$ 47,20) | `APROVADA` integralmente (R$ 47,20) | RN-003, AMB-010 |
| Hospedagem sem nota fiscal acima de R$ 100 | `d-013` (`2026-07-22`, `hospedagem`, R$ 690,00, NF `false`) | `RECUSADA` por `SEM_NOTA_FISCAL` (R$ 0,00) e **não** ativa regime de viagem para a data `2026-07-22` | RN-005, RN-007 |
| Categoria em letras maiúsculas ultrapassando limite por R$ 1,00 | `d-014` (`2026-07-31`, `"ALIMENTACAO"`, R$ 61,00, NF `true`) | Normalizada para `"alimentacao"`; `APROVADA_PARCIALMENTE` (reembolsa R$ 60,00, glosa R$ 1,00) | RN-001, RN-004, RN-008, AMB-003 |

## 8. Ordem de aplicação das regras

A ordem de precedência é determinística e obrigatória, pois altera o motivo de recusa e evita que despesas inválidas consumam saldo diário ou ativem indevidamente o regime de viagem:

1. **Passo 0 — Normalização (RN-001):** Arredondar `valor` para 2 casas decimais (`valor_original`) e normalizar textos (`categoria_normalizada`, `descricao`, `fornecedor`).
2. **Passo 1 — Validação de Elegibilidade Individual (nesta ordem estrita de curto-circuito):**
   - **1.1. Valor positivo (RN-002):** Se `valor_original <= 0.00` → `RECUSADA` (`VALOR_INVALIDO`). Para aqui.
   - **1.2. Período de competência (RN-003):** Se `data < periodo.inicio` ou `data > periodo.fim` → `RECUSADA` (`FORA_PERIODO_COMPETENCIA`). Para aqui.
   - **1.3. Categoria da política (RN-004):** Se `categoria_normalizada` não estiver em `{alimentacao, transporte_urbano, hospedagem}` → `RECUSADA` (`CATEGORIA_NAO_REEMBOLSAVEL`). Para aqui.
   - **1.4. Duplicidade (RN-006):** Se a tupla `(data, categoria_normalizada, descricao_normalizada, fornecedor_normalizado, valor_original)` já tiver sido vista anteriormente no lote → `RECUSADA` (`DESPESA_DUPLICADA`). Para aqui. (Observação: o registro da tupla para detecção de duplicatas ocorre para todo item que chegou até o passo 1.4, antes da checagem de NF).
   - **1.5. Nota fiscal (RN-005):** Se `valor_original > 100.00` e `tem_nota_fiscal == false` → `RECUSADA` (`SEM_NOTA_FISCAL`). Para aqui.
3. **Passo 2 — Apuração das Datas em Viagem (RN-007):**
   - Identificar todas as despesas de `hospedagem` que sobreviveram ao Passo 1; marcar suas datas `D` e `D + 1 dia` como datas em regime de viagem (além de qualquer data/colaborador com flag explícita `em_viagem: true`).
4. **Passo 3 — Aplicação de Limites Diários e Reembolso Parcial (RN-008):**
   - Para cada despesa que sobreviveu ao Passo 1 (na ordem original da entrada), consultar o saldo diário de `(data, categoria_normalizada)` (inicializado com o limite base, ou com o limite ampliado em +50% para `alimentacao` e `transporte_urbano` se a `data` estiver em viagem) e aprovar total (`APROVADA`), parcialmente (`APROVADA_PARCIALMENTE`) ou recusar por limite esgotado (`RECUSADA` / `LIMITE_DIARIO_EXCEDIDO`).

## 9. Critérios de aceite

O sistema está pronto quando:

- [ ] **CA-001:** Ao processar `exemplos/despesas-exemplo.json`, o sistema gera um JSON válido contendo os 14 itens em `resultados` na mesma ordem da entrada, com `total_solicitado: 1861.84`, `total_reembolsado: 585.43`, `total_glosado: 1276.41`, `quantidade_aprovadas: 3`, `quantidade_aprovadas_parcialmente: 4` e `quantidade_recusadas: 7`.
- [ ] **CA-002:** Despesas de mesma categoria e data acumulam consumo contra um único limite diário (`d-001` reembolsa `60.00` e `d-002` reembolsa `0.00`).
- [ ] **CA-003:** Despesa de exatamente `100.00` sem nota fiscal (`d-003`) é aceita para cálculo de limite (reembolsa `80.00`), enquanto despesa de `100.01` sem nota fiscal (`d-004`) é recusada com `SEM_NOTA_FISCAL`.
- [ ] **CA-004:** Categorias são tratadas de forma case-insensitive (`d-014` `"ALIMENTACAO"` é processada como `"alimentacao"` e reembolsa `60.00`) e categorias fora da lista (`d-005` `"coworking"`) são recusadas com `CATEGORIA_NAO_REEMBOLSAVEL`.
- [ ] **CA-005:** Despesas duplicadas (`d-007` idêntica a `d-006` exceto pelo `id`) são recusadas com `DESPESA_DUPLICADA` e não consomem saldo diário.
- [ ] **CA-006:** Despesas fora do intervalo `[periodo.inicio, periodo.fim]` (`d-008`) são recusadas com `FORA_PERIODO_COMPETENCIA`, enquanto despesas em sábado dentro do intervalo (`d-012`) são aprovadas.
- [ ] **CA-007:** Despesas com valor negativo ou zero (`d-009`, `-45.00`) são recusadas com `VALOR_INVALIDO`, não entram no `total_solicitado` e não alteram saldos diários.
- [ ] **CA-008:** Hospedagem válida (`d-010` em `2026-07-14`) é limitada a `250.00` e ativa regime de viagem (+50% nas categorias cotidianas) para `2026-07-14` e `2026-07-15`, avaliando `d-011` (`33.33`) sob o teto ampliado de `90.00`; hospedagem recusada por falta de NF (`d-013`) não ativa regime de viagem.

## 10. O que fica em aberto

- **Múltiplas diárias em um único lançamento de hospedagem:** Como o formato de entrada atual não possui campo estruturado para quantidade de diárias (`quantidade_diarias`) nem datas de `check_in`/`check_out`, decidiu-se provisoriamente (em `AMB-007` e `RN-007`) não fazer parsing do texto livre `descricao`, aplicando o teto de 1 diária na data do lançamento (`D`) e estendendo o status de viagem para `D` e `D + 1`. Caso o schema de entrada passe a fornecer um campo estruturado de diárias no futuro, a regra poderá multiplicar o teto de hospedagem pelo número de diárias estruturado.
- **Sinalização explícita de viagem sem pernoite (bate-volta):** Se o colaborador fizer uma viagem aérea/rodoviária de um único dia sem despesa de hospedagem e sem o campo opcional `em_viagem: true`, o sistema aplicará o limite padrão. Ficou decidido que a adição de um campo booleano `em_viagem` na entrada já é suportada pela `RN-007` caso o sistema emissor passe a enviá-lo.
