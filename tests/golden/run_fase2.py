"""Conferencia da FASE 2 — identificadores padronizados (DN-11).

Escopo desta suite: normalizacao de identificadores e comportamento de colisao,
e mais nada. Regras aprovadas em:
  - DN-11 (normalizacao, rastreabilidade do bruto, colisao) e DN-13 (competencia
    inutilizavel), Issue #10 issuecomment-5589411324 e issuecomment-5589595626;
  - referencias esperadas ja commitadas em tests/fixtures/golden/base-tratada/,
    materializadas por derivacao independente ANTES de qualquer codigo.

Principio: as expectativas sao declaradas AQUI, de forma independente do modulo
sob teste, ou lidas dos golden congelados. O modulo de producao e executado pelo
seu proprio entrypoint, por subprocesso.

Fora de escopo (fases 3 a 7): escolha de versao de duplicata, filtro de status,
pipeline geral de quarentena, base tratada, reconciliacao e qualquer calculo.

Uso: python tests/golden/run_fase2.py
"""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
FIXTURES = RAIZ / "tests" / "fixtures"
ADVERSARIAL = FIXTURES / "adversarial"
GOLDEN = FIXTURES / "golden" / "base-tratada"
SRC = RAIZ / "src"
MODULO = SRC / "identificadores.py"

falhas: list[str] = []

# Chaves que denunciariam comportamento das fases 3 a 7 na saida da fase 2.
CHAVES_FORA_DE_ESCOPO = (
    "base_tratada", "reconciliacao", "excluido_regra", "deduplicacao",
    "versao_vigente", "status_pedido_valido", "receita_liquida", "margem",
    "custo_visitas", "custo_pedidos", "veredito_publicacao", "quarentena_geral",
)

# Casos da funcao pura de normalizacao (DN-11), declarados de forma independente.
CASOS_NORMALIZACAO = [
    ("  c003  ", "C003", "espaco externo removido e maiusculas"),
    (" c003 ", "C003", "caso O004 da fixture"),
    ("c003", "C003", "maiusculas"),
    ("C003", "C003", "idempotente"),
    ("C 003", "C 003", "espaco INTERNO preservado"),
    ("  C 0 03 ", "C 0 03", "espaco interno preservado, externo removido"),
    ("C-003", "C-003", "pontuacao preservada"),
    ("C.003", "C.003", "pontuacao preservada"),
    ("C_003/A", "C_003/A", "nao alfanumericos preservados"),
    ("3", "3", "sem inferencia de prefixo"),
    ("003", "003", "sem inferencia de zero a esquerda"),
    ("c3", "C3", "sem completar zeros"),
    ("", "", "vazio permanece vazio"),
]


def checar(condicao: bool, rotulo: str, detalhe: str = "") -> None:
    if condicao:
        print(f"  ok: {rotulo}")
    else:
        print(f"  FALHA: {rotulo}" + (f" — {detalhe}" if detalhe else ""))
        falhas.append(rotulo)


def sha256(caminho: Path) -> str:
    return hashlib.sha256(caminho.read_bytes()).hexdigest()


def ler(caminho: Path) -> list[dict]:
    with caminho.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def montar_cenario(destino: Path, cenario: str | None) -> Path:
    """Copia as fixtures de origem e aplica a sobreposicao do cenario, se houver."""
    destino.mkdir(parents=True, exist_ok=True)
    for nome in ("clientes", "vendas", "custos_logisticos", "visitas", "parametros"):
        shutil.copy(FIXTURES / f"{nome}.csv", destino / f"{nome}.csv")
    if cenario:
        for arquivo in sorted((ADVERSARIAL / cenario).glob("*.csv")):
            shutil.copy(arquivo, destino / arquivo.name)
    return destino


def rodar(entrada: Path, saida: Path, rotulo: str = "fase2"):
    """Executa o entrypoint de producao. Devolve (returncode, payload|None)."""
    resultado = subprocess.run(
        [sys.executable, str(MODULO), "--entrada", str(entrada),
         "--saida", str(saida), "--rotulo", rotulo, "--periodo", "2026-01:2026-03"],
        cwd=RAIZ, capture_output=True, text=True,
    )
    arquivo = saida / f"identificadores_{rotulo}.json"
    payload = json.loads(arquivo.read_text(encoding="utf-8")) if arquivo.exists() else None
    return resultado, payload


