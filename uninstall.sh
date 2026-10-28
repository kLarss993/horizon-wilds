#!/usr/bin/env bash
# Remove the Horizon Wilds pack from a Horizon game folder.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HORIZON_DIR="${HORIZON_DIR:-$HOME/.local/share/horizon}"
MODS="$HORIZON_DIR/horizon-mods"
TXT="$HORIZON_DIR/horizon-mods.txt"

ids=( "wilds_kit" "wilds_ruins" "wilds_needs" "wilds_climate" )

removed=0
for id in "${ids[@]}"; do
  if [ -f "$MODS/$id.hmod" ]; then
    rm "$MODS/$id.hmod"
    removed=$((removed+1))
    echo "removed: horizon-mods/$id.hmod"
  fi
  if [ -d "$MODS/.horizon-mod-data/$id" ]; then
    rm -rf "$MODS/.horizon-mod-data/$id"
    echo "removed: .horizon-mod-data/$id (its stored settings)"
  fi
done

# Drop the mods' toggle lines, keep everything else.
if [ -f "$TXT" ]; then
  tmp="$(mktemp)"
  grep -v "^mod\.wilds_\(kit\|ruins\|needs\|climate\):" "$TXT" > "$tmp" || true
  cp "$TXT" "$TXT.wilds.bak"
  mv "$tmp" "$TXT"
  echo "cleaned: toggles removed from horizon-mods.txt (backup: horizon-mods.txt.wilds.bak)"
fi

# The shader pack and its pick line, if this install had them.
if [ -d "$HORIZON_DIR/shaderpacks/wilds_light" ]; then
  rm -rf "$HORIZON_DIR/shaderpacks/wilds_light"
  echo "removed: shaderpacks/wilds_light"
fi
if [ -f "$HORIZON_DIR/options.txt" ]; then
  line="$(grep "^pickedShaderPack:wilds_light$" "$HORIZON_DIR/options.txt" || true)"
  if [ -n "$line" ]; then
    tmp="$(mktemp)"
    grep -v "^pickedShaderPack:wilds_light$" "$HORIZON_DIR/options.txt" > "$tmp" || true
    mv "$tmp" "$HORIZON_DIR/options.txt"
    echo "cleaned: pickedShaderPack line removed (none runs until you pick another)"
  fi
fi

echo "Uninstalled $removed mod files. Worlds keep anything already placed/generated."
