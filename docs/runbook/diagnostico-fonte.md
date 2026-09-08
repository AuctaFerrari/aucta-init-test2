# Como rodar o diagnóstico da base do mês

Comando de leitura. Ele **não** altera o arquivo do mês e **não** calcula nenhum número do relatório — só descreve o que a base tem e o que está estranho.

## Passo a passo (Windows)

1. Deixe o arquivo do mês na pasta de sempre (ex.: `C:\Aucta\inputs\01_Base_Operacional.xlsx`).
2. Abra o Prompt de Comando na pasta do programa e rode:

```
python src\diagnostico_fonte.py --entrada C:\Aucta\inputs\01_Base_Operacional.xlsx --rotulo 2026-01 --periodo 2026-01:2026-01
```

3. Abra o relatório gerado em `outputs\diagnostico\diagnostico_2026-01.md`.

## Parâmetros

| Parâmetro | Obrigatório | Para que serve |
| --- | --- | --- |
| `--entrada` | sim | Arquivo `.xlsx` do mês **ou** pasta com uma CSV por aba (é assim que a massa sintética de teste é lida). |
| `--saida` | não | Pasta de saída. Padrão: `outputs/diagnostico` (pasta ignorada pelo Git — dado real nunca sobe). |
| `--rotulo` | não | Nome usado nos arquivos de saída. Use a competência (`2026-01`) para poder comparar meses. |
| `--periodo` | não | Competência esperada (`2026-01:2026-03`). Datas fora da faixa saem como aviso. |

## Como ler o relatório

- **Esquema descoberto** — colunas encontradas em cada base, tipo de cada campo, quantos registros e quantos vazios.
- **Relacionamentos** — quantos registros de uma base não encontram par na outra (pedido sem cliente cadastrado, por exemplo).
- **Achados que exigem atenção** (`D-001`...) — anomalias e avisos, cada um com gravidade, evidência (linha e identificador) e a **decisão pendente do negócio**. É esta a contagem de problemas.
  - `anomalia` — algo que contradiz a estrutura esperada ou impede um cruzamento confiável.
  - `aviso` — algo que merece confirmação antes de virar número.
- **Perfil e inventário da fonte** (`P-001`...) — retrato sem juízo: inventário de status com os ids de cada valor, competências presentes, colunas com vazios possivelmente legítimos. **Não são problemas** e não entram na contagem de achados.
- **Status de evidência** — `observado` (lido diretamente na base) ou `hipótese` (o diagnóstico sugere uma explicação, sem aplicá-la).

## O que fazer com os achados

Os achados **não são regras**. Cada decisão de tratamento (qual versão de um pedido duplicado vale, o que fazer com cancelado, órfão ou campo vazio) muda número entregue à diretoria e entra pelo ciclo de mudança de resultado, com validação da controladoria.

## Dependências

Python 3.9+. A leitura de `.xlsx` usa `openpyxl`, declarado em `requirements.txt` com versão fixa e hash verificado. Instalação reproduzível:

```
python -m pip install --require-hashes -r requirements.txt
```

A leitura de uma pasta de CSVs usa apenas a biblioteca padrão e não depende desse pacote.

## Auditoria

O relatório registra o SHA-256 de cada entrada lida. Mesma entrada produz saída idêntica byte a byte — não há carimbo de data/hora no conteúdo, então dois relatórios diferentes significam entradas diferentes.
