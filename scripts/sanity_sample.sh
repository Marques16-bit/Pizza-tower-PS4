#!/usr/bin/env bash
# Compila o sample oficial hello_world para validar toolchain + empacotamento.
set -euo pipefail
cd "$(dirname "$0")/.."
source project.env
if [ "${RUN_SANITY_SAMPLE:-0}" != "1" ]; then
  echo "sanity desligado em project.env"
  exit 0
fi
: "${OO_PS4_TOOLCHAIN:?OO_PS4_TOOLCHAIN não definido}"
S="$OO_PS4_TOOLCHAIN/samples/hello_world"
make -C "$S"
mkdir -p out/sanity
find "$S" -name '*.pkg' -exec cp {} out/sanity/ \;
ls -la out/sanity
