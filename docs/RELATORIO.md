# Relatório — Desafio SDD

**Aluno:** `dnuneste` · **Repositório:** `https://github.com/dnuneste/sdd-desafio` · **Data:** `2026-11-26`

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
| Identificar ambiguidades | Coautoria (Agente cruzou `DESAFIO.md` × `exemplos/despesas-exemplo.json` no Dia 1 e `00-ENVELOPE-LACRADO.md` × JSONs do envelope no Dia 2; Humano auditou cobertura) | O modelo é excelente em varrer exaustivamente todos os itens dos JSONs contra as regras textuais do RH (`docs/sessions/01-especificacao-e-planejamento.md` e `docs/sessions/03-envelope-politica-v4.md`), encontrando 10 ambiguidades na v3 (`AMB-001` a `AMB-010`) e 6 novas na v4 (`AMB-011` a `AMB-016`). |
| Decidir as ambiguidades | Humano revisou e validou propostas do Agente (`D-001`, `D-002`, `D-004`) | Decisão de negócio não tem gabarito técnico: exigir revisão humana impediu que a regra morta de hospedagem em viagem (`D-002`, commit `053b90a`) passasse para o código e definiu o escopo cirúrgico da v4 (`D-004`, commit `3e68e54`). |
| Escrever a spec | Agente redigiu sob restrição estrita do template; Humano auditou e aprovou v1.0 (`0ba5346`), v1.1 (`053b90a`), v1.2 (`06dadda`) e v2.0 (`3e68e54`, `467c3b3`) | Redigir tabelas de contrato e critérios de aceite é trabalhoso manualmente, mas a revisão humana de que não havia vazamento técnico foi indispensável. |
| Desenhar a arquitetura | Humano definiu stack (`Python 3.12 + pytest`); Agente estruturou o `plan.md` (`6e4fb09`, `c49f175`) com núcleo funcional puro e 2 passagens (`DT-001`, `DT-004`) | Domínio prévio de Python/pytest pelo humano para reduzir atrito; o isolamento em `src/policy.py` e `src/engine.py` foi desenhado justamente para absorver a mudança do Dia 2 sem quebrar a estrutura. |
| Implementar | Agente, estritamente fatiado pelas tasks `T-001` a `T-010` (`48afcd5`, `98de944`, `eb730db`, `d0a9dba`, `1bf9600`, `9f52c16`, `5a6a4b3`, `c707d5c`, `aca19ac`) | Com a `spec.md` desambiguada e o `plan.md` fechado, a tradução para Python com `Decimal` tornou-se 100% determinística e gerada via tasks. |
| Escrever testes | Agente escreveu a suíte `pytest` vinculada aos IDs (`test_rn_XXX_amb_YYY`); Humano auditou os valores esperados item a item em `tests/test_edge_cases.py` (`5fe5c5b`, `aca19ac`) | A vinculação `RN-XXX` → `T-XXX` → `test_rn_XXX` permitiu que os próprios testes denunciassem os erros aritméticos que o modelo havia cometido nos totais agregados em `CA-001` e `CA-009` (`D-003` no commit `06dadda` e `D-005` no commit `467c3b3`). |
| Absorver o envelope | Humano definiu o corte de escopo (Itens A e B obrigatórios; Item C opcional fora de escopo); Agente atualizou `spec.md` (`3e68e54`) → `DECISIONS.md` (`D-004`) → `plan.md` / `tasks.md` (`c49f175`) e reexecutou as tasks `T-008` a `T-010` | Permitiu que **100% das alterações de código** da Política v4 (`5a6a4b3`, `c707d5c`, `aca19ac`) viessem da execução das tasks `T-008`..`T-010` a partir da spec v2.0 atualizada, com **0 linhas de código editadas manualmente**. |

