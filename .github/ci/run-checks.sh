#!/usr/bin/env bash
# Checks do projeto Aucta Foods — Rentabilidade por Cliente (tier 2).
# Adaptado pelo init-repo. Tier >= 2: harness de golden cases com recomputação
# INDEPENDENTE (nunca o código sob teste) — obrigatório quando houver código.
set -euo pipefail
fail=0

echo "== 1. Artefatos canônicos presentes =="
for f in PROJECT.md TRUTHS.md GLOSSARY.md ACCEPTANCE.md OWNERS.md .project/init-state.md; do
  if [ ! -f "$f" ]; then echo "FALHA: artefato canônico ausente: $f"; fail=1; else echo "ok: $f"; fi
done

echo "== 2. Guarda de dados (TRUTH-006): nenhuma base fora de tests/fixtures/ =="
violacoes=$(find . -path ./.git -prune -o -type f \( -name '*.xlsx' -o -name '*.xls' -o -name '*.csv' -o -name '*.parquet' \) -print | grep -v '^./tests/fixtures/' || true)
if [ -n "$violacoes" ]; then
  echo "FALHA: arquivos de dados fora de tests/fixtures/ (dados reais nunca entram no Git):"
  echo "$violacoes"
  fail=1
else
  echo "ok: nenhuma base fora de tests/fixtures/"
fi

echo "== 3. Sintaxe Python (quando houver código) =="
if [ -d src ]; then
  python3 -m compileall -q src || { echo "FALHA: erro de sintaxe em src/"; fail=1; }
else
  echo "ok: src/ ainda não existe (pré-desenvolvimento)"
fi

echo "== 3b. Dependências declaradas (instalação reproduzível) =="
if [ -d src ] && [ -f requirements.txt ]; then
  # Versões fixas com hash verificado (requirements.txt). O caminho .xlsx da
  # solução depende de openpyxl; sem ele a suite Excel do harness reprova.
  if python3 -m pip install --quiet --require-hashes -r requirements.txt >/dev/null 2>&1; then
    echo "ok: dependências instaladas (--require-hashes)"
  elif python3 -m pip install --quiet --require-hashes --break-system-packages -r requirements.txt; then
    echo "ok: dependências instaladas (--require-hashes, --break-system-packages)"
  else
    echo "FALHA: não foi possível instalar as dependências de requirements.txt"
    fail=1
  fi
else
  echo "ok: nada a instalar (sem src/ ou sem requirements.txt)"
fi

echo "== 4. Golden cases (tier 2: obrigatórios quando houver código) =="
if [ -d src ]; then
  if [ -f tests/golden/run_golden.py ]; then
    python3 tests/golden/run_golden.py || { echo "FALHA: golden cases não bateram"; fail=1; }
  else
    echo "FALHA: src/ existe mas tests/golden/run_golden.py não — golden cases são obrigatórios (tier 2)"
    fail=1
  fi
else
  echo "ok: sem código sob teste ainda"
fi

exit $fail
