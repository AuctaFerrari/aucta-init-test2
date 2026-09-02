---
init_version: 0.1.0
projeto: "Aucta Foods — Rentabilidade por Cliente e Cobertura Comercial"
repo: "AuctaFerrari/aucta-init-test2"
risk_tier: 2
status_geral: concluida
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
| init-plugin | concluida | 2026-09-02 | project-plugin/ (router + 7 workflows + pointers + client-rules + MANIFEST D3); CLAUDE.md Router preenchido; stack e fluxos confirmados pelo consultor |
| init-check | concluida | 2026-09-02 | Preflight P1–P11 sem falha bloqueante; harness local verde (4 guardas); drift check 5/5 sem divergência (core = manifest = upstream HEAD); dry run /start-work em simulação ok; DoR: PRONTO |

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
| M. Plugin e skill stack | concluida | init-plugin: 6 skills + camada karpathy (pendente vendorização, fallback embutido); 7 workflows parametrizados |
| N. Release e sustentação | concluida | analista opera, Aucta dá suporte; aceite por e-mail; backup por release em backups/ no OneDrive |
| O. Baseline | concluida | não há código pré-existente; baseline = estado do template (sem tag necessária) |

## Premissas

- Bloco G (IP/licenças): sem dependências pagas ou dados licenciados identificados; propriedade do código a confirmar com o cliente na primeira entrega.
- Fórmulas de cálculo são preliminares (TRUTH-001..005): valem até a validação da controladoria no golden case do piloto.
- Nome do analista operador da rotina ainda não informado (OWNERS.md: "a nomear").
- Contatos de Ana Martins e Bruno Lima "a confirmar" em OWNERS.md.
- Marcos/datas de desenvolvimento não definidos na iniciação; serão definidos no planejamento.
- Backup de releases fora do GitHub: sem SharePoint na v1 → snapshot ZIP por release em `backups/` na pasta do projeto no OneDrive do consultor (parametrizado no /release).
- Repo tornado PÚBLICO em 2026-09-02, por decisão do consultor, para a proteção da main valer no plano Free — aceitável apenas porque a massa é 100% sintética. Projeto real: repo privado + plano Team+ (padrão Aucta).
- Proteção da main sem "Required approvals" (consultor solo — GitHub proíbe auto-aprovação); validação de negócio Muda-numero registrada como comentário no PR.
- GitHub Project (quadro de backlog) adiado a pedido do consultor — item não-bloqueante.
- Estrutura da base de PRODUÇÃO presumida idêntica à base sintética do piloto — não validado (DATA_CATALOG).
- Parâmetro `limiar_margem_servir_baixa` (0,05) marcado "Não validado" na própria base — validar com o sponsor antes do primeiro relatório.
- Skill andrej-karpathy-skills pendente de vendorização no core (tranche 4); workflows operam com fallback embutido até lá.

## Blockers

- _(nenhum bloqueante)_ Histórico: conector GitHub sem permissão de criar repos (403 — resolvido via "Use this template"); pasta local não conectada (resolvido em 2026-09-02).

## Itens manuais/administrativos pendentes (7.2 passo 12)

- Validar `limiar_margem_servir_baixa` com Ana Martins (antes do primeiro relatório).
- Nomear o analista operador e completar contatos de Ana e Bruno em OWNERS.md.
- Criar `tests/golden/` com o primeiro golden case (consultor prepara, Bruno valida) — obrigatório ANTES do primeiro código de cálculo (o harness passa a exigir quando `src/` existir).
- Criar pasta `backups/` no OneDrive do projeto (usada a partir do primeiro /release).
- Opcional: GitHub Project (quadro) quando o time quiser backlog visual.
- Projeto real equivalente: repo privado + plano Team+ (aqui público por ser massa sintética).

## Achados de ambiente

- create_repository via conector: 403 (ASSISTED "Use this template" funcionou).
- Labels de governança: bootstrap automático pela Action do template funcionou (9 labels).
- Ruleset da main: precisou remover admin da bypass list; enforcement em repo privado indisponível no plano Free → repo público.
- Teste de proteção: push direto na main rejeitado com 409 ("Changes must be made through a pull request" + check `checks` obrigatório).
- Leitura de check runs via conector: funcionou nesta sessão (PR #1: check `checks` = failure, merge bloqueado, PR fechado sem merge; PRs #2–#5 verdes e mesclados pelo agente).
- Com a main protegida, atualizações de estado passam por PR + check verde + merge pelo agente.
- Commit de binário (.xlsx) via conector não é suportado — fixture versionada como CSVs (1:1 por aba); o Excel original permanece na pasta conectada como fonte oficial.
- Drift check D3 (2026-09-02): 5 skills conferidas — blob do core = manifest = upstream HEAD; sem divergência. Repo público permitiu clone e execução local do harness (verde).

## Retomada

- Iniciação CONCLUÍDA (DoR: pronto para desenvolvimento). Próximo passo: primeiro ciclo de trabalho via router do project-plugin — /start-work em "Leitura e tratamento da base operacional", desviando para /change-number (regras de tratamento são Muda-numero).