**Onde deleguei e me arrependi:**
Deleguei ao agente a soma manual dos totais agregados dos critérios de aceite (`CA-001` no Dia 1 e `CA-001`/`CA-009` no Dia 2) ao escrever a `spec.md` (`0ba5346`, `3e68e54`) sem conferir na calculadora antes de aprovar a spec. No Dia 1 (`D-003`, commit `06dadda`), o modelo somou as 13 despesas positivas de `despesas-exemplo.json` como `1962.84` em vez de `1861.84`. No Dia 2 (`D-005`, commit `467c3b3`), o erro reincidiu: o modelo incluiu indevidamente os R$ 60,00 brutos da despesa `e-006` (`55 GBP`, recusada por moeda não suportada) no `total_solicitado` de `CA-009` (`2517.52` vs `2457.52`) e errou a soma de `total_reembolsado` da `CA-001` sob a v4 (`373.93` vs `351.43`). Em ambos os dias, foi a execução da suíte `pytest` (`T-006` e `T-010`) que pegou o erro aritmético da spec.

**Onde não deleguei e deveria ter delegado:**
No início da configuração, tentei controlar manualmente o momento de cada commit e da exportação das sessões pelo chat, em vez de já colocar a regra de exportação contínua em `docs/sessions/` dentro do `CLAUDE.md` desde o primeiro minuto. Corrigi isso na Interação 3 da Sessão 01 (`docs/sessions/01-especificacao-e-planejamento.md`, commit `0ba5346`), incorporando a regra diretamente no `CLAUDE.md`.

**Usei subagentes / skills / MCP / hooks?**
Não utilizei subagentes nem servidores MCP externos porque o escopo do motor é autocontido (biblioteca padrão do Python + `pytest`). Em vez disso, concentrei a automação de governança no arquivo `CLAUDE.md` (commit `0ba5346`), estabelecendo travas explícitas: proibição de regra de negócio fora da `spec.md`, obrigatoriedade de referenciar tasks nos commits (`feat(T-XXX)`) e atualização incremental de `docs/sessions/`.

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

**Versão final (após revisão de negócio `D-002` no commit `053b90a` e extensão da Política v4 `D-004` no commit `3e68e54`):**
> ```markdown
> ### RN-007 — Caracterização de colaborador em viagem e ampliação de limites em 50%
>
> **Regra:** Considera-se que uma data `D` opera em regime de **colaborador em viagem** quando:
> 1. O objeto `colaborador` ou uma despesa da data `D` contiver o campo booleano opcional `em_viagem: true`; **OU**
> 2. A data `D` coincidir com a data de estadia (`D_hosp`) ou o dia imediatamente seguinte de check-out (`D_hosp + 1 dia`) de uma despesa de `hospedagem` válida (que sobreviveu a todas as validações de elegibilidade individual, incluindo `RN-004` e `RN-005`); **OU**
> 3. A data `D` possuir uma despesa válida lançada em **moeda estrangeira** (`moeda_original != "BRL"`), caracterizando deslocamento em viagem internacional naquela data (`AMB-015`).
>
> Nas datas caracterizadas como em viagem, os limites diários das despesas cotidianas (`alimentacao` e `transporte_urbano`) do centro de custo do colaborador são ampliados no percentual definido pela política (`acrescimo_em_viagem_percentual`: **+50%**), enquanto `hospedagem` e `representacao` mantêm seus respectivos limites diários da tabela do centro de custo.
> ```

**O que estava ambíguo:**
1. O JSON de entrada (`exemplos/despesas-exemplo.json`) não possui nenhum campo `em_viagem`, embora existam despesas de hotel (`d-010` em `2026-07-14`), café da manhã no mesmo hotel no dia seguinte (`d-011` em `2026-07-15`) e Airbnb sem nota fiscal (`d-013` em `2026-07-22`). No Dia 2 (`despesas-envelope.json`), surgiram também despesas em moeda estrangeira (`EUR` e `USD`) em dias sem lançamento de hospedagem (`e-002`, `e-003`, `e-004`).
2. A política diz que "Colaborador em viagem tem limites ampliados em 50%", mas não esclarece se esse multiplicador de +50% incide apenas sobre as despesas cotidianas que encarecem em viagem (`alimentacao` e `transporte_urbano`) ou se também incide sobre a própria `hospedagem` (e, na v4, sobre `representacao`).

