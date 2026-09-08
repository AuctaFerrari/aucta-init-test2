# Índice de decisões de negócio — Aucta Foods · Rentabilidade por Cliente

> Regras operacionais aprovadas pelo dono do número. Cada item é referenciável por código, tem autorizador nomeado, data e URL de aprovação. Decisão nova entra aqui, não em `TRUTHS.md`: as verdades canônicas descrevem como o projeto é entendido; as decisões DN descrevem como a regra opera.

**Aprovador de todos os itens:** Bruno Lima, Controladoria (dono do número em `OWNERS.md`).
**Papel:** projeto de teste 100% sintético com owners fictícios. O papel de Bruno Lima foi **explicitamente ativado** por Caio Ferrari, item a item, nas aprovações abaixo. O papel nunca é inferido de titularidade técnica, autorização genérica anterior, silêncio ou pedido para prosseguir.
**Data das aprovações:** 2026-09-08.

| Aprovação | URL |
| --- | --- |
| DN-01 a DN-12, fórmulas, regras, exceções, golden e tolerância | https://github.com/AuctaFerrari/aucta-init-test2/issues/10#issuecomment-5589411324 |
| DN-13, ordem de avaliação, comportamento de A5, taxonomia | https://github.com/AuctaFerrari/aucta-init-test2/issues/10#issuecomment-5589595626 |
| Invalidação da aprovação anterior (sem efeito) | https://github.com/AuctaFerrari/aucta-init-test2/issues/10#issuecomment-5589236253 |

Todo item abaixo é **Muda-numero: sim** — decide quais registros e quais valores alimentam o número entregue.

## DN-01 · Movimento de cliente inativo

Movimentos de cliente inativo **permanecem** na base tratada e devem ser **explicitamente marcados** `cliente_inativo`. Não são excluídos em silêncio.
Artefatos afetados: base tratada de pedidos e de visitas (coluna de marcas), relatório de tratamento.

## DN-02 · Competência do pedido

A competência do pedido é determinada por `data_pedido`. `atualizado_em` determina **apenas** a precedência de versão do registro e **nunca** move a competência econômica.
Artefatos afetados: base tratada, reconciliação por competência, veredito por competência.

## DN-03 · `custo_manuseio` igual a zero

`custo_manuseio = 0` é **valor legítimo da fonte**, não dado ausente. Preservar o valor e manter um **aviso informativo de perfil da fonte** enquanto a coluna inteira permanecer zerada.
Artefatos afetados: base tratada, relatório de tratamento (aviso informativo, não bloqueante).

## DN-04 · Empate de `atualizado_em`

Se versões duplicadas empatarem no `atualizado_em` mais recente, **todas as versões empatadas vão para quarentena** e a **competência afetada é bloqueada**. Nunca escolher por ordem do arquivo.
Interage com DN-10 de forma intencional: empate em janeiro torna janeiro `não calcular`, mesmo estando limpo na fixture atual.

## DN-05 · Destino do registro com exceção bloqueante

Registro com exceção bloqueante vai para **quarentena, fora da base tratada oficial**, preservando: o registro bruto, o motivo, a regra, o identificador de origem, a competência quando determinável e a rastreabilidade.

## DN-06 · Status de pedido admitidos

Usar **lista branca**. Somente `Faturado` entra na base tratada neste piloto. `Cancelado` é **exclusão documentada não bloqueante** (TRUTH-012). Qualquer status desconhecido vai para **quarentena e bloqueia a competência afetada**.

## DN-07 · Visita de cliente ausente do cadastro

Visita cujo cliente não existe no cadastro vai para **quarentena**. Se a competência puder ser determinada a partir de uma data de visita válida, **bloquear essa competência**. Se nenhuma competência puder ser determinada com segurança, **bloquear todo o período de processamento solicitado**.

## DN-08 · Registros fora do `--periodo` declarado

Registros fora do período declarado estão **fora do escopo da execução**: **excluir da saída tratada oficial**, **reportar e reconciliar separadamente** como `fora_do_periodo`, e **não** classificar como exceção bloqueante. Observações de qualidade da fonte podem ser reportadas, mas são não bloqueantes para o período solicitado.
**Rejeitado explicitamente:** o comportamento de "marcar e manter" na base tratada. Registro fora do período nunca entra no período solicitado apenas com uma marca.

## DN-09 · Aritmética e arredondamento

Usar **aritmética decimal, nunca ponto flutuante binário**, para cálculo monetário de negócio. **Preservar precisão integral nos cálculos intermediários** e arredondar as saídas monetárias **somente** no resultado final por cliente/mês e nos totais de reconciliação, com **duas casas decimais** e política **`ROUND_HALF_UP`**. Contagens permanecem inteiras.

## DN-10 · Escopo do bloqueio de publicação

Exceções bloqueantes bloqueiam **apenas a competência afetada**, não o relatório inteiro. Janeiro e março podem ser publicados se estiverem limpos; **fevereiro recebe veredito bloqueado** na fixture atual. Competência bloqueada **pode** produzir artefatos de diagnóstico e de quarentena, mas **nenhum indicador oficial nem resultado de rentabilidade publicável**.

## DN-11 · Normalização de identificadores e colisão

- remover espaço em branco no início e no fim;
- converter letras para maiúscula;
- **preservar** espaço em branco interno;
- **preservar** pontuação e outros caracteres não alfanuméricos;
- **não** inferir prefixos nem zeros à esquerda;
- **preservar o identificador bruto original** em campo separado de rastreabilidade;
- se identificadores brutos distintos colidirem após a normalização, **colocar em quarentena todos os registros afetados e bloquear toda competência afetada determinável**;
- se o impacto de uma colisão de cadastro não puder ser delimitado com segurança, **falhar a execução** em vez de escolher por ordem de leitura.

