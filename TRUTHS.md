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

TRUTH-011 │ Pedido duplicado: vale a versão com `atualizado_em` mais recente (ex.: O006 entra com custo_produto 260); a versão descartada é registrada no log de tratamento.
Source: golden cases e regras fornecidos pelo consultor na revisão da iniciação (2026-09-03), conferidos por recomputação manual independente
Owner: Controladoria (Bruno Lima)
Last reviewed: 2026-09-03

TRUTH-012 │ Pedidos com status Cancelado são excluídos dos cálculos, com exclusão documentada na reconciliação.
Source: golden cases e regras fornecidos pelo consultor na revisão da iniciação (2026-09-03)
Owner: Controladoria (Bruno Lima)
Last reviewed: 2026-09-03

TRUTH-013 │ Pedido com campo essencial nulo (custo do produto, frete) ou com cliente inexistente no cadastro bloqueia a publicação do relatório até ser tratado (EX-04..06 em tests/fixtures/expected_exceptions.csv).
Source: regras fornecidas pelo consultor na revisão da iniciação (2026-09-03)
Owner: Controladoria (Bruno Lima)
Last reviewed: 2026-09-03

TRUTH-014 │ Visita com status "Realizada" sem data_realizada é classificada como exceção reportada e não conta como visita válida (ex.: V008).
Source: regras fornecidas pelo consultor na revisão da iniciação (2026-09-03)
Owner: Controladoria (Bruno Lima)
Last reviewed: 2026-09-03

TRUTH-015 │ Identificadores de cliente são normalizados (maiúsculas, sem espaços) antes do cruzamento (ex.: " c003 " → C003), com normalização registrada no log.
Source: golden cases fornecidos pelo consultor na revisão da iniciação (2026-09-03)
Owner: Controladoria (Bruno Lima)
Last reviewed: 2026-09-03

TRUTH-016 │ A base tratada oficial admite pedido apenas por lista branca de status: só `Faturado` entra. `Cancelado` sai por TRUTH-012 (exclusão documentada); qualquer outro status, conhecido ou novo, vai para quarentena com bloqueio de publicação — nunca é incluído por omissão. Registro com exceção bloqueante fica FORA da base tratada, nomeado na quarentena, não marcado dentro dela.
Source: decisões DEC-06 e DEC-07 registradas na Issue #10 em 2026-09-08; autorizador Caio Ferrari no papel de Bruno Lima, com a limitação declarada em ACCEPTANCE.md
Owner: Controladoria (Bruno Lima)
Last reviewed: 2026-09-08

TRUTH-017 │ A competência (mês) de um pedido é a `data_pedido`, nunca a `atualizado_em`: correção de cadastro feita em mês posterior não move o mês do fato.
Source: decisão DEC-02 registrada na Issue #10 em 2026-09-08; autorizador Caio Ferrari no papel de Bruno Lima
Owner: Controladoria (Bruno Lima)
Last reviewed: 2026-09-08

TRUTH-018 │ Movimento de cliente com status `Inativo` entra na base tratada, marcado como `cliente_inativo`: o faturamento aconteceu e o custo de servir existiu. A decisão comercial sobre o cliente é separada do tratamento do dado.
Source: decisão DEC-01 registrada na Issue #10 em 2026-09-08; autorizador Caio Ferrari no papel de Bruno Lima
Owner: Controladoria (Bruno Lima)
Last reviewed: 2026-09-08

TRUTH-019 │ `custo_manuseio` igual a 0 é valor legítimo da fonte, não ausência de dado: o custo logístico de GC-01 (130 = frete 80 + 50) confirma que a coluna não é usada no piloto. Zero não vira nulo nem é imputado.
Source: decisão DEC-03 registrada na Issue #10 em 2026-09-08, conferida contra os golden cases GC-01..03; autorizador Caio Ferrari no papel de Bruno Lima
Owner: Controladoria (Bruno Lima)
Last reviewed: 2026-09-08

TRUTH-020 │ Empate de `atualizado_em` entre duas versões do mesmo pedido: todas as versões vão para quarentena com bloqueio de publicação. A versão vigente nunca é escolhida por ordem de leitura do arquivo.
Source: decisão DEC-04 registrada na Issue #10 em 2026-09-08; autorizador Caio Ferrari no papel de Bruno Lima
Owner: Controladoria (Bruno Lima)
Last reviewed: 2026-09-08
