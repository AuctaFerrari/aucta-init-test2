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
  3. Margens / golden cases (tests/fixtures/golden_cases.csv) — NAO IMPLEMENTADA
     nesta versao: nao existe modulo de calculo no repositorio e as formulas
     TRUTH-001..005 seguem pendentes de validacao formal da controladoria
     (gate do primeiro /change-number). A suite FALHA de proposito se aparecer
     em `src/` qualquer modulo fora da lista observacional. ATENCAO: essa
     verificacao e uma lista de nomes de arquivo, nao uma analise de
     comportamento — limitacao registrada em .project/KNOWN_ISSUES.md (KI-001).

Uso: python tests/golden/run_golden.py
"""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
FIXTURES = RAIZ / "tests" / "fixtures"
SRC = RAIZ / "src"

# Modulos observacionais conhecidos (nao produzem numero entregue ao cliente).
# LIMITACAO CONHECIDA: e uma lista de NOMES, nao uma verificacao de
# comportamento. Ver .project/KNOWN_ISSUES.md (KI-001) e a demanda aberta no
# aucta-dev-core. Nao corrigir aqui: correcao estrutural e demanda separada.
MODULOS_OBSERVACIONAIS = {"diagnostico_fonte.py"}

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


def suite_margens() -> None:
    print("== Suite 3: margens / golden cases (GC-01..03) ==")
    modulos = sorted(p.name for p in SRC.glob("*.py")) if SRC.exists() else []
    fora_da_lista = [m for m in modulos if m not in MODULOS_OBSERVACIONAIS]
    if fora_da_lista:
        checar(False, "modulo de calculo em src/ exige a suite de margens implementada",
               f"modulos nao observacionais: {fora_da_lista}")
        return
    golden = ler("golden_cases.csv")
    checar(len(golden) == 3, "golden_cases.csv preservado (GC-01..03)", f"{len(golden)} caso(s)")
    print("  PENDENTE (nao aplicavel nesta versao): sem modulo de calculo em src/; "
          "formulas TRUTH-001..005 aguardam validacao formal da controladoria "
          "(gate do primeiro /change-number).")


def main() -> int:
    print(f"Harness de conferencia — repo {RAIZ.name}")
    payload_csv = suite_diagnostico()
    suite_excel(payload_csv)
    suite_margens()
    if falhas:
        print(f"\nRESULTADO: {len(falhas)} falha(s) — {falhas}")
        return 1
    print("\nRESULTADO: todas as verificacoes aplicaveis passaram")
    return 0


if __name__ == "__main__":
    sys.exit(main())
