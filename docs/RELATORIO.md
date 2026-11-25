# Relatório — Desafio SDD

**Aluno:** `dnuneste` · **Repositório:** `https://github.com/dnuneste/sdd-desafio` · **Data:** `2026-11-25`

> Isto não é redação. São **evidências**. Toda afirmação deve vir acompanhada de
> arquivo, hash de commit ou trecho de sessão exportada. Um parágrafo bonito sem
> evidência vale menos que uma frase curta com um hash.
>
> Vale 20 dos 100 pontos, e é a seção que mais separa notas.

---

## Delegação

*O que você fez, o que o Claude fez, e por que dividiu assim.*

**A divisão:**

| Atividade | Quem | Por quê |
|---|---|---|
| Identificar ambiguidades | Coautoria (Agente cruzou `DESAFIO.md` × `exemplos/despesas-exemplo.json`; Humano revisou a cobertura dos 14 casos) | O modelo é excelente em varrer exaustivamente os 14 itens do JSON contra as 9 regras textuais do RH (`docs/sessions/01-especificacao-e-planejamento.md`, Interação 1), encontrando 10 ambiguidades (`AMB-001` a `AMB-010`). |
| Decidir as ambiguidades | Humano revisou e validou propostas iniciais do Agente (`D-001` e `D-002`) | Decisão de negócio não tem gabarito técnico: exigir revisão humana impediu que a regra morta de hospedagem em viagem (`D-002`, commit `053b90a`) passasse para o código. |
| Escrever a spec | Agente redigiu sob restrição estrita do template; Humano auditou e aprovou v1.0 (`0ba5346`), v1.1 (`053b90a`) e v1.2 (`06dadda`) | Redigir tabelas de contrato e critérios de aceite é trabalhoso manualmente, mas a revisão humana de que não havia vazamento técnico foi indispensável. |
| Desenhar a arquitetura | Humano definiu stack (`Python 3.12 + pytest`); Agente estruturou o `plan.md` (`6e4fb09`) com núcleo funcional puro e 2 passagens (`DT-001`) | Domínio prévio de Python/pytest pelo humano para reduzir atrito; o isolamento em `src/policy.py` e `src/engine.py` foi desenhado para absorver a mudança do Dia 2. |
| Implementar | Agente, estritamente fatiado pelas tasks `T-001` a `T-007` (`48afcd5`, `98de944`, `eb730db`, `d0a9dba`, `1bf9600`, `9f52c16`) | Com a `spec.md` desambiguada e o `plan.md` fechado, a tradução para Python com `Decimal` tornou-se determinística. |
| Escrever testes | Agente escreveu a suíte `pytest` vinculada aos IDs (`test_rn_XXX_amb_YYY`); Humano auditou os valores esperados por item em `tests/test_edge_cases.py` (`5fe5c5b`) | A vinculação `RN-XXX` → `T-XXX` → `test_rn_XXX` permitiu que os próprios testes denunciassem o erro aritmético que o modelo havia cometido em `CA-001` (`D-003`, commit `06dadda`). |
| Absorver o envelope | *(A preencher no Dia 2 após recebimento do envelope)* | *(A preencher no Dia 2)* |

**Onde deleguei e me arrependi:**
Deleguei ao agente a soma manual dos totais esperados do critério de aceite `CA-001` ao escrever a `spec.md` v1.0 (`0ba5346`) e v1.1 (`053b90a`) sem recalcular na calculadora antes de aprovar a spec. O modelo somou mentalmente as 13 despesas positivas do `exemplos/despesas-exemplo.json` como `1962.84` (R$ 101,00 a mais que o real `1861.84`) e contou `4 aprovadas / 6 recusadas` em vez de `3 aprovadas / 7 recusadas`. O erro só foi pego quando o teste `test_ca_001_lote_referencia_despesas_exemplo` rodou na `T-006` (`5fe5c5b`), exigindo a correção `D-003` (`06dadda`).