**Como percebi:**
Durante a revisão de negócio da `spec.md` v1.0 (`docs/sessions/01-especificacao-e-planejamento.md`, Interação 4), ao cruzar o gatilho de viagem (presença de `hospedagem` válida na data `D`) com o efeito (+50% nos limites), percebi uma contradição lógica: se toda `hospedagem` válida ativa o regime de viagem na data `D`, e se o bônus de +50% também fosse aplicado à categoria `hospedagem`, o limite de **R$ 250,00 por diária** do item 3 da política **nunca seria aplicado em nenhuma execução possível** (toda hospedagem válida teria teto de R$ 375,00, tornando os R$ 250,00 uma regra morta). No Dia 2, essa mesma decisão (`categorias_ampliadas_em_viagem = {"alimentacao", "transporte_urbano"}`) encaixou-se perfeitamente com a nova categoria `representacao` (R$ 300,00) e com o limite de `hospedagem` de `CC-COMERCIAL` (R$ 400,00 em `e-007`).

**Commits da mudança:** `053b90a` (`D-002` em `specs/001-motor-reembolso/DECISIONS.md`) e `3e68e54` (`D-004` em `specs/001-motor-reembolso/DECISIONS.md`).

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

### Caso 2 — Alucinação aritmética do modelo na soma de critérios de aceite agregados (`D-003` e `D-005`)

**O que ele propôs:**
- No Dia 1 (`D-003`, commits `0ba5346` e `053b90a`): Ao redigir `CA-001` na `spec.md`, o agente escreveu `total_solicitado: 1962.84`, `quantidade_aprovadas: 4` e `quantidade_recusadas: 6`.
- No Dia 2 (`D-005`, commit `3e68e54`): Ao atualizar `CA-001` para a Política v4 e criar `CA-009` para `despesas-envelope.json`, o agente escreveu `total_reembolsado: 373.93` em `CA-001` (quando a soma correta dos 7 itens reembolsados é `72.50 + 2.50 + 80.00 + 54.90 + 33.33 + 47.20 + 61.00 = 351.43`) e `total_solicitado: 2517.52` em `CA-009` (quando a soma correta em BRL é `2457.52`).

**Por que estava errado:**
Em ambos os episódios, o modelo acertou 100% das decisões e valores individuais item a item nas tabelas da spec, mas errou a soma mental da coluna ao escrever o parágrafo do critério de aceite agregado (`CA-001` e `CA-009`).

**Como eu detectei:**
Ao rodar `python -m pytest` nas tasks de validação de lote (`T-006` no commit `5fe5c5b` e `T-010` antes do commit `467c3b3`), as asserções item a item passaram todas, mas a asserção do resumo falhou expondo a diferença exata (`Decimal('1861.84') != Decimal('1962.84')` no Dia 1; `Decimal('351.43') != Decimal('373.93')` e `Decimal('2457.52') != Decimal('2517.52')` no Dia 2).

**O que eu fiz:**
Segui estritamente a regra do `CLAUDE.md` ("quando a spec estiver errada, corrigimos a spec primeiro e registramos em `DECISIONS.md`"):
- No Dia 1: corrigi a `spec.md` v1.2 e registrei `D-003` (commit `06dadda`).
- No Dia 2: corrigi a `spec.md` v2.0 e registrei `D-005` (commit `467c3b3`) antes de finalizar o commit da task `T-010` (`aca19ac`).

**Onde está a evidência:** `docs/sessions/02-implementacao-e-testes.md` (Interação 3), `docs/sessions/03-envelope-politica-v4.md` (Interação 3), `specs/001-motor-reembolso/DECISIONS.md` (`D-003` e `D-005`) e commits `5fe5c5b`, `06dadda`, `467c3b3` e `aca19ac`.

