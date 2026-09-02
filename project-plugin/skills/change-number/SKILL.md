---
name: change-number
description: Mudança de resultado entregue (Muda-numero) no projeto Aucta Foods — Rentabilidade por Cliente — obrigatório para qualquer mudança em fórmula, parâmetro, regra de tratamento, classificação ou indicador. Gate de validação: Bruno Lima (Controladoria).
---

# /change-number — mudança de resultado (obrigatório, tier 2)

1. **Fonte primeiro**: quem pediu/aprovou, documento, data. Sem fonte → parar e obter (source-driven).
2. Issue "Mudança de resultado" (template do repo, label muda-numero) com before/after esperado e casos que NÃO devem mudar.
3. **Plano Visual Faseado (obrigatório antes de implementar).** `docs/planos/<mudanca>.md`, pt-BR de negócio: fases nomeadas, esquema mermaid do cálculo antes → depois (onde o número muda), o que NÃO muda, o que o consultor verá por fase. Aprovação do consultor antes de implementar; progresso `Etapa N de X`.
4. Parâmetro rastreável (3.8): nome canônico, valor, unidade, fonte, data, escopo, owner, status — padrão da aba Parametros (TRUTH-004/005).
5. **Golden cases ANTES da mudança**: rodar `tests/golden/` na versão atual e guardar saídas (baseline).
   - **Tolerância explícita:** quando o esperado não é 100% derivável de referência externa, o agente propõe a tolerância e **Bruno Lima aprova explicitamente** — nunca adoção em silêncio; registrada em ACCEPTANCE.md junto aos golden cases.
6. **Mudança de critério de cálculo:** critério novo entra como **modo opcional** com `default = critério vigente`; critérios empilháveis. O vigente só deixa de ser default por decisão registrada do Bruno.
7. Implementar. Rodar golden na versão nova → before/after medido, magnitude, cenários afetados.
   - **Re-verificação do vigente:** todo ciclo que refatora o motor re-roda os golden do critério vigente no mesmo ciclo (diferença R$ 0,00 ou dentro da tolerância aprovada) antes do merge.
8. Análise de impacto + regressão completa; TRUTHS afetadas atualizadas no MESMO PR (D5).
9. **Aprovação de negócio**: Bruno Lima (Controladoria) aprova o before/after ANTES do merge — registrado como comentário no PR (consultor solo: sem required approvals; o comentário é o gate).
10. → /pre-pr (as três camadas D4 confirmam a classificação).
