# Aucta Foods — Rentabilidade por Cliente e Cobertura Comercial — PROJECT.md

> Memória canônica compacta (blueprint 6.1). Contém objetivo, escopo, estado atual, risk tier, arquitetura em uma página e o mapa de navegação. Não é diário de trabalho: detalhes de features vivem em Issues/PRs; fatos e regras vigentes em TRUTHS.md. Atualizado por PR quando o entendimento do projeto muda.

## Objetivo

Automatizar o relatório mensal de rentabilidade por cliente e eficiência da cobertura comercial da Aucta Foods. Hoje o time recebe arquivos operacionais em Excel, cruza tudo manualmente e monta o relatório para a diretoria. A solução extrai as bases, trata identificadores e duplicidades, cruza os dados, calcula receita líquida, margem de contribuição e margem de servir por cliente e mês, avalia aderência das visitas ao planejamento e gera um Excel analítico e um relatório executivo em PDF.

**Decisão apoiada:** redimensionar a frequência de visitas e priorizar clientes (diretoria comercial e controladoria).
**KPI de sucesso:** relatório mensal produzido em menos de 1 dia útil E números validados pela conferência da controladoria (sem ajuste manual).

## Usuários

- **Analista** (Aucta Foods): executa a rotina mensal manualmente em computador corporativo Windows.
- **Diretora Comercial (Ana Martins)**: consome o relatório executivo para decisão de cobertura.
- **Controladoria (Bruno Lima)**: valida os números antes de cada entrega.

## Escopo

**In scope (v1):** extração das bases de clientes, vendas, custos logísticos, visitas e parâmetros; tratamento de identificadores e duplicidades; cruzamento dos dados; cálculo de receita líquida, margem de contribuição e margem de servir por cliente/mês; aderência das visitas realizadas ao planejamento; identificação de clientes rentáveis pouco cobertos e de baixa rentabilidade com excesso de visitas; geração de Excel analítico + PDF executivo; reconciliação de totais origem × processado.

**Out of scope (v1):** autenticação, API externa, deploy/hospedagem, agendamento automático, integração com ERP.

**Premissas e restrições:** execução mensal, manual, por analista, em Windows corporativo; dados reais confidenciais nunca entram no repositório nem saem do computador corporativo (repo: só código, documentação e massa sintética); período piloto jan–mar/2026 com a base sintética `01_Base_Operacional_Sintetica.xlsx`.

## Risk tier

| Tier | Gatilhos | Justificativa |
| --- | --- | --- |
| 2 | Números externos (margens e rankings entregues à diretoria para decisão); dados de cliente (bases operacionais alimentam a saída entregue) | A solução produz números que sustentam decisão de negócio — golden cases obrigatórios e validação formal da controladoria antes de cada entrega. |

O piso tier 2 vale para tudo que produz número entregue. Mudanças estritamente observacionais podem ser classificadas em tier menor, caso a caso, com justificativa na Issue — e sem alterar o piso das regras de tratamento e cálculo.

## Arquitetura em uma página

Programa local em **Python**, executado pelo analista (duplo clique/comando único) no computador corporativo Windows. Fluxo: lê o Excel operacional mensal (5 bases: clientes, vendas, custos logísticos, visitas, parâmetros) → trata identificadores e duplicidades (com registro das correções) → cruza as bases → calcula receita líquida, margem de contribuição e margem de servir por cliente/mês → avalia aderência de visitas → reconcilia totais → gera `Excel analítico` + `PDF executivo` em pasta local. Sem servidor, sem banco de dados, sem rede: entrada e saída são arquivos locais. O que o cliente precisa ter: computador Windows com permissão para executar o programa (Python empacotado ou instalado) e acesso à pasta dos arquivos mensais. Dependência externa declarada em `requirements.txt` (leitura de `.xlsx`), com versão fixa e hash verificado.

## Estado atual

Iniciação concluída com Definition of Ready **segmentado** por fase (ver `.project/init-state.md`). Em desenvolvimento da **fase 1** — leitura e entendimento da base. Primeira entrega da fase: comando de diagnóstico de qualidade da fonte (`src/diagnostico_fonte.py`), observacional. Cálculo de margens e recomendações seguem bloqueados pelos gates de validação (controladoria e sponsor). 2026-09-04.

## Owners (resumo)

Sponsor e aprovadora funcional: Ana Martins (Diretora Comercial). Validador dos cálculos: Bruno Lima (Controladoria). Owner técnico: consultor Aucta responsável pelo projeto. Detalhe em OWNERS.md.

## Mapa de navegação

| Artefato | Onde | O que contém |
| --- | --- | --- |
| TRUTHS.md | raiz | Fatos e regras vigentes |
| GLOSSARY.md | raiz | Vocabulário canônico |
| ACCEPTANCE.md | raiz | Aceite, definição de pronto e estratégia de provas |
| OWNERS.md | raiz | Papéis e responsáveis |
| DATA_CATALOG.md | .project/ | Fontes de dados |
| init-state.md | .project/ | Estado do /init, premissas, blockers e exceções formais |
| KNOWN_ISSUES.md | .project/ | Limitações conhecidas ainda relevantes |
| Plano da feature | docs/planos/ | Plano visual faseado de cada mudança |
| Runbook do diagnóstico | docs/runbook/diagnostico-fonte.md | Como o analista roda o diagnóstico da base do mês |
