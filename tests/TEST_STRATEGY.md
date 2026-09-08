# Estratégia de testes — Aucta Foods · Rentabilidade por Cliente (tier 2)

Materializa o bloco K de ACCEPTANCE.md. Princípio permanente: **toda suite recomputa a referência por implementação INDEPENDENTE do código sob teste**, a partir de `tests/fixtures/*.csv`. Valor esperado nunca é gerado pelo pipeline que ele verifica.

## Política decimal e de arredondamento (DN-09, aprovada)

- Aritmética **decimal**, nunca ponto flutuante binário, em todo cálculo monetário de negócio.
- **Precisão integral** nos cálculos intermediários.
- Arredondamento **somente** no resultado final por cliente/mês e nos totais de reconciliação: **duas casas decimais**, política **`ROUND_HALF_UP`**.
- Contagens permanecem inteiras.
- **Tolerância absoluta R$ 0,00** para os golden sintéticos, aplicada **após** essa política. Aprovada por Bruno Lima em 2026-09-08 (Issue #10, issuecomment-5589411324).

## Golden de margem (`tests/fixtures/golden_cases.csv`)

| Caso | Cliente/Mês | Margem de servir esperada |
| --- | --- | --- |
| GC-01 | C001 / jan-2026 | R$ 330,00 |
| GC-02 | C002 / jan-2026 | R$ 120,00 |
| GC-03 | C003 / jan-2026 | R$ 400,00 |

Colunas intermediárias (receita líquida, MC, custos) também são conferidas — o caso falha em qualquer etapa divergente, não só no total. Os três valores embutem os parâmetros de `.project/PARAMETERS.md` (R$ 100,00/visita válida e R$ 20,00/pedido válido) e dependem de TRUTH-011 (versão vigente de O006) e TRUTH-015/DN-11 (normalização de O004): mudar qualquer um deles muda GC-01..03.

## Golden do tratamento (`tests/fixtures/golden/base-tratada/`)

Materializados **antes** da implementação, por derivação independente one-off fora do repositório, a partir do texto das regras aprovadas. Três arquivos:

- `populacao.csv` — destino esperado de cada linha de Vendas e Visitas, por cenário: `base_tratada`, `excluido_regra`, `quarentena`, `fora_do_periodo`, `valida`, `nao_realizada`, `excecao_reportada`; com regra, sinal de bloqueio, escopo do bloqueio e marcas.
- `reconciliacao.csv` — conservação por bloco e campo, em **cinco populações**: origem = tratada + excluída + quarentena + fora do período. Diferença esperada R$ 0,00.
- `veredito.csv` — veredito por competência: `publicavel`, `bloqueada` ou `falha_execucao`, com escopo e motivo.

Cenários cobertos:

| Cenário | Natureza | Regra exercitada |
| --- | --- | --- |
| BASE | fixture atual | fluxo completo com as exceções conhecidas EX-01..07 |
| A1 | adversarial | DN-08 — registro fora do período, excluído da saída oficial, reconciliado à parte, não bloqueante |
| A2 | adversarial | DN-11 — colisão de identificador delimitável: quarentena dos afetados, bloqueio das competências |
| A3 | adversarial | DN-04 — empate de `atualizado_em`: todas as versões em quarentena, competência bloqueada |
| A4 | adversarial | DN-07 + TRUTH-014 (I-01) — visita órfã sem data usável: dois defeitos reportados, período inteiro bloqueado |
| A5 | adversarial | DN-13 + DN-11 — competência inutilizável e colisão não delimitável: falha controlada de execução |

As entradas adversariais vivem em `tests/fixtures/adversarial/<cenario>/`, como sobreposições das tabelas alteradas. As **cinco fixtures de origem são imutáveis** e não são tocadas por nenhum cenário.

## Exceções esperadas (`tests/fixtures/expected_exceptions.csv`)

EX-01..07: dedupe O006 (fica custo 260), exclusão O005, normalização `" c003 "`, órfão O010/C999, nulos O008/O009, visita V008 sem data. **EX-04, EX-05 e EX-06 bloqueiam a competência afetada** (fev/2026), não o relatório inteiro — escopo de DN-10.

## Harness (`tests/golden/run_golden.py`)

Estado atual do ramo, herdado do ciclo 1, com quatro suites e **46 verificações** na `main`:

**Suite 1 — Diagnóstico da fonte (observacional).** Recomputa contagens, vazios, duplicados e chaves sem correspondência; confere cobertura de EX-01..07; prova que nada foi tratado; determinismo e integridade da origem; nenhum campo de indicador na saída.

**Suite 2 — Caminho `.xlsx`.** Gera a fixture Excel a partir das CSVs versionadas, roda o mesmo entrypoint e exige resultado idêntico ao caminho CSV, com o arquivo intocado. Dependência declarada em `requirements.txt` com hash verificado; sem ela a suite reprova.

**Suite 3 — Textos de apresentação em pt-BR** e decisões pendentes consolidadas.

**Suite 4 — Margens / golden cases: PENDENTE.** Não implementada enquanto não existir módulo de cálculo. A suite **falha de propósito** se aparecer em `src/` qualquer módulo fora da lista observacional declarada no harness. Essa guarda é **lista de nomes de arquivo, não verificação de comportamento** — limitação registrada em `.project/KNOWN_ISSUES.md` (KI-001); o gate real do trabalho que produz número é o `/change-number`.

**A ser construído na fase 2**, sem enfraquecer nenhuma guarda existente: suites do tratamento comparando a saída com `populacao.csv`, `reconciliacao.csv` e `veredito.csv` por recomputação independente; suite do caminho `.xlsx` para o tratamento; suite de derivabilidade dos insumos de GC-01..03 a partir da base tratada, com a conta feita na suite e nunca em `src/`; e as provas negativas de cada regra.

## Demais camadas

- Smoke/E2E: execução ponta a ponta sobre a fixture (Excel → base tratada → Excel analítico + PDF, conforme o ciclo).
- Testes de dados: casos duplicados, órfãos, nulos, colisão, empate e fora do período produzem o destino e o escopo de bloqueio esperados.
- Aceite: ACC-001..007 (ver ACCEPTANCE.md).