**Onde não deleguei e deveria ter delegado:**
No início da configuração, tentei controlar manualmente o momento de cada commit e da exportação das sessões pelo chat, em vez de já colocar a regra de exportação contínua em `docs/sessions/` dentro do `CLAUDE.md` desde o primeiro minuto. Corrigi isso na Interação 3 da Sessão 01 (`docs/sessions/01-especificacao-e-planejamento.md`, commit `0ba5346`), incorporando a regra diretamente no `CLAUDE.md`.

**Usei subagentes / skills / MCP / hooks?**
Não utilizei subagentes nem servidores MCP externos porque o escopo do motor é autocontido (biblioteca padrão do Python + `pytest`). Em vez disso, concentrei a automança de governança no arquivo `CLAUDE.md` (commit `0ba5346`), estabelecendo travas explícitas: proibição de regra de negócio fora da `spec.md`, obrigatoriedade de referenciar tasks nos commits (`feat(T-XXX)`) e atualização incremental de `docs/sessions/`.

---

## Descrição

*Como você transformou requisito ambíguo em requisito verificável.*

Requisito escolhido: **Item 3 ("Hospedagem tem limite de R$ 250 por diária") combinado com o Item 6 ("Colaborador em viagem tem limites ampliados em 50%")** — registrado em `RN-007` e `AMB-008` de `specs/001-motor-reembolso/spec.md`.

**Versão 1 (primeira escrita — commit `0ba5346`):**
> ```markdown
> ### RN-007 — Caracterização de colaborador em viagem e ampliação de limites em 50%
>
> **Regra:** Considera-se que uma despesa ocorreu em regime de **colaborador em viagem** quando:
> 1. O objeto `colaborador` ou a própria despesa contiver o campo booleano opcional `em_viagem: true`; **OU**
> 2. A data da despesa (`data`) coincidir com uma data coberta por uma despesa de `hospedagem` válida (isto é, dentro do período de competência, com valor positivo, não duplicada e com nota fiscal quando exigida). Como o schema de entrada não possui campo estruturado de número de diárias nem data de check-out, cada lançamento válido de `hospedagem` na data `D` caracteriza regime de viagem na data `D` e no dia imediatamente seguinte `D + 1 dia` (data de check-out da estadia).
>
> Nas datas caracterizadas como em viagem, os limites diários de todas as categorias são ampliados em 50%:
> - `alimentacao`: de R$ 60,00 para **R$ 90,00 por dia**
> - `transporte_urbano`: de R$ 80,00 para **R$ 120,00 por dia**
> - `hospedagem`: de R$ 250,00 para **R$ 375,00 por dia**
> ```

**Versão final (após revisão de negócio `D-002` — commit `053b90a`):**
> ```markdown
> ### RN-007 — Caracterização de colaborador em viagem e ampliação de limites em 50%
>
> **Regra:** Considera-se que uma despesa ocorreu em regime de **colaborador em viagem** quando:
> 1. O objeto `colaborador` ou a própria despesa contiver o campo booleano opcional `em_viagem: true`; **OU**
> 2. A data da despesa (`data`) coincidir com uma data coberta por uma despesa de `hospedagem` válida (isto é, dentro do período de competência, com valor positivo, não duplicada e com nota fiscal quando exigida). Como o schema de entrada não possui campo estruturado de número de diárias nem data de check-out, cada lançamento válido de `hospedagem` na data `D` caracteriza regime de viagem na data `D` e no dia imediatamente seguinte `D + 1 dia` (data de check-out da estadia).
>
> Nas datas caracterizadas como em viagem, os limites diários das despesas cotidianas (`alimentacao` e `transporte_urbano`) são ampliados em 50%, enquanto `hospedagem` mantém seu teto próprio de viagem de R$ 250,00 por diária:
> - `alimentacao`: de R$ 60,00 para **R$ 90,00 por dia**
> - `transporte_urbano`: de R$ 80,00 para **R$ 120,00 por dia**
> - `hospedagem`: **R$ 250,00 por diária** (não sofre acréscimo de +50% sobre si mesma, pois toda hospedagem já pressupõe viagem)
> ```

