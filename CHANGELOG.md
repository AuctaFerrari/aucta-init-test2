# Changelog

## [0.1.0] — em desenvolvimento

- Diagnóstico de qualidade da fonte (`src/diagnostico_fonte.py`): comando único, observacional e determinístico, que lê a base operacional do mês (Excel ou pasta de CSVs) e gera relatório de esquema, contagens, faltantes, duplicidades, chaves sem correspondência, contradições e avisos de fonte. Não trata dados e não calcula indicador.
- Harness de conferência (`tests/golden/run_golden.py`): suite do diagnóstico com recomputação independente; suite do caminho `.xlsx` gerando a fixture Excel a partir das CSVs versionadas e exigindo resultado idêntico ao caminho CSV; suite de margens declarada pendente até a validação da controladoria.
- `requirements.txt`: dependência de leitura Excel com versão fixa e hash verificado, instalada pelo CI.
- Relatório separa achados que exigem atenção (`D-###`) de perfil/inventário da fonte (`P-###`), com contadores independentes.
- Projeto criado a partir do template aucta-template-projeto.
