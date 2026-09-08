"""Harness de conferencia — Aucta Foods · Rentabilidade por Cliente (tier 2).

Chamado pela guarda 4 do CI (`.github/ci/run-checks.sh`) sempre que `src/` existe.
Cada suite recomputa a referencia por um caminho INDEPENDENTE do codigo sob teste
(implementacao propria, so `csv` da stdlib) e compara.

Suites:
  1. Diagnostico da fonte (observacional) — contagens, nulos, duplicidades e
     chaves sem correspondencia recomputadas aqui; cobertura das excecoes
     conhecidas (tests/fixtures/expected_exceptions.csv); prova de que nada foi
     tratado; determinismo das saidas; integridade do arquivo de origem.
  2. Caminho .xlsx (entrada principal de producao) — gera a fixture .xlsx a
     partir das CSVs controladas, executa o mesmo entrypoint sobre ela e exige
     resultado identico ao caminho CSV, com o arquivo de entrada intocado.
  3. Textos de apresentacao em pt-BR (titulos e cabecalhos acentuados, nenhuma
     forma desacentuada nos textos fixos), mapeamento de apresentacao dos enums
     (contrato ASCII preservado no JSON, rotulo acentuado no Markdown, coluna de
     status da evidencia) e decisoes pendentes consolidadas: D-003 e D-006
     seguem como dois achados, com uma unica decisao no resumo.
  4. Inventario de modulos de src/ — todo modulo declarado com a sua categoria
     (observacional / tratamento) e nenhum modulo de CALCULO permitido enquanto
     as formulas TRUTH-001..005 seguem pendentes de validacao formal da
     controladoria (gate do primeiro /change-number). ATENCAO: a checagem por
     nome de arquivo NAO e analise de comportamento — limitacao registrada em
     .project/KNOWN_ISSUES.md (KI-001). O que sustenta o limite de escopo de
     cada modulo sao as suites comportamentais 1 e 5.
  5. Base tratada oficial — populacao, excecoes, log, reconciliacao e veredito
     por competencia, comparados com a recomputacao independente feita aqui E
     com os golden congelados (golden_base_tratada, golden_reconciliacao,
     golden_veredito_competencia); contrato de colunas fechado, valores
     identicos a fonte, origem intocada e saida deterministica.
  6. Base tratada pelo caminho .xlsx — mesmo entrypoint sobre a planilha gerada
     no teste, exigindo resultado identico ao caminho CSV.
  7. Derivabilidade de GC-01..03 a partir da base tratada — a conta e feita
     nesta suite, nunca em src/: prova que os insumos dos casos de conferencia
     saem da base tratada com tolerancia R$ 0,00, sem que a entrega calcule
     qualquer margem.

Uso: python tests/golden/run_golden.py
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
FIXTURES = RAIZ / "tests" / "fixtures"
SRC = RAIZ / "src"

# Inventario declarado dos modulos de src/, com a categoria de cada um. Nenhum
# modulo de CALCULO e permitido enquanto as formulas TRUTH-001..005 nao tiverem
# validacao formal da controladoria.
# LIMITACAO CONHECIDA (KI-001, segue aberta): a checagem por nome de arquivo nao
# e verificacao de comportamento. O que sustenta o limite de escopo de cada
# modulo sao as suites comportamentais: a 1 para o diagnostico (nenhum campo de
# indicador na saida) e a 5 para o tratamento (contrato de colunas fechado, toda
# chave conferida e todo valor identico a fonte). A correcao estrutural da guarda
# e demanda do aucta-dev-core (issue #27) — nao se resolve aqui, e a guarda nao
# foi enfraquecida para o codigo deste ciclo passar.
MODULOS_DECLARADOS = {
    "diagnostico_fonte.py": "observacional",
    "base_tratada.py": "tratamento",
}
CATEGORIAS_SEM_CALCULO = {"observacional", "tratamento"}

# Abas correspondentes a cada CSV de fixture (usado para gerar a fixture .xlsx).
CONTRATO_ABAS = {
    "clientes": "Clientes",
    "vendas": "Vendas",
    "custos_logisticos": "Custos_Logisticos",
    "visitas": "Visitas",
    "parametros": "Parametros",
}

falhas: list[str] = []


def checar(condicao: bool, rotulo: str, detalhe: str = "") -> None:
    if condicao:
        print(f"  ok: {rotulo}")
    else:
        print(f"  FALHA: {rotulo}" + (f" — {detalhe}" if detalhe else ""))
        falhas.append(rotulo)


def ler(nome: str) -> list[dict]:
    with (FIXTURES / nome).open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def sha256(caminho: Path) -> str:
    return hashlib.sha256(caminho.read_bytes()).hexdigest()


def rodar_diagnostico(saida: Path, entrada: Path = FIXTURES, rotulo: str = "harness") -> dict:
    """Executa o MESMO entrypoint de producao (src/diagnostico_fonte.py)."""
    resultado = subprocess.run(
        [sys.executable, str(SRC / "diagnostico_fonte.py"),
         "--entrada", str(entrada), "--saida", str(saida),
         "--rotulo", rotulo, "--periodo", "2026-01:2026-03"],
        cwd=RAIZ, capture_output=True, text=True,
    )
    if resultado.returncode != 0:
        print(resultado.stdout)
        print(resultado.stderr)
        raise SystemExit("FALHA: diagnostico terminou com erro")
    return json.loads((saida / f"diagnostico_{rotulo}.json").read_text(encoding="utf-8"))


def suite_diagnostico() -> dict:
    print("== Suite 1: diagnostico da fonte (observacional) ==")

    hashes_antes = {p.name: sha256(p) for p in sorted(FIXTURES.glob("*.csv"))}

    with tempfile.TemporaryDirectory() as tmp:
        saida_a, saida_b = Path(tmp) / "a", Path(tmp) / "b"
        payload = rodar_diagnostico(saida_a)
        rodar_diagnostico(saida_b)

        # 1. fonte intocada (regra 2 de client-rules.md)
        hashes_depois = {p.name: sha256(p) for p in sorted(FIXTURES.glob("*.csv"))}
        checar(hashes_antes == hashes_depois, "arquivos de origem nao foram alterados")

        # 2. determinismo: mesma entrada -> bytes identicos
        for nome in ("diagnostico_harness.json", "diagnostico_harness.md"):
            checar((saida_a / nome).read_bytes() == (saida_b / nome).read_bytes(),
                   f"saida deterministica ({nome})")

    # 3. contagens recomputadas de forma independente
    tabelas = {n: ler(f"{n}.csv") for n in
               ("clientes", "vendas", "custos_logisticos", "visitas", "parametros")}
    esperado = {n: len(r) for n, r in tabelas.items()}
    checar(payload["resumo"]["registros_lidos"] == esperado,
           "contagem de registros por tabela", f"{payload['resumo']['registros_lidos']} != {esperado}")

    # 4. nenhuma regra de tratamento aplicada: brutos preservados
    checar(esperado["vendas"] == 13, "vendas lidas na integra (duplicata preservada)")
    ids_vendas = [r["pedido_id"] for r in tabelas["vendas"]]
    checar(ids_vendas.count("O006") == 2, "duplicata O006 continua na leitura (nao deduplicada)")

    # 5. nulos por coluna recomputados
    for tabela, coluna in (("vendas", "custo_produto"), ("custos_logisticos", "frete"),
                           ("visitas", "data_realizada")):
        nulos_ind = sum(1 for r in tabelas[tabela] if (r.get(coluna) or "").strip() == "")
        nulos_diag = payload["tabelas"][tabela]["perfil_colunas"][coluna]["nulos"]
        checar(nulos_ind == nulos_diag, f"vazios recomputados em {tabela}.{coluna}",
               f"{nulos_ind} != {nulos_diag}")

    # 6. duplicidades recomputadas
    duplicados_ind = sorted({i for i in ids_vendas if ids_vendas.count(i) > 1})
    duplicados_diag = sorted({a["id"] for a in payload["achados"]
                              if a["classe"] == "DUPLICIDADE" and a["entidade"] == "vendas"})
    checar(duplicados_ind == duplicados_diag, "identificadores duplicados em vendas",
           f"{duplicados_ind} != {duplicados_diag}")

    # 7. chaves sem correspondencia recomputadas (comparacao crua, sem normalizar)
    cadastro = {r["cliente_id"] for r in tabelas["clientes"]}
    orfaos_ind = sorted({r["pedido_id"] for r in tabelas["vendas"] if r["cliente_id"] not in cadastro})
    relacao = next(r for r in payload["relacionamentos"]
                   if r["relacao"] == "vendas.cliente_id -> clientes.cliente_id")
    orfaos_diag = sorted({d["id_origem"] for d in relacao["detalhe"]})
    checar(orfaos_ind == orfaos_diag, "chaves de cliente sem correspondencia em vendas",
           f"{orfaos_ind} != {orfaos_diag}")

    # 8. cobertura das excecoes conhecidas (referencia aprovada na iniciacao).
    #    Procura nas DUAS listas: atencao (achados) e perfil/inventario.
    texto_saida = json.dumps([payload["achados"], payload["perfil_fonte"]], ensure_ascii=False)
    nao_cobertas = [linha["id"] for linha in ler("expected_exceptions.csv")
                    if linha["id"] not in texto_saida]
    checar(not nao_cobertas, "toda excecao conhecida (EX-01..07) aparece no diagnostico",
           f"ausentes: {nao_cobertas}")

    # 8b. separacao exigida pelo consultor: inventario de status nao infla a
    #     contagem de problemas; atencao = anomalia/aviso, perfil = informativo
    checar(all(a["severidade"] in ("anomalia", "aviso") for a in payload["achados"]),
           "lista de atencao contem apenas anomalia e aviso")
    checar(all(a["severidade"] == "informativo" for a in payload["perfil_fonte"]),
           "lista de perfil da fonte contem apenas itens informativos")
    checar(payload["resumo"]["achados_total"] == len(payload["achados"])
           and payload["resumo"]["itens_perfil_fonte"] == len(payload["perfil_fonte"]),
           "contadores do resumo separam atencao e perfil")
    codigos = [a["codigo"] for a in payload["achados"]] + [a["codigo"] for a in payload["perfil_fonte"]]
    checar(len(codigos) == len(set(codigos))
           and all(c.startswith("D-") for c in codigos[:len(payload["achados"])]),
           "codigos unicos, com prefixo D- para atencao e P- para perfil")

    # 9. nenhum indicador de negocio calculado: nem como campo de saida,
    #    nem como classe de achado fora do vocabulario observacional
    proibidos = {"receita_liquida", "margem_contribuicao", "margem_servir",
                 "margem", "ranking", "classificacao", "indicador"}
    chaves: set[str] = set()

    def coletar(no) -> None:
        if isinstance(no, dict):
            chaves.update(no.keys())
            for valor in no.values():
                coletar(valor)
        elif isinstance(no, list):
            for item in no:
                coletar(item)

    coletar(payload)
    checar(not (chaves & proibidos), "nenhum campo de indicador de negocio na saida",
           f"campos: {sorted(chaves & proibidos)}")

    classes_ok = {"ESQUEMA", "COMPLETUDE", "DUPLICIDADE", "RELACIONAMENTO", "CONSISTENCIA", "FONTE"}
    classes = {a["classe"] for a in payload["achados"] + payload["perfil_fonte"]}
    checar(classes <= classes_ok, "achados restritos ao vocabulario observacional",
           f"classes inesperadas: {sorted(classes - classes_ok)}")

    return payload


def gerar_xlsx(destino: Path) -> Path:
    """Gera a fixture .xlsx a partir das CSVs controladas, uma aba por arquivo.

    Conteudo deterministico: as celulas saem das mesmas CSVs versionadas, na
    mesma ordem. Os bytes do arquivo variam entre execucoes (o formato xlsx e
    um zip com metadados de tempo), por isso a comparacao entre os caminhos e
    feita pelo CONTEUDO do diagnostico, nunca pelo hash do .xlsx.
    """
    from openpyxl import Workbook

    livro = Workbook()
    livro.remove(livro.active)
    for nome in ("clientes", "vendas", "custos_logisticos", "visitas", "parametros"):
        aba = CONTRATO_ABAS[nome]
        planilha = livro.create_sheet(aba)
        with (FIXTURES / f"{nome}.csv").open(newline="", encoding="utf-8") as fh:
            for linha in csv.reader(fh):
                planilha.append(linha)
    caminho = destino / "01_Base_Operacional_Fixture.xlsx"
    livro.save(caminho)
    return caminho


def comparavel(payload: dict) -> dict:
    """Recorte do diagnostico que deve ser igual nos dois caminhos de entrada.

    Exclui o bloco 'fonte' de cada tabela (nome do arquivo e SHA-256 mudam por
    construcao) e o bloco 'entrada' (nome e tipo da entrada).
    """
    return {
        "registros_lidos": payload["resumo"]["registros_lidos"],
        "achados_total": payload["resumo"]["achados_total"],
        "itens_perfil_fonte": payload["resumo"]["itens_perfil_fonte"],
        "achados": [(a["classe"], a["entidade"], str(a["id"]), a["severidade"], a["descricao"])
                    for a in payload["achados"]],
        "perfil_fonte": [(a["classe"], a["entidade"], str(a["id"]), a["descricao"])
                         for a in payload["perfil_fonte"]],
        "relacionamentos": [(r["relacao"], r["sem_correspondencia"]) for r in payload["relacionamentos"]],
        "tabelas": {n: {k: v for k, v in t.items() if k not in ("fonte", "aba_ou_arquivo")}
                    for n, t in payload["tabelas"].items()},
    }


def suite_excel(payload_csv: dict) -> None:
    print("== Suite 2: caminho .xlsx (entrada principal de producao) ==")
    try:
        import openpyxl
    except ImportError:
        checar(False, "openpyxl disponivel (requirements.txt)",
               "instale com: python -m pip install --require-hashes -r requirements.txt")
        return
    checar(True, f"openpyxl disponivel (versao {openpyxl.__version__})")

    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        xlsx = gerar_xlsx(base)
        hash_antes = sha256(xlsx)

        payload_xlsx = rodar_diagnostico(base / "saida_a", entrada=xlsx, rotulo="harness_xlsx")
        rodar_diagnostico(base / "saida_b", entrada=xlsx, rotulo="harness_xlsx")

        checar(sha256(xlsx) == hash_antes, "arquivo .xlsx de entrada nao foi alterado pela leitura")
        checar((base / "saida_a" / "diagnostico_harness_xlsx.json").read_bytes()
               == (base / "saida_b" / "diagnostico_harness_xlsx.json").read_bytes(),
               "saida deterministica no caminho .xlsx (mesmo arquivo, duas execucoes)")

        esperado, obtido = comparavel(payload_csv), comparavel(payload_xlsx)
        checar(esperado["registros_lidos"] == obtido["registros_lidos"],
               "contagens iguais nos dois caminhos",
               f"{esperado['registros_lidos']} != {obtido['registros_lidos']}")
        checar(esperado["achados"] == obtido["achados"],
               "achados de atencao identicos nos dois caminhos",
               f"csv-so: {sorted(set(esperado['achados']) - set(obtido['achados']))} | "
               f"xlsx-so: {sorted(set(obtido['achados']) - set(esperado['achados']))}")
        checar(esperado["perfil_fonte"] == obtido["perfil_fonte"],
               "perfil da fonte identico nos dois caminhos")
        checar(esperado["relacionamentos"] == obtido["relacionamentos"],
               "relacionamentos identicos nos dois caminhos")
        checar(esperado["tabelas"] == obtido["tabelas"],
               "esquema, tipos e perfis de coluna identicos nos dois caminhos")
        checar(payload_xlsx["entrada"]["tipo"] == "planilha Excel",
               "diagnostico registra a entrada como planilha Excel")
        for nome, tabela in payload_xlsx["tabelas"].items():
            if not tabela["fonte"].get("origem", "").endswith(f"::{CONTRATO_ABAS[nome]}"):
                checar(False, f"origem da tabela {nome} aponta para a aba lida",
                       tabela["fonte"].get("origem"))
                break
        else:
            checar(True, "origem de cada tabela aponta para a aba lida no arquivo")


# Textos fixos de apresentação que devem existir acentuados no relatório.
TITULOS_ACENTUADOS = [
    "# Diagnóstico de qualidade da fonte",
    "## Achados que exigem atenção",
    "## Perfil e inventário da fonte",
    "## Decisões pendentes do negócio",
    "| Código | Sev. | Classe | Entidade | ID | Descrição | Status da evidência | Evidência | Decisão pendente |",
    "| Código | Classe | Entidade | Item | Descrição | Status da evidência | Evidência | Decisão pendente |",
    "| Relação | Força | Registros | Sem correspondência |",
    "- Período informado:",
    "Distribuição de",
]

# Formas SEM acento que nunca devem reaparecer nos textos de apresentação.
# São palavras que só existem no texto fixo — nenhuma delas é nome de coluna,
# valor da fonte ou chave do JSON (chaves seguem snake_case ASCII de propósito).
FORMAS_SEM_ACENTO = [
    "Diagnostico", "Decisao", "Decisoes", "Codigo", "Descricao", "Evidencia",
    "Periodo", "Relacao", "Distribuicao", "negocio", "decisao", "versao",
    "atencao", "inventario", "numerico", "padrao", "competencias",
    "correspondencia", "excluido", "excluidos", "legitimo", "unico",
]

# Mapa de apresentação esperado no Markdown (enum tecnico -> rotulo exibido).
# Declarado aqui de forma independente do modulo sob teste, de proposito.
ROTULOS_ESPERADOS = {
    "observado": "Observado",
    "hipotese": "Hipótese",
    "obrigatoria": "Obrigatória",
    "informativa": "Informativa",
    "COMPLETUDE": "Completude",
    "CONSISTENCIA": "Consistência",
    "DUPLICIDADE": "Duplicidade",
    "FONTE": "Fonte",
    "RELACIONAMENTO": "Relacionamento",
}


def suite_textos(payload: dict, markdown: str) -> None:
    print("== Suite 3: textos de apresentação em pt-BR e decisões consolidadas ==")

    # 1. títulos e cabeçalhos acentuados presentes no relatório
    ausentes = [titulo for titulo in TITULOS_ACENTUADOS if titulo not in markdown]
    checar(not ausentes, "títulos e cabeçalhos do relatório acentuados",
           f"ausentes: {ausentes}")

    # 2. nenhuma forma sem acento no relatório
    achadas = sorted({forma for forma in FORMAS_SEM_ACENTO
                      if re.search(rf"\b{re.escape(forma)}\b", markdown)})
    checar(not achadas, "relatório sem formas desacentuadas nos textos fixos",
           f"encontradas: {achadas}")

    # 3. nenhuma forma sem acento nos textos do JSON (chaves ficam fora:
    #    snake_case ASCII é intencional)
    textos = [payload["natureza"]] + payload["resumo"]["decisoes_pendentes"]
    for item in payload["achados"] + payload["perfil_fonte"]:
        textos += [item["descricao"], item["decisao_pendente"]]
    juntos = "\n".join(textos)
    achadas_json = sorted({forma for forma in FORMAS_SEM_ACENTO
                           if re.search(rf"\b{re.escape(forma)}\b", juntos)})
    checar(not achadas_json, "textos do JSON sem formas desacentuadas",
           f"encontradas: {achadas_json}")

    # 4. UTF-8 de verdade: o relatório decodifica e traz acentuação
    checar(any(c in markdown for c in "áâãéêíóôõúçÁÉÍÓÚ"),
           "relatório carrega caracteres acentuados (UTF-8)")

    # 5. D-003 e D-006 continuam DOIS achados distintos...
    o004 = [a for a in payload["achados"] if a["id"] == "O004"]
    classes = sorted(a["classe"] for a in o004)
    checar(len(o004) == 2 and classes == ["CONSISTENCIA", "RELACIONAMENTO"],
           "identificador fora do padrão e chave sem correspondência seguem como 2 achados",
           f"achados de O004: {[(a['codigo'], a['classe']) for a in o004]}")
    checar(sorted(a["status_evidencia"] for a in o004) == ["hipotese", "observado"],
           "os dois achados preservam status de evidência distintos")

    # 6. ...mas apontam para UMA decisão, com formulação idêntica
    decisoes_o004 = {a["decisao_pendente"] for a in o004}
    checar(len(decisoes_o004) == 1,
           "os dois achados usam a formulação canônica única da decisão",
           f"formulações: {sorted(decisoes_o004)}")

    # 7. o resumo consolidado traz essa decisão uma única vez
    sobre_normalizacao = [d for d in payload["resumo"]["decisoes_pendentes"]
                          if "normaliza" in d.lower()]
    checar(len(sobre_normalizacao) == 1,
           "resumo consolidado com uma única decisão de normalização",
           f"encontradas: {sobre_normalizacao}")

    # 8. o resumo não repete decisão nenhuma
    pendentes = payload["resumo"]["decisoes_pendentes"]
    checar(len(pendentes) == len(set(pendentes)), "resumo sem decisão repetida")

    # 9. contrato tecnico do JSON preservado: enums seguem ASCII
    enums_json = ({a["classe"] for a in payload["achados"] + payload["perfil_fonte"]}
                  | {a["status_evidencia"] for a in payload["achados"] + payload["perfil_fonte"]}
                  | {r["forca"] for r in payload["relacionamentos"]})
    fora_do_contrato = sorted(e for e in enums_json if e not in ROTULOS_ESPERADOS)
    checar(not fora_do_contrato, "JSON preserva os enums tecnicos originais (ASCII)",
           f"valores inesperados: {fora_do_contrato}")
    checar(all(e.isascii() for e in enums_json),
           "nenhum enum do JSON foi acentuado", f"enums: {sorted(enums_json)}")

    # 10. mapeamento aplicado no Markdown: rotulo presente, enum cru ausente
    faltando_rotulo = sorted(ROTULOS_ESPERADOS[e] for e in enums_json
                             if ROTULOS_ESPERADOS[e] not in markdown)
    checar(not faltando_rotulo, "Markdown exibe o rotulo de cada enum presente na saida",
           f"rotulos ausentes: {faltando_rotulo}")
    # A varredura por enum cru cobre so os enums em CAIXA ALTA (classes): os
    # enums minusculos ("observado", "obrigatoria") coincidem com palavras
    # comuns do texto corrido, e verificar a ausencia deles daria falso
    # positivo. Para esses, a garantia vem das verificacoes 11 e 12, que
    # conferem o rotulo na coluna certa de cada linha.
    crus_no_markdown = sorted(e for e in enums_json
                              if e.isupper() and re.search(rf"\b{re.escape(e)}\b", markdown))
    checar(not crus_no_markdown, "Markdown nao expoe classe tecnica crua",
           f"classes cruas no relatorio: {crus_no_markdown}")

    # 11. coluna de status da evidencia preenchida em toda linha de achado
    for item in payload["achados"] + payload["perfil_fonte"]:
        esperado = f"| {ROTULOS_ESPERADOS[item['status_evidencia']]} |"
        if esperado not in markdown:
            checar(False, f"coluna de status da evidencia visivel em {item['codigo']}",
                   f"esperado {esperado}")
            break
    else:
        checar(True, "coluna de status da evidencia visivel em todos os itens")

    # 12. D-006 especificamente: hipotese no JSON, Hipotese no Markdown
    d006 = [a for a in payload["achados"]
            if a["classe"] == "RELACIONAMENTO" and a["status_evidencia"] == "hipotese"]
    checar(len(d006) == 1 and d006[0]["codigo"] == "D-006",
           "D-006 e o unico achado com status_evidencia 'hipotese' no JSON",
           f"encontrados: {[(a['codigo'], a['status_evidencia']) for a in d006]}")
    if d006:
        linha = [l for l in markdown.splitlines() if l.startswith(f"| {d006[0]['codigo']} |")]
        checar(len(linha) == 1 and "| Hipótese |" in linha[0],
               "linha de D-006 no Markdown traz 'Hipótese' na coluna de status",
               f"linha: {linha}")
        outros = [a["codigo"] for a in payload["achados"] if a["codigo"] != "D-006"]
        linhas_outros = [l for l in markdown.splitlines()
                         if any(l.startswith(f"| {c} |") for c in outros)]
        checar(all("| Observado |" in l for l in linhas_outros),
               "todos os demais achados aparecem como 'Observado' no Markdown")


def suite_inventario_modulos() -> None:
    print("== Suite 4: inventario de modulos de src/ (guarda de modulo de calculo) ==")
    modulos = sorted(p.name for p in SRC.rglob("*.py")) if SRC.exists() else []
    nao_declarados = [m for m in modulos if m not in MODULOS_DECLARADOS]
    checar(not nao_declarados,
           "todo modulo de src/ esta declarado no inventario com a sua categoria",
           f"nao declarados: {nao_declarados} — modulo novo exige categoria declarada e, "
           "se produzir numero entregue, a suite de margens implementada e a validacao "
           "formal da controladoria (/change-number)")
    categorias = {MODULOS_DECLARADOS[m] for m in modulos if m in MODULOS_DECLARADOS}
    checar(categorias <= CATEGORIAS_SEM_CALCULO,
           "nenhum modulo de calculo em src/ enquanto TRUTH-001..005 seguem preliminares",
           f"categorias presentes: {sorted(categorias)}")
    print("  PENDENTE (nao aplicavel nesta versao): suite de margens sobre um modulo de "
          "calculo; as formulas TRUTH-001..005 aguardam validacao formal da controladoria. "
          "A derivabilidade dos GC-01..03 a partir da base tratada e conferida na suite 7.")


# ---------------------------------------------------------------------------
# Suites da base tratada (ciclo 2). Recomputacao INDEPENDENTE: a referencia
# abaixo e reimplementada aqui com `csv` da stdlib, sem importar nada de src/.
# ---------------------------------------------------------------------------

# Contrato de colunas declarado de forma INDEPENDENTE do modulo sob teste.
# Se o modulo passar a emitir uma coluna nova, a suite reprova.
COLUNAS_PEDIDOS_ESPERADAS = [
    "competencia", "pedido_id", "cliente_id", "cliente_id_origem", "razao_social",
    "regiao", "segmento", "canal", "status_cliente", "data_pedido", "atualizado_em",
    "receita_bruta", "desconto", "custo_produto", "frete", "custo_manuseio",
    "status_pedido", "marcas", "linha_origem_vendas",
]
COLUNAS_VISITAS_ESPERADAS = [
    "competencia", "visita_id", "cliente_id", "cliente_id_origem", "status",
    "data_planejada", "data_realizada", "classificacao", "marcas", "linha_origem",
]
# Nomes de campo proibidos em qualquer saida do tratamento. A verificacao e
# ESTRUTURAL (chaves e valores), nao varredura de texto livre: a versao de texto
# livre foi justamente a que se enfraqueceu no ciclo anterior (KI-001), porque
# batia no texto explicativo do proprio relatorio.
CHAVES_DE_INDICADOR = (
    "receita_liquida", "margem", "margem_contribuicao", "margem_servir", "ranking",
    "clientes_alerta", "indicador", "score", "limiar", "aderencia", "rentabilidade",
)


def rodar_base_tratada(saida: Path, entrada: Path = FIXTURES, rotulo: str = "harness") -> dict:
    """Executa o MESMO entrypoint de producao (src/base_tratada.py)."""
    resultado = subprocess.run(
        [sys.executable, str(SRC / "base_tratada.py"),
         "--entrada", str(entrada), "--saida", str(saida),
         "--rotulo", rotulo, "--periodo", "2026-01:2026-03"],
        cwd=RAIZ, capture_output=True, text=True,
    )
    if resultado.returncode != 0:
        print(resultado.stdout)
        print(resultado.stderr)
        raise SystemExit("FALHA: base tratada terminou com erro")
    return json.loads((saida / f"tratamento_{rotulo}.json").read_text(encoding="utf-8"))


def esperado_tratamento() -> dict:
    """Recomputacao independente das regras aprovadas, so com csv da stdlib."""
    def norm(valor):
        return (valor or "").strip().upper()

    def numero(valor):
        texto = (valor or "").strip()
        if texto == "":
            return None
        try:
            return float(texto)
        except ValueError:
            return None

    clientes = {norm(r["cliente_id"]): r for r in ler("clientes.csv")}
    logistica = {norm(r["pedido_id"]): r for r in ler("custos_logisticos.csv")}

    versoes = {}
    for i, reg in enumerate(ler("vendas.csv"), start=2):
        versoes.setdefault(norm(reg["pedido_id"]), []).append((i, reg))

    pedidos, excecoes = {}, {}
    for pid, grupo in versoes.items():
        ordenado = sorted(grupo, key=lambda par: (par[1]["atualizado_em"], par[0]))
        recentes = [p for p in ordenado if p[1]["atualizado_em"] == ordenado[-1][1]["atualizado_em"]]
        if len(recentes) > 1:                                   # TRUTH-020
            for linha, _ in ordenado:
                excecoes[(pid, linha)] = ("quarentena", "sim")
            continue
        for linha, _ in ordenado[:-1]:                          # TRUTH-011
            excecoes[(pid, linha)] = ("excluido_regra", "nao")
        linha, reg = ordenado[-1]
        status = reg["status_pedido"].strip()
        if status == "Cancelado":                               # TRUTH-012
            excecoes[(pid, linha)] = ("excluido_regra", "nao")
            continue
        problemas = (
            status != "Faturado"
            or norm(reg["cliente_id"]) not in clientes
            or numero(reg["receita_bruta"]) is None
            or numero(reg["custo_produto"]) is None
            or pid not in logistica
            or numero(logistica.get(pid, {}).get("frete")) is None
        )
        if problemas:                                           # TRUTH-013 / 016
            excecoes[(pid, linha)] = ("quarentena", "sim")
        else:
            pedidos[(pid, linha)] = norm(reg["cliente_id"])

    visitas = {}
    for i, reg in enumerate(ler("visitas.csv"), start=2):
        status = reg["status"].strip()
        realizada = reg["data_realizada"].strip()
        if status == "Realizada" and realizada == "":           # TRUTH-014
            visitas[(norm(reg["visita_id"]), i)] = "excecao_reportada"
        elif status != "Realizada":
            visitas[(norm(reg["visita_id"]), i)] = "nao_realizada"
        else:
            visitas[(norm(reg["visita_id"]), i)] = "valida"
    return {"pedidos": pedidos, "excecoes": excecoes, "visitas": visitas}


def suite_base_tratada() -> dict:
    print("== Suite 5: base tratada, excecoes e reconciliacao ==")

    hashes_antes = {p.name: sha256(p) for p in sorted(FIXTURES.glob("*.csv"))}
    esperado = esperado_tratamento()

    with tempfile.TemporaryDirectory() as tmp:
        saida = Path(tmp) / "bt"
        payload = rodar_base_tratada(saida)
        arquivos = {p.name: p.read_bytes() for p in sorted(saida.iterdir())}
        cabecalhos = {p.name: p.read_text(encoding="utf-8").splitlines()[0].split(",")
                      for p in sorted(saida.glob("*.csv"))}
        saida2 = Path(tmp) / "bt2"
        payload2 = rodar_base_tratada(saida2)
        arquivos2 = {p.name: p.read_bytes() for p in sorted(saida2.iterdir())}

    # 1. populacao da base tratada igual a recomputacao independente
    obtidos = {(p["pedido_id"], p["linha_origem_vendas"]) for p in payload["base_tratada_pedidos"]}
    checar(obtidos == set(esperado["pedidos"]), "pedidos da base tratada = recomputacao independente",
           f"somente no modulo: {sorted(obtidos - set(esperado['pedidos']))} | "
           f"somente na recomputacao: {sorted(set(esperado['pedidos']) - obtidos)}")

    # 2. destino e bloqueio de cada excecao iguais a recomputacao independente
    exc_modulo = {(e["id"], e["linha_origem"]): (e["destino"], e["bloqueia_publicacao"])
                  for e in payload["excecoes"] if e["entidade"] == "pedido"}
    checar(exc_modulo == esperado["excecoes"], "excecoes de pedido = recomputacao independente",
           f"modulo: {sorted(exc_modulo.items())} | esperado: {sorted(esperado['excecoes'].items())}")

    # 3. classificacao das visitas igual a recomputacao independente
    vis_modulo = {(v["visita_id"], v["linha_origem"]): v["classificacao"]
                  for v in payload["base_tratada_visitas"]}
    vis_modulo.update({(e["id"], e["linha_origem"]): e["destino"]
                       for e in payload["excecoes"] if e["entidade"] == "visita"
                       and e["destino"] == "quarentena"})
    checar(vis_modulo == esperado["visitas"], "classificacao das visitas = recomputacao independente",
           f"modulo: {sorted(vis_modulo.items())} | esperado: {sorted(esperado['visitas'].items())}")

    # 4. golden congelado da base tratada (BT-01..24), caso a caso
    destinos = {}
    for p in payload["base_tratada_pedidos"]:
        destinos[("pedido", p["pedido_id"], str(p["linha_origem_vendas"]))] = "base_tratada"
    for v in payload["base_tratada_visitas"]:
        destinos[("visita", v["visita_id"], str(v["linha_origem"]))] = v["classificacao"]
    for e in payload["excecoes"]:
        destinos[(e["entidade"], e["id"], str(e["linha_origem"]))] = e["destino"]
    golden_bt = ler("golden_base_tratada.csv")
    divergentes = []
    for caso in golden_bt:
        chave = (caso["entidade"], caso["id"], caso["linha_origem"])
        obtido = destinos.get(chave)
        if obtido != caso["destino_esperado"]:
            divergentes.append(f"{caso['caso_id']} {chave}: {obtido} != {caso['destino_esperado']}")
    checar(not divergentes, f"golden da base tratada ({len(golden_bt)} casos, tolerancia 0)",
           "; ".join(divergentes))

    # 5. bloqueio de publicacao conforme o golden
    bloq_golden = {(c["entidade"], c["id"], c["linha_origem"]): c["bloqueia_publicacao"]
                   for c in golden_bt if c["bloqueia_publicacao"] == "sim"}
    bloq_modulo = {(e["entidade"], e["id"], str(e["linha_origem"])): e["bloqueia_publicacao"]
                   for e in payload["excecoes"] if e["bloqueia_publicacao"] == "sim"}
    checar(bloq_modulo == bloq_golden, "excecoes bloqueantes = golden",
           f"modulo: {sorted(bloq_modulo)} | golden: {sorted(bloq_golden)}")
    checar(payload["resumo"]["publicacao_bloqueada"] == "sim",
           "publicacao bloqueada com excecao bloqueante aberta (ACC-007)")

    # 6. reconciliacao: golden congelado, celula a celula, e diferenca zero
    rec_modulo = {(r["bloco"], r["campo"]): r for r in payload["reconciliacao"]}
    golden_rec = ler("golden_reconciliacao.csv")
    erros = []
    for caso in golden_rec:
        obtido = rec_modulo.get((caso["bloco"], caso["campo"]))
        if obtido is None:
            erros.append(f"{caso['caso_id']}: bloco ausente")
            continue
        for coluna in ("total_origem", "total_base_tratada", "total_excluido_regra",
                       "total_quarentena"):
            if float(obtido[coluna]) != float(caso[coluna]):
                erros.append(f"{caso['caso_id']}.{coluna}: {obtido[coluna]} != {caso[coluna]}")
        if int(obtido["vazios_origem"]) != int(caso["vazios_origem"]):
            erros.append(f"{caso['caso_id']}.vazios: {obtido['vazios_origem']} != {caso['vazios_origem']}")
    checar(not erros, f"golden da reconciliacao ({len(golden_rec)} casos)", "; ".join(erros))
    checar(all(float(r["diferenca"]) == 0 and r["situacao"] == "ok"
               for r in payload["reconciliacao"]),
           "conservacao: origem = tratada + excluido + quarentena (diferenca 0)",
           str([(r["bloco"], r["campo"], r["diferenca"]) for r in payload["reconciliacao"]
                if float(r["diferenca"]) != 0]))
    checar(payload["resumo"]["reconciliacao"] == "ok", "reconciliacao reportada como ok")

    # 7. veredito por competencia = golden congelado
    ver_modulo = {v["competencia"]: v for v in payload["veredito_competencia"]}
    golden_ver = ler("golden_veredito_competencia.csv")
    erros = []
    for caso in golden_ver:
        obtido = ver_modulo.get(caso["competencia"])
        if obtido is None:
            erros.append(f"{caso['caso_id']}: competencia ausente")
            continue
        if obtido["veredito"] != caso["veredito_esperado"]:
            erros.append(f"{caso['caso_id']}: {obtido['veredito']} != {caso['veredito_esperado']}")
        for coluna, chave in (("linhas_vendas_origem", "linhas_vendas_origem"),
                              ("pedidos_base_tratada", "pedidos_base_tratada"),
                              ("excecoes_bloqueantes", "excecoes_bloqueantes")):
            if int(obtido[chave]) != int(caso[coluna]):
                erros.append(f"{caso['caso_id']}.{coluna}: {obtido[chave]} != {caso[coluna]}")
    checar(not erros, f"golden do veredito por competencia ({len(golden_ver)} casos)",
           "; ".join(erros))

    # 8. cobertura das excecoes esperadas EX-01..07
    codigos_saida = {e["codigo_excecao"] for e in payload["excecoes"] if e["codigo_excecao"]}
    codigos_saida |= {linha["codigo_excecao"] for linha in payload["log_tratamento"]
                      if linha["codigo_excecao"]}
    esperados = {c["caso"] for c in ler("expected_exceptions.csv")}
    checar(esperados <= codigos_saida, "EX-01..07 cobertos pelo tratamento",
           f"ausentes: {sorted(esperados - codigos_saida)}")

    # 9. contrato de colunas: nenhuma coluna nova, nenhum nome de indicador
    checar(cabecalhos.get("base_tratada_pedidos.csv") == COLUNAS_PEDIDOS_ESPERADAS,
           "colunas do arquivo de pedidos = contrato declarado, na ordem",
           f"obtidas: {cabecalhos.get('base_tratada_pedidos.csv')}")
    checar(cabecalhos.get("base_tratada_visitas.csv") == COLUNAS_VISITAS_ESPERADAS,
           "colunas do arquivo de visitas = contrato declarado, na ordem",
           f"obtidas: {cabecalhos.get('base_tratada_visitas.csv')}")
    checar(set(payload["base_tratada_pedidos"][0]) == set(COLUNAS_PEDIDOS_ESPERADAS),
           "nenhum campo extra no registro de pedido do JSON",
           f"extras: {sorted(set(payload['base_tratada_pedidos'][0]) - set(COLUNAS_PEDIDOS_ESPERADAS))}")
    checar(set(payload["base_tratada_visitas"][0]) == set(COLUNAS_VISITAS_ESPERADAS),
           "nenhum campo extra no registro de visita do JSON",
           f"extras: {sorted(set(payload['base_tratada_visitas'][0]) - set(COLUNAS_VISITAS_ESPERADAS))}")

    def chaves(objeto, acumulador):
        if isinstance(objeto, dict):
            for chave, valor in objeto.items():
                acumulador.add(str(chave))
                chaves(valor, acumulador)
        elif isinstance(objeto, list):
            for item in objeto:
                chaves(item, acumulador)
        return acumulador

    proibidas = sorted({k for k in chaves(payload, set())
                        if any(t in k.lower() for t in CHAVES_DE_INDICADOR)})
    checar(not proibidas, "nenhuma chave de indicador de negocio na saida do tratamento",
           f"chaves: {proibidas}")

    # 10. verbatim: todo valor monetario da base tratada e copia da fonte
    vendas = ler("vendas.csv")
    logistica = {r["pedido_id"].strip().upper(): r for r in ler("custos_logisticos.csv")}
    divergentes = []
    for p in payload["base_tratada_pedidos"]:
        origem = vendas[int(p["linha_origem_vendas"]) - 2]
        for campo in ("receita_bruta", "desconto", "custo_produto", "data_pedido",
                      "atualizado_em", "status_pedido"):
            if str(p[campo]) != origem[campo]:
                divergentes.append(f"{p['pedido_id']}.{campo}: {p[campo]} != {origem[campo]}")
        log_origem = logistica[p["pedido_id"]]
        for campo in ("frete", "custo_manuseio"):
            if str(p[campo]) != log_origem[campo]:
                divergentes.append(f"{p['pedido_id']}.{campo}: {p[campo]} != {log_origem[campo]}")
    checar(not divergentes, "valores da base tratada identicos a fonte (nenhum valor calculado)",
           "; ".join(divergentes))

    # 11. toda transformacao aplicada tem linha no log
    ids_normalizados = {p["pedido_id"] for p in payload["base_tratada_pedidos"]
                        if "id_normalizado" in p["marcas"]}
    ids_no_log = {linha["id"] for linha in payload["log_tratamento"]
                  if linha["acao"] == "normalizacao"}
    checar(ids_normalizados <= ids_no_log, "identificador normalizado registrado no log",
           f"sem log: {sorted(ids_normalizados - ids_no_log)}")
    checar(all(linha["regra"] for linha in payload["log_tratamento"]),
           "toda linha do log cita a regra que a autorizou")

    # 12. origem intocada e saida deterministica
    checar(hashes_antes == {p.name: sha256(p) for p in sorted(FIXTURES.glob("*.csv"))},
           "fixtures de origem intocadas pelo tratamento (SHA-256)")
    checar(arquivos == arquivos2, "duas execucoes produzem bytes identicos em todas as saidas",
           str(sorted(n for n in arquivos if arquivos[n] != arquivos2.get(n))))
    checar(payload == payload2, "payload JSON identico entre execucoes")
    return payload


def suite_base_tratada_excel(payload_csv: dict) -> None:
    print("== Suite 6: base tratada pelo caminho .xlsx ==")
    try:
        import openpyxl  # noqa: F401
    except ImportError:
        checar(False, "openpyxl disponivel (requirements.txt)",
               "instale com: python -m pip install --require-hashes -r requirements.txt")
        return

    def recorte(payload):
        return {
            "resumo": payload["resumo"],
            "pedidos": [(p["pedido_id"], p["cliente_id"], p["competencia"], p["receita_bruta"],
                         p["custo_produto"], p["frete"], p["marcas"]) for p in
                        payload["base_tratada_pedidos"]],
            "visitas": [(v["visita_id"], v["classificacao"], v["marcas"]) for v in
                        payload["base_tratada_visitas"]],
            "excecoes": [(e["entidade"], e["id"], e["destino"], e["bloqueia_publicacao"],
                          e["codigo_excecao"]) for e in payload["excecoes"]],
            "reconciliacao": [(r["bloco"], r["campo"], r["total_origem"],
                               r["total_base_tratada"], r["diferenca"]) for r in
                              payload["reconciliacao"]],
            "veredito": [(v["competencia"], v["veredito"]) for v in payload["veredito_competencia"]],
        }

    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        planilha = gerar_xlsx(base)
        hash_antes = sha256(planilha)
        payload_xlsx = rodar_base_tratada(base / "saida", entrada=planilha, rotulo="harness_xlsx")
        checar(sha256(planilha) == hash_antes, "planilha de entrada intocada pela leitura (SHA-256)")

    checar(recorte(payload_xlsx) == recorte(payload_csv),
           "caminho .xlsx produz a mesma base tratada que o caminho CSV")
    checar(payload_xlsx["entrada"]["tipo"] == "planilha .xlsx",
           "entrada .xlsx reconhecida como planilha")


def suite_derivabilidade_golden(payload: dict) -> None:
    """GC-01..03 deriváveis da base tratada — a conta e feita AQUI, nunca em src/."""
    print("== Suite 7: insumos de GC-01..03 deriveis da base tratada ==")
    parametros = {r["parametro"]: float(r["valor"]) for r in ler("parametros.csv")}
    custo_visita = parametros["custo_por_visita_realizada"]
    custo_pedido = parametros["custo_operacional_por_pedido"]

    agregado = {}
    for p in payload["base_tratada_pedidos"]:
        chave = (p["cliente_id"], p["competencia"])
        item = agregado.setdefault(chave, {"rb": 0.0, "desc": 0.0, "cp": 0.0, "log": 0.0,
                                           "pedidos": 0, "visitas": 0})
        item["rb"] += float(p["receita_bruta"])
        item["desc"] += float(p["desconto"] or 0)
        item["cp"] += float(p["custo_produto"])
        item["log"] += float(p["frete"]) + float(p["custo_manuseio"] or 0)
        item["pedidos"] += 1
    for v in payload["base_tratada_visitas"]:
        if v["classificacao"] == "valida":
            chave = (v["cliente_id"], v["competencia"])
            agregado.setdefault(chave, {"rb": 0.0, "desc": 0.0, "cp": 0.0, "log": 0.0,
                                        "pedidos": 0, "visitas": 0})["visitas"] += 1

    erros = []
    for caso in ler("golden_cases.csv"):
        item = agregado.get((caso["cliente_id"], caso["mes_ref"]))
        if item is None:
            erros.append(f"{caso['caso']}: cliente/mes ausente da base tratada")
            continue
        receita_liquida = item["rb"] - item["desc"]
        contribuicao = receita_liquida - item["cp"] - item["log"]
        visitas = item["visitas"] * custo_visita
        pedidos = item["pedidos"] * custo_pedido
        servir = contribuicao - visitas - pedidos
        for nome, obtido, esperado in (
            ("receita_liquida", receita_liquida, float(caso["receita_liquida"])),
            ("custo_produto", item["cp"], float(caso["custo_produto"])),
            ("custo_logistico", item["log"], float(caso["custo_logistico"])),
            ("margem_contribuicao", contribuicao, float(caso["margem_contribuicao"])),
            ("custo_visitas", visitas, float(caso["custo_visitas"])),
            ("custo_pedidos", pedidos, float(caso["custo_pedidos"])),
            ("margem_servir", servir, float(caso["margem_servir"])),
        ):
            if abs(obtido - esperado) > 0:                      # tolerancia R$ 0,00
                erros.append(f"{caso['caso']}.{nome}: {obtido} != {esperado}")
    checar(not erros, "GC-01..03 reproduzidos a partir da base tratada (tolerancia R$ 0,00)",
           "; ".join(erros))
    checar(len(ler("golden_cases.csv")) == 3, "golden_cases.csv preservado (GC-01..03)")


def main() -> int:
    print(f"Harness de conferencia — repo {RAIZ.name}")
    payload_csv = suite_diagnostico()
    suite_excel(payload_csv)
    with tempfile.TemporaryDirectory() as tmp:
        saida = Path(tmp) / "textos"
        payload = rodar_diagnostico(saida, rotulo="harness_textos")
        markdown = (saida / "diagnostico_harness_textos.md").read_text(encoding="utf-8")
    suite_textos(payload, markdown)
    suite_inventario_modulos()
    payload_bt = suite_base_tratada()
    suite_base_tratada_excel(payload_bt)
    suite_derivabilidade_golden(payload_bt)
    if falhas:
        print(f"\nRESULTADO: {len(falhas)} falha(s) — {falhas}")
        return 1
    print("\nRESULTADO: todas as verificacoes aplicaveis passaram")
    return 0


if __name__ == "__main__":
    sys.exit(main())
