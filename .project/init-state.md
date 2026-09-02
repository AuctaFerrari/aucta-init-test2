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
| init-repo | concluida | 2026-09-02 | CODEOWNERS/checks/CLAUDE.md (commit b5d59eb); proteção da main validada por push rejeitado (409); check reprovou PR #1 de teste (fechado sem merge) |
| init-data | concluida | 2026-09-02 | .project/DATA_CATALOG.md + tests/fixtures/*.csv (5 abas, extraídas da base sintética); leitura N1 = 100% das linhas |
| init-plugin | pendente | | |
| init-check | pendente | | |

## init-interview — blocos

| Bloco | Status | Notas |
| --- | --- | --- |
| A. Problema e objetivo | concluida | PROJECT.md (objetivo, KPI) |
| B. Escopo e fronteiras | concluida | PROJECT.md (in/out, restrições) |
| C. Stakeholders e decisão | concluida | OWNERS.md |
| D. Entregáveis e aceite | concluida | ACCEPTANCE.md (ACC-001..006) |
| E. Dados e fontes (inventário) | concluida | fonte única catalogada em DATA_CATALOG.md (status observado); consultor confirmou não haver outras fontes |
| F. Segurança e privacidade | concluida | TRUTH-006 (dados reais fora do repo e do ambiente) |
| G. IP e licenças | concluida | fechado por premissa (ver Premissas) |
| H. Arquitetura inicial | concluida | PROJECT.md (programa local Python, Windows) |
| I. Ambientes e acessos | concluida | GitHub ok; pasta local conectada em 2026-09-02 |
| J. Repositório e governança | concluida | init-repo: itens 1–10 fechados (item 3 baseline n/a — sem código pré-existente; item 7 quadro adiado) |
| K. Estratégia de testes | concluida | ACCEPTANCE.md (golden cases tier 2) |
| L. Conhecimento canônico | concluida | TRUTHS.md (10 verdades), GLOSSARY.md (10 termos) |
| M. Plugin e skill stack | pendente | executado no init-plugin |
| N. Release e sustentação | concluida | analista opera, Aucta dá suporte; aceite por e-mail |
| O. Baseline | concluida | não há código pré-existente; baseline = estado do template (sem tag necessária) |

## Premissas

- Bloco G (IP/licenças): sem dependências pagas ou dados licenciados identificados; propriedade do código a confirmar com o cliente na primeira entrega.
- Fórmulas de cálculo são preliminares (TRUTH-001..005): valem até a validação da controladoria no golden case do piloto.
- Nome do analista operador da rotina ainda não informado (OWNERS.md: "a nomear").
- Contatos de Ana Martins e Bruno Lima "a confirmar" em OWNERS.md.
- Marcos/datas de desenvolvimento não definidos na iniciação; serão definidos no planejamento.
- Backup de releases fora do GitHub (padrão: pasta backups/ no SharePoint) não configurado — projeto não usa SharePoint na v1.
- Repo tornado PÚBLICO em 2026-09-02, por decisão do consultor, para a proteção da main valer no plano Free — aceitável apenas porque a massa é 100% sintética. Projeto real: repo privado + plano Team+ (padrão Aucta).
- Proteção da main sem "Required approvals" (consultor solo — GitHub proíbe auto-aprovação); validação de negócio Muda-numero registrada como comentário no PR.
- GitHub Project (quadro de backlog) adiado a pedido do consultor — item não-bloqueante.
- Estrutura da base de PRODUÇÃO presumida idêntica à base sintética do piloto — não validado (DATA_CATALOG).
- Parâmetro `limiar_margem_servir_baixa` (0,05) marcado "Não validado" na própria base — validar com o sponsor antes do primeiro relatório.

## Blockers

- Conector GitHub sem permissão para criar repositórios (403); criação feita pelo caminho assistido "Use this template" pelo consultor em 2026-09-02. Não bloqueia mais; registrado para o init-check.
- ~~Pasta local não conectada~~ — resolvido em 2026-09-02: pasta "teste 2" conectada; base lida e catalogada.

## Achados de ambiente

- create_repository via conector: 403 (ASSISTED "Use this template" funcionou).
- Labels de governança: bootstrap automático pela Action do template funcionou (9 labels).
- Ruleset da main: precisou remover admin da bypass list; enforcement em repo privado indisponível no plano Free → repo público.
- Teste de proteção: push direto na main rejeitado com 409 ("Changes must be made through a pull request" + check `checks` obrigatório).
- Leitura de check runs via conector: funcionou nesta sessão (PR #1: check `checks` = failure, merge bloqueado, PR fechado sem merge).
- Com a main protegida, atualizações de estado passam por PR + check verde + merge pelo agente.
- Commit de binário (.xlsx) via conector não é suportado — fixture versionada como CSVs (1:1 por aba); o Excel original permanece na pasta conectada como fonte oficial.

## Retomada

- Próximo passo: init-plugin (Etapa 4 de 5 — montagem do plugin do projeto).
- Depois: init-check.