**O que estava ambíguo:**
1. O JSON de entrada (`exemplos/despesas-exemplo.json`) não possui nenhum campo `em_viagem`, embora existam despesas de hotel (`d-010` em `2026-07-14`), café da manhã no mesmo hotel no dia seguinte (`d-011` em `2026-07-15`) e Airbnb sem nota fiscal (`d-013` em `2026-07-22`).
2. A política diz que "Colaborador em viagem tem limites ampliados em 50%", mas não esclarece se esse multiplicador de +50% incide apenas sobre as despesas cotidianas que encarecem em viagem (`alimentacao` e `transporte_urbano`) ou se também incide sobre a própria `hospedagem`.

**Como percebi:**
Durante a revisão de negócio da `spec.md` v1.0 (`docs/sessions/01-especificacao-e-planejamento.md`, Interação 4), ao cruzar o gatilho de viagem (presença de `hospedagem` válida na data `D`) com o efeito (+50% nos limites), percebi uma contradição lógica: se toda `hospedagem` válida ativa o regime de viagem na data `D`, e se o bônus de +50% também fosse aplicado à categoria `hospedagem`, o limite de **R$ 250,00 por diária** do item 3 da política **nunca seria aplicado em nenhuma execução possível** (toda hospedagem válida teria teto de R$ 375,00, tornando os R$ 250,00 uma regra morta).

**Commit da mudança:** `053b90a` (registrado como `D-002` em `specs/001-motor-reembolso/DECISIONS.md`).

---

## Discernimento

*Onde o Claude errou e você pegou.*

### Caso 1 — Regra morta ao aplicar +50% de viagem sobre a própria categoria `hospedagem` (`D-002`)

**O que ele propôs:**
Na versão 1.0 da `spec.md` (commit `0ba5346`), o agente propôs em `RN-007` e `AMB-008` que uma despesa de `hospedagem` válida na data `D` ativasse o regime de viagem na data `D` (e `D + 1`) e ampliasse em 50% todas as três categorias da política, elevando `hospedagem` de R$ 250,00 para R$ 375,00 (o que faria o item `d-010` de R$ 480,00 reembolsar R$ 375,00).

**Por que estava errado:**
Do ponto de vista de domínio, ninguém se hospeda em hotel sem estar em viagem. Se a própria existência de uma despesa de `hospedagem` válida na data `D` é o critério que ativa `em_viagem = true` na data `D`, aplicar o multiplicador de `1.5x` sobre `hospedagem` faz com que o limite base de R$ 250,00 definido pelo RH no item 3 jamais exista no mundo real.

**Como eu detectei:**
Ao fazer a revisão de negócio da `spec.md` antes de autorizar o início da implementação (`docs/sessions/01-especificacao-e-planejamento.md`, Interação 4), avaliando o impacto da regra proposta sobre o item `d-010` (`"Hotel Rio - 2 diarias"`, R$ 480,00).

**O que eu fiz:**
Determinei a revisão da `spec.md` para a versão 1.1 (commit `053b90a`) e o registro da decisão `D-002` em `specs/001-motor-reembolso/DECISIONS.md`, restringindo o multiplicador de +50% às categorias cotidianas (`alimentacao` → R$ 90,00; `transporte_urbano` → R$ 120,00) e mantendo `hospedagem` em R$ 250,00. Na implementação da `T-001` (`src/policy.py`, commit `48afcd5`), isso gerou o atributo explícito `categorias_ampliadas_em_viagem = frozenset({"alimentacao", "transporte_urbano"})`.

**Onde está a evidência:** `docs/sessions/01-especificacao-e-planejamento.md`, trecho `Interação 4 — Revisão de Negócio da Spec v1.1 e Registro de Decisão D-002`, `specs/001-motor-reembolso/DECISIONS.md` (`D-002`) e commit `053b90a`.

### Caso 2 — Alucinação aritmética do modelo na soma de `CA-001` (`D-003`)

**O que ele propôs:**
Ao redigir o critério de aceite `CA-001` na `spec.md` (commits `0ba5346` e `053b90a`), o agente escreveu que, para `exemplos/despesas-exemplo.json`, o resultado esperado seria `total_solicitado: 1962.84`, `total_glosado: 1377.41`, `quantidade_aprovadas: 4` e `quantidade_recusadas: 6`.

