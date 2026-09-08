"""Versão que vale de cada pedido — fase 3 do ciclo da base tratada.

Escopo desta fase, e nada além dele:
  - agrupar versões pelo `pedido_id` normalizado conforme DN-11;
  - escolher a única versão com o `atualizado_em` válido mais recente (TRUTH-011);
  - preservar toda versão descartada em população auditável, com o motivo, a
    regra e os valores brutos;
  - empate no timestamp mais recente: nenhuma vencedora, todas as versões do
    grupo em quarentena e a competência afetada bloqueada (DN-04);
  - `atualizado_em` inutilizável em grupo duplicado: nenhuma vencedora, todas as
    versões em quarentena, toda competência determinável do grupo bloqueada, e
    período inteiro quando nenhuma competência é determinável (DN-14);
  - pedido não duplicado com `atualizado_em` inutilizável permanece vigente e
    gera aviso de qualidade da fonte, não bloqueante (DN-14);
  - resultado independente da ordem das linhas do arquivo.

Regras aprovadas: TRUTH-011, DN-04, DN-11 e DN-14 — Issue #10
(issuecomment-5589411324 e issuecomment-5590561870). Índice: `.project/DECISIONS.md`.

FORA de escopo aqui (fases 4 a 7, deliberadamente ausentes): lista branca de
situação do pedido, tratamento de campo essencial vazio, cliente órfão além do
resultado da fase 2, base tratada oficial, relatório de reconciliação e qualquer
cálculo. Nenhum parâmetro econômico é lido.

Atenção ao vocabulário: `vigente` aqui significa "esta é a versão que vale do
pedido", **não** "este pedido entra na base tratada". Um pedido pode ser vigente
nesta fase e ser excluído nas fases seguintes.

Uso:
  python src/versao_pedido.py --entrada <base.xlsx | pasta-com-csvs>
      [--saida outputs/versao-pedido] [--rotulo 2026-01]

Códigos de saída: 0 = sem ambiguidade, ou ambiguidade delimitada por competência ·
2 = entrada inválida · 6 = ambiguidade cuja competência não é determinável.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from diagnostico_fonte import _sha256, ler_csvs, ler_xlsx  # noqa: E402
from identificadores import normalizar  # noqa: E402

VERSAO = "1.0.0"
FASE = 3
CATEGORIA = "versao"
REGRAS = ["TRUTH-011", "DN-04", "DN-11", "DN-14"]

RE_TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$")
RE_COMPETENCIA = re.compile(r"^(\d{4}-\d{2})")

COLUNAS_VALORES = ["pedido_id", "atualizado_em", "data_pedido", "cliente_id",
                   "receita_bruta", "desconto", "custo_produto", "status_pedido"]
CAMPOS_CONSERVACAO = ["receita_bruta", "desconto", "custo_produto"]


def timestamp_utilizavel(valor: str) -> bool:
    """DN-14: ausente, vazio ou malformado é inutilizável para precedência."""
    return bool(RE_TIMESTAMP.match((valor or "").strip()))


def competencia_de(texto: str) -> str:
    achado = RE_COMPETENCIA.match((texto or "").strip())
    return achado.group(1) if achado else ""


def numero(valor: str):
    texto = (valor or "").strip()
    if texto == "":
        return None
    try:
        return Decimal(texto)
    except Exception:  # noqa: BLE001
        return None


def valores_de(registro: dict) -> dict:
    return {coluna: registro.get(coluna, "") for coluna in COLUNAS_VALORES}


class Versoes:
    def __init__(self, registros: list[dict]):
        self.registros = registros
        self.versoes: list[dict] = []
        self.substituidas: list[dict] = []
        self.avisos: list[dict] = []
        self.bloqueadas: set[str] = set()
        self.periodo_inteiro = False

    def _add(self, pid, linha, registro, destino, regras, motivos, bloqueia, escopo=""):
        self.versoes.append({
            "pedido_id": pid, "linha": linha,
            "competencia": competencia_de(registro.get("data_pedido", "")) or "indeterminada",
            "destino": destino, "regras": "; ".join(regras), "motivos": motivos,
            "bloqueia": bloqueia, "escopo_bloqueio": escopo,
            "valores": valores_de(registro),
        })

    def processar(self) -> None:
        grupos: dict[str, list[tuple[int, dict]]] = {}
        for i, registro in enumerate(self.registros, start=2):
            grupos.setdefault(normalizar(registro.get("pedido_id", "")), []).append((i, registro))

        for pid in sorted(grupos):
            grupo = sorted(grupos[pid], key=lambda par: par[0])
            if len(grupo) == 1:
                linha, registro = grupo[0]
                if not timestamp_utilizavel(registro.get("atualizado_em", "")):
                    self.avisos.append({
                        "pedido_id": pid, "linha": linha,
                        "aviso": "atualizado_em inutilizavel em pedido nao duplicado: o campo "
                                 "serve apenas a precedencia de versao, e nao remove o pedido",
                        "regra": "DN-14", "bloqueia": "nao",
                    })
                self._add(pid, linha, registro, "vigente", ["TRUTH-011"],
                          ["pedido unico: nenhuma escolha de versao"], "nao")
                continue
            self._resolver_grupo(pid, grupo)

    def _resolver_grupo(self, pid: str, grupo: list[tuple[int, dict]]) -> None:
        inutilizaveis = [linha for linha, registro in grupo
                         if not timestamp_utilizavel(registro.get("atualizado_em", ""))]
        if inutilizaveis:                                            # DN-14
            competencias = {competencia_de(r.get("data_pedido", "")) for _, r in grupo}
            competencias = {c for c in competencias if c}
            escopo = "competencia" if competencias else "periodo_inteiro"
            for linha, registro in grupo:
                motivos = ["ambiguidade de duplicata: nenhuma versao vencedora escolhida"]
                if linha in inutilizaveis:
                    motivos.append("atualizado_em inutilizavel nesta versao")
                if not competencias:
                    motivos.append("nenhuma competencia do grupo e determinavel com seguranca")
                self._add(pid, linha, registro, "quarentena", ["DN-14", "TRUTH-011"],
                          motivos, "sim", escopo)
            if competencias:
                self.bloqueadas |= competencias
            else:
                self.periodo_inteiro = True
            return

        ordenado = sorted(grupo, key=lambda par: (par[1]["atualizado_em"], par[0]))
        topo = ordenado[-1][1]["atualizado_em"]
        empatados = [par for par in ordenado if par[1]["atualizado_em"] == topo]
        if len(empatados) > 1:                                       # DN-04
            for linha, registro in ordenado:
                self._add(pid, linha, registro, "quarentena", ["DN-04", "TRUTH-011"],
                          [f"empate de atualizado_em ({topo}): escolha por ordem de leitura "
                           "proibida"], "sim", "competencia")
                competencia = competencia_de(registro.get("data_pedido", ""))
                if competencia:
                    self.bloqueadas.add(competencia)
                else:
                    self.periodo_inteiro = True
            return

        for linha, registro in ordenado[:-1]:                        # TRUTH-011
            motivo = (f"atualizado_em {registro.get('atualizado_em', '')} anterior a {topo}")
            self._add(pid, linha, registro, "versao_substituida", ["TRUTH-011"], [motivo], "nao")
            self.substituidas.append({
                "pedido_id": pid, "linha": linha, "motivo": motivo, "regra": "TRUTH-011",
                "valores": valores_de(registro),
            })
        linha, registro = ordenado[-1]
        self._add(pid, linha, registro, "vigente", ["TRUTH-011"],
                  [f"atualizado_em mais recente ({topo})"], "nao")


def conservar(registros: list[dict], versoes: list[dict]) -> list[dict]:
    destino = {(v["pedido_id"], v["linha"]): v["destino"] for v in versoes}
    grupos = {"vigente": [], "versao_substituida": [], "quarentena": []}
    for i, registro in enumerate(registros, start=2):
        grupos[destino[(normalizar(registro.get("pedido_id", "")), i)]].append(registro)

    linhas = []

    def somar(itens, campo):
        total, vazios = Decimal(0), 0
        for registro in itens:
            valor = numero(registro.get(campo))
            if valor is None:
                vazios += 1
            else:
                total += valor
        return total, vazios

    def linha(campo, unidade):
        if unidade == "contagem":
            origem = len(registros)
            partes = [len(grupos[k]) for k in ("vigente", "versao_substituida", "quarentena")]
            vazios = 0
            fmt = str
        else:
            origem, vazios = somar(registros, campo)
            partes = [somar(grupos[k], campo)[0]
                      for k in ("vigente", "versao_substituida", "quarentena")]
            def fmt(x):
                return str(Decimal(x).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
        diferenca = Decimal(origem) - sum((Decimal(p) for p in partes), Decimal(0))
        linhas.append({
            "campo": campo, "unidade": unidade, "origem": fmt(origem),
            "vigente": fmt(partes[0]), "versao_substituida": fmt(partes[1]),
            "quarentena": fmt(partes[2]), "vazios_origem": vazios,
            "diferenca": fmt(diferenca), "situacao": "ok" if diferenca == 0 else "divergencia",
        })

    linha("linhas", "contagem")
    for campo in CAMPOS_CONSERVACAO:
        linha(campo, "BRL")
    return linhas


def render_markdown(payload: dict) -> str:
    linhas = [
        f"# Versão que vale de cada pedido — {payload['rotulo']}",
        "",
        f"Fase 3 do ciclo · versão {payload['versao']} · regras: "
        f"{', '.join(payload['regras_aplicadas'])}",
        "",
        "> Esta etapa **apenas decide qual versão de cada pedido vale**. `Vigente` aqui não "
        "significa que o pedido entra na base tratada: situação do pedido, campo essencial "
        "vazio e cliente órfão são das fases seguintes. Nada é calculado.",
        "",
    ]
    resumo = payload["resumo"]
    if payload["status"] == "ambiguidade_indelimitavel":
        linhas += ["**EXECUÇÃO INTERROMPIDA — ambiguidade de versão sem competência "
                   "determinável.** Nenhuma versão vencedora foi escolhida e o período "
                   "solicitado inteiro está bloqueado.", ""]
    elif payload["competencias_bloqueadas"]:
        linhas += [f"**AMBIGUIDADE DE VERSÃO** — competência(s) bloqueada(s): "
                   f"{', '.join(payload['competencias_bloqueadas'])}. Nenhuma versão "
                   "vencedora foi escolhida nos grupos afetados.", ""]
    else:
        linhas += ["**Nenhuma ambiguidade de versão.**", ""]

    linhas += [f"- Versões vigentes: **{resumo['vigentes']}**",
               f"- Versões substituídas: **{resumo['substituidas']}**",
               f"- Versões em quarentena: **{resumo['quarentena']}**",
               f"- Avisos de qualidade da fonte (não bloqueantes): **{resumo['avisos']}**", ""]

    if payload["versoes_substituidas"]:
        linhas += ["## Versões substituídas — preservadas para auditoria", "",
                   "| Pedido | Linha | `atualizado_em` | `custo_produto` | Motivo | Regra |",
                   "| --- | --- | --- | --- | --- | --- |"]
        for s in payload["versoes_substituidas"]:
            linhas.append(f"| {s['pedido_id']} | {s['linha']} | "
                          f"`{s['valores']['atualizado_em']}` | "
                          f"`{s['valores']['custo_produto']}` | {s['motivo']} | {s['regra']} |")
        linhas.append("")

    quarentena = [v for v in payload["versoes"] if v["destino"] == "quarentena"]
    if quarentena:
        linhas += ["## Grupos ambíguos — nenhuma versão escolhida", "",
                   "| Pedido | Linha | Competência | Motivos | Regras | Escopo do bloqueio |",
                   "| --- | --- | --- | --- | --- | --- |"]
        for v in quarentena:
            linhas.append(f"| {v['pedido_id']} | {v['linha']} | {v['competencia']} | "
                          f"{'; '.join(v['motivos'])} | {v['regras']} | {v['escopo_bloqueio']} |")
        linhas.append("")

    if payload["avisos"]:
        linhas += ["## Avisos de qualidade da fonte", "",
                   "| Pedido | Linha | Aviso | Regra | Bloqueia |", "| --- | --- | --- | --- | --- |"]
        for a in payload["avisos"]:
            linhas.append(f"| {a['pedido_id']} | {a['linha']} | {a['aviso']} | "
                          f"{a['regra']} | {a['bloqueia']} |")
        linhas.append("")

    linhas += ["## Conservação — origem = vigente + substituída + quarentena", "",
               "| Campo | Unidade | Origem | Vigente | Substituída | Quarentena | Vazios | Diferença | Situação |",
               "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for c in payload["conservacao"]:
        linhas.append(f"| {c['campo']} | {c['unidade']} | {c['origem']} | {c['vigente']} | "
                      f"{c['versao_substituida']} | {c['quarentena']} | {c['vazios_origem']} | "
                      f"{c['diferenca']} | {c['situacao']} |")
    linhas.append("")
    return "\n".join(linhas)


def executar(entrada: Path, saida: Path, rotulo: str) -> tuple[dict, int]:
    if entrada.is_dir():
        tabelas, fontes, _ = ler_csvs(entrada)
        tipo = "pasta de CSVs"
    else:
        tabelas, fontes, _ = ler_xlsx(entrada)
        tipo = "planilha .xlsx"

    if "vendas" not in tabelas:
        raise SystemExit("ERRO: a escolha de versao exige a tabela de vendas na entrada.")

    registros = tabelas["vendas"]["registros"]
    trabalho = Versoes(registros)
    trabalho.processar()
    trabalho.versoes.sort(key=lambda v: (v["pedido_id"], v["linha"]))
    trabalho.substituidas.sort(key=lambda s: (s["pedido_id"], s["linha"]))
    trabalho.avisos.sort(key=lambda a: (a["pedido_id"], a["linha"]))

    conservacao = conservar(registros, trabalho.versoes)
    status = ("ambiguidade_indelimitavel" if trabalho.periodo_inteiro
              else "ambiguidade_delimitada" if trabalho.bloqueadas else "ok")
    contagem = {"vigentes": len([v for v in trabalho.versoes if v["destino"] == "vigente"]),
                "substituidas": len(trabalho.substituidas),
                "quarentena": len([v for v in trabalho.versoes if v["destino"] == "quarentena"]),
                "avisos": len(trabalho.avisos)}

    payload = {
        "versao": VERSAO, "fase": FASE, "categoria": CATEGORIA, "rotulo": rotulo,
        "regras_aplicadas": REGRAS,
        "entrada": {"caminho": str(entrada), "tipo": tipo, "fontes": fontes},
        "resumo": contagem,
        "versoes": trabalho.versoes,
        "versoes_substituidas": trabalho.substituidas,
        "avisos": trabalho.avisos,
        "conservacao": conservacao,
        "competencias_bloqueadas": sorted(trabalho.bloqueadas),
        "bloqueio_periodo_inteiro": trabalho.periodo_inteiro,
        "status": status,
    }

    saida.mkdir(parents=True, exist_ok=True)
    (saida / f"versao_pedido_{rotulo}.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    (saida / f"versao_pedido_{rotulo}.md").write_text(render_markdown(payload), encoding="utf-8")
    return payload, 6 if trabalho.periodo_inteiro else 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Decide qual versao de cada pedido vale (fase 3: TRUTH-011, DN-04, DN-14). "
                    "Nao monta a base tratada e nao calcula indicador.")
    parser.add_argument("--entrada", required=True,
                        help="planilha .xlsx do mês ou pasta com as CSVs (uma por aba)")
    parser.add_argument("--saida", default="outputs/versao-pedido", help="pasta de saída")
    parser.add_argument("--rotulo", default="execucao", help="rótulo da execução")
    args = parser.parse_args(argv)

    entrada = Path(args.entrada)
    if not entrada.exists():
        print(f"ERRO: entrada não encontrada: {entrada}")
        return 2
    hash_antes = _sha256(entrada) if entrada.is_file() else ""

    payload, codigo = executar(entrada, Path(args.saida), args.rotulo)

    if hash_antes and _sha256(entrada) != hash_antes:
        print("ERRO: o arquivo de origem foi alterado durante a leitura.")
        return 3

    resumo = payload["resumo"]
    print(f"Versão de pedido v{payload['versao']} (fase {payload['fase']}) — {payload['rotulo']}")
    print(f"  vigentes: {resumo['vigentes']} | substituídas: {resumo['substituidas']} | "
          f"em quarentena: {resumo['quarentena']} | avisos: {resumo['avisos']}")
    if payload["competencias_bloqueadas"]:
        print(f"  competências bloqueadas: {', '.join(payload['competencias_bloqueadas'])}")
    if payload["bloqueio_periodo_inteiro"]:
        print("  BLOQUEIO DO PERÍODO INTEIRO: ambiguidade sem competência determinável.")
    print(f"  saída: {args.saida}")
    return codigo


if __name__ == "__main__":
    sys.exit(main())
