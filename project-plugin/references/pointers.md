# Ponteiros canônicos — Aucta Foods · Rentabilidade por Cliente

Ordem de leitura na abertura de sessão (6.5): PROJECT.md + TRUTHS.md + Issue/Spec ativa — nada mais por padrão.

| Artefato | Caminho | Propósito |
| --- | --- | --- |
| PROJECT.md | `/PROJECT.md` | Objetivo, escopo, tier 2, arquitetura, mapa |
| TRUTHS.md | `/TRUTHS.md` | Fórmulas e regras vigentes (TRUTH-001..015, incl. regras de tratamento) |
| GLOSSARY.md | `/GLOSSARY.md` | Termos do cliente (margem de servir, clientes-alerta…) |
| ACCEPTANCE.md | `/ACCEPTANCE.md` | ACC-001..007, definição de pronto, estratégia de provas |
| OWNERS.md | `/OWNERS.md` | Ana Martins (sponsor) · Bruno Lima (valida número) · consultor (técnico) |
| DATA_CATALOG.md | `/.project/DATA_CATALOG.md` | Fonte única + armadilhas de qualidade mapeadas |
| Estado do /init | `/.project/init-state.md` | Progresso, premissas, blockers |
| Fixtures | `/tests/fixtures/*.csv` | Massa sintética oficial (jan–mar/2026) |
| Golden cases | `/tests/fixtures/golden_cases.csv` | GC-01..03 — margens esperadas, tolerância R$ 0,00 |
| Exceções esperadas | `/tests/fixtures/expected_exceptions.csv` | EX-01..07 — tratamento e bloqueios de publicação |
| Estratégia de testes | `/tests/TEST_STRATEGY.md` | Golden, tolerância, harness, camadas |
| Harness golden | `/tests/golden/run_golden.py` | A criar com o primeiro código — CI passa a exigir quando `src/` existir |
| CI harness | `/.github/ci/run-checks.sh` | Guardas: artefatos, dados fora de fixtures, sintaxe, golden |

## Módulos-sentinela Muda-numero (camada a do D4)

Qualquer diff que toque: `src/` (cálculo/tratamento quando existir), `tests/fixtures/parametros.csv`, `tests/fixtures/golden_cases.csv`, `tests/fixtures/expected_exceptions.csv`, aba Parametros da base, `tests/golden/`, ou as TRUTHS 001..005/008/011..015 → pergunta Muda-numero obrigatória no /pre-pr.
