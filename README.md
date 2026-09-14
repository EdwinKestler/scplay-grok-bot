# scplay-grok-bot

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Play **StarCraft II** on **Ubuntu Linux** against a Grok Bot (or OpenAI / Claude-coached Playbot) — live in-game chat, structured match logs for training, chaos mode, and gameplay captures.

```bash
git clone https://github.com/EdwinKestler/scplay-grok-bot.git
cd scplay-grok-bot
```

Proven on Ubuntu 24.04 with SC2 running via **Steam Proton + Battle.net** (the “Steam VM” / Proton bottle). Lutris/Wine installs work too if you set paths.

This package is the portable extract of a working Playbot setup. Point your Grok Bot at this repo on the gamer’s machine and say: *“help me install and play.”*

---

## What you get

| Piece | Role |
|-------|------|
| `examples/play_vs_playbot.py` | Human vs `PlaybotSparBot` (Zerg), live SC2 chat + terminal log |
| `scripts/setup_venv.sh` | Python venv + `burnysc2` |
| `scripts/find_sc2.sh` | Auto-detect Proton/Wine `SC2PATH` / `WINE` / `WINEPREFIX` |
| `scripts/install_maps.sh` | Download Blizzard ladder/melee maps into `$SC2PATH/Maps` |
| `scripts/play_vs_playbot.sh` | One-command match launcher |
| `docs/ARCHITECTURE.md` | How Grok Bot + API + Proton fit together |

**Not included:** the StarCraft II game itself (install via Battle.net). Maps are downloaded from Blizzard’s public AI/ML map packs (you accept their license by using the zip password).

---

## Requirements

