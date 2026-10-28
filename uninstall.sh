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

echo "Uninstalled $removed mod files. Worlds keep anything already placed/generated."
