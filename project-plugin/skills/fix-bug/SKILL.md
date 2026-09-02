---
name: fix-bug
description: Corrigir erro reproduzível ou regressão no projeto Aucta Foods — Rentabilidade por Cliente. Investigar o sintoma antes de editar; teste de regressão que falha antes do fix.
---

# /fix-bug — erro reproduzível ou regressão

1. Triagem pelo sintoma (4.1): o que mudou, esperado, casos, desde quando, blocos suspeitos, teste discriminante. [skill: debugging-and-error-recovery]
2. Reproduzir e medir sobre `tests/fixtures/` (evidência mínima 4.3 para anomalia numérica; rótulos medido/inferido/não verificado 4.2).
3. **Teste de regressão que falha** antes do fix. Erro numérico relevante: reconstruir 1 caso por caminho independente (4.4) — ex.: margem de um cliente recalculada à mão.
4. Fix na causa-raiz (plausibilidade não é causa-raiz — 4.7); artefatos gerados não são corrigidos à mão (3.9).
5. QA: regressão verde + casos vizinhos que NÃO deviam mudar (golden do critério vigente).
6. Registrar no known-issues quando relevante (4.8).
7. Se o fix altera número entregue → /change-number. Senão → /pre-pr.
