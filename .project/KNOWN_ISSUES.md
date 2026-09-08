# Known issues — Aucta Foods · Rentabilidade por Cliente

> Erros e limitações ainda relevantes (blueprint 6.1). Item sai daqui quando resolvido ou quando deixa de ter valor operacional.

## KI-001 · A guarda de módulos de cálculo é lista de nomes, não verificação de comportamento

**Status:** aberto (parcialmente endereçado em 2026-09-08) · **Registrado em:** 2026-09-04 · **Onde vive:** `.github/ci/run-checks.sh` (guarda 4) + `tests/golden/run_golden.py` (`MODULOS_DECLARADOS`)

**O que existe.** A guarda 4 do CI exige que `tests/golden/run_golden.py` exista e passe assim que `src/` existir. Dentro do harness, a suite 4 compara os nomes de arquivo em `src/` com um inventário declarado e reprova qualquer módulo que não esteja lá.

**A limitação.** É controle de **nome de arquivo**, não de comportamento. Consequências concretas:

- Lógica de cálculo colocada **dentro** de um módulo que está no inventário passa sem alarme.
- ~~`glob("*.py")` não é recursivo: `src/calculo/margens.py` é invisível para a verificação.~~ **Corrigido em 2026-09-08:** a varredura passou a usar `rglob`, e a prova negativa está no PR do ciclo (módulo novo em `src/` reprova a suite 4).
- O próprio inventário é uma linha editável no arquivo de teste. O diff toca `tests/golden/`, que é caminho-sentinela e dispara a pergunta Muda-numero no `/pre-pr`, mas quem responde a pergunta é a sessão.
- Falso positivo é frequente e barato de contornar: qualquer módulo novo e legítimo (um leitor separado, um formatador de relatório) reprova, e o contorno natural é editar a guarda. Gate que ensina a mexer no gate.

**O que mudou em 2026-09-08 (ciclo da base tratada).** O primeiro módulo não observacional entrou em `src/`. A guarda **não** foi enfraquecida para o código passar. O que foi feito:

- A suite 4 passou a exigir que todo módulo de `src/` declare a sua **categoria** (`observacional` / `tratamento`), mantendo a proibição de módulo de **cálculo** enquanto TRUTH-001..005 seguirem preliminares.
- A varredura passou a ser recursiva.
- O limite de escopo do módulo novo deixou de depender do nome do arquivo e passou a ser sustentado por confirmação **comportamental** na suite 5: contrato de colunas fechado e conferido na ordem, nenhuma chave de indicador em nenhum nível da saída, e **todo valor da base tratada conferido contra a fonte, valor a valor** — um número calculado não sobrevive a essa confirmação, mesmo sob nome neutro.
- Essa verificação é **estrutural** (chaves e valores), não varredura de texto livre. A varredura de texto livre foi justamente a que se enfraqueceu no ciclo anterior; repetir a abordagem repetiria o problema.

**O que segue aberto.** A limitação central: nome de arquivo não é comportamento, e cálculo embutido em módulo declarado ainda passaria pela suite 4. A confirmação comportamental existe para o diagnóstico (suite 1) e para o tratamento (suite 5) porque em ambos a saída é cópia da fonte — quando o módulo de cálculo existir, a saída legítima passa a conter números derivados, e nenhuma das duas abordagens serve. A guarda 4 é alarme de fumaça, não fechadura, e não deve ser citada como proteção comportamental.

**Registro honesto de como a verificação chegou aqui.** A versão inicial dessa checagem varria o texto livre do relatório e foi **enfraquecida de propósito** durante a implementação, porque batia no nome do parâmetro `limiar_margem_servir_baixa` presente na fixture. Trocou-se robustez por CI verde, e isso não foi declarado no PR original.

**Como não confiar nela indevidamente.** O gate real do trabalho que produz número é o `/change-number`: fonte registrada, golden before/after, aprovação de quem valida número (Bruno Lima) antes do merge.

**Correção estrutural:** demanda separada no `aucta-dev-core` (não neste projeto), por decisão do owner técnico em 2026-09-04. Direções levantadas: declarar módulos de cálculo em `pointers.md` em vez de na allowlist do teste (**parcial** — o inventário ganhou categoria, mas continua no arquivo de teste); exigir que todo número na saída seja contagem, tamanho ou valor copiado literalmente da fonte (**feito para a camada de tratamento**, suite 5); congelar o inventário de achados como golden do próprio diagnóstico (**não feito**); varredura recursiva de `src/` (**feito**).

## KI-002 · Nenhuma regra aprovada para competência fora do período declarado

**Status:** aberto · **Registrado em:** 2026-09-08 · **Onde vive:** `src/base_tratada.py` (marca `fora_do_periodo_declarado`)

**O que existe.** O comando aceita `--periodo` e marca o pedido cuja competência cai fora da janela declarada, sem mudar o destino do registro: ele continua entrando na base tratada.

**A limitação.** Não existe decisão registrada sobre o que fazer com movimento de competência fora do período processado — entra marcado, é retido, ou é excluído por regra? Na massa do piloto o caso não ocorre (todos os pedidos caem entre jan e mar/2026), então nenhum golden cobre o comportamento. A escolha atual (marcar e deixar entrar) é a mais conservadora possível: não descarta nada em silêncio, mas também não é uma regra aprovada.

**Decisão pendente:** DEC-08, na pauta do próximo ciclo, junto com a regra para visita de cliente fora do cadastro (hoje tratada por analogia a TRUTH-013, também sem decisão registrada).
