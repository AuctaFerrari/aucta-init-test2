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
