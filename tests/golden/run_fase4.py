"""Conferência da fase 4 — pedidos que não entram.

As expectativas vêm do golden congelado em
tests/fixtures/golden/base-tratada/. O teste usa o entrypoint de produção, mas
não usa a sua implementação para decidir o resultado esperado.
"""

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
MODULO = RAIZ / "src" / "pedidos_nao_entram.py"

falhas: list[str] = []


def checar(condicao: bool, rotulo: str, detalhe: str = "") -> None:
    if condicao:
        print(f"  ok: {rotulo}")
    else:
        print(f"  FALHA: {rotulo}" + (f" — {detalhe}" if detalhe else ""))
        falhas.append(rotulo)


def ler_csv(caminho: Path) -> list[dict]:
    with caminho.open(newline="", encoding="utf-8") as arquivo:
        return list(csv.DictReader(arquivo))


def montar(destino: Path, cenario: str | None) -> Path:
    destino.mkdir(parents=True)
    for nome in ("clientes", "vendas", "custos_logisticos", "visitas", "parametros"):
        shutil.copy(FIXTURES / f"{nome}.csv", destino / f"{nome}.csv")
    if cenario:
        for arquivo in sorted((FIXTURES / "adversarial" / cenario).glob("*.csv")):
            shutil.copy(arquivo, destino / arquivo.name)
    return destino


def esperado(cenario: str) -> dict[tuple[str, str], dict]:
    return {
        (linha["id"], linha["linha"]): linha
        for linha in ler_csv(GOLDEN)
        if linha["cenario"] == cenario and linha["entidade"] == "pedido"
    }


def rodar(cenario: str) -> tuple[subprocess.CompletedProcess, dict | None]:
    with tempfile.TemporaryDirectory() as temporario:
        base = Path(temporario)
        entrada = montar(base / "entrada", None if cenario == "BASE" else cenario)
        saida = base / "saida"
        resultado = subprocess.run(
            [sys.executable, str(MODULO), "--entrada", str(entrada), "--saida", str(saida),
             "--rotulo", cenario.lower(), "--periodo", "2026-01:2026-03"],
            cwd=RAIZ, capture_output=True, text=True,
        )
        arquivo = saida / f"pedidos_nao_entram_{cenario.lower()}.json"
        payload = json.loads(arquivo.read_text(encoding="utf-8")) if arquivo.exists() else None
    return resultado, payload


def conferir(cenario: str, codigo_esperado: int = 0) -> None:
    resultado, payload = rodar(cenario)
    checar(resultado.returncode == codigo_esperado, f"{cenario}: código de saída controlado",
           f"obtido={resultado.returncode}; stderr={resultado.stderr[:180]}")
    checar(payload is not None, f"{cenario}: artefato auditável produzido")
    if payload is None:
        return
    obtido = {
        (linha["pedido_id"], str(linha["linha"])): linha
        for linha in payload["pedidos"]
    }
    referencia = esperado(cenario)
    erros = []
    for chave, linha in referencia.items():
        atual = obtido.get(chave)
        if atual is None:
            erros.append(f"{chave}: ausente")
            continue
        for campo in ("destino", "bloqueia", "escopo_bloqueio"):
            if atual[campo] != linha[campo]:
                erros.append(f"{chave}.{campo}: {atual[campo]} != {linha[campo]}")
    checar(set(obtido) == set(referencia), f"{cenario}: mesma população de pedidos do golden",
           f"extras={sorted(set(obtido)-set(referencia))}; faltas={sorted(set(referencia)-set(obtido))}")
    checar(not erros, f"{cenario}: destino e bloqueio de cada pedido = golden", "; ".join(erros))


def main() -> int:
    print("Conferência da fase 4 (pedidos que não entram)")
    if not MODULO.exists():
        print(f"  FALHA: módulo de produção ausente: {MODULO.relative_to(RAIZ)}")
        return 1
    for cenario in ("BASE", "A1", "A2", "A3"):
        conferir(cenario)
    conferir("A5", codigo_esperado=5)
    if falhas:
        print(f"RESULTADO: {len(falhas)} falha(s) — {falhas}")
        return 1
    print("RESULTADO: fase 4 conferida contra o golden congelado")
    return 0


if __name__ == "__main__":
    sys.exit(main())
