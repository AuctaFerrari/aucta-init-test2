# Project truths

> Verdades canônicas para a **versão atual** do projeto (blueprint 6.2). Cada item é atômico, verificável e relevante para decisões futuras. Uma verdade entra quando muda como a solução deve ser entendida, construída, testada ou operada. Hipóteses, pendências, opiniões e logs NÃO entram. Quando a realidade muda, a verdade é alterada por PR — o Git preserva o histórico.

TRUTH-001 │ Receita líquida = receita bruta − desconto.
Source: fórmulas preliminares fornecidas pelo consultor na iniciação (2026-09-02); sujeitas à validação da controladoria no piloto
Owner: Controladoria (Bruno Lima)
Last reviewed: 2026-09-02

TRUTH-002 │ Margem de contribuição = receita líquida − custo do produto − frete − custo de manuseio.
Source: fórmulas preliminares fornecidas pelo consultor na iniciação (2026-09-02)
Owner: Controladoria (Bruno Lima)
Last reviewed: 2026-09-02

TRUTH-003 │ Margem de servir = margem de contribuição − custo das visitas realizadas − custo operacional dos pedidos.
Source: fórmulas preliminares fornecidas pelo consultor na iniciação (2026-09-02)
Owner: Controladoria (Bruno Lima)
Last reviewed: 2026-09-02

TRUTH-004 │ Custo das visitas = quantidade de visitas válidas realizadas × parâmetro `custo_por_visita_realizada`.
Source: fórmulas preliminares fornecidas pelo consultor na iniciação (2026-09-02)
Owner: Controladoria (Bruno Lima)
Last reviewed: 2026-09-02

TRUTH-005 │ Custo operacional dos pedidos = quantidade de pedidos faturados válidos × parâmetro `custo_operacional_por_pedido`.
Source: fórmulas preliminares fornecidas pelo consultor na iniciação (2026-09-02)
Owner: Controladoria (Bruno Lima)
Last reviewed: 2026-09-02

TRUTH-006 │ Dados reais são confidenciais: nunca entram no repositório nem saem do computador corporativo; o repositório guarda apenas código, documentação e massa sintética.
Source: regra confirmada pelo consultor na entrevista de iniciação (2026-09-02)
Owner: Consultor Aucta
Last reviewed: 2026-09-02

TRUTH-007 │ A fonte oficial de entrada da v1 é o arquivo Excel operacional mensal com as 5 bases (clientes, vendas, custos logísticos, visitas, parâmetros); no piloto, `01_Base_Operacional_Sintetica.xlsx`.
Source: pedido inicial do consultor (2026-09-02)
Owner: Aucta Foods (analista da rotina)
Last reviewed: 2026-09-02

TRUTH-008 │ Reconciliação obrigatória em toda execução: diferença zero entre os totais válidos da origem e os totais processados, após exclusões documentadas.
Source: critério de aceite definido pelo consultor na entrevista de iniciação (2026-09-02)
Owner: Controladoria (Bruno Lima)
Last reviewed: 2026-09-02

TRUTH-009 │ O período piloto é janeiro a março de 2026.
Source: pedido inicial do consultor (2026-09-02)
Owner: Consultor Aucta
Last reviewed: 2026-09-02

TRUTH-010 │ A execução é mensal, manual, por analista, em computador corporativo Windows; a v1 não tem autenticação, API externa nem deploy.
Source: pedido inicial do consultor (2026-09-02)
Owner: Aucta Foods (analista da rotina)
Last reviewed: 2026-09-02
