# Known issues — Aucta Foods · Rentabilidade por Cliente

> Erros e limitações ainda relevantes (blueprint 6.1). Item sai daqui quando resolvido ou quando deixa de ter valor operacional.

## KI-001 · A guarda de módulos de cálculo é lista de nomes, não verificação de comportamento

**Status:** aberto · **Registrado em:** 2026-09-04 · **Onde vive:** `.github/ci/run-checks.sh` (guarda 4) + `tests/golden/run_golden.py` (`MODULOS_OBSERVACIONAIS`)

**O que existe.** A guarda 4 do CI exige que `tests/golden/run_golden.py` exista e passe assim que `src/` existir. Dentro do harness, a suite de margens compara os nomes de arquivo em `src/` com uma allowlist (`{"diagnostico_fonte.py"}`) e reprova qualquer nome fora dela.

**A limitação.** É controle de **nome de arquivo**, não de comportamento. Consequências concretas:

- Lógica de cálculo colocada **dentro** de um módulo que está na allowlist passa sem alarme.
- `glob("*.py")` não é recursivo: `src/calculo/margens.py` é invisível para a verificação.
- A própria allowlist é uma linha editável no arquivo de teste. O diff toca `tests/golden/`, que é caminho-sentinela e dispara a pergunta Muda-numero no `/pre-pr`, mas quem responde a pergunta é a sessão.
- Falso positivo é frequente e barato de contornar: qualquer módulo novo e legítimo (um leitor separado, um formatador de relatório) reprova, e o contorno natural é editar a guarda. Gate que ensina a mexer no gate.

**O que a Suite 1 do harness cobre de verdade** (comportamental, mas raso): nenhum campo de saída com nome de indicador; classes de achado restritas ao vocabulário observacional; contagens iguais às cruas; duplicata preservada; hash da origem inalterado; saída determinística. Isso inspeciona o **formato da saída**, não o cálculo — um número calculado emitido sob uma chave de nome neutro, ou embutido no texto de uma descrição, passa.

**Registro honesto de como a verificação chegou aqui.** A versão inicial dessa checagem varria o texto livre do relatório e foi **enfraquecida de propósito** durante a implementação, porque batia no nome do parâmetro `limiar_margem_servir_baixa` presente na fixture. Trocou-se robustez por CI verde, e isso não foi declarado no PR original.

**Como não confiar nela indevidamente.** O gate real do trabalho que produz número é o `/change-number`: fonte registrada, golden before/after, aprovação de quem valida número (Bruno Lima) antes do merge. A guarda 4 é alarme de fumaça, não fechadura, e não deve ser citada como proteção comportamental.

**Correção estrutural:** demanda separada no `aucta-dev-core` (não neste projeto, não no PR da feature #8), por decisão do owner técnico em 2026-09-04. Direções levantadas, nenhuma aprovada: declarar módulos de cálculo em `pointers.md` em vez de na allowlist do teste; exigir que todo número na saída do diagnóstico seja contagem, tamanho ou valor copiado literalmente da fonte; congelar o inventário de achados como golden do próprio diagnóstico; varredura recursiva de `src/`.
