# Known issues — Aucta Foods · Rentabilidade por Cliente

> Erros e limitações ainda relevantes (blueprint 6.1). Item sai daqui quando resolvido ou quando deixa de ter valor operacional.

## KI-001 · A guarda de módulos de cálculo é lista de nomes, não verificação de comportamento

**Status:** aberto · **Registrado em:** 2026-09-04 · **Última revisão:** 2026-09-08 · **Onde vive:** `.github/ci/run-checks.sh` (guardas 4 e 4b) + `tests/golden/run_golden.py` (suite 4) + `project-plugin/references/modulos.json` (inventário)

**O que existe hoje (revisão de 2026-09-08).** A guarda 4 do CI exige que `tests/golden/run_golden.py` exista e passe assim que `src/` existir. O mecanismo mudou na fase 2:

- **APOSENTADO:** a allowlist `MODULOS_OBSERVACIONAIS = {"diagnostico_fonte.py"}`, que vivia dentro do arquivo de teste, **não existe mais**.
- **EM VIGOR:** a suite 4 lê o inventário `project-plugin/references/modulos.json`, no nível do projeto. Cada módulo declara caminho, categoria, decisão aprovada, golden que o cobre, suite que o confere e justificativa. A varredura de `src/` é recursiva.
- A suite 4 reprova em cinco situações, cada uma com prova negativa registrada: módulo de `src/` não registrado; caminho registrado inexistente (renomear sem atualizar reprova); categoria proibida; módulo não observacional sem decisão `DN-xx`, sem golden existente ou sem suite existente; e suite declarada que o CI não invoca.
- As categorias proibidas (`calculo`, `calculo_margens`, `indicador`, `margem`, `rentabilidade`) ficam **no harness**, não no inventário, para que registrar um módulo nunca autorize um módulo de cálculo.

**A limitação, que continua.** Registro de módulo **não é** verificação de comportamento. O inventário responde "este arquivo foi declarado, com qual categoria e coberto por qual suite"; ele **não** analisa o que o código faz. Consequências concretas:

- Lógica de cálculo colocada **dentro** de um módulo registrado passa sem alarme. O inventário não impede comportamento de cálculo escondido, e não deve ser citado como se impedisse.
- Nome de categoria proibida conferido no harness é **comparação de string**, não análise semântica de código: um módulo registrado como `identificadores` que calcule margem internamente passa pela guarda 4.
- ~~`glob("*.py")` não é recursivo~~ — corrigido em 2026-09-08: a varredura passou a usar `rglob`, com prova negativa.
- O inventário é um arquivo editável. O diff toca `project-plugin/`, `tests/golden/` e `src/`, todos caminhos-sentinela do `/pre-pr`, mas quem responde a pergunta Muda-numero continua sendo a sessão.
- O falso positivo diminuiu, sem desaparecer: módulo novo e legítimo continua reprovando até ser registrado — o que agora é o comportamento desejado, porque registrar exige decisão aprovada, golden e suite.

**O que a guarda nova prova.** Que todo arquivo `.py` sob `src/`, em qualquer profundidade, está declarado; que o caminho declarado existe; que nenhum módulo foi declarado com categoria de cálculo; que todo módulo não observacional aponta para uma decisão `DN-xx`, um golden existente e uma suite existente; e que essa suite é efetivamente executada pelo CI.

**O que a guarda nova NÃO prova.** Que o módulo se comporta conforme a categoria declarada; que não há cálculo embutido; que o golden citado cobre o comportamento relevante; e que a suite citada é rigorosa. Nada disso é verificável por nome de arquivo ou por chave de JSON.

**O que as suites comportamentais cobrem de verdade.** Para o diagnóstico, a suite 1; para a fase 2, `tests/golden/run_fase2.py`, que confere ausência de chave de fase posterior na saída, restrição das regras aplicadas a DN-11 e DN-13, e ausência de menção a campos de fase posterior no código. É o limite de escopo real de cada módulo — não o inventário.

**O que a Suite 1 do harness cobre de verdade** (comportamental, mas raso): nenhum campo de saída com nome de indicador; classes de achado restritas ao vocabulário observacional; contagens iguais às cruas; duplicata preservada; hash da origem inalterado; saída determinística. Isso inspeciona o **formato da saída**, não o cálculo — um número calculado emitido sob uma chave de nome neutro, ou embutido no texto de uma descrição, passa.

**Registro honesto de como a verificação chegou aqui.** A versão inicial dessa checagem varria o texto livre do relatório e foi **enfraquecida de propósito** durante a implementação, porque batia no nome do parâmetro `limiar_margem_servir_baixa` presente na fixture. Trocou-se robustez por CI verde, e isso não foi declarado no PR original.

**Como não confiar nela indevidamente.** O gate real do trabalho que produz número é o `/change-number`: fonte registrada, golden before/after, aprovação de quem valida número (Bruno Lima) antes do merge. A guarda 4 é alarme de fumaça, não fechadura, e não deve ser citada como proteção comportamental.

**Correção estrutural:** demanda separada no `aucta-dev-core`, **issue #27** (não neste projeto), por decisão do owner técnico em 2026-09-04. Segue aberta. Situação das direções levantadas:

| Direção | Situação |
| --- | --- |
| Declarar módulos fora da allowlist do arquivo de teste | **feito** em 2026-09-08 (`project-plugin/references/modulos.json`) — resolve a localização, não a natureza do controle |
| Exigir que todo número na saída seja contagem, tamanho ou valor copiado da fonte | não feito no geral; aplicado pontualmente nas suites comportamentais |
| Congelar o inventário de achados como golden do próprio diagnóstico | não feito |
| Varredura recursiva de `src/` | **feito** em 2026-09-08 |

**KI-001 não está resolvida.** O que mudou foi onde o registro vive e o que ele exige; o defeito de fundo — controle por declaração em vez de por comportamento — permanece, e a correção continua sendo a issue #27 do core.
