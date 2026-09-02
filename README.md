# <Nome do projeto>

Repo criado a partir do template **aucta-template-projeto** (padrão Aucta de desenvolvimento de soluções com IA).

O que já vem pronto:

- Estrutura de pastas (docs/, docs/planos/, tests/regression/, tests/fixtures/, .project/).
- Templates de Issue (Feature, Bug, Mudança de resultado) e de Pull Request com bloco Muda-numero.
- CI (`.github/workflows/ci.yml`) chamando `.github/ci/run-checks.sh` — adapte o script ao projeto.
- Action `bootstrap-labels`: cria as 9 labels de governança automaticamente no primeiro push.
- `CODEOWNERS.example` — o /init gera o CODEOWNERS real a partir do OWNERS.md.

Próximo passo após criar o repo: rodar o **/init** da Aucta (plugin aucta-dev-core) — ele conduz a entrevista, gera os artefatos canônicos (PROJECT, TRUTHS, GLOSSARY, ACCEPTANCE, OWNERS) e configura o resto.

**Dados reais de cliente NUNCA entram neste repo** — ficam na pasta local do consultor; o catálogo (`.project/DATA_CATALOG.md`) aponta onde vivem.
