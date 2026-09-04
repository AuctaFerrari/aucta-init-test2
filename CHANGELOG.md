# Changelog

## [0.1.0] — em desenvolvimento

- Diagnóstico de qualidade da fonte (`src/diagnostico_fonte.py`): comando único, observacional e determinístico, que lê a base operacional do mês (Excel ou pasta de CSVs) e gera relatório de esquema, contagens, faltantes, duplicidades, chaves sem correspondência, contradições e avisos de fonte. Não trata dados e não calcula indicador.
- Harness de conferência (`tests/golden/run_golden.py`): suite do diagnóstico com recomputação independente; suite de margens declarada pendente até a validação da controladoria.
- Projeto criado a partir do template aucta-template-projeto.
