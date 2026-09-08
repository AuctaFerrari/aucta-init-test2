"""Base tratada oficial — Aucta Foods · Rentabilidade por Cliente (tier 2).

Aplica as regras de tratamento APROVADAS sobre a base operacional do mes e produz
a base tratada oficial, as excecoes, o log de tratamento e a reconciliacao.

Regras aplicadas (todas ja registradas em TRUTHS.md antes deste modulo existir):
  TRUTH-011  duplicata: vale a versao com atualizado_em mais recente
  TRUTH-012  pedido Cancelado sai dos calculos, com exclusao documentada
  TRUTH-013  campo essencial vazio ou cliente fora do cadastro: quarentena e
             bloqueio de publicacao
  TRUTH-014  visita "Realizada" sem data: excecao reportada, nao conta como valida
  TRUTH-015  identificadores normalizados antes de qualquer cruzamento
  TRUTH-016  base tratada aceita apenas status na lista branca (DEC-07)
  TRUTH-017  competencia do pedido = data_pedido (DEC-02)
  TRUTH-018  movimento de cliente Inativo entra marcado (DEC-01)
  TRUTH-019  custo_manuseio igual a 0 e valor legitimo da fonte (DEC-03)
  TRUTH-020  empate de atualizado_em: quarentena com bloqueio (DEC-04)

O que este modulo NAO faz (limite de escopo do ciclo, verificado pelo harness):
  - nao calcula receita liquida, margem, ranking, classificacao ou indicador;
  - nao imputa, estima ou corrige valor por inferencia;
  - nao altera o arquivo de origem (leitura somente, SHA-256 conferido);
  - nao consome os parametros economicos da aba Parametros;
  - nao le nem escreve os arquivos de golden.

Todo valor nas saidas e COPIA VERBATIM da fonte ou transformacao registrada no
log de tratamento. Nenhum registro e alterado em silencio.

Uso:
  python src/base_tratada.py --entrada <base.xlsx | pasta-com-csvs>
      [--saida outputs/base-tratada] [--rotulo 2026-01] [--periodo 2026-01:2026-03]
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from diagnostico_fonte import CONTRATO, _sha256, ler_csvs, ler_xlsx  # noqa: E402

VERSAO = "1.0.0"

# ---------------------------------------------------------------------------
# Regras aprovadas, declaradas em um lugar so.
# ---------------------------------------------------------------------------
STATUS_PEDIDO_VALIDOS = {"Faturado"}          # TRUTH-016 / DEC-07 (lista branca)
STATUS_PEDIDO_EXCLUIDO = {"Cancelado"}        # TRUTH-012 (exclusao documentada)
CAMPO_COMPETENCIA = "data_pedido"             # TRUTH-017 / DEC-02
STATUS_VISITA_REALIZADA = "Realizada"         # TRUTH-014
STATUS_CLIENTE_ATIVO = "Ativo"                # TRUTH-018: nao-ativo entra marcado
ESSENCIAIS_PEDIDO = ["receita_bruta", "custo_produto"]   # TRUTH-013
ESSENCIAIS_LOGISTICA = ["frete"]                          # TRUTH-013

# Colunas permitidas em cada saida. Contrato fechado: toda coluna e copia da
# fonte ou metadado de tratamento. Nenhuma coluna derivada de formula economica.
COLUNAS_PEDIDOS = [
    "competencia", "pedido_id", "cliente_id", "cliente_id_origem", "razao_social",
    "regiao", "segmento", "canal", "status_cliente", "data_pedido", "atualizado_em",
    "receita_bruta", "desconto", "custo_produto", "frete", "custo_manuseio",
    "status_pedido", "marcas", "linha_origem_vendas",
]
COLUNAS_VISITAS = [
    "competencia", "visita_id", "cliente_id", "cliente_id_origem", "status",
    "data_planejada", "data_realizada", "classificacao", "marcas", "linha_origem",
]
COLUNAS_EXCECOES = [
    "entidade", "id", "linha_origem", "competencia", "destino", "motivo", "regra",
    "codigo_excecao", "bloqueia_publicacao", "receita_bruta", "desconto",
    "custo_produto", "frete", "status_pedido", "cliente_id_origem",
]
COLUNAS_LOG = [
    "sequencia", "entidade", "id", "linha_origem", "acao", "campo",
    "valor_anterior", "valor_novo", "regra", "codigo_excecao",
]
COLUNAS_RECONCILIACAO = [
    "bloco", "campo", "unidade", "total_origem", "total_base_tratada",
    "total_excluido_regra", "total_quarentena", "vazios_origem", "diferenca",
    "situacao", "observacao",
]

ROTULOS_APRESENTACAO = {
    "base_tratada": "Base tratada",
    "excluido_regra": "Excluído por regra",
    "quarentena": "Quarentena",
    "valida": "Válida",
    "nao_realizada": "Não realizada",
    "excecao_reportada": "Exceção reportada",
    "seguro": "Seguro para cálculo",
    "nao_calcular": "Não calcular",
    "ok": "OK",
    "divergencia": "Divergência",
    "normalizacao": "Normalização",
    "deduplicacao": "Deduplicação",
    "exclusao": "Exclusão",
    "quarentena_acao": "Quarentena",
    "classificacao": "Classificação",
    "sim": "Sim",
    "nao": "Não",
}

RE_COMPETENCIA = re.compile(r"^(\d{4}-\d{2})")


def rotulo(valor: str) -> str:
    return ROTULOS_APRESENTACAO.get(valor, valor)


def norm_id(valor: str) -> str:
    """Normalizacao de identificador (TRUTH-015): sem espacos, maiusculas."""
    return valor.strip().upper()


def dec(valor: str):
    """Decimal do texto da fonte, ou None quando vazio/nao numerico."""
    texto = (valor or "").strip().replace(",", ".")
    if texto == "":
        return None
    try:
        return Decimal(texto)
    except InvalidOperation:
        return None


def brl(valor: Decimal) -> str:
    inteiro, _, centavos = f"{valor:.2f}".partition(".")
    negativo = inteiro.startswith("-")
    inteiro = inteiro.lstrip("-")
    grupos = []
    while len(inteiro) > 3:
        grupos.insert(0, inteiro[-3:])
        inteiro = inteiro[:-3]
    grupos.insert(0, inteiro)
    return ("-" if negativo else "") + ".".join(grupos) + "," + centavos


def competencia_de(texto: str) -> str:
    achado = RE_COMPETENCIA.match((texto or "").strip())
    return achado.group(1) if achado else ""


class Tratamento:
    def __init__(self, tabelas: dict, periodo: str | None):
        self.tabelas = tabelas
        self.periodo = periodo
        self.log: list[dict] = []
        self.excecoes: list[dict] = []
        self.pedidos: list[dict] = []
        self.visitas: list[dict] = []
        self.pendencias: list[str] = []

    # -- log ---------------------------------------------------------------
    def _log(self, entidade, ident, linha, acao, campo, antes, depois, regra, codigo=""):
        self.log.append({
            "sequencia": len(self.log) + 1, "entidade": entidade, "id": ident,
            "linha_origem": linha, "acao": acao, "campo": campo,
            "valor_anterior": antes, "valor_novo": depois, "regra": regra,
            "codigo_excecao": codigo,
        })

    def _excecao(self, entidade, ident, linha, competencia, destino, motivo, regra,
                 codigo, bloqueia, registro=None, cliente_origem=""):
        origem = registro or {}
        self.excecoes.append({
            "entidade": entidade, "id": ident, "linha_origem": linha,
            "competencia": competencia, "destino": destino, "motivo": motivo,
            "regra": regra, "codigo_excecao": codigo, "bloqueia_publicacao": bloqueia,
            "receita_bruta": origem.get("receita_bruta", ""),
            "desconto": origem.get("desconto", ""),
            "custo_produto": origem.get("custo_produto", ""),
            "frete": origem.get("frete", ""),
            "status_pedido": origem.get("status_pedido", ""),
            "cliente_id_origem": cliente_origem,
        })

    # -- clientes ----------------------------------------------------------
    def preparar_clientes(self) -> dict:
        cadastro = {}
        for i, reg in enumerate(self.tabelas.get("clientes", {}).get("registros", []), start=2):
            bruto = reg.get("cliente_id", "")
            cid = norm_id(bruto)
            if cid != bruto:
                self._log("cliente", cid, i, "normalizacao", "cliente_id", bruto, cid, "TRUTH-015")
            cadastro[cid] = reg
        return cadastro

    # -- pedidos -----------------------------------------------------------
    def tratar_pedidos(self, cadastro: dict) -> None:
        logistica, logistica_linha = {}, {}
        for i, reg in enumerate(self.tabelas.get("custos_logisticos", {}).get("registros", []), start=2):
            pid = norm_id(reg.get("pedido_id", ""))
            logistica[pid] = reg
            logistica_linha[pid] = i

        versoes: dict[str, list[tuple[int, dict]]] = {}
        for i, reg in enumerate(self.tabelas.get("vendas", {}).get("registros", []), start=2):
            pid_bruto = reg.get("pedido_id", "")
            pid = norm_id(pid_bruto)
            if pid != pid_bruto:
                self._log("pedido", pid, i, "normalizacao", "pedido_id", pid_bruto, pid, "TRUTH-015")
            versoes.setdefault(pid, []).append((i, reg))

        for pid in sorted(versoes):
            grupo = versoes[pid]
            vigente = self._resolver_duplicata(pid, grupo)
            if vigente is None:
                continue
            linha, reg = vigente
            self._avaliar_pedido(pid, linha, reg, cadastro, logistica, logistica_linha)

    def _resolver_duplicata(self, pid: str, grupo: list):
        """TRUTH-011: vale a versao com atualizado_em mais recente. TRUTH-020: empate -> quarentena."""
        if len(grupo) == 1:
            return grupo[0]
        ordenado = sorted(grupo, key=lambda par: (par[1].get("atualizado_em", ""), par[0]))
        mais_recente = ordenado[-1][1].get("atualizado_em", "")
        empatados = [par for par in ordenado if par[1].get("atualizado_em", "") == mais_recente]
        if len(empatados) > 1:
            for linha, reg in ordenado:
                self._excecao(
                    "pedido", pid, linha, competencia_de(reg.get(CAMPO_COMPETENCIA, "")),
                    "quarentena",
                    f"duas ou mais versões com o mesmo atualizado_em ({mais_recente}) — "
                    "a versão vigente não pode ser escolhida por ordem de leitura",
                    "TRUTH-020", "", "sim", reg, reg.get("cliente_id", ""))
                self._log("pedido", pid, linha, "quarentena_acao", "atualizado_em",
                          mais_recente, "", "TRUTH-020")
            return None
        vigente = ordenado[-1]
        for linha, reg in ordenado[:-1]:
            self._excecao(
                "pedido", pid, linha, competencia_de(reg.get(CAMPO_COMPETENCIA, "")),
                "excluido_regra",
                f"versão descartada na deduplicação: atualizado_em {reg.get('atualizado_em', '')} "
                f"anterior à versão vigente ({mais_recente})",
                "TRUTH-011", "EX-01", "nao", reg, reg.get("cliente_id", ""))
            self._log("pedido", pid, linha, "deduplicacao", "atualizado_em",
                      reg.get("atualizado_em", ""), mais_recente, "TRUTH-011", "EX-01")
        return vigente

    def _avaliar_pedido(self, pid, linha, reg, cadastro, logistica, logistica_linha):
        origem_completa = {**reg, "frete": (logistica.get(pid) or {}).get("frete", "")}
        competencia = competencia_de(reg.get(CAMPO_COMPETENCIA, ""))
        cid_bruto = reg.get("cliente_id", "")
        cid = norm_id(cid_bruto)
        status = (reg.get("status_pedido", "") or "").strip()
        marcas = []

        if cid != cid_bruto:
            self._log("pedido", pid, linha, "normalizacao", "cliente_id", cid_bruto, cid,
                      "TRUTH-015", "EX-03")
            marcas.append("id_normalizado")

        # TRUTH-012 tem precedencia: pedido cancelado sai antes de avaliar completude.
        if status in STATUS_PEDIDO_EXCLUIDO:
            self._excecao("pedido", pid, linha, competencia, "excluido_regra",
                          f"status do pedido igual a {status}", "TRUTH-012", "EX-02", "nao",
                          origem_completa, cid_bruto)
            self._log("pedido", pid, linha, "exclusao", "status_pedido", status, "",
                      "TRUTH-012", "EX-02")
            return

        motivos: list[tuple[str, str, str]] = []   # (motivo, regra, codigo)
        if status not in STATUS_PEDIDO_VALIDOS:
            motivos.append((
                f"status '{status or 'vazio'}' fora da lista branca de status válidos "
                f"({', '.join(sorted(STATUS_PEDIDO_VALIDOS))}) — nunca incluído por omissão",
                "TRUTH-016", ""))
        if cid not in cadastro:
            motivos.append((f"cliente {cid} inexistente no cadastro", "TRUTH-013", "EX-04"))
        for campo in ESSENCIAIS_PEDIDO:
            if dec(reg.get(campo, "")) is None:
                motivos.append((f"campo essencial {campo} vazio ou não numérico",
                                "TRUTH-013", "EX-06" if campo == "custo_produto" else ""))
        log_reg = logistica.get(pid)
        if log_reg is None:
            motivos.append(("pedido sem linha correspondente em Custos_Logisticos",
                            "TRUTH-013", ""))
        else:
            for campo in ESSENCIAIS_LOGISTICA:
                if dec(log_reg.get(campo, "")) is None:
                    motivos.append((f"campo essencial {campo} vazio em Custos_Logisticos",
                                    "TRUTH-013", "EX-05"))

        if motivos:
            codigo = next((c for _, _, c in motivos if c), "")
            regras = ", ".join(dict.fromkeys(r for _, r, _ in motivos))
            self._excecao("pedido", pid, linha, competencia, "quarentena",
                          "; ".join(m for m, _, _ in motivos), regras, codigo, "sim",
                          origem_completa, cid_bruto)
            self._log("pedido", pid, linha, "quarentena_acao", "registro", "preservado",
                      "retido fora da base tratada", regras, codigo)
            return

        cliente = cadastro[cid]
        if (cliente.get("status", "") or "").strip() != STATUS_CLIENTE_ATIVO:
            marcas.append("cliente_inativo")
            self._log("pedido", pid, linha, "classificacao", "status_cliente",
                      cliente.get("status", ""), "entra marcado", "TRUTH-018")
        if self.periodo and not self._no_periodo(competencia):
            marcas.append("fora_do_periodo_declarado")

        self.pedidos.append({
            "competencia": competencia, "pedido_id": pid, "cliente_id": cid,
            "cliente_id_origem": cid_bruto, "razao_social": cliente.get("razao_social", ""),
            "regiao": cliente.get("regiao", ""), "segmento": cliente.get("segmento", ""),
            "canal": cliente.get("canal", ""), "status_cliente": cliente.get("status", ""),
            "data_pedido": reg.get("data_pedido", ""), "atualizado_em": reg.get("atualizado_em", ""),
            "receita_bruta": reg.get("receita_bruta", ""), "desconto": reg.get("desconto", ""),
            "custo_produto": reg.get("custo_produto", ""), "frete": log_reg.get("frete", ""),
            "custo_manuseio": log_reg.get("custo_manuseio", ""), "status_pedido": status,
            "marcas": ";".join(marcas), "linha_origem_vendas": linha,
        })

    def _no_periodo(self, competencia: str) -> bool:
        if not self.periodo or not competencia:
            return True
        inicio, _, fim = self.periodo.partition(":")
        return (not inicio or competencia >= inicio) and (not fim or competencia <= fim)

    # -- visitas -----------------------------------------------------------
    def tratar_visitas(self, cadastro: dict) -> None:
        for i, reg in enumerate(self.tabelas.get("visitas", {}).get("registros", []), start=2):
            vid = norm_id(reg.get("visita_id", ""))
            cid_bruto = reg.get("cliente_id", "")
            cid = norm_id(cid_bruto)
            competencia = (reg.get("mes_ref", "") or "").strip()
            status = (reg.get("status", "") or "").strip()
            realizada = (reg.get("data_realizada", "") or "").strip()
            marcas = []
            if cid != cid_bruto:
                self._log("visita", vid, i, "normalizacao", "cliente_id", cid_bruto, cid,
                          "TRUTH-015")
                marcas.append("id_normalizado")

            if cid not in cadastro:
                self._excecao("visita", vid, i, competencia, "quarentena",
                              f"cliente {cid} inexistente no cadastro — regra aplicada por "
                              "analogia a TRUTH-013 (pendência DEC-08)",
                              "TRUTH-013", "", "sim", None, cid_bruto)
                self.pendencias.append(
                    "DEC-08 — visita de cliente fora do cadastro: regra aplicada por analogia "
                    "a TRUTH-013 (quarentena com bloqueio), ainda sem decisão registrada")
                continue

            if status == STATUS_VISITA_REALIZADA and realizada == "":
                classificacao, regra, codigo = "excecao_reportada", "TRUTH-014", "EX-07"
                self._excecao("visita", vid, i, competencia, "excecao_reportada",
                              "status Realizada sem data_realizada — não conta como visita válida",
                              regra, codigo, "nao", None, cid_bruto)
                self._log("visita", vid, i, "classificacao", "status", status,
                          "excecao_reportada", regra, codigo)
            elif status != STATUS_VISITA_REALIZADA:
                classificacao, regra, codigo = "nao_realizada", "TRUTH-014", ""
                self._log("visita", vid, i, "classificacao", "status", status,
                          "nao_realizada", regra)
            else:
                classificacao, regra, codigo = "valida", "TRUTH-014", ""

            if (cadastro[cid].get("status", "") or "").strip() != STATUS_CLIENTE_ATIVO:
                marcas.append("cliente_inativo")

            self.visitas.append({
                "competencia": competencia, "visita_id": vid, "cliente_id": cid,
                "cliente_id_origem": cid_bruto, "status": status,
                "data_planejada": reg.get("data_planejada", ""), "data_realizada": realizada,
                "classificacao": classificacao, "marcas": ";".join(marcas), "linha_origem": i,
            })


# ---------------------------------------------------------------------------
# Reconciliacao (TRUTH-008 / ACC-006)
# ---------------------------------------------------------------------------
def reconciliar(tabelas: dict, tr: Tratamento) -> list[dict]:
    linhas: list[dict] = []

    def somar(registros, campo):
        total, vazios = Decimal("0"), 0
        for reg in registros:
            valor = dec(reg.get(campo, ""))
            if valor is None:
                vazios += 1
            else:
                total += valor
        return total, vazios

    vendas = tabelas.get("vendas", {}).get("registros", [])
    exc_pedidos = [e for e in tr.excecoes if e["entidade"] == "pedido"]
    excluidos = [e for e in exc_pedidos if e["destino"] == "excluido_regra"]
    retidos = [e for e in exc_pedidos if e["destino"] == "quarentena"]

    def bloco(nome, campo, unidade, origem, tratada, exc, quar, observacao=""):
        if unidade == "contagem":
            t_o, t_t, t_e, t_q, vazios = origem, tratada, exc, quar, 0
        else:
            t_o, vazios = somar(origem, campo)
            t_t, _ = somar(tratada, campo)
            t_e, _ = somar(exc, campo)
            t_q, _ = somar(quar, campo)
        diferenca = Decimal(t_o) - Decimal(t_t) - Decimal(t_e) - Decimal(t_q)
        linhas.append({
            "bloco": nome, "campo": campo, "unidade": unidade,
            "total_origem": str(t_o), "total_base_tratada": str(t_t),
            "total_excluido_regra": str(t_e), "total_quarentena": str(t_q),
            "vazios_origem": vazios, "diferenca": str(diferenca),
            "situacao": "ok" if diferenca == 0 else "divergencia", "observacao": observacao,
        })

    bloco("vendas", "linhas", "contagem", len(vendas), len(tr.pedidos),
          len(excluidos), len(retidos))
    for campo in ["receita_bruta", "desconto", "custo_produto"]:
        bloco("vendas", campo, "BRL", vendas, tr.pedidos, excluidos, retidos)

    logistica = tabelas.get("custos_logisticos", {}).get("registros", [])
    ids_tratados = {p["pedido_id"] for p in tr.pedidos}
    ids_excluidos = {e["id"] for e in excluidos} - ids_tratados
    log_tratada = [r for r in logistica if norm_id(r.get("pedido_id", "")) in ids_tratados]
    log_excluida = [r for r in logistica if norm_id(r.get("pedido_id", "")) in ids_excluidos]
    log_retida = [r for r in logistica
                  if norm_id(r.get("pedido_id", "")) not in ids_tratados | ids_excluidos]
    bloco("custos_logisticos", "linhas", "contagem", len(logistica), len(log_tratada),
          len(log_excluida), len(log_retida), "alocadas pelo destino do pedido")
    for campo in ["frete", "custo_manuseio"]:
        bloco("custos_logisticos", campo, "BRL", logistica, log_tratada, log_excluida, log_retida,
              "zero legítimo da fonte (TRUTH-019)" if campo == "custo_manuseio" else "")

    visitas = tabelas.get("visitas", {}).get("registros", [])
    validas = [v for v in tr.visitas if v["classificacao"] == "valida"]
    nao_realizadas = [v for v in tr.visitas if v["classificacao"] == "nao_realizada"]
    outras = [v for v in tr.visitas if v["classificacao"] == "excecao_reportada"]
    outras_qtd = len(outras) + len([e for e in tr.excecoes if e["entidade"] == "visita"
                                    and e["destino"] == "quarentena"])
    bloco("visitas", "linhas", "contagem", len(visitas), len(validas), len(nao_realizadas),
          outras_qtd, "válidas / não realizadas / exceções")

    clientes = tabelas.get("clientes", {}).get("registros", [])
    bloco("clientes", "linhas", "contagem", len(clientes), len(clientes), 0, 0,
          "nenhum tratamento aplicado")
    return linhas


def veredito_por_competencia(tabelas: dict, tr: Tratamento) -> list[dict]:
    competencias = set()
    origem = {}
    for reg in tabelas.get("vendas", {}).get("registros", []):
        comp = competencia_de(reg.get(CAMPO_COMPETENCIA, ""))
        origem[comp] = origem.get(comp, 0) + 1
        competencias.add(comp)
    for p in tr.pedidos:
        competencias.add(p["competencia"])
    for e in tr.excecoes:
        competencias.add(e["competencia"])

    saida = []
    for comp in sorted(c for c in competencias if c):
        tratados = [p for p in tr.pedidos if p["competencia"] == comp]
        bloqueantes = [e for e in tr.excecoes
                       if e["competencia"] == comp and e["bloqueia_publicacao"] == "sim"]
        marcados = [p for p in tratados if p["marcas"]]
        saida.append({
            "competencia": comp,
            "linhas_vendas_origem": origem.get(comp, 0),
            "pedidos_base_tratada": len(tratados),
            "excecoes_bloqueantes": len(bloqueantes),
            "pedidos_marcados": len(marcados),
            "veredito": "nao_calcular" if bloqueantes else "seguro",
            "ids_bloqueantes": sorted({e["id"] for e in bloqueantes}),
        })
    return saida


# ---------------------------------------------------------------------------
# Saidas
# ---------------------------------------------------------------------------
def escrever_csv(caminho: Path, colunas: list[str], registros: list[dict]) -> None:
    with caminho.open("w", newline="", encoding="utf-8") as fh:
        escritor = csv.DictWriter(fh, fieldnames=colunas, lineterminator="\n",
                                  extrasaction="ignore")
        escritor.writeheader()
        for reg in registros:
            escritor.writerow(reg)


def montar_payload(rotulo_execucao, entrada, tipo_entrada, fontes, tabelas, tr,
                   reconciliacao, veredito, periodo) -> dict:
    bloqueantes = [e for e in tr.excecoes if e["bloqueia_publicacao"] == "sim"]
    impacto = []
    for chave, nome, regra in [
        ("normalizacao", "Identificadores normalizados", "TRUTH-015"),
        ("deduplicacao", "Versão vigente de pedido duplicado", "TRUTH-011"),
        ("exclusao", "Pedido excluído por status", "TRUTH-012"),
        ("quarentena_acao", "Registro retido por informação faltante", "TRUTH-013/016/020"),
        ("classificacao", "Classificação de visita e de cliente", "TRUTH-014/018"),
    ]:
        itens = [linha for linha in tr.log if linha["acao"] == chave]
        if itens:
            impacto.append({
                "acao": chave, "nome": nome, "regra": regra, "registros": len(itens),
                "ids": sorted({linha["id"] for linha in itens}),
            })
    return {
        "versao_base_tratada": VERSAO,
        "rotulo": rotulo_execucao,
        "natureza": "tratamento com regra aprovada; nenhum indicador de negocio calculado",
        "periodo_declarado": periodo or "",
        "entrada": {"caminho": str(entrada), "tipo": tipo_entrada, "fontes": fontes},
        "resumo": {
            "pedidos_base_tratada": len(tr.pedidos),
            "visitas_base_tratada": len(tr.visitas),
            "visitas_validas": len([v for v in tr.visitas if v["classificacao"] == "valida"]),
            "excecoes": len(tr.excecoes),
            "excecoes_bloqueantes": len(bloqueantes),
            "transformacoes_registradas": len(tr.log),
            "publicacao_bloqueada": "sim" if bloqueantes else "nao",
            "reconciliacao": "ok" if all(l["situacao"] == "ok" for l in reconciliacao)
                             else "divergencia",
        },
        "impacto_por_regra": impacto,
        "veredito_competencia": veredito,
        "reconciliacao": reconciliacao,
        "excecoes": tr.excecoes,
        "log_tratamento": tr.log,
        "base_tratada_pedidos": tr.pedidos,
        "base_tratada_visitas": tr.visitas,
        "pendencias_registradas": sorted(set(tr.pendencias)),
    }


def render_markdown(payload: dict) -> str:
    resumo = payload["resumo"]
    linhas = [
        f"# Relatório de tratamento da base operacional — {payload['rotulo']}",
        "",
        f"Versão do tratamento: {payload['versao_base_tratada']} · "
        f"Entrada: `{payload['entrada']['caminho']}` ({payload['entrada']['tipo']})",
        "",
        "> Este relatório registra **o que foi transformado, o que foi excluído e o que foi "
        "retido**, com a regra que autorizou cada decisão. Nenhuma correção, exclusão ou escolha "
        "entre versões acontece em silêncio. Nenhum indicador de negócio é calculado aqui: "
        "receita líquida, margens, ranking e clientes-alerta são do ciclo seguinte.",
        "",
        "## Veredito de publicação",
        "",
    ]
    if resumo["publicacao_bloqueada"] == "sim":
        linhas += [
            f"**PUBLICAÇÃO BLOQUEADA** — {resumo['excecoes_bloqueantes']} exceção(ões) "
            "bloqueante(s) aberta(s) (ACC-007). O relatório ao cliente não pode ser publicado "
            "enquanto não forem tratadas na origem.", ""]
    else:
        linhas += ["**Publicação liberada** — nenhuma exceção bloqueante aberta.", ""]

    linhas += ["### Segurança por competência", "",
               "| Competência | Linhas na origem | Pedidos na base tratada | Exceções bloqueantes | Veredito |",
               "| --- | --- | --- | --- | --- |"]
    for item in payload["veredito_competencia"]:
        ids = f" ({', '.join(item['ids_bloqueantes'])})" if item["ids_bloqueantes"] else ""
        linhas.append(f"| {item['competencia']} | {item['linhas_vendas_origem']} | "
                      f"{item['pedidos_base_tratada']} | {item['excecoes_bloqueantes']}{ids} | "
                      f"{rotulo(item['veredito'])} |")

    linhas += ["", "## Resumo do tratamento", "",
               f"- Pedidos na base tratada: **{resumo['pedidos_base_tratada']}**",
               f"- Visitas válidas: **{resumo['visitas_validas']}** "
               f"(de {resumo['visitas_base_tratada']} classificadas)",
               f"- Exceções: **{resumo['excecoes']}**, das quais "
               f"**{resumo['excecoes_bloqueantes']}** bloqueiam publicação",
               f"- Transformações registradas no log: **{resumo['transformacoes_registradas']}**",
               f"- Reconciliação: **{rotulo(resumo['reconciliacao'])}**", ""]

    linhas += ["## Impacto de cada regra aplicada", "",
               "| Regra | O que fez | Registros | Identificadores |", "| --- | --- | --- | --- |"]
    for item in payload["impacto_por_regra"]:
        linhas.append(f"| {item['regra']} | {item['nome']} | {item['registros']} | "
                      f"{', '.join(item['ids'])} |")

    linhas += ["", "## Exceções — o que não entrou e por quê", "",
               "| Entidade | Id | Linha | Competência | Destino | Motivo | Regra | Código | Bloqueia publicação |",
               "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for e in payload["excecoes"]:
        linhas.append(f"| {e['entidade']} | {e['id']} | {e['linha_origem']} | {e['competencia']} | "
                      f"{rotulo(e['destino'])} | {e['motivo']} | {e['regra']} | "
                      f"{e['codigo_excecao'] or '—'} | {rotulo(e['bloqueia_publicacao'])} |")

    linhas += ["", "## Reconciliação — origem × base tratada × excluídos × retidos", "",
               "| Bloco | Campo | Unidade | Origem | Base tratada | Excluído | Quarentena | Vazios | Diferença | Situação |",
               "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for r in payload["reconciliacao"]:
        fmt = (lambda v: brl(Decimal(v))) if r["unidade"] == "BRL" else (lambda v: v)
        linhas.append(f"| {r['bloco']} | {r['campo']} | {r['unidade']} | {fmt(r['total_origem'])} | "
                      f"{fmt(r['total_base_tratada'])} | {fmt(r['total_excluido_regra'])} | "
                      f"{fmt(r['total_quarentena'])} | {r['vazios_origem']} | "
                      f"{fmt(r['diferenca'])} | {rotulo(r['situacao'])} |")

    linhas += ["", "## Log de tratamento (transformação por transformação)", "",
               "| # | Entidade | Id | Linha | Ação | Campo | Valor anterior | Valor novo | Regra |",
               "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for item in payload["log_tratamento"]:
        acao = rotulo("quarentena_acao" if item["acao"] == "quarentena_acao" else item["acao"])
        linhas.append(f"| {item['sequencia']} | {item['entidade']} | {item['id']} | "
                      f"{item['linha_origem']} | {acao} | {item['campo']} | "
                      f"{rotulo(item['valor_anterior']) or '—'} | "
                      f"{rotulo(item['valor_novo']) or '—'} | "
                      f"{item['regra']} |")

    if payload["pendencias_registradas"]:
        linhas += ["", "## Decisões ainda pendentes do negócio", ""]
        linhas += [f"- {p}" for p in payload["pendencias_registradas"]]

    linhas += ["", "## O que este relatório NÃO contém", "",
               "- Nenhuma receita líquida, margem de contribuição, margem de servir, ranking ou "
               "lista de clientes-alerta — dependem das fórmulas TRUTH-001..005 e do ciclo do cálculo.",
               "- Nenhum valor imputado, estimado ou corrigido por inferência: registro incompleto "
               "é retido, nunca completado por adivinhação.",
               "- Nenhum parâmetro econômico consumido: a camada de tratamento é livre de parâmetro.",
               "- Nenhuma alteração no arquivo de origem (leitura somente, SHA-256 conferido).",
               ""]
    return "\n".join(linhas)


def executar(entrada: Path, saida: Path, rotulo_execucao: str | None, periodo: str | None) -> dict:
    if entrada.is_dir():
        tabelas, fontes, _ = ler_csvs(entrada)
        tipo_entrada = "pasta de CSVs"
    else:
        tabelas, fontes, _ = ler_xlsx(entrada)
        tipo_entrada = "planilha .xlsx"

    faltando = [nome for nome in CONTRATO if nome not in tabelas]
    if faltando:
        raise SystemExit("ERRO: a base tratada exige todas as tabelas do contrato da fonte. "
                         f"Ausentes: {', '.join(faltando)}. Rode o diagnóstico "
                         "(src/diagnostico_fonte.py) para o retrato completo da entrada.")

    tr = Tratamento(tabelas, periodo)
    cadastro = tr.preparar_clientes()
    tr.tratar_pedidos(cadastro)
    tr.tratar_visitas(cadastro)

    tr.pedidos.sort(key=lambda p: (p["competencia"], p["cliente_id"], p["pedido_id"]))
    tr.visitas.sort(key=lambda v: (v["competencia"], v["cliente_id"], v["visita_id"]))
    tr.excecoes.sort(key=lambda e: (e["entidade"], e["id"], e["linha_origem"]))

    reconciliacao = reconciliar(tabelas, tr)
    veredito = veredito_por_competencia(tabelas, tr)
    rotulo_final = rotulo_execucao or "execucao"
    payload = montar_payload(rotulo_final, entrada, tipo_entrada, fontes, tabelas, tr,
                             reconciliacao, veredito, periodo)

    saida.mkdir(parents=True, exist_ok=True)
    escrever_csv(saida / "base_tratada_pedidos.csv", COLUNAS_PEDIDOS, tr.pedidos)
    escrever_csv(saida / "base_tratada_visitas.csv", COLUNAS_VISITAS, tr.visitas)
    escrever_csv(saida / "excecoes.csv", COLUNAS_EXCECOES, tr.excecoes)
    escrever_csv(saida / "log_tratamento.csv", COLUNAS_LOG, tr.log)
    escrever_csv(saida / "reconciliacao.csv", COLUNAS_RECONCILIACAO, reconciliacao)
    (saida / f"tratamento_{rotulo_final}.md").write_text(render_markdown(payload), encoding="utf-8")
    (saida / f"tratamento_{rotulo_final}.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Gera a base tratada oficial da base operacional mensal, com log de "
                    "tratamento, exceções e reconciliação. Não calcula indicador de negócio.")
    parser.add_argument("--entrada", required=True,
                        help="planilha .xlsx do mês ou pasta com as CSVs (uma por aba)")
    parser.add_argument("--saida", default="outputs/base-tratada",
                        help="pasta de saída (padrão: outputs/base-tratada)")
    parser.add_argument("--rotulo", default=None,
                        help="rótulo da execução, usado no nome do relatório")
    parser.add_argument("--periodo", default=None,
                        help="período declarado, no formato 2026-01:2026-03")
    args = parser.parse_args(argv)

    entrada = Path(args.entrada)
    if not entrada.exists():
        print(f"ERRO: entrada não encontrada: {entrada}")
        return 2
    hash_antes = _sha256(entrada) if entrada.is_file() else ""

    payload = executar(entrada, Path(args.saida), args.rotulo, args.periodo)

    if hash_antes and _sha256(entrada) != hash_antes:
        print("ERRO: o arquivo de origem foi alterado durante a leitura.")
        return 3

    resumo = payload["resumo"]
    print(f"Base tratada v{payload['versao_base_tratada']} — {payload['rotulo']}")
    print(f"  pedidos na base tratada: {resumo['pedidos_base_tratada']} | "
          f"visitas válidas: {resumo['visitas_validas']}")
    print(f"  exceções: {resumo['excecoes']} "
          f"({resumo['excecoes_bloqueantes']} bloqueiam publicação) | "
          f"transformações: {resumo['transformacoes_registradas']}")
    print(f"  reconciliação: {resumo['reconciliacao']} | "
          f"publicação bloqueada: {resumo['publicacao_bloqueada']}")
    for item in payload["veredito_competencia"]:
        print(f"  {item['competencia']}: {item['pedidos_base_tratada']} pedido(s), "
              f"{item['excecoes_bloqueantes']} bloqueante(s) → {item['veredito']}")
    print(f"  saída: {args.saida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
