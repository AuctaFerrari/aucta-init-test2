# Referências esperadas da fase 3 — versão que vale de cada pedido

> Materializadas **antes** do código da fase 3 (D10). Não são produzidas pelo programa que verificam.

## Procedência

**Derivação:** script one-off independente, executado **fora do repositório**, escrito a partir do texto das regras aprovadas, com `csv` e `Decimal` da biblioteca padrão.

**Regras cobertas:** TRUTH-011 (vale a versão com `atualizado_em` mais recente, descartada preservada), **DN-04** (empate no timestamp mais recente → todas as versões em quarentena e competência bloqueada), **DN-14** (timestamp inutilizável em grupo duplicado → nenhuma vencedora, todas em quarentena, motivos separados) e **DN-11** (agrupamento pelo `pedido_id` normalizado).

**Aprovações:** Issue #10 —
[issuecomment-5589411324](https://github.com/AuctaFerrari/aucta-init-test2/issues/10#issuecomment-5589411324) (DN-04, TRUTH-011) e
[issuecomment-5590561870](https://github.com/AuctaFerrari/aucta-init-test2/issues/10#issuecomment-5590561870) (DN-14). Índice: `.project/DECISIONS.md`.

**Não reaproveitado:** nada foi lido, copiado, diferenciado, importado ou adaptado do ramo `feat/base-tratada-oficial` (head `5c02e59`).

**Limitação declarada:** a sessão teve exposição conversacional prévia à implementação contaminada. Não se reivindica sala limpa; reivindica-se derivação reescrita a partir das regras, sem cópia de arquivo.

## Vocabulário desta fase

Diferente do golden de `base-tratada/`, que descreve o resultado do tratamento completo. Aqui o destino é o da **escolha de versão**:

| Destino | Significado |
| --- | --- |
| `vigente` | versão que prevalece, ou pedido único sem escolha a fazer |
| `versao_substituida` | versão descartada por TRUTH-011, preservada e auditável |
| `quarentena` | grupo ambíguo: empate (DN-04) ou timestamp inutilizável (DN-14) — **nenhuma vencedora escolhida** |

`vigente` nesta fase **não** significa que o pedido entra na base tratada: filtro de situação, nulos essenciais e cliente órfão são das fases 4 e 5. O pedido cancelado O005, por exemplo, aparece como `vigente` aqui — a fase 3 só decide qual versão vale.

## Arquivos

| Arquivo | Conteúdo |
| --- | --- |
| `versao_pedido.csv` | Destino esperado de cada linha de Vendas, por cenário (39 casos), com regra, motivos, sinal e escopo do bloqueio |
| `conservacao.csv` | Origem = vigente + versão substituída + quarentena, em contagem e em reais. Diferença **0,00** nas 12 linhas |
| `veredito.csv` | Bloqueio por competência em cada cenário (9 casos) |

## Cenários

| Cenário | Natureza | Entrada | Resultado esperado |
| --- | --- | --- | --- |
| **BASE** | comportamento da fixture atual | as cinco fixtures de origem | O006 mantém a versão de 2026-01-21 14:30, com `custo_produto` **260**; a de 2026-01-20 08:00 vira `versao_substituida` com `custo_produto` 250. 12 vigentes, 1 substituída, 0 em quarentena |
| **A3** | adversarial — DN-04 | `adversarial/A3/vendas.csv` (duas versões de O006 com o mesmo timestamp) | as duas versões em quarentena, **2026-01 bloqueada**, nenhuma vencedora |
| **A6** | adversarial — DN-14 | `adversarial/A6/vendas.csv` (segunda versão de O006 com `atualizado_em` vazio) | as duas versões em quarentena, **2026-01 bloqueada**, nenhuma vencedora, **dois motivos separados**: ambiguidade de duplicata e timestamp inutilizável |

Conservação em A3 e A6: quarentena com R$ 1.000,00 de receita bruta, R$ 100,00 de desconto e R$ 510,00 de custo de produto; vigente com R$ 10.950,00 / R$ 840,00 / R$ 5.450,00; diferença **0,00**.

## Casos cobertos apenas no teste, sem golden commitado

Dois casos exigem entrada que não existe nas fixtures e são montados pela própria conferência, em diretório temporário, com a expectativa declarada no teste: **duplicata que atravessa mais de uma competência** e **pedido não duplicado com `atualizado_em` ausente**, que por DN-14 permanece com aviso não bloqueante. Não viram fixture versionada porque não descrevem a massa oficial do piloto.

## Regra de alteração

Alterar qualquer valor esperado aqui é mudança de resultado (tier 2): exige `/change-number`, fonte registrada e aprovação nominal e individual do dono do número. Linguagem agrupada, silêncio, "assuma", aprovação de plano ou revisão de PR **não** constituem aprovação de negócio.
