#!/usr/bin/env bash
# Launch Human vs PlaybotSparBot against Proton/Wine StarCraft II.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -d "$ROOT/.venv" ]]; then
  echo "Missing .venv — run: $ROOT/scripts/setup_venv.sh" >&2
  exit 1
fi
# shellcheck disable=SC1091
source "$ROOT/.venv/bin/activate"

# Auto-detect unless already set
if [[ -z "${SC2PATH:-}" || -z "${WINE:-}" || -z "${WINEPREFIX:-}" || -z "${SC2PF:-}" ]]; then
  while IFS= read -r line; do
    case "$line" in
      SC2PATH=*|WINE=*|WINEPREFIX=*|SC2PF=*) export "$line" ;;
    esac
  done < <("$ROOT/scripts/find_sc2.sh")
fi

export SC2PF="${SC2PF:-WineLinux}"
export PLAYBOT_CHAT_LOG="${PLAYBOT_CHAT_LOG:-$ROOT/replays/playbot_live_chat.log}"
export SCPLAY_LOGS_ROOT="${SCPLAY_LOGS_ROOT:-$ROOT/logs}"
mkdir -p "$ROOT/replays"

echo "SC2PF=$SC2PF"
echo "WINE=$WINE"
echo "WINEPREFIX=$WINEPREFIX"
echo "SC2PATH=$SC2PATH"

if pgrep -af 'SC2_x64\.exe|SC2\.exe' >/dev/null 2>&1; then
  echo "============================================================" >&2
  echo "WARNING: StarCraft II appears to be running." >&2
  echo "Quit Battle.net/Steam SC2 fully, then re-run. Not killing." >&2
  echo "============================================================" >&2
fi

echo "Starting: python -m examples.play_vs_playbot $*"
exec python -m examples.play_vs_playbot "$@"
