# Match logs (play + chat)

Every game writes a folder under `matches/` plus one catalog line in `index.jsonl`.

## Layout

```
logs/
  index.jsonl                          # one JSON object per finished match
  matches/
    20260914T155200Z_AbyssalReefLE_a1b2c3d4/
      match.json                       # metadata + result
      chat.jsonl                       # structured chat (training-friendly)
      chat.txt                         # human-readable chat twin
      play.jsonl                       # events + periodic snapshots
```

## Schemas (schema_version 1.0)

### `chat.jsonl` line

```json
{
  "type": "chat",
  "match_id": "...",
  "logged_at_utc": "2026-09-14T15:52:01Z",
  "speaker": "playbot|human|player_1|player_2|system",
  "player_id": 1,
  "message": "Playbot online — …",
  "game_time": 12.5,
  "iteration": 42,
  "source": "sc2|bot_say"
}
```

Human lines are captured from the SC2 observation chat channel when the API exposes them. Bot lines are logged when Playbot calls `say()`.

### `play.jsonl` line

**Event**

```json
{
  "type": "event",
  "event": "attack_started|milestone_pool|match_start|match_end|…",
  "game_time": 120.0,
  "iteration": 800,
  "data": {}
}
```

**Snapshot** (every ~15s game time)

```json
{
  "type": "snapshot",
  "game_time": 90.0,
  "iteration": 600,
  "bot": {
    "minerals": 150,
    "vespene": 50,
    "supply_used": 30,
    "supply_cap": 39,
    "workers": 18,
    "army_supply": 12,
    "lings": 12,
    "townhalls": 2
  },
  "enemy": {
    "units_seen": 8,
    "structures_seen": 5
  }
}
```

### Training export

```bash
./scripts/export_logs_for_training.sh
```

Writes concatenated JSONL under `logs/export/` for model training / analysis.
