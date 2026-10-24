#!/usr/bin/env bash
# Baixa e extrai o OpenOrbis PS4 Toolchain (última release) e exporta OO_PS4_TOOLCHAIN.
set -euo pipefail
OO_DIR="${OO_DIR:-$HOME/oo}"
mkdir -p "$OO_DIR"
cd "$OO_DIR"
if [ -z "$(find . -maxdepth 4 -type d -name hello_world | head -n1)" ]; then
  gh release download --repo OpenOrbis/OpenOrbis-PS4-Toolchain --pattern '*.tar.gz'
  tar -xzf ./*.tar.gz
fi
HW="$(find "$OO_DIR" -maxdepth 4 -type d -name hello_world | head -n1)"
if [ -z "$HW" ]; then
  echo "ERRO: hello_world não encontrado após extrair o toolchain" >&2
  ls -R "$OO_DIR" | head -50 >&2
  exit 1
fi
TC="$(dirname "$(dirname "$HW")")"
echo "OO_PS4_TOOLCHAIN=$TC"
if [ -n "${GITHUB_ENV:-}" ]; then
  echo "OO_PS4_TOOLCHAIN=$TC" >> "$GITHUB_ENV"
fi
