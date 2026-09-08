# Referências esperadas do tratamento — base tratada oficial

> Fase 1 do plano aprovado. **A resposta esperada existe antes do código** e não é produzida pelo programa que ela verifica (D10).

## Procedência

**Derivação:** script one-off independente, executado **fora do repositório**, escrito a partir do **texto das regras aprovadas**, usando apenas `csv` e `Decimal` da biblioteca padrão. Aritmética decimal e arredondamento conforme DN-09.

**Referência de aprovação:** Issue #10 —
[issuecomment-5589411324](https://github.com/AuctaFerrari/aucta-init-test2/issues/10#issuecomment-5589411324) (fórmulas, DN-01..DN-12, TRUTH-011..015, EX-01..07, GC-01..03, tolerância) e
[issuecomment-5589595626](https://github.com/AuctaFerrari/aucta-init-test2/issues/10#issuecomment-5589595626) (DN-13, ordem de avaliação, comportamento de A5, taxonomia).
Regras consolidadas em `.project/DECISIONS.md`.

**Não reaproveitado:** nada foi lido, copiado, diferenciado, cherry-picked, importado ou adaptado do ramo `feat/base-tratada-oficial` (head `5c02e59`) — nem o módulo de tratamento, nem o harness modificado, nem os três arquivos de golden daquele ramo.

**Limitação declarada:** a sessão que produziu esta derivação teve exposição conversacional prévia àquela implementação. Não se reivindica sala limpa. Reivindica-se que a derivação foi reescrita a partir das regras, que nenhum arquivo foi copiado e que a lógica difere em pontos verificáveis — ordem de avaliação, tratamento de registro fora do período e escopo do bloqueio.

**Nenhum campo `validado_por` derivado do comentário inválido** (`issuecomment-5586649630`, sem efeito): a procedência aponta apenas para as aprovações válidas.

## Arquivos

| Arquivo | Conteúdo |
| --- | --- |
| `populacao.csv` | Destino esperado de cada linha de Vendas e Visitas, por cenário: `base_tratada`, `excluido_regra`, `quarentena`, `fora_do_periodo`, `valida`, `nao_realizada`, `excecao_reportada`. Colunas: regra aplicada, sinal de bloqueio, escopo do bloqueio (`competencia`, `periodo_inteiro`) e marcas. 147 casos |
| `reconciliacao.csv` | Conservação por bloco e campo em **cinco populações**: origem = tratada + excluído + quarentena + fora do período. Diferença esperada **0,00** em todas as 54 linhas |
| `veredito.csv` | Veredito por competência: `publicavel`, `bloqueada` ou `falha_execucao`, com escopo e motivo. 18 casos |

Convenção do bloco `visitas` em `reconciliacao.csv`: a coluna `base_tratada` conta as visitas **válidas**, `excluido` conta as **não válidas** (não realizada e exceção reportada) e `quarentena` conta as retidas. A observação da linha registra isso.

## Cenários

| Cenário | Natureza | Regra exercitada | Entradas |
| --- | --- | --- | --- |
| **BASE** | **comportamento da fixture atual** | fluxo completo com EX-01..07 | as cinco fixtures de origem, sem sobreposição |
| **A1** | adversarial | **DN-08** — registro fora do período: excluído da saída oficial, reconciliado à parte, **não bloqueante** | `adversarial/A1/` (vendas, custos) — pedido O013 em 2025-12 |
| **A2** | adversarial | **DN-11 delimitável** — colisão de identificador: quarentena dos afetados, bloqueio das competências determináveis | `adversarial/A2/clientes.csv` — linha `" c001 "` colide com C001 |
| **A3** | adversarial | **DN-04** — empate no `atualizado_em` mais recente: todas as versões em quarentena, competência bloqueada | `adversarial/A3/vendas.csv` — duas versões de O006 com o mesmo timestamp |
| **A4** | adversarial | **DN-07 + TRUTH-014 (I-01)** — visita órfã sem data usável: dois defeitos reportados, **período inteiro** bloqueado | `adversarial/A4/visitas.csv` — V012, cliente C999, sem datas |
| **A5** | adversarial | **DN-13 + DN-11 não delimitável** — competência inutilizável e colisão: **falha controlada de execução** | `adversarial/A5/` (clientes, vendas, custos) — O014 sem `data_pedido` |

Cada cenário adversarial substitui **apenas** as tabelas listadas; as demais são as fixtures de origem. **As cinco fixtures de origem são imutáveis** e nenhum cenário as altera.

## Resultados esperados, por cenário

| Cenário | Pedidos: tratados / excluídos / quarentena / fora do período | Visitas válidas | Veredito jan / fev / mar |
| --- | --- | --- | --- |
| BASE | 8 / 2 / 3 / 0 | 9 | publicável / **bloqueada** / publicável |
| A1 | 8 / 2 / 3 / **1** | 9 | publicável / bloqueada / publicável |
| A2 | 5 / 2 / **6** / 0 | 6 | **bloqueada / bloqueada / bloqueada** |
| A3 | 7 / 1 / **5** / 0 | 9 | **bloqueada** / bloqueada / publicável |
| A4 | 8 / 2 / 3 / 0 (+1 visita em quarentena) | 9 | **bloqueada / bloqueada / bloqueada** (`periodo_inteiro`) |
| A5 | 5 / 2 / **7** / 0 | 6 | **falha_execucao** nas três |

Reconciliação monetária de referência, campo `receita_bruta`: BASE 11.950,00 = 7.950,00 + 2.000,00 + 2.000,00 + 0,00 · A1 12.250,00 = 7.950,00 + 2.000,00 + 2.000,00 + 300,00 · A2 11.950,00 = 5.250,00 + 2.000,00 + 4.700,00 + 0,00 · A3 11.950,00 = 7.450,00 + 1.500,00 + 3.000,00 + 0,00 · A5 12.150,00 = 5.250,00 + 2.000,00 + 4.900,00 + 0,00. **Diferença 0,00 em todos.**

## Comportamento esperado do A5, em detalhe

DN-13 bloqueia o período solicitado porque a competência de O014 está ausente. DN-11 permanece mais estrita porque o impacto da colisão sobre um registro sem competência não pode ser delimitado. Consequências exigidas na implementação:

- a execução retorna **resultado diferente de zero, controlado**;
- produz um **artefato mínimo auditável de falha**, quando tecnicamente possível;
- **não** produz saída tratada oficial;
- **nunca** escolhe cliente ou registro por ordem de arquivo.

As linhas de `populacao.csv` e `reconciliacao.csv` do A5 descrevem a classificação esperada dos registros **para fins de auditoria da falha**, não uma saída publicável.

## Regra de alteração

Alterar qualquer valor esperado destes arquivos é mudança de resultado (tier 2): exige `/change-number`, fonte registrada e aprovação nominal e individual do dono do número antes do merge. Linguagem agrupada, silêncio, "assuma", aprovação de plano ou revisão de PR **não** constituem aprovação de negócio.
