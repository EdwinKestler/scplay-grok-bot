# Log schema for training & chat analysis

See also [`../logs/README.md`](../logs/README.md).

## Goals

1. **Chat corpus** — reconstruct in-match dialogue between human and Playbot (and any future multi-bot setups).
2. **Play traces** — coarse game state over time for behavior cloning, reward shaping, or debugging.
3. **Match index** — filter by map, result, chaos mode, date.

## Recommended ML uses

| File | Use |
|------|-----|
| `chat.jsonl` | Dialogue fine-tuning, banter quality eval, speaker ID |
| `play.jsonl` snapshots | Imitation / world-model features |
| `play.jsonl` events | Sparse labels (attack timing, tech milestones) |
| `match.json` + `index.jsonl` | Splits, filtering, curriculum |

## Privacy

Logs may include whatever humans type in SC2 chat. Do not publish raw logs without consent. Redact before sharing datasets.
