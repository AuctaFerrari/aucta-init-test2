# Project truths

> Verdades canônicas para a **versão atual** do projeto (blueprint 6.2). Cada item é atômico, verificável e relevante para decisões futuras. Uma verdade entra quando muda como a solução deve ser entendida, construída, testada ou operada. Hipóteses, pendências, opiniões e logs NÃO entram. Quando a realidade muda, a verdade é alterada por PR — o Git preserva o histórico.
>
> Regras operacionais aprovadas pelo dono do número vivem em `.project/DECISIONS.md` como DN-01 a DN-13; parâmetros vivem em `.project/PARAMETERS.md`. Este arquivo não duplica nenhum dos dois.

TRUTH-001 │ Receita líquida = receita bruta − desconto.
Source: aprovada pelo dono do número em 2026-09-08 — Issue #10, issuecomment-5589411324 (antes disso, fórmula preliminar da iniciação de 2026-09-02)
Owner: Controladoria (Bruno Lima)
Last reviewed: 2026-09-08

TRUTH-002 │ Margem de contribuição = receita líquida − custo do produto − frete − custo de manuseio.
Source: aprovada pelo dono do número em 2026-09-08 — Issue #10, issuecomment-5589411324
Owner: Controladoria (Bruno Lima)
Last reviewed: 2026-09-08

TRUTH-003 │ Margem de servir = margem de contribuição − custo das visitas realizadas − custo operacional dos pedidos.
Source: aprovada pelo dono do número em 2026-09-08 — Issue #10, issuecomment-5589411324
Owner: Controladoria (Bruno Lima)
Last reviewed: 2026-09-08

TRUTH-004 │ Custo das visitas = quantidade de visitas válidas realizadas × parâmetro `custo_por_visita_realizada`. O valor, a vigência e a regra de ausência do parâmetro estão em `.project/PARAMETERS.md` (DN-12).
Source: aprovada pelo dono do número em 2026-09-08 — Issue #10, issuecomment-5589411324
Owner: Controladoria (Bruno Lima)
Last reviewed: 2026-09-08

TRUTH-005 │ Custo operacional dos pedidos = quantidade de pedidos faturados válidos × parâmetro `custo_operacional_por_pedido`, confirmado em R$ 20,00 por pedido válido para o piloto (`.project/PARAMETERS.md`).
Source: aprovada pelo dono do número em 2026-09-08 — Issue #10, issuecomment-5589411324
Owner: Controladoria (Bruno Lima)
Last reviewed: 2026-09-08

TRUTH-006 │ Dados reais são confidenciais: nunca entram no repositório nem saem do computador corporativo; o repositório guarda apenas código, documentação e massa sintética.
Source: regra confirmada pelo consultor na entrevista de iniciação (2026-09-02)
Owner: Consultor Aucta
Last reviewed: 2026-09-02

TRUTH-007 │ A fonte oficial de entrada da v1 é o arquivo Excel operacional mensal com as 5 bases (clientes, vendas, custos logísticos, visitas, parâmetros); no piloto, `01_Base_Operacional_Sintetica.xlsx`.
Source: pedido inicial do consultor (2026-09-02)
Owner: Aucta Foods (analista da rotina)
Last reviewed: 2026-09-02

TRUTH-008 │ Reconciliação obrigatória em toda execução: diferença zero entre os totais válidos da origem e os totais processados, após exclusões documentadas. A partir de DN-08, a reconciliação tem cinco populações: origem = tratada + excluída por regra + quarentena + fora do período.
Source: critério de aceite definido pelo consultor na entrevista de iniciação (2026-09-02); populações ampliadas por DN-08, aprovada em 2026-09-08
Owner: Controladoria (Bruno Lima)
Last reviewed: 2026-09-08

TRUTH-009 │ O período piloto é janeiro a março de 2026.
Source: pedido inicial do consultor (2026-09-02)
Owner: Consultor Aucta
Last reviewed: 2026-09-02

TRUTH-010 │ A execução é mensal, manual, por analista, em computador corporativo Windows; a v1 não tem autenticação, API externa nem deploy.
Source: pedido inicial do consultor (2026-09-02)
Owner: Aucta Foods (analista da rotina)
Last reviewed: 2026-09-02

TRUTH-011 │ Pedido duplicado: vale a versão com `atualizado_em` mais recente (ex.: O006 entra com custo_produto 260); a versão descartada é registrada no log de tratamento. Empate no `atualizado_em` mais recente segue DN-04: todas as versões empatadas vão para quarentena e a competência afetada é bloqueada.
Source: aprovada pelo dono do número em 2026-09-08 — Issue #10, issuecomment-5589411324 (regra original fornecida na revisão da iniciação de 2026-09-03, conferida por recomputação manual independente)
Owner: Controladoria (Bruno Lima)
Last reviewed: 2026-09-08

TRUTH-012 │ Pedidos com status Cancelado são excluídos dos cálculos, com exclusão documentada na reconciliação. A exclusão é não bloqueante.
Source: aprovada pelo dono do número em 2026-09-08 — Issue #10, issuecomment-5589411324
Owner: Controladoria (Bruno Lima)
Last reviewed: 2026-09-08

TRUTH-013 │ Pedido com campo essencial nulo (custo do produto, frete) ou com cliente inexistente no cadastro vai para quarentena e bloqueia **apenas a competência afetada**, não o relatório inteiro (EX-04..06 em `tests/fixtures/expected_exceptions.csv`). O destino do registro retido e o conteúdo preservado seguem DN-05; o escopo do bloqueio segue DN-10.
Source: aprovada com esclarecimento pelo dono do número em 2026-09-08 — Issue #10, issuecomment-5589411324
Owner: Controladoria (Bruno Lima)
Last reviewed: 2026-09-08

TRUTH-014 │ Visita com status "Realizada" sem data_realizada é classificada como exceção reportada e não conta como visita válida (ex.: V008). Isoladamente, essa exceção é **não bloqueante**. Quando o mesmo registro também tem cliente fora do cadastro, prevalece a regra mais estrita de DN-07 (esclarecimento I-01).
Source: aprovada pelo dono do número em 2026-09-08 — Issue #10, issuecomment-5589411324 e issuecomment-5589595626
Owner: Controladoria (Bruno Lima)
Last reviewed: 2026-09-08

TRUTH-015 │ Identificadores são normalizados antes de qualquer cruzamento conforme **DN-11**: espaço externo removido, letras em maiúscula, espaço interno e pontuação **preservados**, sem inferência de prefixo ou zero à esquerda, identificador bruto preservado em campo de rastreabilidade, e colisão após normalização tratada com quarentena e bloqueio (ou falha da execução, quando o impacto não é delimitável). Exemplo: `" c003 "` → `C003`, correspondência única, com o valor bruto registrado.
Source: aprovada com esclarecimento pelo dono do número em 2026-09-08 — Issue #10, issuecomment-5589411324. Substitui a formulação anterior "maiúsculas, sem espaços", que era ambígua quanto a espaço interno
Owner: Controladoria (Bruno Lima)
Last reviewed: 2026-09-08
