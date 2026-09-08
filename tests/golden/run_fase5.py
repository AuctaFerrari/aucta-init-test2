"""Conferência da fase 5 — base tratada oficial e visitas válidas."""

from __future__ import annotations

import csv
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
FIXTURES = RAIZ / "tests" / "fixtures"
GOLDEN = FIXTURES / "golden" / "base-tratada" / "populacao.csv"
MODULO = RAIZ / "src" / "base_tratada.py"
falhas: list[str] = []


def checar(condicao: bool, rotulo: str, detalhe: str = "") -> None:
    if condicao:
        print(f"  ok: {rotulo}")
    else:
        print(f"  FALHA: {rotulo}" + (f" — {detalhe}" if detalhe else ""))
        falhas.append(rotulo)


def ler(caminho: Path) -> list[dict]:
    with caminho.open(newline="", encoding="utf-8") as arquivo:
        return list(csv.DictReader(arquivo))


def montar(destino: Path, cenario: str) -> None:
    destino.mkdir(parents=True)
    for nome in ("clientes", "vendas", "custos_logisticos", "visitas", "parametros"):
        shutil.copy(FIXTURES / f"{nome}.csv", destino / f"{nome}.csv")
    if cenario != "BASE":
        for arquivo in (FIXTURES / "adversarial" / cenario).glob("*.csv"):
            shutil.copy(arquivo, destino / arquivo.name)


def conferir(cenario: str) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        montar(base / "entrada", cenario)
        resultado = subprocess.run(
            [sys.executable, str(MODULO), "--entrada", str(base / "entrada"),
             "--saida", str(base / "saida"), "--rotulo", cenario.lower(),
             "--periodo", "2026-01:2026-03"],
            cwd=RAIZ, capture_output=True, text=True,
        )
        arquivo = base / "saida" / f"base_tratada_{cenario.lower()}.json"
        payload = json.loads(arquivo.read_text(encoding="utf-8")) if arquivo.exists() else None
    esperado_codigo = 5 if cenario == "A5" else 0
    checar(resultado.returncode == esperado_codigo, f"{cenario}: código de saída esperado",
           f"obtido={resultado.returncode}; stderr={resultado.stderr[:160]}")
    checar(payload is not None, f"{cenario}: artefato auditável produzido")
    if payload is None:
        return
    referencia = [r for r in ler(GOLDEN) if r["cenario"] == cenario]
    obtido = {}
    for pedido in payload["pedidos"]:
        obtido[("pedido", pedido["id"], str(pedido["linha"]))] = pedido
    for visita in payload["visitas"]:
        obtido[("visita", visita["id"], str(visita["linha"]))] = visita
    erros = []
    for linha in referencia:
        chave = (linha["entidade"], linha["id"], linha["linha"])
        atual = obtido.get(chave)
        if atual is None or atual["destino"] != linha["destino"]:
            erros.append(f"{chave}: {atual and atual['destino']} != {linha['destino']}")
        elif atual["bloqueia"] != linha["bloqueia"]:
            erros.append(f"{chave}.bloqueia: {atual['bloqueia']} != {linha['bloqueia']}")
    checar(set(obtido) == {(r["entidade"], r["id"], r["linha"]) for r in referencia},
           f"{cenario}: população completa, sem sobra nem falta")
    checar(not erros, f"{cenario}: destino e bloqueio = golden ({len(referencia)} registros)",
           "; ".join(erros))
    checar(payload["saida_oficial"] is (cenario != "A5"),
           f"{cenario}: disponibilidade da saída oficial conforme DN-13")


def main() -> int:
    print("Conferência da fase 5 (base tratada e visitas)")
    if not MODULO.exists():
        print("  FALHA: módulo de produção ausente: src/base_tratada.py")
        return 1
    for cenario in ("BASE", "A1", "A2", "A3", "A4", "A5"):
        conferir(cenario)
    if falhas:
        print(f"RESULTADO: {len(falhas)} falha(s) — {falhas}")
        return 1
    print("RESULTADO: fase 5 conferida contra os 147 casos do golden")
    return 0


if __name__ == "__main__":
    sys.exit(main())
