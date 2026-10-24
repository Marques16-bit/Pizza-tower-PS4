#!/usr/bin/env bash
# Empacota out/eboot.bin num .pkg instalável.
# Reaproveita sce_sys e módulos do sample hello_world e troca só a identidade (título e IDs).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
: "${OO_PS4_TOOLCHAIN:?OO_PS4_TOOLCHAIN não definido}"

BIN="$OO_PS4_TOOLCHAIN/bin/linux"
PKGTOOL="$BIN/PkgTool.Core"
GP4TOOL="$BIN/create-gp4"
HW="$OO_PS4_TOOLCHAIN/samples/hello_world"
STAGE="$ROOT/build/pkg"

OLD_CID="IV0000-BREW00083_00-HELLOWORLD000000"
NEW_CID="IV0000-PZTW00001_00-PIZZATOWER000000"
NEW_TID="PZTW00001"
NEW_TITLE="Pizza Tower (Butterscotch)"

if [ ! -f out/eboot.bin ]; then
  echo "ERRO: out/eboot.bin não existe" >&2
  exit 1
fi

echo "== Ferramentas em $BIN =="
ls -la "$BIN" | head -30

# 1) Monta a pasta do pacote
rm -rf "$STAGE"
mkdir -p "$STAGE"
for d in "$HW"/sce_* "$OO_PS4_TOOLCHAIN"/sce_*; do
  if [ -d "$d" ]; then
    cp -rn "$d" "$STAGE/" || true
  fi
done
cp out/eboot.bin "$STAGE/eboot.bin"
if [ -f assets/icon0.png ]; then
  cp assets/icon0.png "$STAGE/sce_sys/icon0.png"
fi
if [ ! -f "$STAGE/sce_sys/param.sfo" ]; then
  echo "ERRO: param.sfo do sample não encontrado" >&2
  ls -R "$HW" | head -40 >&2
  exit 1
fi

# 2) Troca título e IDs no param.sfo (se falhar, mantém o SFO original do sample)
SFO="$STAGE/sce_sys/param.sfo"
cp "$SFO" /tmp/param.sfo.bak
set_entry() {
  local key="$1" type="$2" max="$3" val="$4"
  "$PKGTOOL" sfo_setentry "$SFO" "$key" --type "$type" --maxsize "$max" --value "$val" \
    || "$PKGTOOL" sfo_setentry "$SFO" "$key" --type "$(echo "$type" | tr 'A-Z' 'a-z')" --maxsize "$max" --value "$val"
}
CID="$OLD_CID"
if set_entry CONTENT_ID Utf8 48 "$NEW_CID" \
   && set_entry TITLE_ID Utf8 12 "$NEW_TID" \
   && set_entry TITLE Utf8 128 "$NEW_TITLE"; then
  CID="$NEW_CID"
  echo "SFO atualizado: $CID"
else
  echo "AVISO: não consegui editar o SFO; mantendo a identidade do hello_world"
  cp /tmp/param.sfo.bak "$SFO"
  "$PKGTOOL" sfo_listentries "$SFO" || true
  "$PKGTOOL" || true
fi

# 3) GP4 + PKG
cd "$STAGE"
FILES="$(find . -type f ! -name '*.gp4' | sed 's|^\./||' | sort | tr '\n' ' ')"
echo "Arquivos no pacote: $FILES"
"$GP4TOOL" -out "$CID.gp4" --content-id="$CID" --files "$FILES"
"$PKGTOOL" pkg_build "$CID.gp4" "$ROOT/out"

cd "$ROOT"
PKG="$(find "$ROOT/out" "$STAGE" -maxdepth 1 -name '*.pkg' -newer "$STAGE/$CID.gp4" | head -n1)"
if [ -z "$PKG" ]; then
  echo "ERRO: pkg_build não gerou .pkg" >&2
  exit 1
fi
case "$PKG" in
  "$ROOT"/out/*) ;;
  *) cp "$PKG" out/ ;;
esac
ls -la out
