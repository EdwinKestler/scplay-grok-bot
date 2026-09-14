"""Structured play + chat logs for training and review.

Each match writes:
  logs/matches/<match_id>/match.json   — metadata + result
  logs/matches/<match_id>/chat.jsonl   — every chat line (bot + human)
  logs/matches/<match_id>/play.jsonl   — events + periodic snapshots

Also appends one line to logs/index.jsonl (match catalog).
"""

from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _json_dump(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


@dataclass
class MatchMeta:
    match_id: str
    started_at_utc: str
    map_name: str
    human_race: str
    bot_race: str
    bot_name: str = "PlaybotSparBot"
    chaos: bool = False
    fast: bool = False
    realtime: bool = True
    sc2path: str | None = None
    schema_version: str = "1.0"
    ended_at_utc: str | None = None
    result_bot: str | None = None
    result_human: str | None = None
    duration_game_seconds: float | None = None
    duration_wall_seconds: float | None = None
    chat_lines: int = 0
    play_events: int = 0
    notes: dict[str, Any] = field(default_factory=dict)


class MatchLogger:
    """Append-only JSONL logger for one SC2 match."""

    def __init__(
        self,
        *,
        logs_root: Path | None = None,
        map_name: str,
        human_race: str,
        bot_race: str,
        chaos: bool = False,
        fast: bool = False,
        realtime: bool = True,
        bot_name: str = "PlaybotSparBot",
    ) -> None:
        root = logs_root or Path(
            os.environ.get(
                "SCPLAY_LOGS_ROOT",
                str(Path(__file__).resolve().parents[1] / "logs"),
            )
        )
        self.logs_root = Path(root)
        self.matches_root = self.logs_root / "matches"
        self.matches_root.mkdir(parents=True, exist_ok=True)

        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        short = uuid.uuid4().hex[:8]
        safe_map = "".join(c if c.isalnum() or c in "-_" else "_" for c in map_name)[:40]
        self.match_id = f"{stamp}_{safe_map}_{short}"
        self.match_dir = self.matches_root / self.match_id
        self.match_dir.mkdir(parents=True, exist_ok=True)

        self.chat_path = self.match_dir / "chat.jsonl"
        self.play_path = self.match_dir / "play.jsonl"
        self.meta_path = self.match_dir / "match.json"
        self.index_path = self.logs_root / "index.jsonl"

        self._wall_start = time.time()
        self._chat_count = 0
        self._play_count = 0
        self._seen_chat: set[tuple[int, str, int]] = set()

        self.meta = MatchMeta(
            match_id=self.match_id,
            started_at_utc=_utc_now(),
            map_name=map_name,
            human_race=human_race,
            bot_race=bot_race,
            bot_name=bot_name,
            chaos=chaos,
            fast=fast,
            realtime=realtime,
            sc2path=os.environ.get("SC2PATH"),
        )
        self._write_meta()
        self.event(
            "match_start",
            {
                "map": map_name,
                "human_race": human_race,
                "bot_race": bot_race,
                "chaos": chaos,
                "fast": fast,
                "realtime": realtime,
            },
            game_time=0.0,
            iteration=0,
        )
        print(f"[MatchLogger] logging to {self.match_dir}", flush=True)

    def _write_meta(self) -> None:
        self.meta.chat_lines = self._chat_count
        self.meta.play_events = self._play_count
        self.meta_path.write_text(
            json.dumps(asdict(self.meta), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    def _append(self, path: Path, record: dict[str, Any]) -> None:
        record.setdefault("match_id", self.match_id)
        record.setdefault("logged_at_utc", _utc_now())
        with path.open("a", encoding="utf-8") as f:
            f.write(_json_dump(record) + "\n")

    def chat(
        self,
        *,
        speaker: str,
        player_id: int | None,
        message: str,
        game_time: float,
        iteration: int,
        source: str = "sc2",
    ) -> None:
        """Log one chat line. speaker: playbot | human | player_<id> | system."""
        key = (player_id or -1, message, int(game_time * 10))
        if key in self._seen_chat:
            return
        self._seen_chat.add(key)
        rec = {
            "type": "chat",
            "speaker": speaker,
            "player_id": player_id,
            "message": message,
            "game_time": round(game_time, 3),
            "iteration": iteration,
            "source": source,
        }
        self._append(self.chat_path, rec)
        self._chat_count += 1
        # Human-readable twin for quick grepping
        twin = self.match_dir / "chat.txt"
        with twin.open("a", encoding="utf-8") as f:
            who = speaker
            f.write(f"t={game_time:8.1f}s  [{who}] {message}\n")

    def event(
        self,
        event_type: str,
        data: dict[str, Any] | None = None,
        *,
        game_time: float = 0.0,
        iteration: int = 0,
    ) -> None:
        rec = {
            "type": "event",
            "event": event_type,
            "game_time": round(game_time, 3),
            "iteration": iteration,
            "data": data or {},
        }
        self._append(self.play_path, rec)
        self._play_count += 1

    def snapshot(
        self,
        *,
        game_time: float,
        iteration: int,
        bot: dict[str, Any],
        enemy: dict[str, Any] | None = None,
    ) -> None:
        rec = {
            "type": "snapshot",
            "game_time": round(game_time, 3),
            "iteration": iteration,
            "bot": bot,
            "enemy": enemy or {},
        }
        self._append(self.play_path, rec)
        self._play_count += 1

    def close(
        self,
        *,
        result_bot: str,
        result_human: str | None = None,
        game_time: float | None = None,
    ) -> None:
        self.meta.ended_at_utc = _utc_now()
        self.meta.result_bot = result_bot
        self.meta.result_human = result_human
        self.meta.duration_game_seconds = game_time
        self.meta.duration_wall_seconds = round(time.time() - self._wall_start, 3)
        self.event(
            "match_end",
            {
                "result_bot": result_bot,
                "result_human": result_human,
                "duration_game_seconds": game_time,
                "duration_wall_seconds": self.meta.duration_wall_seconds,
            },
            game_time=game_time or 0.0,
        )
        self._write_meta()
        with self.index_path.open("a", encoding="utf-8") as f:
            f.write(
                _json_dump(
                    {
                        "match_id": self.match_id,
                        "path": str(self.match_dir),
                        "map": self.meta.map_name,
                        "started_at_utc": self.meta.started_at_utc,
                        "ended_at_utc": self.meta.ended_at_utc,
                        "result_bot": result_bot,
                        "result_human": result_human,
                        "chaos": self.meta.chaos,
                        "fast": self.meta.fast,
                        "chat_lines": self._chat_count,
                        "play_events": self._play_count,
                    }
                )
                + "\n"
            )
        print(
            f"[MatchLogger] closed {self.match_id}  "
            f"chat={self._chat_count} play={self._play_count}  "
            f"result_bot={result_bot}",
            flush=True,
        )
