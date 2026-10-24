#!/usr/bin/env bash
# Aplica patches/*.patch no runner, configura com CMake, compila para PS4 e empacota o .pkg.
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

echo "== Caminhos e argumentos no main do PS4 =="
grep -nE 'data\.win|"/|argv|usb|fopen' "$B/src/ps4/main.c" || true
mkdir -p out/info
cp "$B/src/ps4/main.c" out/info/ps4_main.c 2>/dev/null || true
cp "$B/cmake/ps4.cmake" out/info/ps4.cmake 2>/dev/null || true

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

echo "== Empacotando .pkg =="
bash scripts/package_pkg.sh
