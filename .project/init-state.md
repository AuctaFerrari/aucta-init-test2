---
init_version: 0.1.0
projeto: "Aucta Foods — Rentabilidade por Cliente e Cobertura Comercial"
repo: "AuctaFerrari/aucta-init-test2"
risk_tier: 2
status_geral: em_andamento
iniciado_em: 2026-09-02
atualizado_em: 2026-09-02
---

# Estado do /init — Aucta Foods — Rentabilidade por Cliente e Cobertura Comercial

Arquivo de estado do Aucta Dev Init. Registra **progresso**, não conteúdo: respostas e decisões vivem nos artefatos canônicos (PROJECT.md, TRUTHS.md, GLOSSARY.md, ACCEPTANCE.md, OWNERS.md, DATA_CATALOG.md). Atualizado e commitado pelo agente a cada avanço material.

## Sub-skills

| Sub-skill | Status | Última atualização | Evidência |
| --- | --- | --- | --- |
| init-interview | concluida | 2026-09-02 | PROJECT.md, TRUTHS.md, GLOSSARY.md, ACCEPTANCE.md, OWNERS.md (commit 85e49e8) |
| init-repo | pendente | | |
| init-data | pendente | | |
| init-plugin | pendente | | |
| init-check | pendente | | |

## init-interview — blocos

| Bloco | Status | Notas |
| --- | --- | --- |
| A. Problema e objetivo | concluida | PROJECT.md (objetivo, KPI) |
| B. Escopo e fronteiras | concluida | PROJECT.md (in/out, restrições) |
| C. Stakeholders e decisão | concluida | OWNERS.md |
| D. Entregáveis e aceite | concluida | ACCEPTANCE.md (ACC-001..006) |
| E. Dados e fontes (inventário) | concluida | 1 fonte: 01_Base_Operacional_Sintetica.xlsx (5 bases); detalhamento no init-data |
| F. Segurança e privacidade | concluida | TRUTH-006 (dados reais fora do repo e do ambiente) |
| G. IP e licenças | concluida | fechado por premissa (ver Premissas) |
| H. Arquitetura inicial | concluida | PROJECT.md (programa local Python, Windows) |
| I. Ambientes e acessos | concluida | GitHub ok; pasta local pendente (ver Blockers) |
| J. Repositório e governança | pendente | executado no init-repo |
| K. Estratégia de testes | concluida | ACCEPTANCE.md (golden cases tier 2) |
| L. Conhecimento canônico | concluida | TRUTHS.md (10 verdades), GLOSSARY.md (10 termos) |
| M. Plugin e skill stack | pendente | executado no init-plugin |
| N. Release e sustentação | concluida | analista opera, Aucta dá suporte; aceite por e-mail |
| O. Baseline | concluida | não há código pré-existente; baseline = repo novo do template (tag no init-repo) |

## Premissas

- Bloco G (IP/licenças): sem dependências pagas ou dados licenciados identificados; propriedade do código a confirmar com o cliente na primeira entrega.
- Fórmulas de cálculo são preliminares (TRUTH-001..005): valem até a validação da controladoria no golden case do piloto.
- Nome do analista operador da rotina ainda não informado (OWNERS.md: "a nomear").
- Contatos de Ana Martins e Bruno Lima "a confirmar" em OWNERS.md.
- Marcos/datas de desenvolvimento não definidos na iniciação; serão definidos no planejamento.
- Backup de releases fora do GitHub (padrão: pasta backups/ no SharePoint) não configurado — projeto não usa SharePoint na v1.

## Blockers

- Conector GitHub sem permissão para criar repositórios (403); criação feita pelo caminho assistido "Use this template" pelo consultor em 2026-09-02. Não bloqueia mais; registrado para o init-check.
- Pasta local com `01_Base_Operacional_Sintetica.xlsx` ainda não conectada ao Claude. Bloqueia a leitura da base no init-data (Etapa 3). Ação: consultor conectar a pasta no app desktop ("Adicionar pasta").

## Retomada

- Próximo passo: iniciar init-repo (Etapa 2 de 5 — organização do repositório).
- Depois: init-data (requer pasta local conectada), init-plugin, init-check.
