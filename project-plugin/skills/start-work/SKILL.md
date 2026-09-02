---
name: start-work
description: Abrir qualquer mudança no projeto Aucta Foods — Rentabilidade por Cliente. Sempre o primeiro workflow de uma demanda; cria Issue, branch e plano de validação.
---

# /start-work — abrir qualquer mudança

1. **Contexto mínimo** (6.5): read PROJECT.md, TRUTHS.md and the active Issue/Spec. Nothing else by default. [skill: context-engineering — vendored no core]
2. **Classificar**: change tier (0–3) + provável Muda-numero (neste projeto: qualquer toque em cálculo/parâmetro/tratamento → sim). Router decides the follow-up workflow.
3. **Issue**: create/update com resultado desejado, critérios de aceite, tier, Muda-numero — template do repo; label de risco correspondente. [agente]
4. **Branch**: `feat|fix|refactor|docs/<tema>` from main. [agente — D6: consultor nunca digita Git]
5. **Plano de validação**: testes before/after proporcionais ao tier; para tier 2, golden cases em `tests/golden/` sobre `tests/fixtures/`; rollback quando aplicável; baseline capturado se o comportamento puder ser comparado (3.6).
6. Confirm branch, baseline e working tree limpos (ritual 3.5).

Gate de saída: Issue existe, branch criada, plano de validação registrado na Issue.