**Padrão que eu notei:**
LLMs são excelentes em estruturar regras lógicas simbólicas item a item (ele acertou o resultado individual de todos os 28 lançamentos somados dos 3 arquivos JSON na primeira tentativa), mas falham de forma recorrente em **aritmética mental agregada** (somar uma coluna de números decimais no texto da spec) e em **consequências reflexivas de regras** (não perceber que um gatilho baseado em hospedagem anulava o limite base da própria hospedagem).

---

## Diligência

*O que você verificou antes de aceitar.*

**Meu procedimento de verificação:**
1. Na fase de documentação: verifiquei se a `spec.md` não continha nenhum termo técnico proibido (Python, classes, bibliotecas) e se cada item de `despesas-exemplo.json`, `despesas-envelope.json` e `despesas-envelope-cc-desconhecido.json` tinha uma regra (`RN-001`..`RN-009`) e uma ambiguidade (`AMB-001`..`AMB-016`) correspondente.
2. Na fase de código (`T-001` a `T-010`): exigi a execução de `python -m pytest -v` ao final de cada task antes de permitir o commit e verifiquei o `git status` / `git log` para garantir que cada task gerasse seu próprio commit atômico e atualizasse `[x]` no `tasks.md`.

**Li o diff inteiro em que porcentagem das entregas?**
Li o diff/conteúdo completo em cerca de **85% das entregas** (especialmente `spec.md`, `DECISIONS.md`, `src/policy.py`, `src/engine.py` e as tabelas item-a-item de `tests/test_edge_cases.py`). Nos **15% restantes** (os totais somados dos resumos em `CA-001` e `CA-009` da `spec.md`), passei o olho sem somar parcela por parcela na calculadora — e foi exatamente aí que os erros aritméticos de `D-003` e `D-005` entraram na spec e tiveram que ser capturados pelo `pytest`.

**O que aceitei sem verificar direito, e o que me custou:**
Aceitei os números agregados de `CA-001` (`0ba5346`) e depois de `CA-009` (`3e68e54`) na `spec.md` confiando na soma mental do modelo. Isso me custou duas quebras de teste (`T-006` e `T-010`) e dois ciclos extras de correção formal da spec (`D-003` no commit `06dadda` e `D-005` no commit `467c3b3`).

**Testes: quem escreveu, e como você sabe que eles testam a coisa certa?**
O agente escreveu o código dos testes em `tests/test_engine.py`, `tests/test_edge_cases.py` e `tests/test_cli.py`, mas eu garanti que eles testam a coisa certa por dois mecanismos:
1. Em `tests/test_edge_cases.py`, os testes `test_ca_001_lote_referencia_despesas_exemplo`, `test_ca_009_lote_envelope_cc_comercial_e_cambio` e `test_ca_010_lote_envelope_cc_desconhecido_fallback_padrao` declaram explicitamente o dicionário `esperado` com a tupla `(StatusDespesa, CodigoMotivo, valor_reembolsado, valor_glosado)` para **cada um dos 28 IDs** (`d-001`..`d-014`, `e-001`..`e-010`, `f-001`..`f-004`), sem reutilizar funções do motor para calcular o gabarito.
2. A prova empírica de que os testes não eram tautológicos foi que eles **quebraram nas duas vezes em que o texto da spec tinha erro de soma** (`D-003` e `D-005`), provando que o motor calculava a aritmética exata com `Decimal` e denunciava a soma errada da spec.

---

## O envelope

*A mudança de requisito do Dia 2.*