def esperado_colisao(cenario: str):
    """Expectativa lida do golden congelado: registros marcados com DN-11."""
    afetados, competencias, escopos = set(), set(), set()
    for linha in ler(GOLDEN / "populacao.csv"):
        if linha["cenario"] != cenario or "DN-11" not in linha["regras"]:
            continue
        afetados.add((linha["entidade"], linha["id"], linha["linha"]))
        escopos.add(linha["escopo_bloqueio"])
        if linha["escopo_bloqueio"] == "competencia":
            competencias.add(linha["competencia"])
    return afetados, competencias, escopos


def suite_funcao_pura() -> None:
    print("== Fase 2 · Suite A: normalizacao, caso a caso (DN-11) ==")
    sys.path.insert(0, str(SRC))
    try:
        from identificadores import normalizar
    except Exception as erro:  # noqa: BLE001
        checar(False, "modulo src/identificadores.py importavel", repr(erro))
        return
    for bruto, esperado, motivo in CASOS_NORMALIZACAO:
        obtido = normalizar(bruto)
        checar(obtido == esperado, f"{motivo}: {bruto!r} -> {esperado!r}",
               f"obtido {obtido!r}")


def suite_fixture_atual() -> dict | None:
    print("== Fase 2 · Suite B: fixture atual, O004 e rastreabilidade ==")
    hashes_antes = {p.name: sha256(p) for p in sorted(FIXTURES.glob("*.csv"))}
    with tempfile.TemporaryDirectory() as tmp:
        entrada = montar_cenario(Path(tmp) / "in", None)
        resultado, payload = rodar(entrada, Path(tmp) / "out")
        if payload is None:
            checar(False, "execucao produz saida na fixture atual",
                   f"exit={resultado.returncode} stderr={resultado.stderr[:200]}")
            return None
        checar(resultado.returncode == 0, "exit 0 sem colisao na fixture atual",
               f"exit={resultado.returncode}")
        # duas execucoes: bytes identicos (determinismo)
        saida_b = Path(tmp) / "out_b"
        rodar(entrada, saida_b)
        a = (Path(tmp) / "out" / "identificadores_fase2.json").read_bytes()
        b = (saida_b / "identificadores_fase2.json").read_bytes()
        checar(a == b, "duas execucoes produzem bytes identicos")

    normalizacoes = payload["normalizacoes"]
    o004 = [n for n in normalizacoes if n["id"] == "O004" and n["campo"] == "cliente_id"]
    checar(len(o004) == 1, "O004 gera exatamente uma normalizacao de cliente_id",
           f"{len(o004)} registro(s)")
    if o004:
        checar(o004[0]["valor_novo"] == "C003", "O004 normaliza para C003",
               f"obtido {o004[0]['valor_novo']!r}")
        checar(o004[0]["valor_anterior"] == " c003 ",
               "valor bruto de O004 preservado no log, verbatim",
               f"obtido {o004[0]['valor_anterior']!r}")
        checar(o004[0]["regra"] == "DN-11", "normalizacao cita DN-11 como regra",
               f"obtido {o004[0]['regra']!r}")
    checar(all(n["regra"] for n in normalizacoes),
           "toda normalizacao registrada cita a regra que a autorizou")
    checar(payload["colisoes"] == [], "nenhuma colisao na fixture atual",
           str(payload["colisoes"]))
    checar(payload["competencias_bloqueadas"] == [],
           "nenhuma competencia bloqueada na fixture atual",
           str(payload["competencias_bloqueadas"]))
    checar(payload["status"] == "ok", "status ok na fixture atual",
           str(payload["status"]))

    # o bruto continua disponivel ao lado do normalizado, por registro
    mapa = payload["identificadores"]
    linha_o004 = [m for m in mapa if m["entidade"] == "pedido" and m["id"] == "O004"
                  and m["campo"] == "cliente_id"]
    checar(len(linha_o004) == 1 and linha_o004[0]["bruto"] == " c003 "
           and linha_o004[0]["normalizado"] == "C003",
           "identificador bruto preservado em campo separado do normalizado",
           str(linha_o004))
    checar(all({"bruto", "normalizado"} <= set(m) for m in mapa),
           "todo identificador mapeado traz bruto e normalizado em campos distintos")

    checar(hashes_antes == {p.name: sha256(p) for p in sorted(FIXTURES.glob("*.csv"))},
           "fixtures de origem intocadas (SHA-256 antes/depois)")
    return payload


