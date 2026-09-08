"""Conferencia da FASE 3 — versao que vale de cada pedido.

Escopo: agrupamento pelo pedido_id normalizado (DN-11), escolha da unica versao
com o atualizado_em valido mais recente (TRUTH-011), preservacao auditavel das
versoes descartadas, empate (DN-04) e timestamp inutilizavel (DN-14). Nada mais.

Expectativas: declaradas AQUI de forma independente, ou lidas dos golden
congelados em tests/fixtures/golden/fase3/, materializados antes do codigo.

Aprovacoes: Issue #10, issuecomment-5589411324 (TRUTH-011, DN-04) e
issuecomment-5590561870 (DN-14).

Uso: python tests/golden/run_fase3.py
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
GOLDEN = FIXTURES / "golden" / "fase3"
SRC = RAIZ / "src"
MODULO = SRC / "versao_pedido.py"

falhas: list[str] = []

# Chaves que denunciariam comportamento das fases 4 a 7 na saida da fase 3.
CHAVES_FORA_DE_ESCOPO = (
    "base_tratada", "excluido_regra", "fora_do_periodo", "status_pedido_valido",
    "cliente_inativo", "receita_liquida", "margem", "custo_visitas", "custo_pedidos",
    "veredito_publicacao", "visitas_validas",
)
# Termos de fase posterior que nao devem aparecer no codigo da fase 3.
TERMOS_FORA_DO_CODIGO = ("Cancelado", "frete", "custo_manuseio", "data_realizada", "margem")


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


def montar(destino: Path, cenario: str | None, vendas: list[str] | None = None) -> Path:
    """Fixtures de origem + sobreposicao do cenario, ou vendas montada no teste."""
    destino.mkdir(parents=True, exist_ok=True)
    for nome in ("clientes", "vendas", "custos_logisticos", "visitas", "parametros"):
        shutil.copy(FIXTURES / f"{nome}.csv", destino / f"{nome}.csv")
    if cenario:
        for arquivo in sorted((ADVERSARIAL / cenario).glob("*.csv")):
            shutil.copy(arquivo, destino / arquivo.name)
    if vendas is not None:
        (destino / "vendas.csv").write_text("\n".join(vendas) + "\n", encoding="utf-8")
    return destino


def rodar(entrada: Path, saida: Path, rotulo: str = "fase3"):
    resultado = subprocess.run(
        [sys.executable, str(MODULO), "--entrada", str(entrada),
         "--saida", str(saida), "--rotulo", rotulo],
        cwd=RAIZ, capture_output=True, text=True,
    )
    arquivo = saida / f"versao_pedido_{rotulo}.json"
    payload = json.loads(arquivo.read_text(encoding="utf-8")) if arquivo.exists() else None
    return resultado, payload


def esperado(cenario: str):
    """Destino esperado por (pedido_id, linha), lido do golden congelado."""
    return {(l["pedido_id"], l["linha"]): l for l in ler(GOLDEN / "versao_pedido.csv")
            if l["cenario"] == cenario}


def obtido(payload: dict):
    return {(v["pedido_id"], str(v["linha"])): v for v in payload["versoes"]}


def conferir_cenario(nome: str, cenario: str | None) -> dict | None:
    esp = esperado(nome)
    with tempfile.TemporaryDirectory() as tmp:
        entrada = montar(Path(tmp) / "in", cenario)
        resultado, payload = rodar(entrada, Path(tmp) / "out", nome.lower())
    if payload is None:
        checar(False, f"{nome}: execucao produz saida",
               f"exit={resultado.returncode} stderr={resultado.stderr[:200]}")
        return None
    obt = obtido(payload)
    divergentes = [f"{k}: {obt.get(k, {}).get('destino')} != {v['destino']}"
                   for k, v in esp.items() if obt.get(k, {}).get("destino") != v["destino"]]
    checar(not divergentes, f"{nome}: destino de cada versao = golden ({len(esp)} casos)",
           "; ".join(divergentes))
    checar(set(obt) == set(esp), f"{nome}: mesmas linhas do golden, sem sobra nem falta",
           f"so no modulo: {sorted(set(obt) - set(esp))} | so no golden: {sorted(set(esp) - set(obt))}")

    # conservacao conferida contra o golden congelado
    cons_esp = {l["campo"]: l for l in ler(GOLDEN / "conservacao.csv") if l["cenario"] == nome}
    cons_obt = {c["campo"]: c for c in payload["conservacao"]}
    erros = []
    for campo, linha in cons_esp.items():
        o = cons_obt.get(campo)
        if o is None:
            erros.append(f"{campo}: ausente"); continue
        for col in ("origem", "vigente", "versao_substituida", "quarentena"):
            if float(o[col]) != float(linha[col]):
                erros.append(f"{campo}.{col}: {o[col]} != {linha[col]}")
    checar(not erros, f"{nome}: conservacao = golden ({len(cons_esp)} campos)", "; ".join(erros))
    checar(all(float(c["diferenca"]) == 0 and c["situacao"] == "ok"
               for c in payload["conservacao"]),
           f"{nome}: origem = vigente + substituida + quarentena (diferenca 0)",
           str([(c["campo"], c["diferenca"]) for c in payload["conservacao"]
                if float(c["diferenca"]) != 0]))

    # veredito por competencia conferido contra o golden
    ver_esp = {l["competencia"]: l["veredito"] for l in ler(GOLDEN / "veredito.csv")
               if l["cenario"] == nome}
    bloqueadas_esp = {c for c, v in ver_esp.items() if v == "bloqueada"}
    checar(set(payload["competencias_bloqueadas"]) == bloqueadas_esp,
           f"{nome}: competencias bloqueadas = golden",
           f"modulo {payload['competencias_bloqueadas']} vs golden {sorted(bloqueadas_esp)}")
    return payload


def suite_base() -> dict | None:
    print("== Fase 3 · Suite A: fixture atual, O006 e versao substituida ==")
    hashes_antes = {p.name: sha256(p) for p in sorted(FIXTURES.glob("*.csv"))}
    payload = conferir_cenario("BASE", None)
    if payload is None:
        return None

    vigentes = [v for v in payload["versoes"] if v["destino"] == "vigente"]
    substituidas = payload["versoes_substituidas"]
    checar(len(vigentes) == 12, "12 versoes vigentes na fixture atual", str(len(vigentes)))
    checar(len(substituidas) == 1, "exatamente uma versao substituida", str(len(substituidas)))

    o006_vig = [v for v in vigentes if v["pedido_id"] == "O006"]
    checar(len(o006_vig) == 1, "O006 tem exatamente uma versao vigente", str(len(o006_vig)))
    if o006_vig:
        checar(o006_vig[0]["linha"] == 8, "vence a linha 8 (atualizado_em 2026-01-21 14:30)",
               str(o006_vig[0]["linha"]))
        checar(o006_vig[0]["valores"]["custo_produto"] == "260",
               "versao vigente de O006 traz custo_produto 260",
               str(o006_vig[0]["valores"]))

    if substituidas:
        s = substituidas[0]
        checar(s["pedido_id"] == "O006" and s["linha"] == 7,
               "versao substituida e a linha 7 de O006", str((s["pedido_id"], s["linha"])))
        checar(s["valores"]["custo_produto"] == "250" and s["valores"]["atualizado_em"] == "2026-01-20 08:00",
               "versao substituida preserva os valores brutos, verbatim", str(s["valores"]))
        checar("2026-01-21 14:30" in s["motivo"] and s["regra"] == "TRUTH-011",
               "versao substituida registra motivo e regra", f"{s['regra']} · {s['motivo']}")

    unicos = [v for v in payload["versoes"] if v["pedido_id"] != "O006"]
    checar(all(v["destino"] == "vigente" for v in unicos),
           "pedido nao duplicado permanece vigente e inalterado",
           str([(v["pedido_id"], v["destino"]) for v in unicos if v["destino"] != "vigente"]))
    checar(payload["competencias_bloqueadas"] == [],
           "nenhuma competencia bloqueada na fixture atual")
    checar(hashes_antes == {p.name: sha256(p) for p in sorted(FIXTURES.glob("*.csv"))},
           "fixtures de origem intocadas (SHA-256 antes/depois)")
    return payload


def suite_empate() -> None:
    print("== Fase 3 · Suite B: empate de timestamp (A3, DN-04) ==")
    payload = conferir_cenario("A3", "A3")
    if payload is None:
        return
    o006 = [v for v in payload["versoes"] if v["pedido_id"] == "O006"]
    checar(len(o006) == 2 and all(v["destino"] == "quarentena" for v in o006),
           "as duas versoes empatadas vao para quarentena",
           str([(v["linha"], v["destino"]) for v in o006]))
    checar(not any(v["destino"] == "vigente" for v in o006),
           "nenhuma versao vencedora escolhida no empate")
    checar(payload["competencias_bloqueadas"] == ["2026-01"], "janeiro bloqueado",
           str(payload["competencias_bloqueadas"]))
    checar(all("DN-04" in v["regras"] for v in o006), "DN-04 citada nas duas versoes",
           str([v["regras"] for v in o006]))
    checar(payload["versoes_substituidas"] == [],
           "empate nao produz versao substituida")


def suite_timestamp_inutilizavel() -> None:
    print("== Fase 3 · Suite C: timestamp inutilizavel em duplicata (A6, DN-14) ==")
    payload = conferir_cenario("A6", "A6")
    if payload is None:
        return
    o006 = [v for v in payload["versoes"] if v["pedido_id"] == "O006"]
    checar(len(o006) == 2 and all(v["destino"] == "quarentena" for v in o006),
           "as duas versoes do grupo vao para quarentena",
           str([(v["linha"], v["destino"]) for v in o006]))
    checar(not any(v["destino"] == "vigente" for v in o006),
           "nenhuma versao vencedora escolhida")
    checar(payload["competencias_bloqueadas"] == ["2026-01"],
           "competencia determinavel do grupo bloqueada",
           str(payload["competencias_bloqueadas"]))
    checar(all("DN-14" in v["regras"] for v in o006), "DN-14 citada nas duas versoes",
           str([v["regras"] for v in o006]))
    invalida = [v for v in o006 if v["linha"] == 8]
    checar(invalida and len(invalida[0]["motivos"]) >= 2,
           "timestamp invalido e ambiguidade reportados como motivos SEPARADOS",
           str(invalida[0]["motivos"] if invalida else None))
    valida = [v for v in o006 if v["linha"] == 7]
    checar(valida and len(valida[0]["motivos"]) == 1,
           "versao de timestamp valido reporta so a ambiguidade do grupo",
           str(valida[0]["motivos"] if valida else None))


def suite_multi_competencia() -> None:
    print("== Fase 3 · Suite D: duplicata atravessando mais de uma competencia ==")
    base = (FIXTURES / "vendas.csv").read_text(encoding="utf-8").splitlines()
    # O020 duplicado: versao de janeiro e versao de fevereiro, com empate de timestamp
    linhas = base + [
        "O020,2026-02-01 09:00,2026-01-15,C001,300,0,150,Faturado",
        "O020,2026-02-01 09:00,2026-02-15,C001,300,0,150,Faturado",
    ]
    with tempfile.TemporaryDirectory() as tmp:
        entrada = montar(Path(tmp) / "in", None, vendas=linhas)
        resultado, payload = rodar(entrada, Path(tmp) / "out", "multi")
    if payload is None:
        checar(False, "execucao produz saida no cenario multi-competencia",
               f"exit={resultado.returncode}")
        return
    o020 = [v for v in payload["versoes"] if v["pedido_id"] == "O020"]
    checar(len(o020) == 2 and all(v["destino"] == "quarentena" for v in o020),
           "as duas versoes do grupo multi-competencia vao para quarentena",
           str([(v["linha"], v["destino"]) for v in o020]))
    checar(set(payload["competencias_bloqueadas"]) == {"2026-01", "2026-02"},
           "TODA competencia representada no grupo e bloqueada",
           str(payload["competencias_bloqueadas"]))


def suite_unico_sem_timestamp() -> None:
    print("== Fase 3 · Suite E: pedido nao duplicado com atualizado_em ausente (DN-14) ==")
    base = (FIXTURES / "vendas.csv").read_text(encoding="utf-8").splitlines()
    linhas = base + ["O021,,2026-03-20,C001,400,0,200,Faturado"]
    with tempfile.TemporaryDirectory() as tmp:
        entrada = montar(Path(tmp) / "in", None, vendas=linhas)
        resultado, payload = rodar(entrada, Path(tmp) / "out", "unico")
    if payload is None:
        checar(False, "execucao produz saida no cenario de pedido unico sem timestamp",
               f"exit={resultado.returncode}")
        return
    o021 = [v for v in payload["versoes"] if v["pedido_id"] == "O021"]
    checar(len(o021) == 1 and o021[0]["destino"] == "vigente",
           "pedido nao duplicado com timestamp ausente PERMANECE vigente",
           str([(v["linha"], v["destino"]) for v in o021]))
    avisos = [a for a in payload["avisos"] if a["pedido_id"] == "O021"]
    checar(len(avisos) == 1, "o caso vira aviso de qualidade da fonte", str(avisos))
    if avisos:
        checar(avisos[0]["bloqueia"] == "nao" and avisos[0]["regra"] == "DN-14",
               "aviso e nao bloqueante e cita DN-14", str(avisos[0]))
    checar("2026-03" not in payload["competencias_bloqueadas"],
           "marco nao e bloqueado por causa do aviso",
           str(payload["competencias_bloqueadas"]))


def suite_ordem_de_leitura() -> None:
    print("== Fase 3 · Suite F: resultado independente da ordem do arquivo ==")
    original = (FIXTURES / "vendas.csv").read_text(encoding="utf-8").splitlines()
    invertido = [original[0]] + list(reversed(original[1:]))
    with tempfile.TemporaryDirectory() as tmp:
        e1 = montar(Path(tmp) / "a", None)
        _, p1 = rodar(e1, Path(tmp) / "outa", "direto")
        e2 = montar(Path(tmp) / "b", None, vendas=invertido)
        _, p2 = rodar(e2, Path(tmp) / "outb", "invertido")
    if p1 is None or p2 is None:
        checar(False, "as duas execucoes produzem saida")
        return

    def semantico(p):
        return {
            "vigentes": sorted((v["pedido_id"], v["valores"]["atualizado_em"],
                                v["valores"]["custo_produto"])
                               for v in p["versoes"] if v["destino"] == "vigente"),
            "substituidas": sorted((s["pedido_id"], s["valores"]["atualizado_em"],
                                    s["valores"]["custo_produto"])
                                   for s in p["versoes_substituidas"]),
            "quarentena": sorted((v["pedido_id"], v["valores"]["atualizado_em"])
                                 for v in p["versoes"] if v["destino"] == "quarentena"),
            "bloqueadas": sorted(p["competencias_bloqueadas"]),
            "conservacao": sorted((c["campo"], c["origem"], c["vigente"],
                                   c["versao_substituida"], c["quarentena"])
                                  for c in p["conservacao"]),
        }

    checar(semantico(p1) == semantico(p2),
           "inverter a ordem das linhas nao muda o resultado semantico")
    checar(json.dumps(semantico(p1), sort_keys=True).encode()
           == json.dumps(semantico(p2), sort_keys=True).encode(),
           "recorte semantico byte a byte identico entre as duas ordens")


def suite_escopo(payload: dict | None) -> None:
    print("== Fase 3 · Suite G: nenhum comportamento das fases 4 a 7 ==")
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
    checar(not proibidas, "nenhuma chave de fase posterior na saida da fase 3",
           f"chaves: {proibidas}")
    checar(payload["fase"] == 3, "saida se declara como fase 3", str(payload.get("fase")))
    checar(set(payload["regras_aplicadas"]) <= {"TRUTH-011", "DN-04", "DN-14", "DN-11"},
           "apenas TRUTH-011, DN-04, DN-14 e DN-11 aplicadas",
           str(payload["regras_aplicadas"]))
    modulos = sorted(p.name for p in SRC.rglob("*.py"))
    checar(modulos == ["diagnostico_fonte.py", "identificadores.py", "versao_pedido.py"],
           "src/ contem apenas os modulos das fases ja autorizadas", f"modulos: {modulos}")
    fonte = MODULO.read_text(encoding="utf-8")
    for termo in TERMOS_FORA_DO_CODIGO:
        checar(termo not in fonte,
               f"modulo da fase 3 nao referencia {termo} (regra de fase posterior)")


def main() -> int:
    print(f"Conferencia da fase 3 (versao que vale de cada pedido) — repo {RAIZ.name}")
    if not MODULO.exists():
        print(f"  FALHA: modulo de producao ausente: {MODULO.relative_to(RAIZ)}")
        print("\nRESULTADO: 1 falha — implementacao da fase 3 ainda nao existe")
        return 1
    payload = suite_base()
    suite_empate()
    suite_timestamp_inutilizavel()
    suite_multi_competencia()
    suite_unico_sem_timestamp()
    suite_ordem_de_leitura()
    suite_escopo(payload)
    if falhas:
        print(f"\nRESULTADO: {len(falhas)} falha(s) — {falhas}")
        return 1
    print("\nRESULTADO: fase 3 conferida, todas as verificacoes passaram")
    return 0


if __name__ == "__main__":
    sys.exit(main())
