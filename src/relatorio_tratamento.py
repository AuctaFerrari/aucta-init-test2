"""Fase 6 — reconciliação e relatório auditável da base tratada.

Produz os sete artefatos previstos no plano. Não calcula indicador econômico;
somente conserva populações e valores já presentes na fonte.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from base_tratada import carregar, processar  # noqa: E402
from diagnostico_fonte import _sha256  # noqa: E402
from identificadores import normalizar  # noqa: E402

VERSAO = "1.0.0"
FASE = 6
CATEGORIA = "reconciliacao"
COLUNAS_RECON = ["bloco", "campo", "unidade", "origem", "base_tratada", "excluido",
                 "quarentena", "fora_do_periodo", "vazios", "diferenca", "situacao",
                 "observacao"]


def numero(valor: str) -> Decimal | None:
    texto = (valor or "").strip()
    if not texto:
        return None
    try:
        return Decimal(texto)
    except InvalidOperation:
        return None


def dinheiro(valor: Decimal) -> str:
    return str(valor.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def somar(registros: list[dict], campo: str) -> tuple[Decimal, int]:
    total, vazios = Decimal(0), 0
    for registro in registros:
        valor = numero(registro.get(campo, ""))
        if valor is None:
            vazios += 1
        else:
            total += valor
    return total, vazios


def linha_recon(bloco: str, campo: str, unidade: str, origem: list[dict],
                partes: dict[str, list[dict]], observacao: str = "") -> dict:
    nomes = ("base_tratada", "excluido", "quarentena", "fora_do_periodo")
    if unidade == "contagem":
        total = len(origem)
        valores = {nome: len(partes[nome]) for nome in nomes}
        vazios = 0
        diferenca = total - sum(valores.values())
        fmt = str
    else:
        total, vazios = somar(origem, campo)
        valores = {nome: somar(partes[nome], campo)[0] for nome in nomes}
        diferenca = total - sum(valores.values(), Decimal(0))
        fmt = dinheiro
    return {
        "bloco": bloco, "campo": campo, "unidade": unidade, "origem": fmt(total),
        **{nome: fmt(valores[nome]) for nome in nomes}, "vazios": str(vazios),
        "diferenca": fmt(diferenca), "situacao": "ok" if diferenca == 0 else "divergencia",
        "observacao": observacao,
    }


def reconciliar(tabelas: dict, trabalho) -> list[dict]:
    destinos_vendas = {p["linha"]: p["destino"] for p in trabalho.pedidos}
    vendas_origem = tabelas["vendas"]["registros"]
    venda_partes = {nome: [] for nome in ("base_tratada", "excluido", "quarentena", "fora_do_periodo")}
    for linha, registro in enumerate(vendas_origem, start=2):
        destino = destinos_vendas[linha]
        chave = "excluido" if destino == "excluido_regra" else destino
        venda_partes[chave].append(registro)

    por_pid: dict[str, set[str]] = {}
    for pedido in trabalho.pedidos:
        por_pid.setdefault(pedido["id"], set()).add(pedido["destino"])

    def destino_custo(pid: str) -> str:
        destinos = por_pid.get(normalizar(pid), {"quarentena"})
        for destino in ("base_tratada", "fora_do_periodo", "quarentena", "excluido_regra"):
            if destino in destinos:
                return "excluido" if destino == "excluido_regra" else destino
        return "quarentena"

    custos_origem = tabelas["custos_logisticos"]["registros"]
    custo_partes = {nome: [] for nome in venda_partes}
    for registro in custos_origem:
        custo_partes[destino_custo(registro.get("pedido_id", ""))].append(registro)

    visitas_origem = tabelas["visitas"]["registros"]
    visita_partes = {nome: [] for nome in venda_partes}
    for visita in trabalho.visitas:
        registro = visita["valores"]
        destino = visita["destino"]
        if destino == "valida":
            chave = "base_tratada"
        elif destino in ("nao_realizada", "excecao_reportada"):
            chave = "excluido"
        else:
            chave = destino
        visita_partes[chave].append(registro)

    clientes = tabelas["clientes"]["registros"]
    cliente_partes = {nome: [] for nome in venda_partes}
    cliente_partes["base_tratada"] = list(clientes)
    linhas = [linha_recon("vendas", "linhas", "contagem", vendas_origem, venda_partes)]
    for campo in ("receita_bruta", "desconto", "custo_produto"):
        linhas.append(linha_recon("vendas", campo, "BRL", vendas_origem, venda_partes))
    linhas.append(linha_recon("custos_logisticos", "linhas", "contagem", custos_origem,
                              custo_partes, "alocadas pelo destino do pedido"))
    for campo in ("frete", "custo_manuseio"):
        linhas.append(linha_recon("custos_logisticos", campo, "BRL", custos_origem, custo_partes))
    linhas.append(linha_recon("visitas", "linhas", "contagem", visitas_origem, visita_partes,
                              "validas / nao validas / quarentena"))
    linhas.append(linha_recon("clientes", "linhas", "contagem", clientes, cliente_partes,
                              "nenhum tratamento aplicado"))
    return linhas


def competencias(periodo: str) -> list[str]:
    inicio, _, fim = periodo.partition(":")
    ano, mes = map(int, inicio.split("-"))
    fim_ano, fim_mes = map(int, (fim or inicio).split("-"))
    itens = []
    while (ano, mes) <= (fim_ano, fim_mes):
        itens.append(f"{ano:04d}-{mes:02d}")
        mes += 1
        if mes == 13:
            ano, mes = ano + 1, 1
    return itens


def vereditos(trabalho, periodo: str) -> list[dict]:
    resultado = []
    for comp in competencias(periodo):
        if trabalho.status == "falha_delimitacao":
            veredito, escopo = "falha_execucao", "execucao"
            motivo = ("colisao de cadastro com registro afetado sem competencia determinavel: "
                      "execucao falha em vez de escolher por ordem de leitura")
        elif trabalho.periodo_inteiro:
            veredito, escopo = "bloqueada", "periodo_inteiro"
            motivo = "bloqueio de periodo inteiro (DN-07 com I-01)"
        elif comp in trabalho.bloqueadas:
            veredito, escopo = "bloqueada", "competencia"
            motivo = "excecao bloqueante nesta competencia"
        else:
            veredito, escopo = "publicavel", "competencia"
            motivo = "nenhuma excecao bloqueante"
        resultado.append({"competencia": comp, "veredito": veredito,
                          "escopo": escopo, "motivo": motivo})
    return resultado


def escrever_csv(caminho: Path, linhas: list[dict], colunas: list[str]) -> None:
    with caminho.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=colunas, extrasaction="ignore")
        escritor.writeheader()
        escritor.writerows(linhas)


def pedidos_oficiais(trabalho) -> list[dict]:
    saida = []
    for item in trabalho.pedidos:
        if item["destino"] != "base_tratada":
            continue
        valores, logistica = item["valores"], item["logistica"]
        saida.append({
            "competencia": item["competencia"], "pedido_id": item["id"],
            "cliente_id": item["cliente_id"], "cliente_id_origem": item["cliente_id_origem"],
            "status_cliente": item["status_cliente"], "data_pedido": valores.get("data_pedido", ""),
            "atualizado_em": valores.get("atualizado_em", ""),
            "receita_bruta": valores.get("receita_bruta", ""), "desconto": valores.get("desconto", ""),
            "custo_produto": valores.get("custo_produto", ""), "frete": logistica.get("frete", ""),
            "custo_manuseio": logistica.get("custo_manuseio", ""),
            "status_pedido": valores.get("status_pedido", ""), "marcas": item["marcas"],
            "linha_origem": item["linha"],
        })
    return saida


def visitas_oficiais(trabalho) -> list[dict]:
    return [{"competencia": v["competencia"], "visita_id": v["id"],
             "cliente_id": v["cliente_id"], "cliente_id_origem": v["cliente_id_origem"],
             "status": v["valores"].get("status", ""),
             "data_planejada": v["valores"].get("data_planejada", ""),
             "data_realizada": v["valores"].get("data_realizada", ""),
             "classificacao": v["destino"], "marcas": v["marcas"],
             "linha_origem": v["linha"]} for v in trabalho.visitas if v["destino"] == "valida"]


def renderizar(payload: dict) -> str:
    linhas = [f"# Tratamento da base — {payload['rotulo']}", "",
              f"Período: **{payload['periodo_declarado']}**", "",
              "## Veredito por competência", "",
              "| Competência | Veredito | Escopo | Motivo |", "| --- | --- | --- | --- |"]
    for item in payload["veredito_competencia"]:
        linhas.append(f"| {item['competencia']} | {item['veredito']} | {item['escopo']} | {item['motivo']} |")
    linhas += ["", "## Reconciliação", "",
               "A origem é igual à soma de base tratada, excluídos, quarentena e fora do período.", ""]
    for item in payload["reconciliacao"]:
        linhas.append(f"- {item['bloco']}.{item['campo']}: diferença {item['diferenca']} ({item['situacao']})")
    return "\n".join(linhas) + "\n"


def executar(entrada: Path, saida: Path, rotulo: str, periodo: str) -> tuple[dict, int]:
    tabelas, fontes, tipo = carregar(entrada)
    trabalho = processar(tabelas, periodo)
    payload = {
        "versao": VERSAO, "fase": FASE, "categoria": CATEGORIA, "rotulo": rotulo,
        "periodo_declarado": periodo, "entrada": {"caminho": str(entrada), "tipo": tipo,
                                                   "fontes": fontes},
        "pedidos": trabalho.pedidos, "visitas": trabalho.visitas,
        "base_tratada_pedidos": pedidos_oficiais(trabalho),
        "base_tratada_visitas": visitas_oficiais(trabalho),
        "reconciliacao": reconciliar(tabelas, trabalho),
        "veredito_competencia": vereditos(trabalho, periodo),
        "status": trabalho.status, "saida_oficial": trabalho.status == "ok",
    }
    saida.mkdir(parents=True, exist_ok=True)
    json_path = saida / f"tratamento_{rotulo}.json"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                         encoding="utf-8")
    if trabalho.status == "falha_delimitacao":
        return payload, 5
    pedidos = payload["base_tratada_pedidos"]
    visitas = payload["base_tratada_visitas"]
    excecoes = [x for x in trabalho.pedidos + trabalho.visitas
                if x["destino"] not in ("base_tratada", "valida")]
    logs = []
    for item in trabalho.pedidos + trabalho.visitas:
        if item.get("cliente_id_origem") != item.get("cliente_id"):
            logs.append({"entidade": item.get("entidade", "pedido"), "id": item["id"],
                         "linha": item["linha"], "acao": "normalizacao",
                         "valor_anterior": item["cliente_id_origem"],
                         "valor_novo": item["cliente_id"], "regra": "DN-11"})
        if item["destino"] not in ("base_tratada", "valida"):
            logs.append({"entidade": item.get("entidade", "pedido"), "id": item["id"],
                         "linha": item["linha"], "acao": item["destino"],
                         "valor_anterior": "preservado", "valor_novo": "",
                         "regra": item["regras"]})
    escrever_csv(saida / "base_tratada_pedidos.csv", pedidos,
                 list(pedidos[0]) if pedidos else ["competencia", "pedido_id"])
    escrever_csv(saida / "base_tratada_visitas.csv", visitas,
                 list(visitas[0]) if visitas else ["competencia", "visita_id"])
    col_exc = ["entidade", "id", "linha", "competencia", "destino", "regras", "bloqueia",
               "escopo_bloqueio", "marcas", "motivos"]
    escrever_csv(saida / "excecoes.csv", excecoes, col_exc)
    escrever_csv(saida / "log_tratamento.csv", logs,
                 ["entidade", "id", "linha", "acao", "valor_anterior", "valor_novo", "regra"])
    escrever_csv(saida / "reconciliacao.csv", payload["reconciliacao"], COLUNAS_RECON)
    (saida / f"tratamento_{rotulo}.md").write_text(renderizar(payload), encoding="utf-8")
    return payload, 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Gera base tratada, reconciliação e relatório.")
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
    print(f"Tratamento {rotulo if (rotulo := args.rotulo) else 'execucao'}: status={payload['status']}")
    return codigo


if __name__ == "__main__":
    sys.exit(main())