**Quantos arquivos toquei na mão:** **`0` arquivos editados manualmente**; **100% da absorção (12 arquivos modificados + 5 arquivos do envelope adicionados)** foi gerada pelo agente através do fluxo SDD: atualização da `spec.md` v2.0 + `DECISIONS.md` (`D-004`, commit `3e68e54`) → atualização do `plan.md` v2.0 + criação das tasks `T-008` a `T-010` em `tasks.md` (commit `c49f175`) → execução sequencial das tasks `T-008` (`5a6a4b3`), `T-009` (`c707d5c`), correção `D-005` (`467c3b3`) e `T-010` (`aca19ac`).
**Quanto tempo levou:** **~22 minutos** no total (das 15:03 às 15:25 do mesmo dia na linha do tempo dos commits, sendo ~10 minutos na análise das 6 novas ambiguidades e atualização de `spec.md`/`DECISIONS.md`/`plan.md`/`tasks.md` e ~12 minutos na execução e testes das tasks `T-008`, `T-009` e `T-010`).
**Diff de absorção:**
- **Apenas código e testes (`git diff 5584cf6 aca19ac --stat -- src/ tests/`):** `8 arquivos alterados, +680/-139 linhas` (sendo 5 arquivos em `src/` e 3 arquivos em `tests/`).
- **Repositório completo incluindo spec, plan, tasks, decisions, README e os 5 arquivos do envelope (`git diff 5584cf6 aca19ac --stat`):** `18 arquivos, +1351/-460 linhas`.

**Absorveu de graça:**
1. **Isolamento da política em `src/policy.py`:** Como o `plan.md` v1.0 já concentrava todas as regras de elegibilidade e limites nos métodos `PoliticaReembolso.categoria_elegivel()` e `PoliticaReembolso.obter_limite_diario()`, bastou adicionar o parâmetro opcional `centro_custo` e o construtor `PoliticaReembolso.de_dict()` lendo `politica-v4.json`. Nenhuma constante precisou ser caçada dentro de `src/engine.py`.
2. **Arquitetura em duas passagens (`DT-001` em `src/engine.py`):** A separação entre a Passagem 1 (validação de elegibilidade individual) e a Passagem 2 (apuração das datas em viagem `RN-007` e consumo de saldo diário `RN-008`) absorveu de graça duas regras críticas da v4:
   - Como `hospedagem` em `CC-ENG-PLATAFORMA` (`limite: 0.00`) é barrada na Passagem 1 (`RN-004` / `AMB-014`), ela automaticamente não chega na Passagem 2 e **não ativa indevidamente o regime de viagem** para `d-010` e `d-011`.
   - A conversão cambial (`RN-009`) encaixou-se na Passagem 1 logo antes de `validar_nota_fiscal` (`RN-005`), garantindo que `e-005` (`40.00 USD = R$ 220,00` sem NF) fosse barrada por `SEM_NOTA_FISCAL` antes de consumir saldo diário.
3. **Decisão `D-002` do Dia 1 (`categorias_ampliadas_em_viagem`):** Ter definido no Dia 1 um `frozenset({"alimentacao", "transporte_urbano"})` para o bônus de +50% em viagem fez com que a nova categoria `representacao` (limite R$ 300,00 em `CC-COMERCIAL`) já mantivesse seu teto próprio sem precisar de lógica especial.

**Resistiu:**
1. **Modelagem de moeda única em `DespesaInput` e `ResultadoDespesa` (`src/models.py`):** Na v1.0, `DespesaInput` e `ResultadoDespesa` assumiam implicitamente que `valor_original` já estava em `BRL`. Para manter transparência de auditoria nas despesas internacionais, foi necessário estender `DespesaInput` e `ResultadoDespesa` com `moeda_original`, `valor_moeda_original` e `taxa_cambio_aplicada` (usando defaults `"BRL"` e `Decimal("1.00")` para não quebrar nenhum dos 15 testes do Dia 1).
2. **Vigência retroativa da Política v4 sobre `despesas-exemplo.json` (`AMB-016`):** Como o comunicado determinou vigência retroativa à competência `2026-07` e o lote do Dia 1 (`exemplos/despesas-exemplo.json`) era do centro de custo `CC-ENG-PLATAFORMA`, o gabarito de `CA-001` em `tests/test_edge_cases.py` e `tests/test_cli.py` precisou ser atualizado para refletir o novo limite de alimentação de R$ 75,00 e a recusa de `hospedagem` (`d-010`).

