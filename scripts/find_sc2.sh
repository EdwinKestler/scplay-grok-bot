#!/usr/bin/env bash
# Print best-guess SC2PATH / WINE / WINEPREFIX for Steam Proton Battle.net SC2 on Linux.
set -euo pipefail

STEAM_ROOT="${STEAM_ROOT:-$HOME/.local/share/Steam}"
COMPAT="$STEAM_ROOT/steamapps/compatdata"

found_pfx=""
found_sc2=""

if [[ -d "$COMPAT" ]]; then
  while IFS= read -r -d '' sc2dir; do
    found_sc2="$sc2dir"
    # .../pfx/drive_c/Program Files (x86)/StarCraft II
    found_pfx="$(dirname "$(dirname "$(dirname "$sc2dir")")")"
    break
  done < <(find "$COMPAT" -type d -path '*/drive_c/Program Files (x86)/StarCraft II' -print0 2>/dev/null | head -z -n 1)
fi

# Fallback: Lutris default
if [[ -z "$found_sc2" ]]; then
  for cand in \
    "$HOME/Games/battlenet/drive_c/Program Files (x86)/StarCraft II" \
    "$HOME/.wine/drive_c/Program Files (x86)/StarCraft II"
  do
    if [[ -d "$cand" ]]; then
      found_sc2="$cand"
      found_pfx="$(dirname "$(dirname "$(dirname "$cand")")")"
      break
    fi
  done
fi

PROTON_WINE=""
for p in \
  "$STEAM_ROOT/steamapps/common/Proton - Experimental/files/bin/wine" \
  "$STEAM_ROOT/steamapps/common/Proton 9.0 (Beta)/files/bin/wine" \
  "$STEAM_ROOT/steamapps/common/Proton - Experimental/dist/bin/wine"
do
  if [[ -x "$p" || -f "$p" ]]; then
    PROTON_WINE="$p"
    break
  fi
done

if [[ -z "$found_sc2" ]]; then
  echo "ERROR: Could not find StarCraft II under Steam Proton or common Wine/Lutris paths." >&2
  echo "Set SC2PATH / WINEPREFIX / WINE yourself (see README)." >&2
  exit 1
fi

echo "SC2PATH=$found_sc2"
echo "WINEPREFIX=$found_pfx"
if [[ -n "$PROTON_WINE" ]]; then
  echo "WINE=$PROTON_WINE"
else
  echo "WINE=${WINE:-/usr/bin/wine}"
  echo "# WARNING: Proton wine binary not found; using \$WINE or /usr/bin/wine" >&2
fi
echo "SC2PF=WineLinux"
