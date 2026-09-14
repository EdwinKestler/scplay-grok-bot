# Architecture

```
┌─────────────────────────┐     ┌──────────────────────────────┐
│  Grok Bot / assistant   │     │  Ubuntu host (gamer PC)      │
│  (chat, install help)   │────▶│  scplay-grok-bot scripts     │
└─────────────────────────┘     │         │                    │
                                │         ▼                    │
                                │  burnysc2 PlaybotSparBot     │
                                │         │  SC2 API (WS)      │
                                │         ▼                    │
                                │  StarCraft II (Proton/Wine)  │
                                │  Human Terran  vs  Bot Zerg  │
                                └──────────────────────────────┘
```

## Why not remote-click the SC2 UI?

RTS APM and fog-of-war make GUI automation brittle. The official SC2 API lets a bot join as player 2 while you play as player 1 in the same process the library launches.

## Proton vs Lutris

- **Proton + Battle.net**: common on Ubuntu; set `SC2PF=WineLinux` and point `WINE` at Proton’s wine, `WINEPREFIX` at the compatdata `pfx`.
- **Lutris**: same WineLinux flags; `find_sc2.sh` falls back to `~/Games/battlenet/...` if present.
- **Official Linux headless SC2**: great for bot-vs-bot in Docker; **not** for Human-vs-bot with a visible client.

## Live chat

`PlaybotSparBot.say()` → `chat_send` (in-game) + stdout + `replays/playbot_live_chat.log`.

## Chaos cheats

Issued once on `on_start` via `Client.debug_*` (see BurnySc2 docs). Resource gifts are periodic; free/fast_build/tech_tree are toggles.
