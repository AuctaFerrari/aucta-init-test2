# Índice de parâmetros — Aucta Foods · Rentabilidade por Cliente

> Índice legível dos parâmetros de negócio (blueprint 3.8 / decisão D11 do core). O **valor de execução** vive em um lugar só, no código, quando o módulo de cálculo existir; este índice é a referência auditável, com fonte, owner, status, escopo, vigência e regra para valor ausente ou expirado.
>
> **Regra dura:** a fonte bruta em `tests/fixtures/parametros.csv` é **imutável** — ela registra o que a fonte originalmente diz, inclusive quando o status observado difere do aprovado. Override aprovado se registra aqui, nunca corrigindo a fonte.
>
> Nenhum módulo de cálculo pode consumir um parâmetro que não esteja neste índice com todos os campos preenchidos.

## `custo_por_visita_realizada`

| Campo | Valor |
| --- | --- |
| Nome canônico | `custo_por_visita_realizada` |
| Valor aprovado | **R$ 100,00** |
| Unidade | BRL por visita válida |
| Fonte da aprovação | Issue #10, comentário de aprovação válido — https://github.com/AuctaFerrari/aucta-init-test2/issues/10#issuecomment-5589411324 |
| Owner de negócio | Bruno Lima (Controladoria) — papel fictício explicitamente ativado por Caio Ferrari neste teste sintético |
| Status | **Aprovado para piloto** |
| Escopo | Piloto sintético Aucta Foods |
| Início de vigência | 2026-01-01 |
| Fim de vigência | 2026-03-31 |
| Ausente ou expirado | **Bloqueia o cálculo. Nenhum fallback, silencioso ou não.** Fora da vigência, a execução não produz indicador |
| Status observado na fonte bruta | **`Provisório`**, com fonte "Premissa do sponsor para piloto", preservado sem alteração em `tests/fixtures/parametros.csv` |
| Usado por | TRUTH-004 (`custo_visitas = visitas_validas × custo_por_visita_realizada`) |
| Muda-numero | sim |

Nota de materialidade: os casos golden GC-01..03 embutem este valor. GC-01 usa 2 visitas válidas × R$ 100,00 = R$ 200,00; GC-02 e GC-03 usam 1 visita × R$ 100,00. Alterar este parâmetro muda GC-01..03 e exige novo `/change-number`.

## `custo_operacional_por_pedido`

| Campo | Valor |
| --- | --- |
| Nome canônico | `custo_operacional_por_pedido` |
| Valor confirmado | **R$ 20,00** |
| Unidade | BRL por pedido válido |
| Fonte na fixture | `tests/fixtures/parametros.csv` — "Controladoria - regra vigente" |
| Status observado na fonte bruta | **`Vigente`** |
| Confirmação de negócio | Issue #10 — https://github.com/AuctaFerrari/aucta-init-test2/issues/10#issuecomment-5589411324 ("`custo_operacional_por_pedido = R$ 20,00 por pedido válido` confirmado para o piloto") |
| Owner de negócio | Bruno Lima (Controladoria) |
| Status neste índice | Vigente, confirmado para o piloto |
| Escopo | Piloto sintético Aucta Foods |
| Início de vigência | 2026-01-01 |
| Fim de vigência | 2026-03-31 |
| Ausente ou expirado | **Bloqueia o cálculo. Nenhum fallback.** |
| Usado por | TRUTH-005 (`custo_pedidos = pedidos_validos × custo_operacional_por_pedido`) |
| Muda-numero | sim |

Nota de materialidade: GC-01 usa 2 pedidos × R$ 20,00 = R$ 40,00; GC-02 1 pedido; GC-03 2 pedidos (O004 normalizado + O006 na versão vigente).

## `limiar_margem_servir_baixa` — NÃO validado, fora de escopo

| Campo | Valor |
| --- | --- |
| Valor na fonte bruta | 0.05 (% da receita líquida) |
| Status observado na fonte bruta | **`Não validado`**, fonte "A validar com sponsor" |
| Status neste índice | **Não aprovado.** Nenhuma aprovação existe |
| Aprovador necessário | Ana Martins (Diretora Comercial), para o limiar de recomendação; Bruno Lima para o número que o alimenta |
| Uso permitido | **Nenhum.** Só afeta classificação e lista de clientes-alerta, que estão fora do escopo do ciclo atual |
| Ausente ou expirado | Bloqueia qualquer classificação ou recomendação |

Registrado aqui de propósito, com status negativo explícito: um parâmetro não aprovado precisa ser visível como não aprovado, não ausente do índice.

## Regra de manutenção

1. Parâmetro de negócio tocado em um diff sem entrada correspondente neste índice → o `/pre-pr` recusa abrir o PR (D11).
2. Mudança de valor, vigência ou escopo é mudança de resultado: exige `/change-number` com fonte registrada e aprovação nominal do dono do número antes do merge.
3. Divergência entre o status observado na fonte bruta e o status aprovado é **normal e deve ficar visível** — nunca se "corrige" a fonte para casar com a aprovação.
