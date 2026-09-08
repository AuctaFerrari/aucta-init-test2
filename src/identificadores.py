"""Identificadores padronizados — fase 2 do ciclo da base tratada.

Escopo desta fase, e nada além dele:
  - normalizar identificadores conforme DN-11;
  - preservar o identificador bruto em campo separado, para rastreabilidade;
  - registrar cada normalização com valor anterior, valor novo e a regra;
  - detectar colisão entre identificadores brutos distintos que normalizam para
    o mesmo valor, colocar em quarentena todo registro afetado e bloquear cada
    competência afetada determinável;
  - quando o impacto da colisão não puder ser delimitado com segurança (DN-13),
    falhar de forma controlada, sem produzir saída oficial.

Regras aprovadas: DN-11 e DN-13, Issue #10 (issuecomment-5589411324 e
issuecomment-5589595626). Índice: `.project/DECISIONS.md`.

FORA de escopo aqui (fases 3 a 7, deliberadamente ausentes): escolha de versão
entre registros repetidos, lista branca de situação do pedido, quarentena por
informação faltante, base tratada oficial, reconciliação e qualquer cálculo de
indicador. Nenhum parâmetro econômico é lido.

Limite declarado: a janela `--periodo` é apenas registrada nesta fase. A regra
de escopo de execução (DN-08) é da fase 4; um registro afetado por colisão fora
da janela declarada bloquearia a sua competência aqui, e esse recorte será
revisto quando a DN-08 for implementada.

Uso:
  python src/identificadores.py --entrada <base.xlsx | pasta-com-csvs>
      [--saida outputs/identificadores] [--rotulo 2026-01] [--periodo 2026-01:2026-03]

Códigos de saída: 0 = sem colisão ou colisão delimitada · 2 = entrada inválida ·
5 = falha controlada de delimitação (DN-11 com DN-13).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from diagnostico_fonte import CONTRATO, _sha256, ler_csvs, ler_xlsx  # noqa: E402

VERSAO = "1.0.0"
FASE = 2
CATEGORIA = "identificadores"
REGRAS = ["DN-11", "DN-13"]

RE_COMPETENCIA = re.compile(r"^(\d{4}-\d{2})")

# Campos de identificador tratados nesta fase, por tabela.
CAMPOS_IDENTIFICADOR = {
    "clientes": [("cliente", "cliente_id", "cliente_id")],
    "vendas": [("pedido", "pedido_id", "pedido_id"), ("pedido", "pedido_id", "cliente_id")],
    "custos_logisticos": [("custo", "pedido_id", "pedido_id")],
    "visitas": [("visita", "visita_id", "visita_id"), ("visita", "visita_id", "cliente_id")],
}

# Campos que datam o registro, para determinar a competência afetada.
CAMPOS_DATA = {"vendas": ["data_pedido"], "visitas": ["data_realizada", "data_planejada"]}


def normalizar(valor: str) -> str:
    """DN-11: remove espaço externo e converte letras para maiúscula.

    Preserva espaço interno, pontuação e demais caracteres não alfanuméricos.
    Não infere prefixo nem zero à esquerda.
    """
    return (valor or "").strip().upper()


def competencia_de(texto: str) -> str:
    achado = RE_COMPETENCIA.match((texto or "").strip())
    return achado.group(1) if achado else ""


class Identificadores:
    def __init__(self, tabelas: dict):
        self.tabelas = tabelas
        self.normalizacoes: list[dict] = []
        self.mapa: list[dict] = []

    def _registrar(self, entidade, ident, linha, campo, bruto, normalizado) -> None:
        if campo.endswith("_id"):
            self.mapa.append({"entidade": entidade, "id": ident, "linha": linha,
                              "campo": campo, "bruto": bruto, "normalizado": normalizado})
        if bruto != normalizado:
            self.normalizacoes.append({
                "entidade": entidade, "id": ident, "linha": linha, "campo": campo,
                "valor_anterior": bruto, "valor_novo": normalizado, "regra": "DN-11",
            })

    def percorrer(self) -> None:
        for tabela, campos in CAMPOS_IDENTIFICADOR.items():
            registros = self.tabelas.get(tabela, {}).get("registros", [])
            for i, registro in enumerate(registros, start=2):
                for entidade, campo_id, campo in campos:
                    ident = normalizar(registro.get(campo_id, ""))
                    bruto = registro.get(campo, "")
                    self._registrar(entidade, ident, i, campo, bruto, normalizar(bruto))

    def colisoes_de_cadastro(self) -> list[dict]:
        """Identificadores brutos distintos que normalizam para o mesmo valor."""
        agrupado: dict[str, list[tuple[int, str]]] = {}
        for i, registro in enumerate(self.tabelas.get("clientes", {}).get("registros", []),
                                     start=2):
            bruto = registro.get("cliente_id", "")
            agrupado.setdefault(normalizar(bruto), []).append((i, bruto))
        colisoes = []
        for normalizado, ocorrencias in sorted(agrupado.items()):
            brutos = sorted({bruto for _, bruto in ocorrencias})
            if len(brutos) > 1:
                colisoes.append({
                    "normalizado": normalizado,
                    "brutos": brutos,
                    "linhas": sorted(linha for linha, _ in ocorrencias),
                    "regra": "DN-11",
                    "resolucao": "nenhuma: a colisao nao e resolvida por ordem de leitura",
                })
        return colisoes

    def afetados_por(self, colisoes: list[dict]) -> list[dict]:
        """Todo registro que aponta para um identificador em colisão."""
        alvos = {c["normalizado"] for c in colisoes}
        if not alvos:
            return []
        afetados = []
        for tabela in ("vendas", "visitas"):
            entidade = "pedido" if tabela == "vendas" else "visita"
            campo_id = "pedido_id" if tabela == "vendas" else "visita_id"
            for i, registro in enumerate(self.tabelas.get(tabela, {}).get("registros", []),
                                         start=2):
                if normalizar(registro.get("cliente_id", "")) not in alvos:
                    continue
                competencia = ""
                for campo in CAMPOS_DATA[tabela]:
                    competencia = competencia_de(registro.get(campo, ""))
                    if competencia:
                        break
                regras = ["DN-11"]
                if not competencia:
                    regras.append("DN-13")
                afetados.append({
                    "entidade": entidade,
                    "id": normalizar(registro.get(campo_id, "")),
                    "linha": i,
                    "competencia": competencia or "indeterminada",
                    "regras": "; ".join(regras),
                    "bloqueia": "sim",
                    "escopo_bloqueio": "competencia" if competencia else "periodo_inteiro",
                })
        afetados.sort(key=lambda r: (r["entidade"], r["id"], r["linha"]))
        return afetados


def render_markdown(payload: dict) -> str:
    linhas = [
        f"# Identificadores padronizados — {payload['rotulo']}",
        "",
        f"Fase 2 do ciclo · versão {payload['versao']} · regras aplicadas: "
        f"{', '.join(payload['regras_aplicadas'])}",
        "",
        "> Esta etapa **apenas padroniza identificadores e detecta colisão**. Não escolhe "
        "versão entre registros repetidos, não filtra situação de pedido, não monta a base "
        "tratada, não reconcilia e não calcula nenhum indicador.",
        "",
    ]
    if payload["status"] == "falha_delimitacao":
        linhas += [
            "**EXECUÇÃO INTERROMPIDA — impacto de colisão não delimitável.** "
            "Existe registro afetado por colisão de identificador cuja competência não pode "
            "ser determinada com segurança. Nenhuma saída oficial foi produzida, e a escolha "
            "por ordem de leitura é proibida. Trate a origem e execute de novo.", ""]
    elif payload["colisoes"]:
        linhas += [
            f"**COLISÃO DETECTADA E DELIMITADA** — {len(payload['registros_afetados'])} "
            f"registro(s) em quarentena; competência(s) bloqueada(s): "
            f"{', '.join(payload['competencias_bloqueadas'])}.", ""]
    else:
        linhas += ["**Nenhuma colisão de identificador.**", ""]

    linhas += [f"- Normalizações aplicadas: **{len(payload['normalizacoes'])}**",
               f"- Identificadores em colisão: **{len(payload['colisoes'])}**",
               f"- Registros afetados: **{len(payload['registros_afetados'])}**", ""]

    if payload["normalizacoes"]:
        linhas += ["## Normalizações — valor anterior → valor novo", "",
                   "| Entidade | Id | Linha | Campo | Valor anterior | Valor novo | Regra |",
                   "| --- | --- | --- | --- | --- | --- | --- |"]
        for n in payload["normalizacoes"]:
            linhas.append(f"| {n['entidade']} | {n['id']} | {n['linha']} | {n['campo']} | "
                          f"`{n['valor_anterior']}` | `{n['valor_novo']}` | {n['regra']} |")
        linhas.append("")

    if payload["colisoes"]:
        linhas += ["## Colisões de identificador", "",
                   "| Normalizado | Identificadores brutos | Linhas do cadastro | Resolução |",
                   "| --- | --- | --- | --- |"]
        for c in payload["colisoes"]:
            brutos = ", ".join(f"`{b}`" for b in c["brutos"])
            linhas.append(f"| {c['normalizado']} | {brutos} | "
                          f"{', '.join(str(l) for l in c['linhas'])} | {c['resolucao']} |")
        linhas += ["", "## Registros afetados", "",
                   "| Entidade | Id | Linha | Competência | Regras | Escopo do bloqueio |",
                   "| --- | --- | --- | --- | --- | --- |"]
        for r in payload["registros_afetados"]:
            linhas.append(f"| {r['entidade']} | {r['id']} | {r['linha']} | {r['competencia']} | "
                          f"{r['regras']} | {r['escopo_bloqueio']} |")
        linhas.append("")
    return "\n".join(linhas)


def executar(entrada: Path, saida: Path, rotulo: str, periodo: str | None) -> tuple[dict, int]:
    if entrada.is_dir():
        tabelas, fontes, _ = ler_csvs(entrada)
        tipo = "pasta de CSVs"
    else:
        tabelas, fontes, _ = ler_xlsx(entrada)
        tipo = "planilha .xlsx"

    faltando = [nome for nome in CONTRATO if nome not in tabelas]
    if faltando:
        raise SystemExit("ERRO: a padronização de identificadores exige todas as tabelas do "
                         f"contrato da fonte. Ausentes: {', '.join(faltando)}.")

    trabalho = Identificadores(tabelas)
    trabalho.percorrer()
    colisoes = trabalho.colisoes_de_cadastro()
    afetados = trabalho.afetados_por(colisoes)
    indelimitavel = [r for r in afetados if r["escopo_bloqueio"] == "periodo_inteiro"]
    status = "falha_delimitacao" if indelimitavel else "ok"
    bloqueadas = sorted({r["competencia"] for r in afetados
                         if r["escopo_bloqueio"] == "competencia"})

    payload = {
        "versao": VERSAO,
        "fase": FASE,
        "categoria": CATEGORIA,
        "rotulo": rotulo,
        "regras_aplicadas": REGRAS,
        "periodo_declarado": periodo or "",
        "entrada": {"caminho": str(entrada), "tipo": tipo, "fontes": fontes},
        "normalizacoes": trabalho.normalizacoes,
        "identificadores": trabalho.mapa,
        "colisoes": colisoes,
        "registros_afetados": afetados,
        "competencias_bloqueadas": bloqueadas,
        "status": status,
        "saida_oficial": status == "ok",
    }

    saida.mkdir(parents=True, exist_ok=True)
    (saida / f"identificadores_{rotulo}.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    (saida / f"identificadores_{rotulo}.md").write_text(render_markdown(payload),
                                                        encoding="utf-8")
    return payload, 5 if status == "falha_delimitacao" else 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Padroniza identificadores e detecta colisão (fase 2, DN-11). "
                    "Não monta a base tratada e não calcula indicador.")
    parser.add_argument("--entrada", required=True,
                        help="planilha .xlsx do mês ou pasta com as CSVs (uma por aba)")
    parser.add_argument("--saida", default="outputs/identificadores",
                        help="pasta de saída (padrão: outputs/identificadores)")
    parser.add_argument("--rotulo", default="execucao", help="rótulo da execução")
    parser.add_argument("--periodo", default=None,
                        help="período declarado, apenas registrado nesta fase")
    args = parser.parse_args(argv)

    entrada = Path(args.entrada)
    if not entrada.exists():
        print(f"ERRO: entrada não encontrada: {entrada}")
        return 2
    hash_antes = _sha256(entrada) if entrada.is_file() else ""

    payload, codigo = executar(entrada, Path(args.saida), args.rotulo, args.periodo)

    if hash_antes and _sha256(entrada) != hash_antes:
        print("ERRO: o arquivo de origem foi alterado durante a leitura.")
        return 3

    print(f"Identificadores v{payload['versao']} (fase {payload['fase']}) — {payload['rotulo']}")
    print(f"  normalizações: {len(payload['normalizacoes'])} | "
          f"colisões: {len(payload['colisoes'])} | "
          f"registros afetados: {len(payload['registros_afetados'])}")
    if payload["competencias_bloqueadas"]:
        print(f"  competências bloqueadas: {', '.join(payload['competencias_bloqueadas'])}")
    if payload["status"] == "falha_delimitacao":
        print("  FALHA CONTROLADA: impacto de colisão não delimitável (DN-11 com DN-13); "
              "nenhuma saída oficial produzida.")
    print(f"  saída: {args.saida}")
    return codigo


if __name__ == "__main__":
    sys.exit(main())
