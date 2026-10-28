#!/usr/bin/env bash
# Install the Horizon Wilds pack into a Horizon game folder.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HORIZON_DIR="${HORIZON_DIR:-$HOME/.local/share/horizon}"
MODS="$HORIZON_DIR/horizon-mods"
TXT="$HORIZON_DIR/horizon-mods.txt"

# The pack's four mods: folder -> .hmod id.
mods=( "wilds-kit:wilds_kit" "wilds-ruins:wilds_ruins"
       "wilds-needs:wilds_needs" "wilds-climate:wilds_climate" )

[ -d "$HORIZON_DIR" ] || { echo "No Horizon game folder at $HORIZON_DIR" >&2; exit 1; }
mkdir -p "$MODS"

installed=0
for spec in "${mods[@]}"; do
  folder="${spec%%:*}"; id="${spec#*:}"
  hmod="$HERE/mods-src/$folder/target/horizon-mod/$id.hmod"
  [ -f "$hmod" ] || { echo "missing build output: $hmod" >&2
                      echo "build it first (see README.md)" >&2; exit 1; }
  install -m 644 "$hmod" "$MODS/$id.hmod"
  installed=$((installed+1))
done

# Enable lines mod.<id>:true, appended exactly once; nothing else is touched.
if [ -f "$TXT" ]; then
  cp "$TXT" "$TXT.wilds.bak"
else
  touch "$TXT"
fi
for spec in "${mods[@]}"; do
  id="${spec#*:}"
  if [ -f "$TXT" ] && grep -qs "^mod\.$id:" "$TXT"; then
    echo "already configured: mod.$id (kept as is: $(grep "^mod\.$id:" "$TXT" | tail -1))"
  else
    printf 'mod.%s:true\n' "$id" >> "$TXT"
    echo "enabled: mod.$id"
  fi
done

echo
echo "Installed $installed mods into $MODS"
echo "Start Horizon: blocks, items and recipes are there right away;"
echo "camps and shrines only generate in new / unvisited chunks."
