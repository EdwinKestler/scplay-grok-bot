#!/usr/bin/env bash
# Download Blizzard ladder/melee map packs into $SC2PATH/Maps
# Password for zips: iagreetotheeula (Blizzard AI/ML license)
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ -z "${SC2PATH:-}" ]]; then
  # shellcheck disable=SC1091
  eval "$("$ROOT/scripts/find_sc2.sh" | grep -E '^(SC2PATH|WINEPREFIX|WINE|SC2PF)=')"
fi

MAPS="$SC2PATH/Maps"
CACHE="${SC2_MAP_CACHE:-$ROOT/sc2-cache/map-packs}"
PASS="iagreetotheeula"
mkdir -p "$MAPS" "$CACHE"

download() {
  local url="$1" out="$2"
  if [[ -f "$out" ]]; then
    echo "Already have $out"
  else
    echo "Downloading $url"
    curl -L --fail -o "$out" "$url"
  fi
}

download "https://blzdistsc2-a.akamaihd.net/MapPacks/Melee.zip" "$CACHE/Melee.zip"
download "https://blzdistsc2-a.akamaihd.net/MapPacks/Ladder2019Season3.zip" "$CACHE/Ladder2019Season3.zip"
download "https://blzdistsc2-a.akamaihd.net/MapPacks/Ladder2018Season2_Updated.zip" "$CACHE/Ladder2018Season2_Updated.zip"
download "https://blzdistsc2-a.akamaihd.net/MapPacks/Ladder2017Season1.zip" "$CACHE/Ladder2017Season1.zip"

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

unzip -o -P "$PASS" "$CACHE/Melee.zip" -d "$TMP/Melee"
unzip -o -P "$PASS" "$CACHE/Ladder2019Season3.zip" -d "$TMP/L2019"
unzip -o -P "$PASS" "$CACHE/Ladder2018Season2_Updated.zip" -d "$TMP/L2018"
unzip -o -P "$PASS" "$CACHE/Ladder2017Season1.zip" -d "$TMP/L2017"

rm -rf "$MAPS/Melee" "$MAPS/Ladder2019Season3" "$MAPS/Ladder2018Season2" "$MAPS/Ladder2017Season1"
cp -a "$TMP/Melee/Melee" "$MAPS/Melee"
cp -a "$TMP/L2019/Ladder2019Season3" "$MAPS/Ladder2019Season3"
mkdir -p "$MAPS/Ladder2018Season2"
cp -a "$TMP/L2018/Ladder2018Season2/." "$MAPS/Ladder2018Season2/"
cp -a "$TMP/L2017/Ladder2017Season1" "$MAPS/Ladder2017Season1"

# Root symlinks so maps.get("AbyssalReefLE") works
cd "$MAPS"
find . -name '*.SC2Map' | while read -r f; do
  base=$(basename "$f")
  clean=$(echo "$base" | sed -E 's/^\([0-9]+\)//')
  if [[ ! -e "$clean" ]]; then
    ln -s "$f" "$clean"
  fi
done

echo "Installed maps under: $MAPS"
echo "AbyssalReefLE -> $(ls -la "$MAPS/AbyssalReefLE.SC2Map" 2>/dev/null || echo MISSING)"
echo "Map count: $(find "$MAPS" -name '*.SC2Map' | wc -l)"
