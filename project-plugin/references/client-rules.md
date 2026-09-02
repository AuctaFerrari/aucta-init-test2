# Regras inegociáveis — Aucta Foods · Rentabilidade por Cliente

1. **Dados reais nunca entram no Git nem saem do computador corporativo** (TRUTH-006). No repo: só código, documentação e massa sintética em `tests/fixtures/`.
2. **As bases mensais originais são intocáveis**: a solução lê a base e escreve saídas em pasta própria — nunca altera o arquivo de origem.
3. **Reconciliação obrigatória em toda execução** (TRUTH-008/ACC-006): diferença zero entre totais válidos da origem e processados, após exclusões documentadas.
4. **Nenhum número entregue muda sem /change-number**: fonte registrada, golden before/after, aprovação do Bruno Lima ANTES do merge.
5. **Saídas são geradas, nunca editadas à mão** (3.9): correção se faz no código/parâmetro e regenera.
6. **Execução pelo analista sem dependência do consultor** (ACC-004): toda entrega preserva o caminho "duplo clique/comando único" no Windows.
7. **Consultor nunca digita Git** (D6): todo branch/commit/PR/merge é executado pelo agente.
