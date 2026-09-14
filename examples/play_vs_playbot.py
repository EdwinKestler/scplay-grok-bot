#!/usr/bin/env python3
"""Human vs PlaybotSparBot for Proton/Wine StarCraft II (burnysc2).

Requires env (see scripts/play_vs_playbot.sh):
  SC2PATH, WINE, WINEPREFIX, SC2PF=WineLinux

Modes:
  default     — normal realtime sparring + live chat
  --chaos     — free buildings, instant build/research, tech unlocked, fat wallet
  --fast      — non-realtime (game runs faster than wall-clock; still playable)
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

from sc2 import maps
from sc2.bot_ai import BotAI
from sc2.data import Race, Result
from sc2.ids.ability_id import AbilityId
from sc2.ids.buff_id import BuffId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId
from sc2.main import run_game
from sc2.player import Bot, Human
from sc2.position import Point2
from sc2.unit import Unit


RACE_MAP = {
    "terran": Race.Terran,
    "zerg": Race.Zerg,
    "protoss": Race.Protoss,
    "random": Race.Random,
}

_REPO_ROOT = Path(__file__).resolve().parents[1]
CHAT_LOG = Path(
    os.environ.get(
        "PLAYBOT_CHAT_LOG",
        str(_REPO_ROOT / "replays" / "playbot_live_chat.log"),
    )
)


class PlaybotSparBot(BotAI):
    """Zerg sparring partner. Optional chaos cheats + live chat."""

    def __init__(self, *, chaos: bool = False) -> None:
        super().__init__()
        self.chaos = chaos
        self.attack_started = False
        self._said: set[str] = set()
        self._last_banter_time = 0.0
        self._last_resource_topup = -999.0
        self._chaos_ready = False
        self._banter_index = 0
        self._banter_lines = [
            "Still here. Watching your mineral line…",
            "Don't turtle forever — I get bored.",
            "Ling count climbing. You feeling that?",
            "I'm Playbot, not the built-in AI. Say hi in chat if you want.",
            "Map's getting spicy. Keep scouting.",
            "Gas is flowing. What's your plan, Terran?",
            "I can hear those barracks from here.",
            "Rematch clause: loser buys imaginary pizza.",
        ]
        if chaos:
            self._banter_lines = [
                "CHAOS MODE — free stuff, instant tech. Go nuts.",
                "Wallet's fake. Army is real.",
                "Research already done. What's your excuse?",
                "Faster timeline. Keep up.",
                "I'm printing lings like it's free. Oh wait — it is.",
                "No eco stress. Pure violence.",
            ]

    async def on_start(self) -> None:
        self.client.game_step = 2 if not self.chaos else 1
        CHAT_LOG.parent.mkdir(parents=True, exist_ok=True)
        CHAT_LOG.write_text("")
        if self.chaos:
            await self._enable_chaos()
            await self.say(
                "Playbot CHAOS online — infinite money, instant research/build, "
                "tech unlocked. glhf and don't blink."
            )
        else:
            await self.say(
                "Playbot online — I'm the one typing. glhf. "
                "I'll call shots as we go."
            )

    async def _enable_chaos(self) -> None:
        """Toggle SC2 debug cheats. free/fast_build/tech_tree are usually game-wide."""
        # Order matters a bit; toggles are idempotent if we only call once.
        await self.client.debug_free()  # units/buildings/upgrades cost 0
        await self.client.debug_fast_build()  # build + research time → 0
        await self.client.debug_tech_tree()  # skip tech requirements
        await self.client.debug_cooldown()  # ability cooldowns off (bot side)
        await self.client.debug_all_resources()  # +5k/5k to this player
        # Unlock successive upgrade tiers for the bot
        for _ in range(4):
            await self.client.debug_upgrade()
        self._chaos_ready = True
        self._last_resource_topup = self.time
        await self.say("Cheats on: free + instant build/research + tech tree.", once_key="chaos_on")

    async def _topup_chaos(self) -> None:
        if not self.chaos or not self._chaos_ready:
            return
        # Refresh wallet every ~20s (debug_all_resources is +5k, not a true toggle)
        if self.time - self._last_resource_topup < 20:
            return
        await self.client.debug_all_resources()
        # Keep upgrade tiers topped in case new buildings unlocked more
        await self.client.debug_upgrade()
        self._last_resource_topup = self.time

    async def on_end(self, result: Result) -> None:
        if result == Result.Victory:
            msg = "GG — Playbot takes it. Rematch when you're ready."
        elif result == Result.Defeat:
            msg = "GG — you got me. Respect. Run it back?"
        else:
            msg = f"GG — match over ({result})."
        await self.say(msg, sc2=False)

    async def say(self, msg: str, *, once_key: str | None = None, sc2: bool = True) -> None:
        if once_key is not None:
            if once_key in self._said:
                return
            self._said.add(once_key)
        line = f"[Playbot] {msg}"
        print(line, flush=True)
        try:
            with CHAT_LOG.open("a", encoding="utf-8") as f:
                f.write(f"{time.strftime('%H:%M:%S')} {line}\n")
        except OSError:
            pass
        if not sc2:
            return
        try:
            await self.chat_send(msg)
        except Exception as exc:  # noqa: BLE001
            err = str(exc)
            if "already ended" in err.lower() or "Status.ended" in err:
                return
            print(f"[Playbot] chat_send failed: {exc}", flush=True)

    async def on_step(self, iteration: int) -> None:
        if not self.townhalls:
            await self.say("All hatcheries gone — all-in time!", once_key="all_in")
            for unit in self.units.exclude_type({UnitTypeId.EGG, UnitTypeId.LARVA}):
                unit.attack(self.enemy_start_locations[0])
            return

        hatch = self.townhalls.first
        await self._topup_chaos()
        await self._maybe_banter()
        await self._call_milestones()
        await self._distribute_workers()
        await self._expand_supply()
        await self._build_economy(hatch)
        await self._build_army_buildings(hatch)
        await self._train_units()
        await self._inject(hatch)
        await self._maybe_research()
        await self._attack()

    async def _maybe_banter(self) -> None:
        interval = 30 if self.chaos else 45
        if self.time - self._last_banter_time < interval:
            return
        if self.time < 20:
            return
        self._last_banter_time = self.time
        line = self._banter_lines[self._banter_index % len(self._banter_lines)]
        self._banter_index += 1
        await self.say(line)

    async def _call_milestones(self) -> None:
        if self.structures(UnitTypeId.SPAWNINGPOOL).ready:
            await self.say("Spawning pool's up. Lings incoming.", once_key="pool")
        if self.units(UnitTypeId.QUEEN).amount >= 1:
            await self.say("Queen online — injects rolling.", once_key="queen")
        if self.already_pending_upgrade(UpgradeId.ZERGLINGMOVEMENTSPEED) > 0:
            await self.say("Ling speed researching. Clock's ticking.", once_key="speed")
        if self.townhalls.amount >= 2:
            await self.say("Took my natural. Don't let me snowball.", once_key="natural")
        if self.supply_army >= 20:
            await self.say(
                f"Army supply ~{int(self.supply_army)}. Pressure's coming.",
                once_key="army20",
            )
        if self.enemy_units.amount >= 8:
            await self.say("I see your army. Cute.", once_key="see_army")
        if self.enemy_structures(UnitTypeId.BARRACKS).amount >= 1:
            await self.say("Barracks spotted. Bio or cheese?", once_key="rax")
        if self.enemy_structures(UnitTypeId.FACTORY).amount >= 1:
            await self.say("Factory — going mech?", once_key="factory")

    async def _distribute_workers(self) -> None:
        await self.distribute_workers()

    async def _expand_supply(self) -> None:
        pending_cap = 8 if self.chaos else 2
        if self.supply_left < (12 if self.chaos else 4) and self.already_pending(
            UnitTypeId.OVERLORD
        ) < pending_cap:
            if self.can_afford(UnitTypeId.OVERLORD):
                self.train(UnitTypeId.OVERLORD)

    async def _build_economy(self, hatch: Unit) -> None:
        worker_cap = 30 if self.chaos else 22
        if self.supply_workers < worker_cap and self.can_afford(UnitTypeId.DRONE):
            self.train(UnitTypeId.DRONE)

        if (
            self.gas_buildings.amount + self.already_pending(UnitTypeId.EXTRACTOR) == 0
            and self.supply_workers >= (10 if self.chaos else 14)
            and self.can_afford(UnitTypeId.EXTRACTOR)
            and self.workers
        ):
            drone = self.workers.closest_to(hatch)
            geyser = self.vespene_geyser.closest_to(drone)
            drone.build_gas(geyser)

        hatch_target = 3 if self.chaos else 2
        if (
            self.townhalls.amount + self.already_pending(UnitTypeId.HATCHERY) < hatch_target
            and self.minerals > (100 if self.chaos else 350)
            and self.workers
        ):
            loc = await self.get_next_expansion()
            if loc and await self.can_place_single(UnitTypeId.HATCHERY, loc):
                self.workers.closest_to(loc).build(UnitTypeId.HATCHERY, loc)

    async def _build_army_buildings(self, hatch: Unit) -> None:
        if (
            self.structures(UnitTypeId.SPAWNINGPOOL).amount
            + self.already_pending(UnitTypeId.SPAWNINGPOOL)
            == 0
            and self.can_afford(UnitTypeId.SPAWNINGPOOL)
            and self.workers
        ):
            for d in range(4, 15):
                pos: Point2 = hatch.position.towards(self.game_info.map_center, d)
                if await self.can_place_single(UnitTypeId.SPAWNINGPOOL, pos):
                    self.workers.closest_to(pos).build(UnitTypeId.SPAWNINGPOOL, pos)
                    break

        # Chaos: throw down a few more pools for ling spam
        if self.chaos and self.structures(UnitTypeId.SPAWNINGPOOL).amount < 3:
            if self.can_afford(UnitTypeId.SPAWNINGPOOL) and self.workers:
                for d in range(4, 18):
                    pos = hatch.position.towards(self.game_info.map_center, d)
                    if await self.can_place_single(UnitTypeId.SPAWNINGPOOL, pos):
                        self.workers.closest_to(pos).build(UnitTypeId.SPAWNINGPOOL, pos)
                        break

        if (
            self.structures(UnitTypeId.SPAWNINGPOOL).ready
            and self.units(UnitTypeId.QUEEN).amount + self.already_pending(UnitTypeId.QUEEN)
            < self.townhalls.amount
            and self.can_afford(UnitTypeId.QUEEN)
        ):
            self.train(UnitTypeId.QUEEN)

    async def _train_units(self) -> None:
        if not self.structures(UnitTypeId.SPAWNINGPOOL).ready:
            return
        if self.larva and self.can_afford(UnitTypeId.ZERGLING) and self.supply_left > 0:
            if self.chaos or self.supply_workers >= 16 or self.attack_started:
                self.train(UnitTypeId.ZERGLING, min(self.larva.amount, 16 if self.chaos else 8))

    async def _inject(self, hatch: Unit) -> None:
        for queen in self.units(UnitTypeId.QUEEN):
            if queen.energy >= 25 and not hatch.has_buff(BuffId.QUEENSPAWNLARVATIMER):
                queen(AbilityId.EFFECT_INJECTLARVA, hatch)

    async def _maybe_research(self) -> None:
        if (
            self.already_pending_upgrade(UpgradeId.ZERGLINGMOVEMENTSPEED) == 0
            and self.can_afford(UpgradeId.ZERGLINGMOVEMENTSPEED)
            and self.structures(UnitTypeId.SPAWNINGPOOL).ready
        ):
            self.research(UpgradeId.ZERGLINGMOVEMENTSPEED)

    async def _attack(self) -> None:
        lings = self.units(UnitTypeId.ZERGLING)
        trigger = 6 if self.chaos else 12
        late = 180 if self.chaos else 360
        if lings.amount >= trigger or (self.time > late and lings.amount >= 4):
            if not self.attack_started:
                self.attack_started = True
                await self.say(
                    f"Attack wave — {lings.amount} lings. Defend or die screaming."
                )
        if not self.attack_started:
            rally = self.game_info.map_center.towards(self.start_location, 20)
            for ling in lings.idle:
                ling.attack(rally)
            return

        target = (
            self.enemy_structures.not_flying.closest_to(self.enemy_start_locations[0])
            if self.enemy_structures.not_flying
            else None
        )
        dest = target.position if target else self.enemy_start_locations[0]
        for ling in lings:
            ling.attack(dest)
        if lings.amount >= (12 if self.chaos else 20):
            for queen in self.units(UnitTypeId.QUEEN).idle:
                queen.attack(dest)


def _parse_race(name: str) -> Race:
    key = name.strip().lower()
    if key not in RACE_MAP:
        raise argparse.ArgumentTypeError(
            f"Unknown race {name!r}; choose from {', '.join(RACE_MAP)}"
        )
    return RACE_MAP[key]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Human vs PlaybotSparBot")
    parser.add_argument("--human-race", default=os.environ.get("HUMAN_RACE", "Terran"), type=_parse_race)
    parser.add_argument("--bot-race", default=os.environ.get("BOT_RACE", "Zerg"), type=_parse_race)
    parser.add_argument("--map", default=os.environ.get("SC2_MAP", "AbyssalReefLE"))
    parser.add_argument(
        "--chaos",
        action="store_true",
        help="Free build, instant research/build, unlocked tech, resource top-ups",
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Faster than realtime (game steps as fast as both clients allow)",
    )
    args = parser.parse_args(argv)

    missing = [v for v in ("SC2PATH", "WINE", "WINEPREFIX", "SC2PF") if not os.environ.get(v)]
    if missing:
        print(
            "WARNING: missing env vars (Proton/Wine launch may fail): " + ", ".join(missing),
            file=sys.stderr,
        )

    if args.bot_race != Race.Zerg:
        print(
            "NOTE: PlaybotSparBot builds Zerg units; non-Zerg --bot-race will misbehave.",
            file=sys.stderr,
        )

    realtime = not args.fast
    print("Playbot will talk in SC2 chat + this terminal during the match.", flush=True)
    print(f"Live chat log: {CHAT_LOG}", flush=True)
    print(
        f"Mode: chaos={args.chaos} fast={args.fast} realtime={realtime}",
        flush=True,
    )
    if args.chaos:
        print(
            "Note: free/instant/tech cheats are usually game-wide. "
            "If your buildings still cost money, say so and we'll dig further.",
            flush=True,
        )

    run_game(
        maps.get(args.map),
        [
            Human(args.human_race),
            Bot(args.bot_race, PlaybotSparBot(chaos=args.chaos)),
        ],
        realtime=realtime,
    )


if __name__ == "__main__":
    main()
