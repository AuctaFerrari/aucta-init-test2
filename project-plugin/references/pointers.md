# Ponteiros canônicos — Aucta Foods · Rentabilidade por Cliente

Ordem de leitura na abertura de sessão (6.5): PROJECT.md + TRUTHS.md + Issue/Spec ativa — nada mais por padrão.

| Artefato | Caminho | Propósito |
| --- | --- | --- |
| PROJECT.md | `/PROJECT.md` | Objetivo, escopo, tier 2, arquitetura, mapa |
| TRUTHS.md | `/TRUTHS.md` | Fórmulas e regras vigentes (TRUTH-001..015). Não duplica decisões nem parâmetros |
| DECISIONS.md | `/.project/DECISIONS.md` | **DN-01..DN-13** — regras operacionais aprovadas pelo dono do número, ordem de avaliação, esclarecimentos I-01..I-04, definição de `GATE-CN-01`, mapeamento dos identificadores DEC antigos |
| PARAMETERS.md | `/.project/PARAMETERS.md` | Índice canônico de parâmetros (D11): valor, unidade, fonte, owner, status, escopo, vigência e regra para valor ausente ou expirado. Nenhum cálculo pode usar parâmetro que não esteja aqui |
| GLOSSARY.md | `/GLOSSARY.md` | Termos do cliente (margem de servir, clientes-alerta…) |
| ACCEPTANCE.md | `/ACCEPTANCE.md` | ACC-001..007, registro de aprovação dos golden e da tolerância, definição de pronto |
| OWNERS.md | `/OWNERS.md` | Ana Martins (sponsor) · Bruno Lima (valida número) · consultor (técnico) |
| DATA_CATALOG.md | `/.project/DATA_CATALOG.md` | Fonte única + armadilhas de qualidade mapeadas |
| Known issues | `/.project/KNOWN_ISSUES.md` | KI-001 — guarda de módulos por nome de arquivo |
| Estado do /init | `/.project/init-state.md` | Progresso, premissas, blockers, `GATE-CN-01`, exceções formais EF-002 a EF-004 |
| Plano aprovado do ciclo | `/docs/planos/base-tratada-oficial.md` | Plano Visual Faseado de **sete fases**, aprovado prospectivamente em 2026-09-08. Fases 1 a 3 concluídas; fases 4 a 7 não iniciadas |
| Fixtures de origem | `/tests/fixtures/*.csv` | Massa sintética oficial (jan–mar/2026) — **imutáveis**, inclusive `parametros.csv` com o status observado da fonte |
| Golden cases de margem | `/tests/fixtures/golden_cases.csv` | GC-01..03 — margens esperadas, tolerância R$ 0,00, aprovados em 2026-09-08 |
| Exceções esperadas | `/tests/fixtures/expected_exceptions.csv` | EX-01..07 — tratamento e escopo do bloqueio |
| Golden do tratamento | `/tests/fixtures/golden/base-tratada/` | `populacao.csv` (147 casos), `reconciliacao.csv` (54 casos, diferença 0,00), `veredito.csv` (18 casos) e `README.md` com procedência. Cenários BASE e A1–A5 |
| Entradas adversariais | `/tests/fixtures/adversarial/<cenario>/` | Sobreposições de tabela por cenário (A1..A6); as demais tabelas são as fixtures de origem |
| Estratégia de testes | `/tests/TEST_STRATEGY.md` | Política decimal DN-09, tolerância, harness, camadas, cenários |
| Harness golden | `/tests/golden/run_golden.py` | Suites 1 a 4; a suite 4 confere o inventário de módulos. Exigido pelo CI sempre que `src/` existir |
| Inventário de módulos | `/project-plugin/references/modulos.json` | Registro no nível do projeto: caminho, categoria, decisão aprovada, golden e suite de cada módulo de `src/`. Módulo não registrado reprova a guarda 4; categoria de cálculo nunca é autorizada por este arquivo |
| Módulo da fase 2 | `/src/identificadores.py` | Normalização de identificador e colisão (DN-11, DN-13) |
| Conferência da fase 2 | `/tests/golden/run_fase2.py` | 7 suites; guarda 4b do CI |
| Módulo da fase 3 | `/src/versao_pedido.py` | Versão que vale de cada pedido (TRUTH-011, DN-04, DN-14) |
| Conferência da fase 3 | `/tests/golden/run_fase3.py` | 7 suites; guarda 4c do CI |
| Golden da fase 3 | `/tests/fixtures/golden/fase3/` | `versao_pedido.csv`, `conservacao.csv`, `veredito.csv` e `README.md` com procedência. Cenários BASE, A3 e A6 |
| Entrada adversarial A6 | `/tests/fixtures/adversarial/A6/` | Grupo duplicado com `atualizado_em` inutilizável — cobre DN-14 |
| CI harness | `/.github/ci/run-checks.sh` | Guardas: artefatos, dados fora de fixtures, sintaxe, dependências, golden |

