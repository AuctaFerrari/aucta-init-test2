# Changelog

## [0.1.0] — em desenvolvimento

- **Base tratada oficial** (`src/base_tratada.py`): comando único que aplica as regras aprovadas de tratamento (TRUTH-011..020) sobre a base operacional do mês e produz a base tratada de pedidos com o cliente cruzado, as visitas classificadas, as exceções separadas em excluídos por regra e retidos em quarentena, o log de transformação por transformação, a reconciliação origem × saída com diferença R$ 0,00 e o relatório legível pela controladoria com veredito de publicação por competência. Não calcula indicador de negócio, não imputa valor, não consome parâmetro econômico e não altera o arquivo de origem.
- Golden do tratamento materializado antes da implementação: `tests/fixtures/golden_base_tratada.csv` (BT-01..24, destino esperado linha a linha), `golden_reconciliacao.csv` (RC-01..09, conservação) e `golden_veredito_competencia.csv` (VC-01..03, veredito de segurança por mês).
- Harness de conferência ganha as suites 5 (base tratada, com recomputação independente e golden congelado), 6 (mesmo resultado pelo caminho `.xlsx`) e 7 (insumos de GC-01..03 deriváveis da base tratada, com a conta feita na suite e nunca em `src/`). A suite 4 deixa de ser a suite de margens e passa a ser o inventário de módulos de `src/` com categoria declarada, agora com varredura recursiva.
- Diagnóstico de qualidade da fonte (`src/diagnostico_fonte.py`): comando único, observacional e determinístico, que lê a base operacional do mês (Excel ou pasta de CSVs) e gera relatório de esquema, contagens, faltantes, duplicidades, chaves sem correspondência, contradições e avisos de fonte. Não trata dados e não calcula indicador.
- Harness de conferência (`tests/golden/run_golden.py`): suite do diagnóstico com recomputação independente; suite do caminho `.xlsx` gerando a fixture Excel a partir das CSVs versionadas e exigindo resultado idêntico ao caminho CSV.
- `requirements.txt`: dependência de leitura Excel com versão fixa e hash verificado, instalada pelo CI.
- Relatório separa achados que exigem atenção (`D-###`) de perfil/inventário da fonte (`P-###`), com contadores independentes.
- Projeto criado a partir do template aucta-template-projeto.
