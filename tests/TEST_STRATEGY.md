# Estratégia de testes — Aucta Foods · Rentabilidade por Cliente (tier 2)

Materializa o bloco K de ACCEPTANCE.md. Golden cases fornecidos pelo consultor no briefing e conferidos por **recomputação manual independente** (2026-09-03) — nunca pelo pipeline que será desenvolvido.

## Golden cases (tests/fixtures/golden_cases.csv)

| Caso | Cliente/Mês | Margem de servir esperada |
| --- | --- | --- |
| GC-01 | C001 / jan-2026 | R$ 330 |
| GC-02 | C002 / jan-2026 | R$ 120 |
| GC-03 | C003 / jan-2026 | R$ 400 |

Colunas intermediárias (receita líquida, MC, custos) também são conferidas — o caso falha em qualquer etapa divergente, não só no total.

**Tolerância:** R$ 0,00 (valores 100% deriváveis das fórmulas TRUTH-001..005 sobre a massa sintética). Aprovação formal da tolerância e dos casos: Bruno Lima (Controladoria) — **pendente**; gate antes do merge do primeiro /change-number.

## Exceções esperadas (tests/fixtures/expected_exceptions.csv)

EX-01..07: dedupe O006 (fica custo 260), exclusão O005, normalização " c003 ", órfão O010/C999, nulos O008/O009, visita V008 sem data. **EX-04, EX-05 e EX-06 bloqueiam a publicação do relatório** enquanto não tratadas.

## Harness (tests/golden/run_golden.py — criado em 2026-09-04, com o primeiro código)

Princípio permanente: toda suite recomputa a referência por implementação INDEPENDENTE do código sob teste, a partir de `tests/fixtures/*.csv`.

**Suite 1 — Diagnóstico da fonte (observacional) — IMPLEMENTADA.** Recomputa contagens por tabela, vazios por coluna, identificadores duplicados e chaves sem correspondência; confere que cada exceção conhecida (EX-01..07) aparece nos achados; prova que nada foi tratado (13 registros de vendas lidos, duplicata O006 preservada); confere determinismo (duas execuções, bytes idênticos) e integridade da origem (SHA-256 antes/depois); confere que nenhum campo de indicador de negócio existe na saída.

**Suite 2 — Margens / golden cases (GC-01..03) — PENDENTE.** Não implementada enquanto não existir módulo de cálculo: as fórmulas TRUTH-001..005 aguardam validação formal da controladoria (gate do primeiro `/change-number`). A suite **falha de propósito** se aparecer em `src/` qualquer módulo fora da lista observacional declarada no harness — o gate de tier 2 não pode ser atravessado sem golden. Quando implementada, deve cobrir:

1. Comparação com golden_cases.csv (tolerância R$ 0,00) e com a saída do pipeline.
2. Log de tratamento cobrindo TODAS as linhas de expected_exceptions.csv, com EX-04..06 travando a publicação.
3. Reconciliação (ACC-006): totais válidos da origem × processados = diferença zero após exclusões documentadas.

O CI (`.github/ci/run-checks.sh`, guarda 4) passa a EXIGIR o harness assim que `src/` existir. Golden rodam before/after em todo /change-number; refatoração do motor re-roda os golden do critério vigente no mesmo ciclo.

## Demais camadas

- Smoke/E2E: execução ponta a ponta sobre a fixture (Excel → Excel analítico + PDF).
- Testes de dados: casos duplicados/órfãos/nulos produzem o log esperado.
- Aceite: ACC-001..006 (ver ACCEPTANCE.md).