Substitui a expressão ambígua "sem espaços" de TRUTH-015.

## DN-12 · Parâmetro `custo_por_visita_realizada` — piloto

`custo_por_visita_realizada = R$ 100,00 por visita válida`, **vigência 2026-01-01 a 2026-03-31**, escopo **piloto sintético Aucta Foods**, owner **Bruno Lima**, status **`Aprovado para piloto`**. **Nenhum fallback silencioso** é permitido fora do período de vigência.
O status observado na fonte bruta (`Provisório`, em `tests/fixtures/parametros.csv`) é **preservado sem alteração**: a fonte registra o que a fonte diz. O override aprovado vive em `.project/PARAMETERS.md`.

## DN-13 · Pedido com competência inutilizável

Se `data_pedido` estiver **ausente, vazia, malformada ou de outra forma inutilizável**, o pedido vai para **quarentena**. Como a competência não pode ser determinada com segurança, **todo o período de processamento solicitado é bloqueado**. O registro **nunca** pode ser classificado silenciosamente como fora do período. Artefatos de diagnóstico, quarentena e veredito bloqueado continuam sendo produzidos quando tecnicamente possível, mas **nenhuma saída tratada oficial nem indicador de rentabilidade** pode ser publicado.
Origem: caso descoberto pela derivação independente, ausente do conjunto aprovado até então, registrado como aberto em vez de resolvido pelo agente.

## Ordem de avaliação aprovada

1. Validar se `data_pedido` está presente e é parseável.
2. Se inutilizável, aplicar **DN-13**.
3. Se válida, determinar a competência e compará-la com `--periodo`.
4. Se fora do período solicitado, aplicar **DN-08**: excluir da saída oficial, reconciliar como `fora_do_periodo` e **não** rodar as demais regras bloqueantes para o período solicitado.
5. Observações de qualidade da fonte podem ser reportadas para registro fora do período, sem bloquear o período solicitado.
6. Se dentro do período, aplicar todas as demais regras de tratamento.

## Esclarecimentos de interação aprovados

**I-01 · Defeitos combinados em visita.** Visita com cliente sem correspondência **e** sem `data_realizada` utilizável: prevalece a regra mais estrita — quarentena, não conta como válida, **bloqueio de todo o período solicitado** porque a competência não é determinável, os **dois defeitos reportados independentemente**, e o caráter não bloqueante de TRUTH-014 **não** anula o defeito de identidade de DN-07.

**I-02 · Fora do período.** DN-08 muda deliberadamente o comportamento implementado no ramo contaminado. "Marcar e manter" está rejeitado e não deve ser tratado como aprovado.

**I-03 · Empate de timestamp.** A interação DN-04 × DN-10 é intencional: empate manda todas as versões para quarentena e bloqueia a competência afetada, inclusive janeiro.

**I-04 · Colisão não delimitável (cenário A5).** DN-13 bloqueia o período solicitado por competência ausente; DN-11 permanece mais estrita quando a colisão não pode ser delimitada; a execução retorna **resultado diferente de zero, controlado**, e produz **artefato mínimo auditável de falha** quando tecnicamente possível; **nenhuma** saída tratada oficial é produzida; **nunca** se escolhe cliente ou registro por ordem de arquivo.

## GATE-CN-01 · Gate de validação funcional do primeiro `/change-number`

**Status: FECHADO em 2026-09-08.** Fecha somente a **aprovação funcional**. Não torna conforme nenhuma implementação.

Cobertura exigida para o fechamento, toda satisfeita item a item: TRUTH-001 a TRUTH-005 · DN-01 a **DN-13** · TRUTH-011 a TRUTH-015 · EX-01 a EX-07 · GC-01 a GC-03 · tolerância R$ 0,00 · parâmetros `custo_por_visita_realizada` e `custo_operacional_por_pedido` · política decimal e de arredondamento · escopo de bloqueio · normalização e rastreabilidade · esclarecimentos I-01 a I-04 · ordem de avaliação.

O gate **reabre** se qualquer regra aprovada mudar: item novo exige aprovação nominal, individual, do dono do número.

## Mapeamento de identificadores antigos

| Antigo | Novo | Observação |
| --- | --- | --- |
| DEC-01 | DN-01 | — |
| DEC-02 | DN-02 | — |
| DEC-03 | DN-03 | — |
| DEC-04 | DN-04 | — |
| **DEC-05** | — | **Aposentada como decisão.** Não era decisão de negócio, era o próprio gate de validação. Convertida em `GATE-CN-01` |
| DEC-06 | DN-05 | — |
| DEC-07 | DN-06 | — |
| DEC-08 | **DN-07 + DN-08** | Continha duas escolhas de política independentes, desmembradas |
| — | DN-09 a DN-13 | Itens novos: arredondamento, escopo de bloqueio, normalização, parâmetro do piloto, competência inutilizável |

## Taxonomia

Decidido pelo owner técnico em 2026-09-08: as regras operacionais novas ficam aqui como DN-01 a DN-13; **TRUTH-016 a TRUTH-020 não são criadas nesta recuperação**; apenas os identificadores TRUTH já existentes são refinados. As TRUTH-016..020 gravadas no ramo `feat/base-tratada-oficial` (head `5c02e59`) foram escritas com fonte inválida e **não** correspondem às decisões aprovadas aqui.
