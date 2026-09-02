# CLAUDE.md — Aucta Foods — Rentabilidade por Cliente e Cobertura Comercial

Padrão Aucta (gerado pelo /init). Minimal context for ANY agent session opened in this repo — read before acting.

## Read first (in order)

1. `.project/init-state.md` — orchestration state: what is closed, blocked, and where to resume. Never re-ask what it marks closed.
2. `PROJECT.md` · `TRUTHS.md` · `GLOSSARY.md` · `ACCEPTANCE.md` · `OWNERS.md` — canonical artifacts (problem, current facts/rules, terms, acceptance + golden cases, who decides what).
3. `.project/DATA_CATALOG.md` — every data source: where it lives, sensitivity, freshness.
4. `project-plugin/` — router and workflows. Route requests through it; a change that alters a delivered number goes through /change-number (Muda-numero gate).

## Non-negotiable rules

- **REGRA DE OURO:** the agent only uses/alters files inside the project's connected folder and this repository. As bases mensais originais da Aucta Foods são INTOCÁVEIS — a solução lê a base e escreve saídas em pasta própria, nunca altera o arquivo de origem.
- Real client data NEVER enters Git (fixtures sintéticas apenas, somente em `tests/fixtures/`; ver TRUTH-006 e DATA_CATALOG).
- The agent executes ALL Git (branch/commit/push/PR/merge) — the consultant never types commands (D6).
- Business approval before merging any Muda-numero change: quem valida número é Bruno Lima (Controladoria) — ver OWNERS.md.
- Consultant dialogue in pt-BR per linguagem-consultor (conceitos traduzidos, abertura didática, progresso "Etapa N de X", 1 decisão por pergunta).

## Project facts

- Risk tier: 2 — a solução produz números (margens por cliente) que sustentam decisão da diretoria; golden cases obrigatórios.
- Ambiente/infra: programa local em Python executado manualmente pelo analista em computador corporativo Windows; entrada = Excel operacional mensal (5 bases), saída = Excel analítico + PDF executivo em pasta local; sem servidor, sem rede, sem autenticação na v1.
- Backup: projeto não usa SharePoint na v1 — snapshot de release a definir (registrado como premissa no init-state).

## Router

<preenchido/atualizado pelo init-plugin quando project-plugin/ existir: como invocar /start-work, /build-feature, /change-number, /pre-pr, /release, /handoff>