**Por que estava errado:**
A soma real das 13 despesas positivas de `exemplos/despesas-exemplo.json` (com `d-011` arredondada para `33.33` e excluindo o estorno negativo `d-009` de `-45.00` conforme `RN-002`) é exatamente:
`72.50 + 38.00 + 100.00 + 100.01 + 89.00 + 54.90 + 54.90 + 41.00 + 480.00 + 33.33 + 47.20 + 690.00 + 61.00 = 1861.84` (o modelo havia errado a soma mental em exatos R$ 101,00). Além disso, os itens com status `APROVADA` são 3 (`d-006`, `d-011`, `d-012`), os `APROVADA_PARCIALMENTE` são 4 (`d-001`, `d-003`, `d-010`, `d-014`) e os `RECUSADA` são 7 (`d-002`, `d-004`, `d-005`, `d-007`, `d-008`, `d-009`, `d-013`).

**Como eu detectei:**
Ao rodar `python -m pytest -v` na task `T-006` (commit `5fe5c5b`), o teste `test_ca_001_lote_referencia_despesas_exemplo` falhou com `AssertionError: assert 3 == 4` e mostrou `total_solicitado=Decimal('1861.84')`. Como todas as 14 asserções individuais item a item (`d-001` a `d-014`) passaram, ficou provado que o motor estava certo e a soma manual escrita pelo modelo em `CA-001` na `spec.md` estava errada.

**O que eu fiz:**
Segui a regra do `CLAUDE.md` ("quando a spec estiver errada, corrigimos a spec primeiro e registramos em `DECISIONS.md`"): atualizei `CA-001` na `spec.md` para a versão 1.2, registrei a entrada `D-003` em `specs/001-motor-reembolso/DECISIONS.md` e ajustei o teste em `tests/test_edge_cases.py` (commit `06dadda`).

**Onde está a evidência:** `docs/sessions/02-implementacao-e-testes.md`, trecho `Interação 3 — Task T-006: Detecção de Erro Aritmético em CA-001 e Registro D-003`, `specs/001-motor-reembolso/DECISIONS.md` (`D-003`) e commits `5fe5c5b` e `06dadda`.

**Padrão que eu notei:**
LLMs são excelentes em estruturar regras lógicas simbólicas item a item (ele acertou o resultado individual de todos os 14 lançamentos `d-001`..`d-014` na primeira tentativa), mas falham com frequência em **aritmética mental agregada** (somar uma coluna de 13 números decimais no texto da spec) e em **consequências reflexivas de regras** (não perceber que um gatilho baseado em hospedagem anulava o limite base da própria hospedagem).

---

## Diligência

*O que você verificou antes de aceitar.*

**Meu procedimento de verificação:**
1. Na fase de documentação: verifiquei se a `spec.md` não continha nenhum termo técnico proibido (Python, classes, bibliotecas) e se cada um dos 14 itens de `exemplos/despesas-exemplo.json` tinha uma regra (`RN-001`..`RN-008`) e uma ambiguidade (`AMB-001`..`AMB-010`) correspondente.
2. Na fase de código (`T-001` a `T-007`): exigi a execução de `python -m pytest -v` ao final de cada task antes de permitir o commit e verifiquei o `git status` / `git log` para garantir que cada task gerasse seu próprio commit atômico e atualizasse `[x]` no `tasks.md`.

**Li o diff inteiro em que porcentagem das entregas?**
Li o diff/conteúdo completo em cerca de **85% das entregas** (especialmente `spec.md`, `DECISIONS.md`, `src/policy.py`, `src/engine.py` e a tabela item-a-item de `tests/test_edge_cases.py`). Nos **15% restantes** (como os totais somados do resumo em `CA-001` da `spec.md` v1.0 e o boilerplate de `argparse` em `src/cli.py`), apenas passei o olho — e foi justamente onde o erro de soma de R$ 101,00 em `CA-001` passou despercebido até a execução da `T-006`.