def suite_escopo(payload: dict | None) -> None:
    print("== Fase 2 · Suite C: nenhum comportamento das fases 3 a 7 ==")
    if payload is None:
        checar(False, "payload disponivel para conferir escopo")
        return

    chaves: set[str] = set()

    def coletar(no) -> None:
        if isinstance(no, dict):
            for chave, valor in no.items():
                chaves.add(str(chave).lower())
                coletar(valor)
        elif isinstance(no, list):
            for item in no:
                coletar(item)

    coletar(payload)
    proibidas = sorted(k for k in chaves if any(t in k for t in CHAVES_FORA_DE_ESCOPO))
    checar(not proibidas, "nenhuma chave de fase posterior na saida da fase 2",
           f"chaves: {proibidas}")
    checar(payload["fase"] == 2, "saida se declara como fase 2", str(payload.get("fase")))
    checar(set(payload["regras_aplicadas"]) <= {"DN-11", "DN-13"},
           "apenas DN-11 e DN-13 aplicadas nesta fase",
           str(payload["regras_aplicadas"]))
    # nenhum modulo de fase posterior foi criado junto
    modulos = sorted(p.name for p in SRC.rglob("*.py"))
    checar(modulos == ["diagnostico_fonte.py", "identificadores.py"],
           "src/ contem apenas o modulo observacional e o da fase 2",
           f"modulos: {modulos}")
    fonte = MODULO.read_text(encoding="utf-8")
    for termo in ("atualizado_em", "Cancelado", "receita_bruta", "custo_produto"):
        checar(termo not in fonte,
               f"modulo da fase 2 nao referencia {termo} (regra de fase posterior)")


def suite_colisao_delimitavel() -> None:
    print("== Fase 2 · Suite D: colisao com competencias determinaveis (cenario A2) ==")
    afetados_esp, competencias_esp, escopos_esp = esperado_colisao("A2")
    checar(len(afetados_esp) == 6 and escopos_esp == {"competencia"},
           "golden do A2 traz 6 registros afetados, todos de escopo competencia",
           f"{len(afetados_esp)} afetados, escopos {escopos_esp}")

    with tempfile.TemporaryDirectory() as tmp:
        entrada = montar_cenario(Path(tmp) / "in", "A2")
        resultado, payload = rodar(entrada, Path(tmp) / "out", "a2")
        if payload is None:
            checar(False, "execucao produz saida no A2",
                   f"exit={resultado.returncode} stderr={resultado.stderr[:200]}")
            return
        obtidos = {(r["entidade"], r["id"], str(r["linha"])) for r in payload["registros_afetados"]}
        checar(obtidos == afetados_esp, "registros afetados pela colisao = golden do A2",
               f"somente no modulo: {sorted(obtidos - afetados_esp)} | "
               f"somente no golden: {sorted(afetados_esp - obtidos)}")
        checar(set(payload["competencias_bloqueadas"]) == competencias_esp,
               "competencias bloqueadas = golden do A2",
               f"modulo {payload['competencias_bloqueadas']} vs golden {sorted(competencias_esp)}")
        checar(payload["status"] == "ok" and resultado.returncode == 0,
               "colisao delimitavel nao derruba a execucao",
               f"status={payload['status']} exit={resultado.returncode}")
        colididos = {c["normalizado"] for c in payload["colisoes"]}
        checar(colididos == {"C001"}, "colisao detectada exatamente em C001",
               str(colididos))
        brutos = set(payload["colisoes"][0]["brutos"]) if payload["colisoes"] else set()
        checar(brutos == {"C001", " c001 "},
               "os dois identificadores brutos em colisao ficam registrados, verbatim",
               str(sorted(brutos)))
        checar(all(r["bloqueia"] == "sim" and r["escopo_bloqueio"] == "competencia"
                   for r in payload["registros_afetados"]),
               "todo registro afetado bloqueia a sua competencia")


