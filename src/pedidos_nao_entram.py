"""Fase 4 — classifica pedidos sem produzir cálculo ou indicador.

Ordem obrigatória: validar competência; separar fora do período; detectar
colisões; escolher versão; aplicar lista branca, completude e relacionamento.
As regras são as DN-01..DN-14 e TRUTH-011..015 aprovadas na Issue #10.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from diagnostico_fonte import CONTRATO, _sha256, ler_csvs, ler_xlsx  # noqa: E402
from identificadores import Identificadores, normalizar  # noqa: E402
from versao_pedido import timestamp_utilizavel  # noqa: E402

VERSAO = "1.0.0"
FASE = 4
CATEGORIA = "tratamento_pedidos"
REGRAS = ["DN-01", "DN-04", "DN-05", "DN-06", "DN-08", "DN-10", "DN-11",
          "DN-13", "DN-14", "TRUTH-011", "TRUTH-012", "TRUTH-013", "TRUTH-015"]
RE_DATA = re.compile(r"^(\d{4}-\d{2})-\d{2}$")


def competencia(valor: str) -> str:
    achado = RE_DATA.match((valor or "").strip())
    return achado.group(1) if achado else ""


def decimal_valido(valor: str) -> bool:
    texto = (valor or "").strip()
    if not texto:
        return False
    try:
        Decimal(texto)
        return True
    except InvalidOperation:
        return False


def dentro(comp: str, periodo: str) -> bool:
    inicio, _, fim = periodo.partition(":")
    return (not inicio or comp >= inicio) and (not fim or comp <= fim)


class Classificador:
    def __init__(self, tabelas: dict, periodo: str):
        self.tabelas = tabelas
        self.periodo = periodo
        self.pedidos: list[dict] = []
        self.bloqueadas: set[str] = set()
        self.periodo_inteiro = False

    def adicionar(self, linha: int, registro: dict, destino: str, regras: list[str],
                  bloqueia: str = "nao", escopo: str = "", marcas: str = "",
                  motivos: list[str] | None = None) -> None:
        comp = competencia(registro.get("data_pedido", "")) or "indeterminada"
        self.pedidos.append({
            "pedido_id": normalizar(registro.get("pedido_id", "")),
            "linha": linha,
            "competencia": comp,
            "destino": destino,
            "regras": "; ".join(regras),
            "bloqueia": bloqueia,
            "escopo_bloqueio": escopo,
            "marcas": marcas,
            "motivos": motivos or [],
            "registro": dict(registro),
        })
        if bloqueia == "sim":
            if escopo == "periodo_inteiro" or comp == "indeterminada":
                self.periodo_inteiro = True
            else:
                self.bloqueadas.add(comp)

    def executar(self) -> None:
        vendas = self.tabelas["vendas"]["registros"]
        clientes = self.tabelas["clientes"]["registros"]
        custos = self.tabelas["custos_logisticos"]["registros"]
        cadastro = {normalizar(r.get("cliente_id", "")): r for r in clientes}
        logistica = {normalizar(r.get("pedido_id", "")): r for r in custos}

        ids = Identificadores(self.tabelas)
        colisoes = {item["normalizado"] for item in ids.colisoes_de_cadastro()}

        restantes: list[tuple[int, dict]] = []
        for linha, registro in enumerate(vendas, start=2):
            comp = competencia(registro.get("data_pedido", ""))
            if not comp:
                self.adicionar(linha, registro, "quarentena", ["DN-13"], "sim",
                               "periodo_inteiro", motivos=["data_pedido inutilizável"])
            elif not dentro(comp, self.periodo):
                self.adicionar(linha, registro, "fora_do_periodo", ["DN-08"])
            elif normalizar(registro.get("cliente_id", "")) in colisoes:
                self.adicionar(linha, registro, "quarentena", ["DN-11"], "sim",
                               "competencia", motivos=["identificador de cliente em colisão"])
            else:
                restantes.append((linha, registro))

        grupos: dict[str, list[tuple[int, dict]]] = {}
        for item in restantes:
            grupos.setdefault(normalizar(item[1].get("pedido_id", "")), []).append(item)

        for pid in sorted(grupos):
            grupo = grupos[pid]
            if len(grupo) > 1 and any(not timestamp_utilizavel(r.get("atualizado_em", ""))
                                      for _, r in grupo):
                for linha, registro in grupo:
                    self.adicionar(linha, registro, "quarentena", ["DN-14", "TRUTH-011"],
                                   "sim", "competencia",
                                   motivos=["duplicata com atualizado_em inutilizável"])
                continue
            if len(grupo) > 1:
                topo = max(r.get("atualizado_em", "") for _, r in grupo)
                empatados = [(l, r) for l, r in grupo if r.get("atualizado_em", "") == topo]
                if len(empatados) > 1:
                    for linha, registro in grupo:
                        self.adicionar(linha, registro, "quarentena", ["DN-04", "TRUTH-011"],
                                       "sim", "competencia",
                                       motivos=["empate no atualizado_em mais recente"])
                    continue
                vigente = empatados[0]
                for linha, registro in grupo:
                    if (linha, registro) != vigente:
                        self.adicionar(linha, registro, "excluido_regra", ["TRUTH-011"])
                self.avaliar(*vigente, cadastro, logistica)
            else:
                self.avaliar(*grupo[0], cadastro, logistica)

        self.pedidos.sort(key=lambda item: item["linha"])

    def avaliar(self, linha: int, registro: dict, cadastro: dict, logistica: dict) -> None:
        pid = normalizar(registro.get("pedido_id", ""))
        cid = normalizar(registro.get("cliente_id", ""))
        status = (registro.get("status_pedido", "") or "").strip()
        if status == "Cancelado":
            self.adicionar(linha, registro, "excluido_regra", ["TRUTH-012", "DN-06"])
            return
        motivos: list[str] = []
        if status != "Faturado":
            motivos.append("status fora da lista branca Faturado")
        if cid not in cadastro:
            motivos.append("cliente inexistente no cadastro")
        if not decimal_valido(registro.get("receita_bruta", "")):
            motivos.append("receita_bruta vazia ou não numérica")
        if not decimal_valido(registro.get("custo_produto", "")):
            motivos.append("custo_produto vazio ou não numérico")
        custo = logistica.get(pid)
        if custo is None:
            motivos.append("linha logística ausente")
        elif not decimal_valido(custo.get("frete", "")):
            motivos.append("frete vazio ou não numérico")
        if motivos:
            self.adicionar(linha, registro, "quarentena", ["TRUTH-013"], "sim",
                           "competencia", motivos=motivos)
            return
        marcas = "cliente_inativo" if cadastro[cid].get("status") != "Ativo" else ""
        self.adicionar(linha, registro, "base_tratada", ["DN-06", "TRUTH-013"],
                       marcas=marcas)


def executar(entrada: Path, saida: Path, rotulo: str, periodo: str) -> tuple[dict, int]:
    if entrada.is_dir():
        tabelas, fontes, _ = ler_csvs(entrada)
        tipo = "pasta de CSVs"
    else:
        tabelas, fontes, _ = ler_xlsx(entrada)
        tipo = "planilha .xlsx"
    faltantes = [nome for nome in CONTRATO if nome not in tabelas]
    if faltantes:
        raise SystemExit(f"ERRO: tabelas ausentes: {', '.join(faltantes)}")
    trabalho = Classificador(tabelas, periodo)
    trabalho.executar()
    status = "falha_delimitacao" if trabalho.periodo_inteiro and any(
        p["regras"] == "DN-11; DN-13" for p in trabalho.pedidos) else "ok"
    # A colisão que envolve registro sem competência é a falha controlada de A5.
    ids = Identificadores(tabelas)
    colisoes = {c["normalizado"] for c in ids.colisoes_de_cadastro()}
    if any(p["competencia"] == "indeterminada" and
           normalizar(p["registro"].get("cliente_id", "")) in colisoes
           for p in trabalho.pedidos):
        status = "falha_delimitacao"
        for p in trabalho.pedidos:
            if p["competencia"] == "indeterminada" and normalizar(
                    p["registro"].get("cliente_id", "")) in colisoes:
                p["regras"] = "DN-11; DN-13"
    payload = {
        "versao": VERSAO, "fase": FASE, "categoria": CATEGORIA, "rotulo": rotulo,
        "periodo_declarado": periodo, "regras_aplicadas": REGRAS,
        "entrada": {"caminho": str(entrada), "tipo": tipo, "fontes": fontes},
        "pedidos": trabalho.pedidos,
        "competencias_bloqueadas": sorted(trabalho.bloqueadas),
        "periodo_inteiro_bloqueado": trabalho.periodo_inteiro,
        "status": status, "saida_oficial": status == "ok",
    }
    saida.mkdir(parents=True, exist_ok=True)
    arquivo = saida / f"pedidos_nao_entram_{rotulo}.json"
    arquivo.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                       encoding="utf-8")
    return payload, 5 if status == "falha_delimitacao" else 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Classifica pedidos que não entram (fase 4).")
    parser.add_argument("--entrada", required=True)
    parser.add_argument("--saida", default="outputs/pedidos-nao-entram")
    parser.add_argument("--rotulo", default="execucao")
    parser.add_argument("--periodo", required=True)
    args = parser.parse_args(argv)
    entrada = Path(args.entrada)
    if not entrada.exists():
        print(f"ERRO: entrada não encontrada: {entrada}")
        return 2
    hash_antes = _sha256(entrada) if entrada.is_file() else ""
    payload, codigo = executar(entrada, Path(args.saida), args.rotulo, args.periodo)
    if hash_antes and _sha256(entrada) != hash_antes:
        return 3
    print(f"Fase 4: {len(payload['pedidos'])} pedidos classificados; status={payload['status']}")
    return codigo


if __name__ == "__main__":
    sys.exit(main())
