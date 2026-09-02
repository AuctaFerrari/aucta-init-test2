---
name: router
description: Control plane do projeto Aucta Foods — Rentabilidade por Cliente. Use para classificar QUALQUER demanda do consultor (feature, bug, mudança de número, doc) e rotear para o workflow mínimo. Sempre o primeiro ponto de entrada de uma demanda de trabalho neste repo.
---

# Router — Aucta Foods · Rentabilidade por Cliente (tier padrão: 2)

Rotear, não sobrecarregar (blueprint 7.4). Classify first, load only what the step needs.

## Steps

1. Read `project-plugin/references/pointers.md`; open the session on PROJECT.md + TRUTHS.md + active Issue/Spec — nothing else by default.
2. Classify the demand: type (feature / bug / número / doc / release / handoff) and change tier (0–3, per change; project floor heuristics below).
3. Route:

| Demanda | Workflow |
| --- | --- |
| Qualquer mudança — abertura | /start-work (sempre primeiro) |
| Tier 0 (editorial/doc, sem regra econômica) | caminho leve: branch → mudança → review → PR (via /pre-pr) |
| Tier 1 funcional | /build-feature ou /fix-bug |
| Toca fórmula, parâmetro, regra de negócio, classificação ou qualquer número entregue | /change-number (gate Muda-numero — OBRIGATÓRIO) |
| Antes de abrir/atualizar QUALQUER PR | /pre-pr |
| Versão entregue | /release |
| Troca de sessão/pessoa | /handoff |

4. Judgment questions only to the consultant (aprovações, validação de negócio, escopo ambíguo); everything mechanical — including ALL Git — is executed by the agent (D6). Dialogue in pt-BR per linguagem-consultor.

## Heurísticas deste projeto

- Os módulos de cálculo (receita líquida, margens, custos de visita/pedido, aderência, listas-alerta), os parâmetros da aba Parametros e as regras de tratamento (dedupe, IDs, exclusões) são TODOS território Muda-numero → /change-number.
- Quem valida número: Bruno Lima (Controladoria) — aprovação registrada como comentário no PR ANTES do merge (sem required approvals — consultor solo).
- Golden cases em `tests/golden/` rodam sobre `tests/fixtures/*.csv`; referência externa preparada pelo consultor e validada pelo Bruno.
- Saídas (Excel analítico, PDF executivo) são artefatos gerados — nunca editados à mão (3.9).
