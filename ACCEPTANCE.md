# Aucta Foods — Rentabilidade por Cliente — ACCEPTANCE.md

> Critérios de aceite, definição de pronto e estratégia de provas (blocos D e K do checklist). Critérios são testáveis; cada um pode virar caso de teste.

## Entrega

**Formato:** Excel analítico (rentabilidade por cliente/mês) + relatório executivo em PDF, gerados por programa local em Python.
**Ambiente alvo:** computador corporativo Windows do analista; execução mensal manual; entrada e saída em pastas locais.
**Mecanismo de aprovação:** e-mail de aceite enviado a joao.santos@aucta.capital com a entrega; aprovação = resposta positiva ao e-mail, arquivada como referência no repositório. Validação dos números por Bruno Lima (Controladoria) antecede o e-mail.

## Critérios de aceite

| # | Critério (testável) | Como provar |
| --- | --- | --- |
| ACC-001 | Excel analítico com receita líquida, margem de contribuição e margem de servir por cliente e mês do piloto (jan–mar/2026). | Execução sobre a base sintética + golden cases GC-01..03 (`tests/fixtures/golden_cases.csv`). |
| ACC-002 | PDF executivo com aderência de visitas ao planejamento e as duas listas de clientes-alerta. | Inspeção do PDF gerado no piloto; listas conferidas contra o golden case. |
| ACC-003 | Números do piloto batem com a referência externa validada pela controladoria. | Golden cases GC-01..03 com tolerância R$ 0,00; validação formal de Bruno Lima. |
| ACC-004 | Analista executa sozinho no Windows, de ponta a ponta, sem apoio do consultor. | Teste assistido de execução: analista roda a rotina completa apenas com o guia de uso. |
| ACC-005 | Duplicidades e identificadores tratados com registro do que foi corrigido/excluído. | Log de tratamento cobre TODAS as linhas de `tests/fixtures/expected_exceptions.csv` (EX-01..07). |
| ACC-006 | Reconciliação: diferença zero entre totais válidos da origem e totais processados, após exclusões documentadas. | Bloco de reconciliação no Excel analítico, conferido em cada execução do piloto. |
| ACC-007 | Relatório NÃO é publicado enquanto houver exceção bloqueante aberta (órfão, custo/frete nulo — EX-04..06). | Execução sobre a fixture: pipeline sinaliza bloqueio de publicação com O008/O009/O010 presentes. |

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
| Golden cases | **Materializados** em `tests/fixtures/golden_cases.csv` (GC-01..03, fornecidos no briefing, conferidos por recomputação manual independente em 2026-09-03; tolerância R$ 0,00). Validação formal de Bruno Lima = gate antes do merge do primeiro /change-number. Rodam before/after em toda mudança de número; harness independente em `tests/golden/run_golden.py` (entra com o primeiro código; CI já exige). |
| Exceções esperadas | `tests/fixtures/expected_exceptions.csv` (EX-01..07): dedupe, exclusão, normalização, bloqueios de publicação. |
| Smoke / E2E | Execução completa da rotina sobre a base sintética (jan–mar/2026), do Excel de entrada até Excel analítico + PDF. |
| Testes de dados | Duplicidades e identificadores produzem o log esperado; reconciliação (ACC-006) verificada em toda execução. |