**O que aceitei sem verificar direito, e o que me custou:**
Aceitei os números agregados de `CA-001` (`total_solicitado: 1962.84` e `quantidade_aprovadas: 4`) na `spec.md` v1.0 (`0ba5346`) confiando que o modelo havia somado corretamente os 14 itens do JSON. Isso me custou uma falha de teste na `T-006` (`5fe5c5b`) e a necessidade de abrir a decisão `D-003` e o commit corretivo `06dadda` para alinhar a spec à aritmética real.

**Testes: quem escreveu, e como você sabe que eles testam a coisa certa?**
O agente escreveu o código dos testes em `tests/test_engine.py`, `tests/test_edge_cases.py` e `tests/test_cli.py`, mas eu garanti que eles testam a coisa certa por dois mecanismos:
1. Em `tests/test_edge_cases.py::test_ca_001_lote_referencia_despesas_exemplo`, o dicionário `esperado` declara explicitamente a tupla `(StatusDespesa, CodigoMotivo, valor_reembolsado, valor_glosado)` para **cada um dos 14 IDs** (`d-001` a `d-014`) calculados a partir da spec, sem reutilizar funções do motor para gerar o gabarito.
2. A prova empírica de que os testes não eram tautológicos foi que `test_ca_001_lote_referencia_despesas_exemplo` **quebrou na primeira execução** (`5fe5c5b`), expondo a divergência entre a soma real do motor (`1861.84`) e o número escrito na spec (`1962.84`).

---

## O envelope

*A mudança de requisito do Dia 2.*

> *(Seção reservada para preenchimento no Dia 2, às 10h, após o recebimento e absorção da mudança de requisito via `spec.md` → `DECISIONS.md` → `tasks.md` Fase 5 → implementação e testes).*

**Quantos arquivos toquei na mão:** `<pendente Dia 2>`
**Quanto tempo levou:** `<pendente Dia 2>`
**Diff de absorção:** `<pendente Dia 2>`

**Absorveu de graça:** `<pendente Dia 2>`

**Resistiu:** `<pendente Dia 2>`

**Ordem em que fiz:** `<pendente Dia 2>`

**Se eu tivesse escrito a spec original sabendo desta mudança:** `<pendente Dia 2>`

**O que a spec me poupou, em concreto:** `<pendente Dia 2>`

---

## Fechamento

**Para qual tamanho de projeto isto valeu a pena?**
Vale a pena para qualquer projeto com **regras de negócio densas, políticas com precedência entre si ou vida útil superior a uma única sessão de chat** (mesmo que o código final tenha menos de 500 linhas, como este motor). Quando existem 10 ambiguidades interagindo (duplicata vs. nota fiscal vs. limite diário vs. viagem), o custo cognitivo não está na sintaxe do Python, mas na consistência das regras.

**Para qual não valeria?**
Não valeria para scripts descartáveis de uso único (one-off de migração ou formatação de arquivos), protótipos puramente visuais de interface ou correções triviais de bug de uma linha onde o requisito já é óbvio e sem casos de fronteira.

**O que eu faria diferente:**
1. Teria validado com um script rápido ou planilha a soma matemática dos dados de exemplo (`exemplos/despesas-exemplo.json`) **antes** de congelar os números de `CA-001` na `spec.md` v1.0, evitando o retrabalho documentado em `D-003` (`06dadda`).
2. Teria incluído a regra de exportação incremental para `docs/sessions/` no `CLAUDE.md` já no primeiro minuto da Sessão 01.

**A coisa mais desconfortável que aprendi sobre como eu trabalho com IA:**
Percebi o quão fácil é ser seduzido por uma documentação bem formatada gerada pela IA: quando o modelo entregou a `spec.md` v1.0 com tabelas impecáveis e justificativas eloquentes, meu instinto imediato foi assumir que a lógica interna (`RN-007` aplicando +50% em hospedagem) e a soma aritmética (`1962.84`) estavam corretas só porque o texto parecia profissional. A fluência textual do modelo mascara erros lógicos e aritméticos se o humano não auditar as fronteiras com ceticismo.
