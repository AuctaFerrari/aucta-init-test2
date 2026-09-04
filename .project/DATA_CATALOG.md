# Aucta Foods — Rentabilidade por Cliente — DATA_CATALOG.md

> Inventário e avaliação das fontes de dados (blueprint 2.4). Uma seção por fonte, com os 8 campos mínimos. O catálogo é um mapa — não contém cópias das bases. Aprofundamento acontece na tarefa que precisar (profundidade progressiva); o que não foi verificado fica marcado `não validado`.

## Base Operacional Mensal (piloto: sintética)

| Campo | Conteúdo |
| --- | --- |
| Fonte e localização | `01_Base_Operacional_Sintetica.xlsx` — pasta conectada do consultor (OneDrive → Aucta Blueprint Dev AI → inputs → teste 2). Origem de negócio: extrações operacionais mensais da Aucta Foods consolidadas em Excel. Na produção, o time recebe a base mensal equivalente. |
| Owner | Aucta Foods — analista da rotina mensal (a nomear); no piloto, consultor Aucta. |
| Uso na solução | Única entrada da v1. Alimenta todos os cálculos: receita líquida, margem de contribuição, margem de servir, aderência de visitas, listas de clientes-alerta, reconciliação e os dois entregáveis (Excel analítico + PDF executivo). |
| Estrutura | 5 abas: **Clientes** (6 linhas; chave `cliente_id`; razão social, região, segmento, canal, status) · **Vendas** (13 pedidos jan–mar/2026; chave `pedido_id`; `cliente_id` FK; receita_bruta, desconto, custo_produto, status_pedido, atualizado_em) · **Custos_Logisticos** (12 linhas; `pedido_id` FK; frete, custo_manuseio) · **Visitas** (11 linhas; chave `visita_id`; `cliente_id` FK; mes_ref, data_planejada, data_realizada, status) · **Parametros** (3 parâmetros: custo_por_visita_realizada=100 BRL, custo_operacional_por_pedido=20 BRL, limiar_margem_servir_baixa=0,05). |
| Qualidade | Armadilhas presentes na massa (intencionais, a tratar pela solução): `pedido_id` **O006 duplicado** · `cliente_id` sujo **" c003 "** · pedido **O010 → C999 órfão** · **O009 sem custo_produto** · **O005 Cancelado** · **O008 sem frete** · visita **V008 "Realizada" sem data** · **V005 não realizada** · cliente **C006 Inativo** com pedido (O012) e visita (V011) · `custo_manuseio` = 0 no piloto. Tratamento esperado de cada uma: `tests/fixtures/expected_exceptions.csv` (EX-01..07) + TRUTHS 011..015. |
| Status de evidência | **observado** — base pequena, 100% das linhas lidas no scan de classificação (2026-09-02). Estrutura da base de PRODUÇÃO: **não validado** (premissa: idêntica à sintética). |
| Sensibilidade | Massa piloto **sintética** — sem PII real, liberada para o repo. Base de produção: **confidencial** — nunca entra no Git nem sai do computador corporativo (TRUTH-006). Fixture versionada: `tests/fixtures/*.csv` (uma por aba, extraídas da base sintética em 2026-09-02). |
| Atualização | Mensal (base recebida pelo time no fechamento). Piloto cobre jan–mar/2026; último dado observado: 2026-03-16. Processo de refresh da produção: não validado. |

### Notas de tratamento (atualizadas na revisão de 2026-09-03)

- Regras de tratamento MATERIALIZADAS: dedupe por `atualizado_em` mais recente (TRUTH-011), exclusão de cancelados (TRUTH-012), bloqueio de publicação por nulos/órfãos (TRUTH-013), visita sem data = exceção (TRUTH-014), normalização de IDs (TRUTH-015). Resultados esperados: `tests/fixtures/golden_cases.csv` (GC-01..03) e `tests/fixtures/expected_exceptions.csv` (EX-01..07); estratégia em `tests/TEST_STRATEGY.md`.
- **Verificação reproduzível (2026-09-04):** as armadilhas acima passaram a ser conferidas por comando (`src/diagnostico_fonte.py`; ver `docs/runbook/diagnostico-fonte.md`). A execução sobre as fixtures confirmou todas as 10 armadilhas catalogadas, sem divergência entre o caminho `.xlsx` e o caminho CSV. Observação adicional do diagnóstico: **dois dos três parâmetros não são regra vigente** — `custo_por_visita_realizada` está "Provisório" e `limiar_margem_servir_baixa` "Não validado".
- Parâmetro `limiar_margem_servir_baixa` segue **"Não validado"** na própria base — validação com o sponsor pendente; bloqueia classificação/recomendação de clientes-alerta, não bloqueia ingestão e tratamento.