## Aprovações válidas na Issue #10

| Conteúdo | URL |
| --- | --- |
| DN-01..DN-12, fórmulas TRUTH-001..005, regras TRUTH-011..015, EX-01..07, GC-01..03, tolerância R$ 0,00 | https://github.com/AuctaFerrari/aucta-init-test2/issues/10#issuecomment-5589411324 |
| DN-13, ordem de avaliação, comportamento do cenário A5, taxonomia | https://github.com/AuctaFerrari/aucta-init-test2/issues/10#issuecomment-5589595626 |
| Aceitação do texto canônico de A4 e da estrutura de 13 commits | https://github.com/AuctaFerrari/aucta-init-test2/issues/10#issuecomment-5589855363 |
| **DN-14** — timestamp inutilizável em grupo duplicado; refechamento do `GATE-CN-01` | https://github.com/AuctaFerrari/aucta-init-test2/issues/10#issuecomment-5590561870 |
| Invalidação da aprovação anterior — **sem efeito**, preservada como evidência | https://github.com/AuctaFerrari/aucta-init-test2/issues/10#issuecomment-5589236253 |

Aprovação de negócio exige: aprovador nomeado em `OWNERS.md` (ou papel fictício **explicitamente ativado**, item a item, neste teste sintético), registro individual por item, e distinção entre verificação técnica e aprovação funcional. Linguagem agrupada, silêncio, "assuma", aprovação de plano e revisão de PR **não** constituem aprovação de negócio.

## Demandas abertas no `aucta-dev-core`

| Demanda | Situação |
| --- | --- |
| Guarda de módulos de cálculo por nome de arquivo (KI-001) | issue **#27**, aberta |
| Gate de aprovação aceita artefato sem validar autoridade e procedência (EF-003) | issue **#28**, aberta — https://github.com/AuctaFerrari/aucta-dev-core/issues/28 |
| Conferência de bytes/hash de artefato rematerializado | rascunho, **não publicada** |

## Ramo contaminado — nunca como fonte de implementação

`feat/base-tratada-oficial`, head **`5c02e59`**: preservado **exclusivamente como evidência forense** da EF-003. Não é retroativamente conforme, é inelegível para PR e merge, e **não pode ser lido, copiado, diferenciado, cherry-picked, importado ou adaptado** como fonte de código, harness ou golden. As TRUTH-016..020 gravadas nele não são decisões aprovadas.

Ramo de trabalho da recuperação: `feat/base-tratada-oficial-clean`, a partir da `main` em `a1a0390`.

## Módulos-sentinela Muda-numero (camada a do D4)

Qualquer diff que toque: `src/`, `tests/fixtures/parametros.csv`, `tests/fixtures/golden_cases.csv`, `tests/fixtures/expected_exceptions.csv`, `tests/fixtures/golden/base-tratada/*`, `tests/fixtures/golden/fase3/*`, `tests/fixtures/adversarial/*`, aba Parametros da base, `tests/golden/`, `project-plugin/references/modulos.json`, `.project/PARAMETERS.md`, `.project/DECISIONS.md`, ou as TRUTHS 001..005/008/011..015 → pergunta Muda-numero obrigatória no /pre-pr.
