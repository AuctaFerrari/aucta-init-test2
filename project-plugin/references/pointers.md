# Ponteiros canônicos — Aucta Foods · Rentabilidade por Cliente

Ordem de leitura na abertura de sessão (6.5): PROJECT.md + TRUTHS.md + Issue/Spec ativa — nada mais por padrão.

| Artefato | Caminho | Propósito |
| --- | --- | --- |
| PROJECT.md | `/PROJECT.md` | Objetivo, escopo, tier 2, arquitetura, mapa |
| TRUTHS.md | `/TRUTHS.md` | Fórmulas e regras vigentes (TRUTH-001..020, incl. regras de tratamento e composição da base tratada) |
| GLOSSARY.md | `/GLOSSARY.md` | Termos do cliente (margem de servir, clientes-alerta…) |
| ACCEPTANCE.md | `/ACCEPTANCE.md` | ACC-001..007, registro de validação da tolerância, definição de pronto |
| OWNERS.md | `/OWNERS.md` | Ana Martins (sponsor) · Bruno Lima (valida número) · consultor (técnico) |
| DATA_CATALOG.md | `/.project/DATA_CATALOG.md` | Fonte única + armadilhas de qualidade mapeadas |
| Known issues | `/.project/KNOWN_ISSUES.md` | KI-001 (guarda de módulos) · KI-002 (competência fora do período) |
| Estado do /init | `/.project/init-state.md` | Progresso, premissas, blockers |
| Fixtures | `/tests/fixtures/*.csv` | Massa sintética oficial (jan–mar/2026) |
| Golden cases | `/tests/fixtures/golden_cases.csv` | GC-01..03 — margens esperadas, tolerância R$ 0,00 |
| Exceções esperadas | `/tests/fixtures/expected_exceptions.csv` | EX-01..07 — tratamento e bloqueios de publicação |
| Golden da base tratada | `/tests/fixtures/golden_base_tratada.csv` | BT-01..24 — destino esperado de cada linha de Vendas e Visitas |
| Golden da reconciliação | `/tests/fixtures/golden_reconciliacao.csv` | RC-01..09 — conservação por bloco e campo |
| Golden do veredito | `/tests/fixtures/golden_veredito_competencia.csv` | VC-01..03 — segurança de cálculo por competência |
| Estratégia de testes | `/tests/TEST_STRATEGY.md` | Golden, tolerância, harness, camadas |
| Harness golden | `/tests/golden/run_golden.py` | Suites 1–7; CI exige verde sempre que `src/` existir |
| CI harness | `/.github/ci/run-checks.sh` | Guardas: artefatos, dados fora de fixtures, sintaxe, dependências, golden |
| Plano do ciclo | `/docs/planos/base-tratada-oficial.md` | Plano Visual Faseado aprovado da base tratada |

## Módulos de `src/` e a sua categoria

| Módulo | Categoria | O que pode fazer |
| --- | --- | --- |
| `diagnostico_fonte.py` | observacional | Descreve a fonte. Não trata, não corrige, não calcula. |
| `base_tratada.py` | tratamento | Aplica regra aprovada, separa exceção, registra transformação. Todo valor de saída é cópia da fonte. Não calcula indicador nem consome parâmetro econômico. |
| — | cálculo | **Nenhum permitido** enquanto TRUTH-001..005 seguirem preliminares. Entra somente por `/change-number`, com validação formal da controladoria. |

Módulo novo em `src/` reprova a suite 4 do harness até ser declarado aqui e no inventário do harness, com a categoria.

## Módulos-sentinela Muda-numero (camada a do D4)

Qualquer diff que toque: `src/`, `tests/fixtures/parametros.csv`, `tests/fixtures/golden_cases.csv`, `tests/fixtures/expected_exceptions.csv`, `tests/fixtures/golden_base_tratada.csv`, `tests/fixtures/golden_reconciliacao.csv`, `tests/fixtures/golden_veredito_competencia.csv`, aba Parametros da base, `tests/golden/`, ou as TRUTHS 001..005/008/011..020 → pergunta Muda-numero obrigatória no /pre-pr.
