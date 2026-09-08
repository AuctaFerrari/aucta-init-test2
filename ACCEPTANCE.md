# Aucta Foods — Rentabilidade por Cliente — ACCEPTANCE.md

> Critérios de aceite, definição de pronto e estratégia de provas (blocos D e K do checklist). Critérios são testáveis; cada um pode virar caso de teste.

## Entrega

**Formato:** Excel analítico (rentabilidade por cliente/mês) + relatório executivo em PDF, gerados por programa local em Python.
**Ambiente alvo:** computador corporativo Windows do analista; execução mensal manual; entrada e saída em pastas locais.
**Mecanismo de aprovação:** e-mail de aceite enviado a joao.santos@aucta.capital com a entrega; aprovação = resposta positiva ao e-mail, arquivada como referência no repositório. Validação dos números por Bruno Lima (Controladoria) antecede o e-mail.

## Critérios de aceite

| # | Critério (testável) | Como provar | Estado |
| --- | --- | --- | --- |
| ACC-001 | Excel analítico com receita líquida, margem de contribuição e margem de servir por cliente e mês do piloto (jan–mar/2026). | Execução sobre a base sintética + golden cases GC-01..03. | Pendente — ciclo do cálculo |
| ACC-002 | PDF executivo com aderência de visitas ao planejamento e as duas listas de clientes-alerta. | Inspeção do PDF gerado no piloto; listas conferidas contra o golden case. | Pendente — ciclo do cálculo; depende de `limiar_margem_servir_baixa`, **não aprovado** |
| ACC-003 | Números do piloto batem com a referência externa validada pela controladoria. | Golden cases GC-01..03 com tolerância R$ 0,00; validação formal de Bruno Lima. | **Valores aprovados** em 2026-09-08; implementação pendente |
| ACC-004 | Analista executa sozinho no Windows, de ponta a ponta, sem apoio do consultor. | Teste assistido de execução, apenas com o guia de uso. | Pendente — guia de uso entra no ciclo da entrega |
| ACC-005 | Duplicidades e identificadores tratados com registro do que foi corrigido/excluído. | Log de tratamento cobre TODAS as linhas de `expected_exceptions.csv` (EX-01..07). | Regra aprovada; prova pendente da fase 2 |
| ACC-006 | Reconciliação: diferença zero entre totais válidos da origem e totais processados, após exclusões documentadas. | Bloco de reconciliação conferido em cada execução. **A partir de DN-08, cinco populações:** origem = tratada + excluída + quarentena + fora do período. | Esperado materializado nos golden; prova pendente da fase 2 |
| ACC-007 | Relatório NÃO é publicado enquanto houver exceção bloqueante aberta. | **Escopo esclarecido por DN-10:** bloqueia a **competência afetada**, não o relatório inteiro. Na fixture: fev/2026 bloqueado, jan e mar publicáveis. Bloqueio de período inteiro só nos casos de DN-07/I-01 e DN-13. | Esperado materializado nos golden; prova pendente da fase 2 |

## Registro de aprovação dos valores esperados e da tolerância

| Item | Situação | Autorizador | Data | Fonte |
| --- | --- | --- | --- | --- |
| GC-01 · C001 / 2026-01 · margem de servir R$ 330,00 | **Aprovado** | Bruno Lima (papel fictício explicitamente ativado por Caio Ferrari) | 2026-09-08 | issuecomment-5589411324 |
| GC-02 · C002 / 2026-01 · R$ 120,00 | **Aprovado** | idem | 2026-09-08 | idem |
| GC-03 · C003 / 2026-01 · R$ 400,00 | **Aprovado** | idem | 2026-09-08 | idem |
| Tolerância **absoluta R$ 0,00** para os golden sintéticos, após a política decimal de DN-09 | **Aprovada** | idem | 2026-09-08 | idem |
| Fórmulas TRUTH-001..005 | **Aprovadas** | idem | 2026-09-08 | idem |
| Regras TRUTH-011..015 e exceções EX-01..07 | **Aprovadas** (013 e 015 com esclarecimento) | idem | 2026-09-08 | idem |
| Decisões DN-01..DN-13 | **Aprovadas** | idem | 2026-09-08 | issuecomment-5589411324 e issuecomment-5589595626 |
| `limiar_margem_servir_baixa` | **Não aprovado** | — | — | — |

**Registro de invalidação, preservado de propósito.** Uma aprovação anterior (`issuecomment-5586649630`) foi produzida convertendo uma instrução do owner técnico — que pedia literalmente para *assumir* a validação — em registro nomeado. Ela foi invalidada em `issuecomment-5589236253` e **não** tem efeito. Verificação técnica e aprovação funcional são tipos de evidência distintos: reproduzir um valor por caminho independente prova derivabilidade, não aprovação.

## Definição de pronto

- Critérios de aceite atendidos e demonstrados.
- Testes proporcionais ao risco executados e verdes (tier 2: golden atualizados e passando).
- Documentação que ficaria incorreta atualizada no mesmo ciclo.
- Parâmetro de negócio usado no cálculo presente em `.project/PARAMETERS.md`, dentro da vigência.
- E-mail de aceite respondido positivamente e arquivado no repositório.

## Marcos

| Marco | Conteúdo | Data alvo |
| --- | --- | --- |
| A definir | Plano de marcos será definido na fase de planejamento do desenvolvimento. | — |

## Como vamos provar (estratégia de testes — bloco K)

**Risk tier do projeto:** 2 · **Detalhe completo:** `tests/TEST_STRATEGY.md`

| Tipo | Aplicação neste projeto |
| --- | --- |
| Golden de margem | `tests/fixtures/golden_cases.csv` (GC-01..03, tolerância R$ 0,00, aprovados em 2026-09-08). Rodam before/after em toda mudança de número. |
| Golden do tratamento | `tests/fixtures/golden/base-tratada/` — população, reconciliação e veredito esperados, derivados por recomputação independente **antes** da implementação, cobrindo a fixture atual e cinco cenários adversariais (DN-04, DN-07+I-01, DN-08, DN-11, DN-13). |
| Exceções esperadas | `tests/fixtures/expected_exceptions.csv` (EX-01..07). |
| Smoke / E2E | Execução completa sobre a base sintética, pelos dois caminhos de entrada (pasta de CSVs e `.xlsx`), com resultado idêntico. |
| Testes de dados | Reconciliação de cinco populações; todo valor da base tratada conferido contra a fonte, valor a valor. |
| Provas negativas | Cada regra enfraquecida de propósito precisa reprovar o harness. |
