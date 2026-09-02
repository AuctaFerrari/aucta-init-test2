---
name: pre-pr
description: Gate antes de abrir/atualizar qualquer PR no projeto Aucta Foods — Rentabilidade por Cliente — testes, QA, verificação Muda-numero em 3 camadas (D4) e check de TRUTHS (D5).
---

# /pre-pr — gate antes de abrir/atualizar PR (sempre)

1. **Testes**: suite aplicável ao tier verde; evidências coletadas. Tier 2: golden cases em `tests/golden/` sobre `tests/fixtures/`.
2. **QA**: fluxo crítico exercitado (execução ponta a ponta sobre a fixture); Excel/PDF regenerados, nunca editados à mão (3.9).
3. **Code review preparatório**: diff revisado por simplicidade e mudanças laterais (dividir PR se objetivos independentes — 3.6).
4. **Muda-numero — verificação em 3 camadas (D4), nunca só declaração:**
   - a) *Caminho*: diff tocou módulos de regra/cálculo/parâmetros (lista em pointers.md) → pergunta obrigatória;
   - b) *Conteúdo*: diff altera constantes numéricas ou fórmulas → idem;
   - c) *Golden before/after*: rodar harness na base e no head; qualquer saída diferente → Muda-numero = **fato medido** → exigir artefatos do /change-number (fonte, magnitude, aprovação do Bruno).
5. **Check de TRUTHS (D5)**: diff + contexto vs TRUTHS.md → (a) verdades contraditas/alteradas; (b) fatos novos canônicos. Confirmar com o consultor; atualização entra no MESMO PR. A IA detecta; o consultor decide.
6. **Docs sync** (3.11): docs que ficariam incorretos atualizados no ciclo.
7. **Risk gate**: tier 2 → validação de negócio do Bruno registrada (comentário no PR) quando Muda-numero.
8. **PR**: abrir/atualizar com o template preenchido (contexto, o quê, por quê, Muda-numero, risco, validação, release). [agente — D6]
