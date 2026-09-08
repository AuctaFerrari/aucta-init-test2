"""Conferência da fase 6 — reconciliação e relatório de tratamento."""

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
GOLDEN = FIXTURES / "golden" / "base-tratada"
MODULO = RAIZ / "src" / "relatorio_tratamento.py"
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
        saida = base / "saida"
        resultado = subprocess.run(
            [sys.executable, str(MODULO), "--entrada", str(base / "entrada"),
             "--saida", str(saida), "--rotulo", cenario.lower(),
             "--periodo", "2026-01:2026-03"],
            cwd=RAIZ, capture_output=True, text=True,
        )
        json_path = saida / f"tratamento_{cenario.lower()}.json"
        payload = json.loads(json_path.read_text(encoding="utf-8")) if json_path.exists() else None
        nomes = sorted(p.name for p in saida.iterdir()) if saida.exists() else []
    checar(resultado.returncode == (5 if cenario == "A5" else 0),
           f"{cenario}: código de saída controlado", str(resultado.returncode))
    checar(payload is not None, f"{cenario}: JSON auditável produzido")
    if payload is None:
        return
    rec_esp = {(r["bloco"], r["campo"]): r for r in ler(GOLDEN / "reconciliacao.csv")
               if r["cenario"] == cenario}
    rec_obt = {(r["bloco"], r["campo"]): r for r in payload["reconciliacao"]}
    erros = []
    for chave, esp in rec_esp.items():
        obt = rec_obt.get(chave)
        if obt is None:
            erros.append(f"{chave}: ausente")
            continue
        for campo in ("origem", "base_tratada", "excluido", "quarentena",
                      "fora_do_periodo", "vazios", "diferenca", "situacao"):
            if str(obt[campo]) != str(esp[campo]):
                erros.append(f"{chave}.{campo}: {obt[campo]} != {esp[campo]}")
    checar(not erros, f"{cenario}: reconciliação = golden ({len(rec_esp)} linhas)",
           "; ".join(erros[:10]))
    ver_esp = {(r["competencia"], r["veredito"], r["escopo"], r["motivo"])
               for r in ler(GOLDEN / "veredito.csv") if r["cenario"] == cenario}
    ver_obt = {(r["competencia"], r["veredito"], r["escopo"], r["motivo"])
               for r in payload["veredito_competencia"]}
    checar(ver_obt == ver_esp, f"{cenario}: veredito por competência = golden",
           f"obtido={sorted(ver_obt)}")
    if cenario == "A5":
        checar(nomes == ["tratamento_a5.json"],
               "A5: apenas artefato mínimo de falha, sem saída oficial", str(nomes))
    else:
        obrigatorios = {"base_tratada_pedidos.csv", "base_tratada_visitas.csv",
                        "excecoes.csv", "log_tratamento.csv", "reconciliacao.csv",
                        f"tratamento_{cenario.lower()}.md", f"tratamento_{cenario.lower()}.json"}
        checar(set(nomes) == obrigatorios, f"{cenario}: sete artefatos previstos no plano",
               str(nomes))


def main() -> int:
    print("Conferência da fase 6 (reconciliação e relatório)")
    if not MODULO.exists():
        print("  FALHA: módulo de produção ausente: src/relatorio_tratamento.py")
        return 1
    for cenario in ("BASE", "A1", "A2", "A3", "A4", "A5"):
        conferir(cenario)
    if falhas:
        print(f"RESULTADO: {len(falhas)} falha(s) — {falhas}")
        return 1
    print("RESULTADO: fase 6 conferida contra reconciliação e veredito congelados")
    return 0


if __name__ == "__main__":
    sys.exit(main())
