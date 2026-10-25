#!/usr/bin/env bash
# Aplica patches e a checagem prévia no runner, configura com CMake, compila para PS4 e empacota o .pkg.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
source project.env
: "${OO_PS4_TOOLCHAIN:?OO_PS4_TOOLCHAIN não definido}"
B=vendor/butterscotch

echo "== Commit em uso =="
git -C "$B" log -1 --stat | head -40

for p in patches/*.patch; do
  [ -e "$p" ] || continue
  echo "== Aplicando $p =="
  git -C "$B" apply "$ROOT/$p"
done

echo "== Checagem prévia dos arquivos do jogo =="
mkdir -p out/info
cp "$B/src/ps4/main.c" out/info/ps4_main_original.c 2>/dev/null || true
cp "$B/cmake/ps4.cmake" out/info/ps4.cmake 2>/dev/null || true
for f in src/loop.c src/loop.h src/platformdefs.h src/backends/sdl2.c CMakeLists.txt; do
  cp "$B/$f" out/info/ 2>/dev/null || true
done
python3 scripts/inject_preflight.py "$B/src/ps4/main.c" | tee out/info/injecao.txt
cp "$B/src/ps4/main.c" out/info/ps4_main_injetado.c

if [ -n "${GITHUB_STEP_SUMMARY:-}" ]; then
  {
    echo "## Checagem prévia"
    echo '```'
    cat out/info/injecao.txt || true
    echo '```'
    echo "## Caminhos de arquivo no código do PS4"
    echo '```'
    {
      grep -rnE '"[^"]*(/data|/app0|/mnt|data\.win|[Bb]utterscotch)[^"]*"' \
        "$B/src/ps4" "$B/cmake/ps4.cmake" "$B"/src/backends/sdl*.c "$B/src/platformdefs.h" 2>/dev/null
      grep -rnE '"(/data|/app0|/mnt)[^"]*"' "$B/src" 2>/dev/null
    } | sort -u | head -60 || true
    echo '```'
    echo "## SDL: video e controle (backend SDL)"
    echo '```'
    grep -nE 'SDL_(Init|Quit|SetVideoMode|Flip|Joystick|JoystickOpen|PollEvent|CreateRGB)|JOYSTICK|JOYBUTTON|JOYHAT' "$B"/src/backends/sdl*.c 2>/dev/null | head -60 || true
    echo '```'
    echo "## ps4.cmake (SDL e link)"
    echo '```'
    grep -nE 'SDL|LINK|link|lib|include' "$B/cmake/ps4.cmake" 2>/dev/null | head -40 || true
    echo '```'
    echo "## main.c original do PS4"
    echo '```c'
    cat out/info/ps4_main_original.c || true
    echo '```'
  } >> "$GITHUB_STEP_SUMMARY"
fi

cmake -S "$B" -B build $CMAKE_ARGS
cmake --build build -j"$(nproc)"

mkdir -p out
find build -type f \( -name 'eboot.bin' -o -name '*.oelf' -o -name '*.elf' \) -exec cp {} out/ \;
ls -la out

echo "== Empacotando .pkg =="
bash scripts/package_pkg.sh

echo "== Resumo da checagem prévia =="
cat out/info/injecao.txt
