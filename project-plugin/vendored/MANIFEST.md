# Manifesto de vendorização — projeto Aucta Foods · Rentabilidade por Cliente (D3)

Este projeto **NÃO copia skills de terceiros**: consome as cópias auditadas do núcleo Aucta (`AuctaFerrari/aucta-dev-core`, diretório `vendored/`). Operação nunca depende de upstream vivo. Cópia local só se o repo precisar ser autossuficiente (ex.: entrega ao cliente sem acesso ao núcleo) — não é o caso (registrado).

Core de referência: `AuctaFerrari/aucta-dev-core` @ `e525e82` (2026-09-02).

| Skill | Origem upstream (repo @ commit) | Caminho no core | Core commit | Auditoria | Responsável |
| --- | --- | --- | --- | --- | --- |
| spec-driven-development | addyosmani/agent-skills @ `d2c37ef` | `vendored/spec-driven-development` (SKILL.md `f3f5877`) | `e525e82` | 2026-08-31 — limpa | Claude; revisão Caio Ferrari |
| planning-and-task-breakdown | addyosmani/agent-skills @ `d2c37ef` | `vendored/planning-and-task-breakdown` (SKILL.md `296249b`) | `e525e82` | 2026-08-31 — limpa | idem |
| test-driven-development | addyosmani/agent-skills @ `d2c37ef` | `vendored/test-driven-development` (SKILL.md `0cfd2f3`) | `e525e82` | 2026-08-31 — limpa | idem |
| debugging-and-error-recovery | addyosmani/agent-skills @ `d2c37ef` | `vendored/debugging-and-error-recovery` (SKILL.md `0377580`) | `e525e82` | 2026-08-31 — limpa | idem |
| context-engineering | addyosmani/agent-skills @ `d2c37ef` | `vendored/context-engineering` (SKILL.md `be99110`) | `e525e82` | 2026-08-31 — limpa | idem |
| andrej-karpathy-skills | — | **pendente de vendorização no core** (backlog tranche 4) | — | pendente | — |

Enquanto `andrej-karpathy-skills` estiver pendente, os workflows operam com o fallback documentado: princípios de simplicidade/mudança cirúrgica embutidos nos próprios workflows.

Drift check: executado pelo init-check e sob demanda, comparando git blob SHA local do core vs upstream HEAD — divergência sinaliza sem bloquear (regras no MANIFEST do core).