def suite_colisao_indelimitavel() -> None:
    print("== Fase 2 · Suite E: colisao sem delimitacao segura (cenario A5) ==")
    _, _, escopos_esp = esperado_colisao("A5")
    checar("periodo_inteiro" in escopos_esp,
           "golden do A5 exige escopo periodo_inteiro", str(escopos_esp))

    with tempfile.TemporaryDirectory() as tmp:
        entrada = montar_cenario(Path(tmp) / "in", "A5")
        resultado, payload = rodar(entrada, Path(tmp) / "out", "a5")
        checar(resultado.returncode != 0,
               "execucao retorna resultado diferente de zero, controlado",
               f"exit={resultado.returncode}")
        checar(resultado.returncode < 64, "falha controlada, nao excecao nao tratada",
               f"exit={resultado.returncode}")
        if payload is None:
            checar(False, "artefato minimo auditavel de falha produzido")
            return
        checar(payload["status"] == "falha_delimitacao",
               "status declara falha de delimitacao", str(payload["status"]))
        checar(payload.get("saida_oficial") is False,
               "nenhuma saida oficial e produzida na falha",
               str(payload.get("saida_oficial")))
        indeterminados = [r for r in payload["registros_afetados"]
                          if r["escopo_bloqueio"] == "periodo_inteiro"]
        checar(indeterminados, "registro sem competencia determinavel nomeado no artefato")
        checar(any("DN-13" in r["regras"] for r in indeterminados),
               "DN-13 citada no registro de competencia inutilizavel",
               str([r["regras"] for r in indeterminados]))


def suite_sem_ordem_de_leitura() -> None:
    print("== Fase 2 · Suite F: colisao nunca resolvida por ordem de leitura ==")
    with tempfile.TemporaryDirectory() as tmp:
        entrada = montar_cenario(Path(tmp) / "in", "A2")
        _, payload_direto = rodar(entrada, Path(tmp) / "out", "direto")

        # inverte a ordem das linhas do cadastro, preservando o cabecalho
        original = (entrada / "clientes.csv").read_text(encoding="utf-8").splitlines()
        invertido = [original[0]] + list(reversed(original[1:]))
        (entrada / "clientes.csv").write_text("\n".join(invertido) + "\n", encoding="utf-8")
        _, payload_invertido = rodar(entrada, Path(tmp) / "out2", "invertido")

    if payload_direto is None or payload_invertido is None:
        checar(False, "as duas execucoes produzem saida")
        return

    def comparavel(p):
        return {
            "status": p["status"],
            "colisoes": sorted((c["normalizado"], tuple(sorted(c["brutos"]))) for c in p["colisoes"]),
            "afetados": sorted((r["entidade"], r["id"], str(r["linha"]), r["bloqueia"],
                                r["escopo_bloqueio"]) for r in p["registros_afetados"]),
            "bloqueadas": sorted(p["competencias_bloqueadas"]),
        }

    checar(comparavel(payload_direto) == comparavel(payload_invertido),
           "inverter a ordem do cadastro nao muda o resultado (sem last-write-wins)")
    checar(not any("vencedor" in json.dumps(c).lower() or "prevalece" in json.dumps(c).lower()
                   for c in payload_direto["colisoes"]),
           "nenhum identificador em colisao e eleito vencedor")


def suite_cenarios_sem_colisao() -> None:
    print("== Fase 2 · Suite G: cenarios sem colisao no golden (BASE, A1, A3, A4) ==")
    for cenario in ("A1", "A3", "A4"):
        afetados, _, _ = esperado_colisao(cenario)
        checar(not afetados, f"golden do {cenario} nao tem registro marcado com DN-11",
               str(sorted(afetados)))
        with tempfile.TemporaryDirectory() as tmp:
            entrada = montar_cenario(Path(tmp) / "in", cenario)
            resultado, payload = rodar(entrada, Path(tmp) / "out", cenario.lower())
            if payload is None:
                checar(False, f"execucao produz saida no {cenario}",
                       f"exit={resultado.returncode}")
                continue
            checar(payload["colisoes"] == [] and payload["status"] == "ok",
                   f"{cenario}: nenhuma colisao detectada",
                   f"colisoes={payload['colisoes']} status={payload['status']}")
            checar(payload["registros_afetados"] == [],
                   f"{cenario}: nenhum registro afetado por colisao")


def main() -> int:
    print(f"Conferencia da fase 2 (identificadores) — repo {RAIZ.name}")
    if not MODULO.exists():
        print(f"  FALHA: modulo de producao ausente: {MODULO.relative_to(RAIZ)}")
        print("\nRESULTADO: 1 falha — implementacao da fase 2 ainda nao existe")
        return 1
    suite_funcao_pura()
    payload = suite_fixture_atual()
    suite_escopo(payload)
    suite_colisao_delimitavel()
    suite_colisao_indelimitavel()
    suite_sem_ordem_de_leitura()
    suite_cenarios_sem_colisao()
    if falhas:
        print(f"\nRESULTADO: {len(falhas)} falha(s) — {falhas}")
        return 1
    print("\nRESULTADO: fase 2 conferida, todas as verificacoes passaram")
    return 0


if __name__ == "__main__":
    sys.exit(main())
