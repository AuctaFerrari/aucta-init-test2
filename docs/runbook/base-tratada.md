# Runbook — base tratada oficial

## Pré-requisitos

- Python 3 instalado no computador do analista.
- Dependências instaladas em ambiente virtual a partir de `requirements.txt`.
- Arquivo Excel com as cinco abas previstas no catálogo, ou pasta com as cinco CSVs equivalentes.
- Período informado no formato `AAAA-MM:AAAA-MM`.

## Comando

```bash
python src/relatorio_tratamento.py \
  --entrada caminho/para/base.xlsx \
  --saida outputs/base-tratada \
  --rotulo 2026-01a03 \
  --periodo 2026-01:2026-03
```

## Saídas

Uma execução válida produz:

- `base_tratada_pedidos.csv`
- `base_tratada_visitas.csv`
- `excecoes.csv`
- `log_tratamento.csv`
- `reconciliacao.csv`
- `tratamento_<rotulo>.md`
- `tratamento_<rotulo>.json`

Quando a competência não pode ser delimitada com segurança, o comando retorna
exit code `5`, grava somente o JSON mínimo de auditoria e não produz saída
oficial.

## Conferência pelo analista

1. Verifique no relatório o veredito de cada competência.
2. Confirme que toda linha da reconciliação está com `situacao = ok` e diferença zero.
3. Entregue para o ciclo de cálculo apenas competências com veredito `publicavel`.
4. Corrija a origem dos registros em quarentena e execute novamente; não edite a saída manualmente.

O comando não calcula margem, ranking ou recomendação e nunca altera o arquivo de entrada.
