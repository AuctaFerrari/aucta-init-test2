---
name: build-feature
description: Construir funcionalidade material (tier 1+) no projeto Aucta Foods — Rentabilidade por Cliente, com spec curta, Plano Visual Faseado aprovado pelo consultor e TDD na lógica.
---

# /build-feature — feature material (tier 1+)

1. Requisitos: fechar lacunas com perguntas curtas (linguagem-consultor Rule 4 — 1 decisão por pergunta, contexto em bullets antes).
2. Spec curta: comportamento + critérios de aceite, ancorados em ACCEPTANCE.md e TRUTHS.md. [skill: spec-driven-development]
3. **Plano Visual Faseado (obrigatório antes de implementar).** `docs/planos/<feature>.md`, pt-BR de negócio: fases com nomes de negócio ("Fase 1 — leitura da base de vendas"), esquema mermaid do fluxo antes → depois, o que muda / o que NÃO muda, o que o consultor verá por fase. Aprovação do consultor ANTES de implementar. [skill: planning-and-task-breakdown]
4. Implementação incremental com TDD onde há lógica/regra, progresso `Etapa N de X — <nome>`. [skill: test-driven-development] Uma mudança lógica por branch/PR (3.6); commits atômicos. [agente]
5. Simplicidade: revisar overengineering (camada de comportamento karpathy — fallback embutido).
6. QA: testes do fluxo + evidências; saídas geradas (Excel/PDF) nunca editadas à mão (3.9).
7. Se a feature toca cálculo/parâmetro → desviar para /change-number. Senão → /pre-pr.
