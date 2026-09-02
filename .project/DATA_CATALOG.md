# Aucta Foods — Rentabilidade por Cliente — DATA_CATALOG.md

> Inventário e avaliação das fontes de dados (blueprint 2.4). Uma seção por fonte, com os 8 campos mínimos. O catálogo é um mapa — não contém cópias das bases. Aprofundamento acontece na tarefa que precisar (profundidade progressiva); o que não foi verificado fica marcado `não validado`.

## Base Operacional Mensal (piloto: sintética)

| Campo | Conteúdo |
| --- | --- |
| Fonte e localização | `01_Base_Operacional_Sintetica.xlsx` — pasta conectada do consultor (OneDrive → Aucta Blueprint Dev AI → inputs → teste 2). Origem de negócio: extrações operacionais mensais da Aucta Foods consolidadas em Excel. Na produção, o time recebe a base mensal equivalente. |
| Owner | Aucta Foods — analista da rotina mensal (a nomear); no piloto, consultor Aucta. |
| Uso na solução | Única entrada da v1. Alimenta todos os cálculos: receita líquida, margem de contribuição, margem de servir, aderência de visitas, listas de clientes-alerta, reconciliação e os dois entregáveis (Excel analítico + PDF executivo). |
| Estrutura | 5 abas: **Clientes** (6 linhas; chave `cliente_id`; razão social, região, segmento, canal, status) · **Vendas** (13 pedidos jan–mar/2026; chave `pedido_id`; `cliente_id` FK; receita_bruta, desconto, custo_produto, status_pedido, atualizado_em) · **Custos_Logisticos** (12 linhas; `pedido_id` FK; frete, custo_manuseio) · **Visitas** (11 linhas; chave `visita_id`; `cliente_id` FK; mes_ref, data_planejada, data_realizada, status) · **Parametros** (3 parâmetros: custo_por_visita_realizada=100 BRL, custo_operacional_por_pedido=20 BRL, limiar_margem_servir_baixa=0,05). |
| Qualidade | Armadilhas presentes na massa (intencionais, a tratar pela solução): `pedido_id` **O006 duplicado** (custo_produto 250 vs 260; `atualizado_em` distinto — critério de desempate a definir); `cliente_id` sujo **" c003 "** (espaços/minúsculas); pedido **O010 → C999 órfão** (cliente inexistente); **O009 sem custo_produto**; **O005 Cancelado**; **O008 sem frete** em Custos_Logisticos; visita **V008 status "Realizada" sem data_realizada** (inconsistência); **V005 não realizada**; cliente **C006 Inativo** com pedido (O012) e visita (V011); `custo_manuseio` = 0 em todas as linhas do piloto. |
| Status de evidência | **observado** — base pequena, 100% das linhas lidas no scan de classificação (2026-09-02). Estrutura da base de PRODUÇÃO: **não validado** (premissa: idêntica à sintética). |
| Sensibilidade | Massa piloto **sintética** — sem PII real, liberada para o repo. Base de produção: **confidencial** — nunca entra no Git nem sai do computador corporativo (TRUTH-006). Fixture versionada: `tests/fixtures/*.csv` (uma por aba, extraídas da base sintética em 2026-09-02). |
| Atualização | Mensal (base recebida pelo time no fechamento). Piloto cobre jan–mar/2026; último dado observado: 2026-03-16. Processo de refresh da produção: não validado. |

### Notas de tratamento (para a fase de construção)

- Regras de dedupe (O006), normalização de IDs (" c003 "), tratamento de órfãos (C999), nulos (O009, O08/frete) e definição de "visita válida"/"pedido faturado válido" serão especificadas como regras de negócio na fase de construção e promovidas a TRUTHS quando aprovadas pela controladoria. Exclusões entram no log de tratamento (ACC-005) e na reconciliação (ACC-006).
- Parâmetro `limiar_margem_servir_baixa` está **"Não validado"** na própria base — validação com o sponsor pendente (premissa no init-state).
