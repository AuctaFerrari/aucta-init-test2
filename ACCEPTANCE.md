# Aucta Foods — Rentabilidade por Cliente — ACCEPTANCE.md

> Critérios de aceite, definição de pronto e estratégia de provas (blocos D e K do checklist). Critérios são testáveis; cada um pode virar caso de teste.

## Entrega

**Formato:** Excel analítico (rentabilidade por cliente/mês) + relatório executivo em PDF, gerados por programa local em Python.
**Ambiente alvo:** computador corporativo Windows do analista; execução mensal manual; entrada e saída em pastas locais.
**Mecanismo de aprovação:** e-mail de aceite enviado a joao.santos@aucta.capital com a entrega; aprovação = resposta positiva ao e-mail, arquivada como referência no repositório. Validação dos números por Bruno Lima (Controladoria) antecede o e-mail.

## Critérios de aceite

| # | Critério (testável) | Como provar | Estado |
| --- | --- | --- | --- |
| ACC-001 | Excel analítico com receita líquida, margem de contribuição e margem de servir por cliente e mês do piloto (jan–mar/2026). | Execução sobre a base sintética + golden cases GC-01..03 (`tests/fixtures/golden_cases.csv`). | Pendente — ciclo do cálculo |
| ACC-002 | PDF executivo com aderência de visitas ao planejamento e as duas listas de clientes-alerta. | Inspeção do PDF gerado no piloto; listas conferidas contra o golden case. | Pendente — ciclo do cálculo |
| ACC-003 | Números do piloto batem com a referência externa validada pela controladoria. | Golden cases GC-01..03 com tolerância R$ 0,00; validação formal de Bruno Lima. | Insumos provados em 2026-09-08 (suite 7: GC-01..03 deriváveis da base tratada, diferença R$ 0,00); as margens seguem pendentes de implementação |
| ACC-004 | Analista executa sozinho no Windows, de ponta a ponta, sem apoio do consultor. | Teste assistido de execução: analista roda a rotina completa apenas com o guia de uso. | Pendente — guia de uso entra no ciclo da entrega |
| ACC-005 | Duplicidades e identificadores tratados com registro do que foi corrigido/excluído. | Log de tratamento cobre TODAS as linhas de `tests/fixtures/expected_exceptions.csv` (EX-01..07). | **Atendido em 2026-09-08** — `outputs/base-tratada/log_tratamento.csv` registra valor anterior → valor novo e a regra de cada transformação; suite 5 exige cobertura de EX-01..07 |
| ACC-006 | Reconciliação: diferença zero entre totais válidos da origem e totais processados, após exclusões documentadas. | Bloco de reconciliação no Excel analítico, conferido em cada execução do piloto. | **Atendido em 2026-09-08 na camada de tratamento** — `reconciliacao.csv` fecha em R$ 0,00 nos 9 blocos (RC-01..09); repetir no Excel analítico quando ele existir |
| ACC-007 | Relatório NÃO é publicado enquanto houver exceção bloqueante aberta (órfão, custo/frete nulo — EX-04..06). | Execução sobre a fixture: pipeline sinaliza bloqueio de publicação com O008/O009/O010 presentes. | **Atendido em 2026-09-08** — o relatório de tratamento abre com PUBLICAÇÃO BLOQUEADA e nomeia as 3 exceções; veredito por competência isola 2026-02 como não calculável |

## Registro de validação dos valores esperados e da tolerância

| Item | Situação | Autorizador | Data |
| --- | --- | --- | --- |
| Tolerância R$ 0,00 para todo golden do projeto | Validada | Bruno Lima (Controladoria), papel delegado a Caio Ferrari | 2026-09-08 |
| Regras de tratamento TRUTH-011..015 | Validadas | idem | 2026-09-08 |
| Exceções esperadas EX-01..07 | Validadas | idem | 2026-09-08 |
| Decisões DEC-01..07 (TRUTH-016..020) | Aprovadas | idem | 2026-09-08 |
| Fórmulas TRUTH-001..005 | **Seguem preliminares** — não validadas | — | — |

**Limitação declarada, registrada aqui de propósito.** A validação acima vale como decisão do dono do número porque a massa é 100% sintética e o papel de Bruno Lima foi delegado por escrito ao consultor na abertura do ciclo (Issue #10, 2026-09-08). Em projeto com dado real, número entregue sem o registro do próprio validador é **blocker**, não exceção formal. Este registro não cria precedente e não vale para as fórmulas TRUTH-001..005, que seguem exigindo validação da controladoria antes do ciclo do cálculo.

## Definição de pronto

- Critérios de aceite atendidos e demonstrados.
- Testes proporcionais ao risco executados e verdes (tier 2: golden cases atualizados e passando).
- Documentação que ficaria incorreta foi atualizada no mesmo ciclo.
- E-mail de aceite respondido positivamente e arquivado no repositório.

## Marcos

| Marco | Conteúdo | Data alvo |
| --- | --- | --- |
| A definir | Plano de marcos será definido na fase de planejamento do desenvolvimento. | — |

## Como vamos provar (estratégia de testes — bloco K)

**Risk tier do projeto:** 2 · **Detalhe completo:** `tests/TEST_STRATEGY.md`

| Tipo | Aplicação neste projeto |
| --- | --- |
| Golden cases | **Materializados** em `tests/fixtures/golden_cases.csv` (GC-01..03, fornecidos no briefing, conferidos por recomputação manual independente em 2026-09-03; tolerância R$ 0,00, validada em 2026-09-08). Rodam before/after em toda mudança de número; harness independente em `tests/golden/run_golden.py`. |
| Golden do tratamento | `golden_base_tratada.csv` (BT-01..24 — destino de cada linha), `golden_reconciliacao.csv` (RC-01..09 — conservação por bloco e campo) e `golden_veredito_competencia.csv` (VC-01..03 — veredito de segurança por mês), materializados por recomputação independente **antes** da implementação em 2026-09-08. |
| Exceções esperadas | `tests/fixtures/expected_exceptions.csv` (EX-01..07): dedupe, exclusão, normalização, bloqueios de publicação. |
| Smoke / E2E | Execução completa da rotina sobre a base sintética (jan–mar/2026), do Excel de entrada até Excel analítico + PDF. Hoje cobre até a base tratada, pelos dois caminhos de entrada (pasta de CSVs e `.xlsx`), com resultado idêntico. |
| Testes de dados | Duplicidades e identificadores produzem o log esperado; reconciliação (ACC-006) verificada em toda execução; todo valor da base tratada é conferido contra a fonte, valor a valor. |
| Provas negativas | Cada regra é enfraquecida de propósito e o harness precisa reprovar: aceitar nulo essencial, inverter a deduplicação, emitir coluna calculada, incluir módulo não declarado em `src/`. Executadas em 2026-09-08 e registradas no PR do ciclo. |
