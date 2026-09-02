# Ponteiros canônicos — Aucta Foods · Rentabilidade por Cliente

Ordem de leitura na abertura de sessão (6.5): PROJECT.md + TRUTHS.md + Issue/Spec ativa — nada mais por padrão.

| Artefato | Caminho | Propósito |
| --- | --- | --- |
| PROJECT.md | `/PROJECT.md` | Objetivo, escopo, tier 2, arquitetura, mapa |
| TRUTHS.md | `/TRUTHS.md` | Fórmulas e regras vigentes (TRUTH-001..010) |
| GLOSSARY.md | `/GLOSSARY.md` | Termos do cliente (margem de servir, clientes-alerta…) |
| ACCEPTANCE.md | `/ACCEPTANCE.md` | ACC-001..006, definição de pronto, estratégia de provas |
| OWNERS.md | `/OWNERS.md` | Ana Martins (sponsor) · Bruno Lima (valida número) · consultor (técnico) |
| DATA_CATALOG.md | `/.project/DATA_CATALOG.md` | Fonte única + armadilhas de qualidade mapeadas |
| Estado do /init | `/.project/init-state.md` | Progresso, premissas, blockers |
| Fixtures | `/tests/fixtures/*.csv` | Massa sintética oficial (jan–mar/2026) |
| Golden cases | `/tests/golden/` | A criar antes do primeiro código de cálculo (tier 2) |
| CI harness | `/.github/ci/run-checks.sh` | Guardas: artefatos, dados fora de fixtures, sintaxe, golden |

## Módulos-sentinela Muda-numero (camada a do D4)

Qualquer diff que toque: `src/` (cálculo/tratamento quando existir), `tests/fixtures/parametros.csv`, aba Parametros da base, `tests/golden/`, ou as TRUTHS 001..005/008 → pergunta Muda-numero obrigatória no /pre-pr.
