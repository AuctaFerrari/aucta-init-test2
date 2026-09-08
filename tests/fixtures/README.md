# Fixtures sintéticas — Base Operacional (piloto jan–mar/2026)

Extraídas 1:1 do `01_Base_Operacional_Sintetica.xlsx` (uma CSV por aba) em 2026-09-02. São a massa oficial de teste e conferência do projeto — 100% sintética (TRUTH-006: dados reais nunca entram no Git).

O arquivo Excel original permanece na pasta conectada do consultor (fonte oficial de entrada da solução); estas CSVs existem para versionar a massa e alimentar a conferência automática e os golden cases.

| Arquivo | Aba de origem |
| --- | --- |
| clientes.csv | Clientes |
| vendas.csv | Vendas |
| custos_logisticos.csv | Custos_Logisticos |
| visitas.csv | Visitas |
| parametros.csv | Parametros |

As armadilhas de qualidade da massa (duplicidade O006, ID sujo " c003 ", órfão C999, nulos, cancelado, inconsistência V008) são intencionais — ver `.project/DATA_CATALOG.md`.

## Valores esperados (golden)

Nenhum arquivo desta seção é gerado pelo código sob teste. Todos existem **antes** da implementação que verificam.

| Arquivo | Casos | O que congela | Procedência |
| --- | --- | --- | --- |
| golden_cases.csv | GC-01..03 | Margens esperadas por cliente e mês, tolerância R$ 0,00 | Fornecidos no briefing e conferidos por recomputação manual independente em 2026-09-03 |
| expected_exceptions.csv | EX-01..07 | Tratamento esperado de cada armadilha e quais bloqueiam publicação | Regras fornecidas pelo consultor na revisão da iniciação em 2026-09-03 |
| golden_base_tratada.csv | BT-01..24 | Destino de cada linha de Vendas e Visitas: base tratada, excluído por regra, quarentena, válida, não realizada ou exceção reportada — com motivo, regra e sinal de bloqueio | Recomputação independente por script one-off, fora do pipeline, em 2026-09-08 |
| golden_reconciliacao.csv | RC-01..09 | Conservação por bloco e campo: origem = base tratada + excluído + quarentena | Recomputação independente, 2026-09-08 |
| golden_veredito_competencia.csv | VC-01..03 | Veredito de segurança de cálculo por competência do piloto | Recomputação independente, 2026-09-08 |

Validação registrada: Bruno Lima (Controladoria) em 2026-09-08, com o papel delegado a Caio Ferrari na sessão de teste — limitação declarada na Issue #10 e em `ACCEPTANCE.md`. Alterar qualquer valor esperado destes arquivos é mudança de resultado (tier 2): exige `/change-number`, com fonte registrada e aprovação do dono do número antes do merge.