- Ubuntu (tested 24.04); other Linux may work
- StarCraft II (Windows build via Steam Proton + Battle.net is the happy path)
- Python 3.11+ (`python3`, `python3-venv`, `curl`, `unzip`)
- Enough disk for map packs (~75 MB zips)

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip curl unzip
```

---

## Quick start (gamer machine)

### 1. Get SC2 running once via Proton

1. Install Steam, enable Proton, add a non-Steam shortcut for Battle.net setup if needed.
2. Install **StarCraft II** through Battle.net inside that Proton prefix.
3. Launch SC2 once so the install + prefix exist, then **fully quit** SC2 and Battle.net before using the API launcher (the bot starts its own SC2 process).

### 2. Clone / copy this repo

```bash
cd ~/github   # or anywhere you like
# if you already have the folder:
cd scplay-grok-bot
```

### 3. Python env

```bash
./scripts/setup_venv.sh
```

### 4. Install ladder maps

```bash
./scripts/install_maps.sh
```

This pulls Melee + Ladder 2017 S1 / 2018 S2 / 2019 S3 packs (password `iagreetotheeula`) into your SC2 `Maps` folder and adds root symlinks so names like `AbyssalReefLE` resolve.

### 5. Play

Normal sparring (realtime, live chat):

```bash
./scripts/play_vs_playbot.sh
```

Chaos + faster:

```bash
./scripts/play_vs_playbot.sh --chaos --fast
```

Options:

```bash
./scripts/play_vs_playbot.sh --human-race Terran --bot-race Zerg --map AbyssalReefLE
./scripts/play_vs_playbot.sh --chaos          # free + instant research/build + tech unlock
./scripts/play_vs_playbot.sh --fast           # faster than wall-clock
```

Watch **in-game SC2 chat** and the launch terminal for `[Playbot]` lines. A copy is also written to `replays/playbot_live_chat.log`.

---

## Environment variables (optional)

Auto-detection usually works for Steam Proton. Override if needed:

| Variable | Meaning |
|----------|---------|
| `SC2PATH` | `.../StarCraft II` directory |
| `WINE` | Wine/Proton `wine` binary |
| `WINEPREFIX` | Proton `pfx` or Wine prefix |
| `SC2PF` | Set to `WineLinux` on Linux Wine/Proton |
| `PLAYBOT_CHAT_LOG` | Path for mirrored chat log |

Detect only:

```bash
./scripts/find_sc2.sh
```

---

## How this pairs with a Grok Bot

1. Put this repo on the **host machine** that runs SC2 (same PC as the game).
2. Your Grok Bot / desktop assistant uses **local shell on that machine** to run the scripts (or you run them yourself).
3. The bot that *plays* is `PlaybotSparBot` inside `burnysc2` — not remote mouse clicks.
4. “Chat during gameplay” = SC2 `chat_send` from the bot (plus terminal/log). The assistant chat app does not get mid-match turns unless you build an extra bridge.

Suggested first message to your Grok Bot after copying this repo:

> I have `~/github/scplay-grok-bot`. Help me run `setup_venv`, `install_maps`, then launch Human vs Playbot. SC2 is on Steam Proton.

---

## Chaos mode notes

`--chaos` enables SC2 debug toggles via the API:

- `debug_free` — buildings/units/upgrades cost 0  
- `debug_fast_build` — build & research time → 0  
- `debug_tech_tree` — ignore tech requirements  
- resource top-ups + upgrade unlock spam for the bot  

`free` / `fast_build` / `tech_tree` are usually **game-wide**. If the human side still pays full cost, open an issue / ask your bot to dig further.

`--fast` sets `realtime=False` so the match advances as fast as both clients step (snappier; still human-controlled).

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `maps.get("AbyssalReefLE")` fails | Run `./scripts/install_maps.sh`; confirm `$SC2PATH/Maps/AbyssalReefLE.SC2Map` |
| SC2 won’t launch / Wine errors | Quit existing SC2; check `./scripts/find_sc2.sh`; try Proton Experimental wine path |
| Match connects then dies | Don’t leave Battle.net SC2 open; API wants its own instance |
| `chat_send failed: Game has already ended` | Harmless on match end (GG goes to terminal/log only) |
| Bot race ≠ Zerg | `PlaybotSparBot` is Zerg-oriented; keep `--bot-race Zerg` |

---




## LLM connectors (OpenAI + Claude)

Evaluate or coach Playbot with other assistants. Keys from env only:

```bash
export OPENAI_API_KEY=...
export CLAUDE_API_KEY=...   # ANTHROPIC_API_KEY also works
./scripts/probe_llm.sh
./scripts/play_vs_playbot.sh --llm openai
./scripts/play_vs_playbot.sh --llm claude
./scripts/eval_match_with_llm.sh claude logs/matches/<id>/chat.txt
```

Details: [`docs/LLM_CONNECTORS.md`](docs/LLM_CONNECTORS.md).

## Structured play + chat logs (training DB)

Every match writes under [`logs/matches/<match_id>/`](logs/):

| File | Contents |
|------|----------|
| `match.json` | Map, races, chaos/fast, results, durations |
| `chat.jsonl` | Bot + human SC2 chat (one JSON object per line) |
| `chat.txt` | Same chat, greppable text |
| `play.jsonl` | Events + ~15s economy/army snapshots |
| `logs/index.jsonl` | Catalog of all finished matches |

Export for training:

```bash
./scripts/export_logs_for_training.sh
```

Schema details: [`logs/README.md`](logs/README.md), [`docs/LOG_SCHEMA.md`](docs/LOG_SCHEMA.md).

## Captures (screenshots & video)

Put gameplay screenshots and short clips in [`captures/`](captures/):

- `captures/screenshots/` — stills (png/jpg)
- `captures/gameplay/` — video clips (kept local by default; see `captures/README.md`)

## License

MIT for the scripts and bot code in this repo. StarCraft II © Blizzard. Map packs are subject to [Blizzard’s AI and Machine Learning License](http://blzdistsc2-a.akamaihd.net/AI_AND_MACHINE_LEARNING_LICENSE.html).

---

## Credits

- [BurnySc2/python-sc2](https://github.com/BurnySc2/python-sc2) (`burnysc2`)
- [Blizzard/s2client-proto](https://github.com/Blizzard/s2client-proto) map packs
- Originated from a working Ubuntu Proton + Grok Bot “Playbot” sparring setup
