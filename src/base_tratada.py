"""Fase 5 — compõe a população oficial de pedidos e classifica visitas.

Não calcula margem, receita líquida, ranking ou recomendação. Cada registro
permanece ligado à linha e aos valores da fonte.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from diagnostico_fonte import CONTRATO, _sha256, ler_csvs, ler_xlsx  # noqa: E402
from identificadores import Identificadores, normalizar  # noqa: E402
from pedidos_nao_entram import Classificador, dentro  # noqa: E402

VERSAO = "1.0.0"
FASE = 5
CATEGORIA = "base_tratada"
REGRAS = ["DN-01", "DN-05", "DN-07", "DN-08", "DN-10", "DN-11", "DN-13",
          "TRUTH-011", "TRUTH-012", "TRUTH-013", "TRUTH-014", "TRUTH-015"]


def carregar(entrada: Path) -> tuple[dict, list, str]:
    if entrada.is_dir():
        tabelas, fontes, _ = ler_csvs(entrada)
        tipo = "pasta de CSVs"
    else:
        tabelas, fontes, _ = ler_xlsx(entrada)
        tipo = "planilha .xlsx"
    faltantes = [nome for nome in CONTRATO if nome not in tabelas]
    if faltantes:
        raise SystemExit(f"ERRO: tabelas ausentes: {', '.join(faltantes)}")
    return tabelas, fontes, tipo


def comp_visita(registro: dict) -> str:
    return (registro.get("mes_ref", "") or "").strip()


def data_comp_visita(registro: dict) -> str:
    for campo in ("data_realizada", "data_planejada"):
        valor = (registro.get(campo, "") or "").strip()
        if len(valor) >= 7 and valor[4] == "-":
            return valor[:7]
    return ""


class BaseTratada:
    def __init__(self, tabelas: dict, periodo: str):
        self.tabelas = tabelas
        self.periodo = periodo
        self.classificador = Classificador(tabelas, periodo)
        self.pedidos: list[dict] = []
        self.visitas: list[dict] = []
        self.bloqueadas: set[str] = set()
        self.periodo_inteiro = False
        self.status = "ok"

    def executar(self) -> None:
        self.classificador.executar()
        self.pedidos = [self.enriquecer_pedido(p) for p in self.classificador.pedidos]
        self.bloqueadas |= self.classificador.bloqueadas
        self.periodo_inteiro |= self.classificador.periodo_inteiro
        self.status = self.status_pedidos()
        self.classificar_visitas()

    def status_pedidos(self) -> str:
        ids = Identificadores(self.tabelas)
        colisoes = {c["normalizado"] for c in ids.colisoes_de_cadastro()}
        if any(p["competencia"] == "indeterminada" and
               normalizar(p["registro"].get("cliente_id", "")) in colisoes
               for p in self.classificador.pedidos):
            return "falha_delimitacao"
        return "ok"

    def enriquecer_pedido(self, item: dict) -> dict:
        registro = item["registro"]
        pid = item["pedido_id"]
        cid = normalizar(registro.get("cliente_id", ""))
        cadastro = {normalizar(r.get("cliente_id", "")): r
                    for r in self.tabelas["clientes"]["registros"]}
        logistica = {normalizar(r.get("pedido_id", "")): r
                     for r in self.tabelas["custos_logisticos"]["registros"]}
        return {
            **{k: v for k, v in item.items() if k != "registro"},
            "id": pid,
            "cliente_id": cid,
            "cliente_id_origem": registro.get("cliente_id", ""),
            "status_cliente": cadastro.get(cid, {}).get("status", ""),
            "valores": dict(registro),
            "logistica": dict(logistica.get(pid, {})),
        }

    def classificar_visitas(self) -> None:
        cadastro = {normalizar(r.get("cliente_id", "")): r
                    for r in self.tabelas["clientes"]["registros"]}
        ids = Identificadores(self.tabelas)
        colisoes = {c["normalizado"] for c in ids.colisoes_de_cadastro()}
        for linha, registro in enumerate(self.tabelas["visitas"]["registros"], start=2):
            vid = normalizar(registro.get("visita_id", ""))
            cid = normalizar(registro.get("cliente_id", ""))
            comp = comp_visita(registro) or "indeterminada"
            destino, regras, bloqueia, escopo, marcas = "valida", ["TRUTH-014"], "nao", "", ""
            motivos: list[str] = []
            if comp != "indeterminada" and not dentro(comp, self.periodo):
                destino, regras = "fora_do_periodo", ["DN-08"]
            elif cid in colisoes:
                destino, regras, bloqueia = "quarentena", ["DN-11"], "sim"
                escopo = "competencia" if comp != "indeterminada" else "periodo_inteiro"
                motivos.append("identificador de cliente em colisão")
            elif cid not in cadastro:
                destino, regras, bloqueia = "quarentena", ["DN-07", "TRUTH-014"], "sim"
                data_comp = data_comp_visita(registro)
                escopo = "competencia" if data_comp else "periodo_inteiro"
                motivos.extend(["cliente inexistente no cadastro", "evidência de data ausente"])
            elif registro.get("status") != "Realizada":
                destino, regras = "nao_realizada", ["TRUTH-014"]
            elif not (registro.get("data_realizada") or "").strip():
                destino, regras = "excecao_reportada", ["TRUTH-014"]
                motivos.append("visita Realizada sem data_realizada")
            if cid in cadastro and cadastro[cid].get("status") != "Ativo":
                marcas = "cliente_inativo"
            item = {
                "entidade": "visita", "id": vid, "linha": linha, "competencia": comp,
                "destino": destino, "regras": "; ".join(regras), "bloqueia": bloqueia,
                "escopo_bloqueio": escopo, "marcas": marcas, "motivos": motivos,
                "cliente_id": cid, "cliente_id_origem": registro.get("cliente_id", ""),
                "valores": dict(registro),
            }
            self.visitas.append(item)
            if bloqueia == "sim":
                if escopo == "periodo_inteiro":
                    self.periodo_inteiro = True
                elif comp != "indeterminada":
                    self.bloqueadas.add(comp)
        self.visitas.sort(key=lambda item: item["linha"])


def processar(tabelas: dict, periodo: str) -> BaseTratada:
    trabalho = BaseTratada(tabelas, periodo)
    trabalho.executar()
    return trabalho


def executar(entrada: Path, saida: Path, rotulo: str, periodo: str) -> tuple[dict, int]:
    tabelas, fontes, tipo = carregar(entrada)
    trabalho = processar(tabelas, periodo)
    if trabalho.periodo_inteiro and trabalho.status == "ok":
        # Bloqueio do período inteiro pode ser publicável como artefato de tratamento;
        # apenas A5 é falha de execução sem saída oficial.
        pass
    payload = {
        "versao": VERSAO, "fase": FASE, "categoria": CATEGORIA, "rotulo": rotulo,
        "periodo_declarado": periodo, "regras_aplicadas": REGRAS,
        "entrada": {"caminho": str(entrada), "tipo": tipo, "fontes": fontes},
        "pedidos": trabalho.pedidos, "visitas": trabalho.visitas,
        "competencias_bloqueadas": sorted(trabalho.bloqueadas),
        "periodo_inteiro_bloqueado": trabalho.periodo_inteiro,
        "status": trabalho.status, "saida_oficial": trabalho.status == "ok",
    }
    saida.mkdir(parents=True, exist_ok=True)
    (saida / f"base_tratada_{rotulo}.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    return payload, 5 if trabalho.status == "falha_delimitacao" else 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Monta a população da base tratada (fase 5).")
    parser.add_argument("--entrada", required=True)
    parser.add_argument("--saida", default="outputs/base-tratada")
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
    print(f"Fase 5: pedidos={len(payload['pedidos'])}; visitas={len(payload['visitas'])}; "
          f"status={payload['status']}")
    return codigo


if __name__ == "__main__":
    sys.exit(main())
