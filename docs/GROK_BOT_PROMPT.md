# Paste this to your Grok Bot

Use this when onboarding another assistant on a gamer’s Ubuntu PC:

---

I want you to be my StarCraft II sparring partner on this Ubuntu machine.

Repo: `~/github/scplay-grok-bot` (or tell me the path).

Please:
1. Read the README in that repo.
2. Run `./scripts/setup_venv.sh` if `.venv` is missing.
3. Detect SC2 with `./scripts/find_sc2.sh` (Steam Proton + Battle.net is expected).
4. Run `./scripts/install_maps.sh` if maps are missing.
5. Remind me to fully quit SC2/Battle.net, then launch:
   - normal: `./scripts/play_vs_playbot.sh`
   - chaos: `./scripts/play_vs_playbot.sh --chaos --fast`
6. After matches, help tune chat banter, race/map, or bot strength.

You play via `burnysc2` (PlaybotSparBot), not by clicking my mouse. Talk to me in SC2 chat during the game.

---
