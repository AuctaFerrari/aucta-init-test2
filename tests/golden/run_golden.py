"""Harness de conferencia — Aucta Foods · Rentabilidade por Cliente (tier 2).

Chamado pela guarda 4 do CI (`.github/ci/run-checks.sh`) sempre que `src/` existe.
Cada suite recomputa a referencia por um caminho INDEPENDENTE do codigo sob teste
(implementacao propria, so `csv` da stdlib) e compara.

Suites:
  1. Diagnostico da fonte (observacional) — contagens, nulos, duplicidades e
     chaves sem correspondencia recomputadas aqui; cobertura das excecoes
     conhecidas (tests/fixtures/expected_exceptions.csv); prova de que nada foi
     tratado; determinismo das saidas; integridade do arquivo de origem.
  2. Margens / golden cases (tests/fixtures/golden_cases.csv) — NAO IMPLEMENTADA
     nesta versao: nao existe modulo de calculo no repositorio e as formulas
     TRUTH-001..005 seguem pendentes de validacao formal da controladoria
     (gate do primeiro /change-number). A suite FALHA de proposito se aparecer
     em `src/` qualquer modulo fora da lista observacional — assim o gate de
     tier 2 nao pode ser atravessado sem golden.

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
MODULOS_OBSERVACIONAIS = {"diagnostico_fonte.py"}

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


def rodar_diagnostico(saida: Path) -> dict:
    resultado = subprocess.run(
        [sys.executable, str(SRC / "diagnostico_fonte.py"),
         "--entrada", str(FIXTURES), "--saida", str(saida),
         "--rotulo", "harness", "--periodo", "2026-01:2026-03"],
        cwd=RAIZ, capture_output=True, text=True,
    )
    if resultado.returncode != 0:
        print(resultado.stdout)
        print(resultado.stderr)
        raise SystemExit("FALHA: diagnostico terminou com erro")
    return json.loads((saida / "diagnostico_harness.json").read_text(encoding="utf-8"))


def suite_diagnostico() -> None:
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

    # 8. cobertura das excecoes conhecidas (referencia aprovada na iniciacao)
    texto_achados = json.dumps(payload["achados"], ensure_ascii=False)
    nao_cobertas = [linha["id"] for linha in ler("expected_exceptions.csv")
                    if linha["id"] not in texto_achados]
    checar(not nao_cobertas, "toda excecao conhecida (EX-01..07) aparece no diagnostico",
           f"ausentes: {nao_cobertas}")

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
    classes = {a["classe"] for a in payload["achados"]}
    checar(classes <= classes_ok, "achados restritos ao vocabulario observacional",
           f"classes inesperadas: {sorted(classes - classes_ok)}")


def suite_margens() -> None:
    print("== Suite 2: margens / golden cases (GC-01..03) ==")
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
    suite_diagnostico()
    suite_margens()
    if falhas:
        print(f"\nRESULTADO: {len(falhas)} falha(s) — {falhas}")
        return 1
    print("\nRESULTADO: todas as verificacoes aplicaveis passaram")
    return 0


if __name__ == "__main__":
    sys.exit(main())
