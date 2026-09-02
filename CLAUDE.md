# CLAUDE.md — <NOME_DO_PROJETO>

Padrão Aucta (repo criado do template; o /init preenche os placeholders). Minimal context for ANY agent session opened in this repo — read before acting.

## Read first (in order)

1. `.project/init-state.md` — orchestration state: what is closed, blocked, and where to resume. Never re-ask what it marks closed.
2. `PROJECT.md` · `TRUTHS.md` · `GLOSSARY.md` · `ACCEPTANCE.md` · `OWNERS.md` — canonical artifacts (problem, current facts/rules, terms, acceptance + golden cases, who decides what).
3. `.project/DATA_CATALOG.md` — every data source: where it lives, sensitivity, freshness.
4. `project-plugin/` — router and workflows. Route requests through it; a change that alters a delivered number goes through /change-number (Muda-numero gate).

## Non-negotiable rules

- **REGRA DE OURO:** the agent only uses/alters files inside the project's connected folder and this repository. <ajustar conforme restrições do PROJECT.md>
- Real client data NEVER enters Git (fixtures sintéticas apenas; ver DATA_CATALOG).
- The agent executes ALL Git (branch/commit/push/PR/merge) — the consultant never types commands (D6).
- Business approval before merging any Muda-numero change: quem valida número está em OWNERS.md.
- Consultant dialogue in pt-BR per linguagem-consultor (conceitos traduzidos, abertura didática, progresso "Etapa N de X", 1 decisão por pergunta).

## Project facts

- Risk tier: <tier + justificativa de uma linha>
- Ambiente/infra: <onde a solução roda, incl. ambiente do cliente>
- Backup: snapshot do repo em `backups/` na pasta do projeto no SharePoint a cada release (independência do GitHub).

## Router

<preenchido pelo init-plugin quando project-plugin/ existir>
