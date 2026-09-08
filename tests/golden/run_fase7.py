"""Fase 7 — conferência independente do ciclo completo de tratamento."""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from decimal import Decimal
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
FIXTURES = RAIZ / "tests" / "fixtures"
MODULO = RAIZ / "src" / "relatorio_tratamento.py"
DIAGNOSTICO = RAIZ / "src" / "diagnostico_fonte.py"
falhas: list[str] = []


def checar(condicao: bool, rotulo: str, detalhe: str = "") -> None:
    if condicao:
        print(f"  ok: {rotulo}")
    else:
        print(f"  FALHA: {rotulo}" + (f" — {detalhe}" if detalhe else ""))
        falhas.append(rotulo)


def sha(caminho: Path) -> str:
    return hashlib.sha256(caminho.read_bytes()).hexdigest()


def ler(caminho: Path) -> list[dict]:
    with caminho.open(newline="", encoding="utf-8") as arquivo:
        return list(csv.DictReader(arquivo))


def rodar(entrada: Path, saida: Path, rotulo: str = "final") -> tuple[int, dict]:
    resultado = subprocess.run(
        [sys.executable, str(MODULO), "--entrada", str(entrada), "--saida", str(saida),
         "--rotulo", rotulo, "--periodo", "2026-01:2026-03"],
        cwd=RAIZ, capture_output=True, text=True,
    )
    payload = json.loads((saida / f"tratamento_{rotulo}.json").read_text(encoding="utf-8"))
    return resultado.returncode, payload


def gerar_xlsx(destino: Path) -> Path:
    from openpyxl import Workbook
    abas = {"clientes": "Clientes", "vendas": "Vendas",
            "custos_logisticos": "Custos_Logisticos", "visitas": "Visitas",
            "parametros": "Parametros"}
    livro = Workbook()
    livro.remove(livro.active)
    for nome, aba in abas.items():
        planilha = livro.create_sheet(aba)
        with (FIXTURES / f"{nome}.csv").open(newline="", encoding="utf-8") as arquivo:
            for linha in csv.reader(arquivo):
                planilha.append(linha)
    caminho = destino / "base.xlsx"
    livro.save(caminho)
    return caminho


def recorte(payload: dict) -> dict:
    return {
        "pedidos": [(p["pedido_id"], p["cliente_id"], p["competencia"], p["marcas"])
                    for p in payload["base_tratada_pedidos"]],
        "visitas": [(v["visita_id"], v["cliente_id"], v["competencia"])
                    for v in payload["base_tratada_visitas"]],
        "populacao": [(p["id"], p["linha"], p["destino"]) for p in payload["pedidos"]]
                     + [(v["id"], v["linha"], v["destino"]) for v in payload["visitas"]],
        "reconciliacao": payload["reconciliacao"],
        "veredito": payload["veredito_competencia"],
    }


def main() -> int:
    print("Conferência independente da fase 7")
    hashes_antes = {p.name: sha(p) for p in sorted(FIXTURES.glob("*.csv"))}
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        codigo1, payload = rodar(FIXTURES, base / "a")
        codigo2, payload2 = rodar(FIXTURES, base / "b")
        arquivos1 = {p.name: p.read_bytes() for p in (base / "a").iterdir()}
        arquivos2 = {p.name: p.read_bytes() for p in (base / "b").iterdir()}
        checar(codigo1 == codigo2 == 0, "duas execuções completas terminam com exit 0")
        checar(arquivos1 == arquivos2, "todas as saídas são determinísticas byte a byte")

        planilha = gerar_xlsx(base)
        hash_xlsx = sha(planilha)
        codigo_xlsx, payload_xlsx = rodar(planilha, base / "xlsx", "excel")
        checar(codigo_xlsx == 0, "caminho Excel termina com exit 0")
        checar(sha(planilha) == hash_xlsx, "arquivo Excel permanece intocado")
        checar(recorte(payload_xlsx) == recorte(payload),
               "CSV e Excel produzem o mesmo resultado semântico")

        diag_a, diag_b = base / "diag-a", base / "diag-b"
        for saida in (diag_a, diag_b):
            subprocess.run([sys.executable, str(DIAGNOSTICO), "--entrada", str(FIXTURES),
                            "--saida", str(saida), "--rotulo", "controle",
                            "--periodo", "2026-01:2026-03"], cwd=RAIZ, check=True,
                           capture_output=True, text=True)
        checar({p.name: p.read_bytes() for p in diag_a.iterdir()} ==
               {p.name: p.read_bytes() for p in diag_b.iterdir()},
               "diagnóstico observacional permanece determinístico e independente")

    checar(hashes_antes == {p.name: sha(p) for p in sorted(FIXTURES.glob("*.csv"))},
           "fixtures brutas permanecem byte-idênticas")
    checar(len(payload["pedidos"]) + len(payload["visitas"]) == 24,
           "população BASE contém os 24 registros esperados")
    checar(len(payload["base_tratada_pedidos"]) == 8 and
           len(payload["base_tratada_visitas"]) == 9,
           "saída oficial BASE contém 8 pedidos e 9 visitas válidas")
    checar(all(Decimal(r["diferenca"]) == 0 and r["situacao"] == "ok"
               for r in payload["reconciliacao"]),
           "reconciliação fecha em zero em todas as linhas")

    agregado: dict[tuple[str, str], dict[str, Decimal | int]] = {}
    for pedido in payload["base_tratada_pedidos"]:
        chave = (pedido["cliente_id"], pedido["competencia"])
        item = agregado.setdefault(chave, {"rb": Decimal(0), "d": Decimal(0),
                                           "cp": Decimal(0), "log": Decimal(0),
                                           "pedidos": 0, "visitas": 0})
        item["rb"] += Decimal(pedido["receita_bruta"])
        item["d"] += Decimal(pedido["desconto"] or "0")
        item["cp"] += Decimal(pedido["custo_produto"])
        item["log"] += Decimal(pedido["frete"]) + Decimal(pedido["custo_manuseio"] or "0")
        item["pedidos"] += 1
    for visita in payload["base_tratada_visitas"]:
        chave = (visita["cliente_id"], visita["competencia"])
        agregado.setdefault(chave, {"rb": Decimal(0), "d": Decimal(0), "cp": Decimal(0),
                                    "log": Decimal(0), "pedidos": 0, "visitas": 0})["visitas"] += 1
    erros = []
    for caso in ler(FIXTURES / "golden_cases.csv"):
        item = agregado[(caso["cliente_id"], caso["mes_ref"])]
        calculado = ((item["rb"] - item["d"] - item["cp"] - item["log"])
                     - Decimal(item["visitas"]) * Decimal("100")
                     - Decimal(item["pedidos"]) * Decimal("20"))
        if calculado != Decimal(caso["margem_servir"]):
            erros.append(f"{caso['caso']}: {calculado} != {caso['margem_servir']}")
    checar(not erros, "GC-01..03 são deriváveis da base tratada com tolerância R$ 0,00",
           "; ".join(erros))

    texto = json.dumps(payload, ensure_ascii=False)
    chaves_proibidas = ("margem_servir", "margem_contribuicao", "ranking", "clientes_alerta")
    checar(not any(f'"{chave}"' in texto for chave in chaves_proibidas),
           "saída de produção não contém indicador econômico")
    if falhas:
        print(f"RESULTADO: {len(falhas)} falha(s) — {falhas}")
        return 1
    print("RESULTADO: fase 7 concluída; ciclo conferido por caminho independente")
    return 0


if __name__ == "__main__":
    sys.exit(main())
