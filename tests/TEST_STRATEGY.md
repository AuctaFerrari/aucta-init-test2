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

**Suite 1 — Diagnóstico da fonte (observacional) — IMPLEMENTADA.** Recomputa contagens por tabela, vazios por coluna, identificadores duplicados e chaves sem correspondência; confere que cada exceção conhecida (EX-01..07) aparece na saída; prova que nada foi tratado (13 registros de vendas lidos, duplicata O006 preservada); confere determinismo (duas execuções, bytes idênticos) e integridade da origem (SHA-256 antes/depois); confere que nenhum campo de indicador de negócio existe na saída e que a separação atenção/perfil está correta (contadores independentes, prefixos D-/P-).

**Suite 2 — Caminho `.xlsx` (entrada principal de produção) — IMPLEMENTADA.** Gera a fixture `.xlsx` durante o teste a partir das CSVs versionadas (uma aba por arquivo, mesma ordem), executa o **mesmo entrypoint de produção** sobre ela e exige resultado idêntico ao caminho CSV: contagens, achados de atenção, itens de perfil, relacionamentos, esquema e perfis de coluna. Confere também que o `.xlsx` não é alterado pela leitura (SHA-256 antes/depois) e que duas execuções sobre o mesmo arquivo produzem bytes idênticos. Os bytes do `.xlsx` gerado variam entre execuções (o formato é um zip com metadados de tempo), por isso a comparação é de **conteúdo do diagnóstico**, nunca de hash do arquivo. A dependência de leitura está declarada em `requirements.txt` com versão fixa e hash verificado (`openpyxl==3.1.5`), instalada pelo CI na guarda 3b com `--require-hashes`; **sem ela a suite reprova** — ausência de dependência não vira teste silenciosamente pulado.

**Suite 3 — Margens / golden cases (GC-01..03) — PENDENTE.** Não implementada enquanto não existir módulo de cálculo: as fórmulas TRUTH-001..005 aguardam validação formal da controladoria (gate do primeiro `/change-number`). A suite **falha de propósito** se aparecer em `src/` qualquer módulo fora da lista observacional declarada no harness. Quando implementada, deve cobrir:

1. Comparação com golden_cases.csv (tolerância R$ 0,00) e com a saída do pipeline.
2. Log de tratamento cobrindo TODAS as linhas de expected_exceptions.csv, com EX-04..06 travando a publicação.
3. Reconciliação (ACC-006): totais válidos da origem × processados = diferença zero após exclusões documentadas.

A guarda que reprova módulo fora da lista observacional é **lista de nomes de arquivo, não verificação de comportamento** — limitação registrada em `.project/KNOWN_ISSUES.md` (KI-001); o gate real do trabalho que produz número é o `/change-number`. O CI (`.github/ci/run-checks.sh`, guarda 4) passa a EXIGIR o harness assim que `src/` existir, e a guarda 3b instala as dependências declaradas antes disso. Golden rodam before/after em todo /change-number; refatoração do motor re-roda os golden do critério vigente no mesmo ciclo.

## Demais camadas

- Smoke/E2E: execução ponta a ponta sobre a fixture (Excel → Excel analítico + PDF).
- Testes de dados: casos duplicados/órfãos/nulos produzem o log esperado.
- Aceite: ACC-001..006 (ver ACCEPTANCE.md).
