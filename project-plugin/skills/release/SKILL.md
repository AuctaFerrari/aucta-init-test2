---
name: release
description: Entregar versão do projeto Aucta Foods — Rentabilidade por Cliente — validação completa, release notes com Muda-numero quantificado, tag, e-mail de aceite e backup fora do GitHub.
---

# /release — versão entregue

1. Validação prévia (5.1): novas features, regressão, fluxos críticos, golden cases, comparação com versão anterior. **Entregável = configuração validada**: o Excel analítico e o PDF executivo saem da MESMA configuração/parâmetros usados na validação golden — nunca de caminho paralelo.
2. Docs e mapas refletem a versão (5.2); higienização (5.5) — sem temporários, versão vigente identificada.
3. Release notes (5.3): versão, mudanças, bugs corrigidos, limitações, testes, cuidados; **Muda-numero quantificado** (5.4): regra/parâmetro, before/after, magnitude, segmentos, aprovação do Bruno — nunca só "melhoria técnica".
4. Tag + GitHub Release com artefato. [agente quando o ambiente permite; senão click-path na UI]
5. Manifest (9.7): tag, commit, data, owner, checksum SHA-256 do artefato.
6. **Aceite formal**: e-mail de entrega para joao.santos@aucta.capital; aprovação = resposta positiva, arquivada como referência no repositório (ACCEPTANCE.md · mecanismo de aprovação). Validação dos números pelo Bruno antecede o e-mail.
7. **Backup do repositório — independência do GitHub:** projeto sem SharePoint na v1 → snapshot ZIP do repo na tag salvo em `backups/<tag>.zip` na pasta do projeto no OneDrive do consultor (Aucta Blueprint Dev AI). Click-path: página do repo na tag → Code → Download ZIP → salvar em `backups/`. [assistido; agente valida via pasta conectada e registra no manifest]
8. CHANGELOG + VERSION atualizados. [agente]
