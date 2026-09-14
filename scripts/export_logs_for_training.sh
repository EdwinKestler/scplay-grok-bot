#!/usr/bin/env bash
# Concatenate all match chat/play JSONL into logs/export/ for training.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="$ROOT/logs/export"
mkdir -p "$OUT"
stamp=$(date -u +%Y%m%dT%H%M%SZ)
CHAT_OUT="$OUT/chat_all_${stamp}.jsonl"
PLAY_OUT="$OUT/play_all_${stamp}.jsonl"
: > "$CHAT_OUT"
: > "$PLAY_OUT"
count=0
while IFS= read -r -d '' f; do
  cat "$f" >> "$CHAT_OUT"
  count=$((count + 1))
done < <(find "$ROOT/logs/matches" -name chat.jsonl -print0 2>/dev/null || true)
play_n=0
while IFS= read -r -d '' f; do
  cat "$f" >> "$PLAY_OUT"
  play_n=$((play_n + 1))
done < <(find "$ROOT/logs/matches" -name play.jsonl -print0 2>/dev/null || true)
# Stable latest pointers
ln -sfn "$(basename "$CHAT_OUT")" "$OUT/chat_all_latest.jsonl"
ln -sfn "$(basename "$PLAY_OUT")" "$OUT/play_all_latest.jsonl"
echo "Exported $count chat files -> $CHAT_OUT"
echo "Exported $play_n play files -> $PLAY_OUT"
echo "Pointers: $OUT/chat_all_latest.jsonl  $OUT/play_all_latest.jsonl"
