#!/usr/bin/env bash
# Aplica patches/*.patch no runner, configura com CMake e compila para PS4.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
source project.env
: "${OO_PS4_TOOLCHAIN:?OO_PS4_TOOLCHAIN não definido}"
B=vendor/butterscotch

echo "== Commit em uso =="
git -C "$B" log -1 --stat | head -40
echo "== Opções de plataforma no CMake (para ajustar CMAKE_ARGS) =="
grep -niE 'PLATFORM|BACKEND|ps4' "$B/CMakeLists.txt" | head -40 || true

for p in patches/*.patch; do
  [ -e "$p" ] || continue
  echo "== Aplicando $p =="
  git -C "$B" apply "$ROOT/$p"
done

cmake -S "$B" -B build $CMAKE_ARGS
cmake --build build -j"$(nproc)"

mkdir -p out
find build -type f \( -name '*.pkg' -o -name 'eboot.bin' -o -name '*.oelf' -o -name '*.elf' \) -exec cp {} out/ \;
ls -la out