**Ordem em que fiz:**
Ordem estrita SDD, comprovada pelos timestamps e sequência do `git log`:
1. `3e68e54` — `docs(spec): atualiza spec para v2.0 (Politica v4 e cambio) e registra D-004 no DECISIONS.md`
2. `c49f175` — `docs(tasks): cria Fase 5 (T-008..T-010), atualiza plan.md para v2.0 e versiona arquivos do envelope`
3. `5a6a4b3` — `feat(T-008): estende modelos, politica v4 por centro de custo e tabela de cambio com fallback`
4. `c707d5c` — `feat(T-009): atualiza motor para conversao cambial RN-009, viagem por moeda estrangeira e limites por CC`
5. `467c3b3` — `docs(spec): corrige totais agregados de CA-001 e CA-009 detectados pelos testes da T-010 (D-005)`
6. `aca19ac` — `feat(T-010): valida lotes do envelope e vigencia retroativa v4, CLI com --politica/--cambio e README`

**Se eu tivesse escrito a spec original sabendo desta mudança:**
1. Teria incluído `moeda_original` (padrão `"BRL"`) na chave de duplicidade (`RN-006`) e no contrato de saída desde a versão 1.0.
2. Teria definido em `RN-004` desde a v1.0 que uma categoria só é elegível quando consta na tabela aplicável ao colaborador com `limite > 0.00`.

**O que a spec me poupou, em concreto:**
Poupou ter que descobrir durante a codificação a ordem exata entre **conversão cambial (`RN-009`)**, **obrigatoriedade de nota fiscal acima de R$ 100 (`RN-005`)** e **ativação do regime de viagem por moeda estrangeira (`RN-007`)**. Sem a Seção 8 da `spec.md` ("Ordem de aplicação das regras"), o caso `e-005` (`40.00 USD` sem nota fiscal, que parece `<= 100` em dólar mas vale `R$ 220,00` em reais) e o caso `e-004` (`30.00 EUR` em um sábado sem cotação PTAX no dia, exigindo fallback para sexta-feira `17/07` **e** ativação do limite de viagem de R$ 135,00 de `CC-COMERCIAL`) teriam gerado bugs silenciosos e retrabalho manual.

---

## Fechamento

**Para qual tamanho de projeto isto valeu a pena?**
Vale a pena para qualquer projeto com **regras de negócio densas, políticas com precedência entre si ou vida útil superior a uma única sessão de chat** (mesmo que o código final tenha menos de 600 linhas, como este motor). Quando existem 16 ambiguidades interagindo (centro de custo vs. fallback padrão vs. câmbio em fim de semana vs. nota fiscal pós-conversão vs. limite diário em viagem), o custo cognitivo não está na sintaxe do Python, mas na consistência das regras.

**Para qual não valeria?**
Não valeria para scripts descartáveis de uso único (one-off de migração ou formatação de arquivos), protótipos puramente visuais de interface ou correções triviais de bug de uma linha onde o requisito já é óbvio e sem casos de fronteira.

**O que eu faria diferente:**
1. Teria usado um script rápido para somar matematicamente os lotes JSON **antes** de congelar os números de `CA-001` e `CA-009` na `spec.md`, evitando as correções `D-003` (`06dadda`) e `D-005` (`467c3b3`).
2. Teria incluído a regra de exportação incremental para `docs/sessions/` no `CLAUDE.md` já no primeiro minuto da Sessão 01.

**A coisa mais desconfortável que aprendi sobre como eu trabalho com IA:**
Percebi o quão fácil é ser seduzido por uma documentação bem formatada gerada pela IA — e que **saber de um viés do modelo não impede você de cair nele de novo se não criar uma trava de processo**. Mesmo depois de ter pego o erro de soma mental do modelo no Dia 1 (`D-003`), voltei a confiar na soma mental dele ao redigir `CA-009` no Dia 2 (`D-005`). A fluência textual do modelo mascara erros lógicos e aritméticos; a única defesa confiável é transformar a verificação em teste executável (`pytest`).
