"""
chapter_config.py - one chapter's settings, merged over the core defaults.

Every chapter-specific value the site, the functions, the decks and the
emails need lives in that chapter's `chapter.json`. Nothing about any one
chapter is written into the core any more: Nexus West is just the first
chapter.json, not the code.

    from chapter_config import load
    cfg = load("path/to/chapter.json")
    cfg.get("meeting.start")            # "7:30am"
    cfg.feature("tradesheet")           # True / False
    cfg.asset("brand.lockup")           # Path, resolved against the chapter

How a new setting reaches old chapters: add it to chapter.defaults.json with a
safe default. A chapter.json written before it existed still builds, and gets
the default until the chapter chooses otherwise. That is the whole upgrade
story - never make a new key required.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
DEFAULTS = SKILL / "config" / "chapter.defaults.json"

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
            "Saturday", "Sunday"]

# What a chapter MUST say. Everything else has a default.
REQUIRED = [
    "chapter.name", "chapter.short_name", "site.origin",
    "meeting.weekday", "meeting.start", "meeting.arrive", "meeting.timezone",
    "meeting.mode",
]

MODES = ("alternating", "hybrid", "in_person", "online")


def _merge(base: dict, over: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in over.items():
        if k.startswith("$") or k.startswith("_"):
            continue                       # $schema, _comment and friends
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


class Chapter:
    def __init__(self, data: dict, chapter_dir: Path, source: Path | None):
        self.data = data
        self.dir = chapter_dir
        self.source = source

    # ---- reading -----------------------------------------------------------
    def get(self, path: str, default=None):
        cur = self.data
        for part in path.split("."):
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            else:
                return default
        return cur

    def feature(self, name: str) -> bool:
        return bool(self.get(f"features.{name}", False))

    def asset(self, path: str) -> Path | None:
        """A file named in the config. Chapter-relative first, so a chapter can
        ship its own logo; then core-relative, so the defaults can point at
        the generic BNI artwork the core carries."""
        rel = self.get(path)
        if not rel:
            return None
        for base in (self.dir, SKILL):
            p = (base / rel).resolve()
            if p.exists():
                return p
        raise SystemExit(f"chapter.json: {path} points at {rel!r}, "
                         f"which is in neither {self.dir} nor the core")

    # ---- derived -----------------------------------------------------------
    @property
    def weekday(self) -> str:
        return self.get("meeting.weekday")

    @property
    def weekday_index(self) -> int:      # Monday = 0
        return WEEKDAYS.index(self.weekday)

    def weekday_before(self, days: int) -> str:
        return WEEKDAYS[(self.weekday_index - days) % 7]

    def playlist_cron(self) -> str:
        """When the playlist job runs, in UTC.

        It loads the coming meeting's hour five days ahead, early in the
        chapter's morning. 20:00 UTC is 6-7am the NEXT day on Australia's
        east coast either side of daylight saving, so the UTC weekday is one
        before the local one. Chapters anywhere else set spotify.cron."""
        if self.get("spotify.cron"):
            return self.get("spotify.cron")
        local = (self.weekday_index - 5) % 7          # Monday = 0
        utc = (local - 1) % 7
        return f"0 20 * * {(utc + 1) % 7}"            # cron: Sunday = 0

    def playlist_day(self) -> str:
        return WEEKDAYS[(self.weekday_index - 5) % 7]

    def deadline(self) -> dict:
        d = self.get("education.deck_deadline") or {}
        days = int(d.get("days_before", 4))
        return {
            "days": days,
            "weekday": self.weekday_before(days),
            "time": d.get("time", "12pm"),
            "who": d.get("who", "the Vice President"),
        }

    def warn_unknown(self) -> list[str]:
        """Keys a chapter set that the core does not know. Usually a typo,
        and a typo in a settings file fails silently, so say it."""
        base = json.loads(DEFAULTS.read_text(encoding="utf-8"))
        own = json.loads(self.source.read_text(encoding="utf-8")) if self.source else {}
        found = []

        def walk(over, ref, prefix=""):
            for k, v in over.items():
                if k.startswith(("$", "_")):
                    continue
                if not isinstance(ref, dict) or k not in ref:
                    found.append(prefix + k)
                elif isinstance(v, dict) and isinstance(ref[k], dict) and ref[k]:
                    walk(v, ref[k], prefix + k + ".")
        walk(own, base)
        return found


def load(path: str | Path | None) -> Chapter:
    defaults = json.loads(DEFAULTS.read_text(encoding="utf-8"))
    if path is None:
        raise SystemExit("--chapter is required: point it at the chapter's chapter.json")
    src = Path(path).resolve()
    if not src.exists():
        raise SystemExit(f"no chapter config at {src}")
    own = json.loads(src.read_text(encoding="utf-8"))
    ch = Chapter(_merge(defaults, own), src.parent, src)

    missing = [k for k in REQUIRED if ch.get(k) in (None, "")]
    if missing:
        raise SystemExit(f"{src.name} is missing required settings: {', '.join(missing)}")
    if ch.weekday not in WEEKDAYS:
        raise SystemExit(f"meeting.weekday must be one of {WEEKDAYS}, not {ch.weekday!r}")
    if ch.get("meeting.mode") not in MODES:
        raise SystemExit(f"meeting.mode must be one of {MODES}")
    if ch.get("meeting.mode") != "in_person" and not ch.get("meeting.zoom_url"):
        raise SystemExit("meeting.zoom_url is required unless meeting.mode is in_person")
    if ch.get("meeting.mode") != "online" and not ch.get("meeting.venue.name"):
        raise SystemExit("meeting.venue.name is required unless meeting.mode is online")
    for k in ch.warn_unknown():
        print(f"     note: {src.name} sets '{k}', which the core does not use (typo?)")
    for k in todo(ch.data):
        print(f"     TODO: {k} still needs a real value")
    return ch


def todo(d, prefix="") -> list[str]:
    """Settings still holding a REPLACE-ME placeholder from the starter."""
    found = []
    if isinstance(d, dict):
        for k, v in d.items():
            found += todo(v, f"{prefix}{k}.")
    elif isinstance(d, list):
        for i, v in enumerate(d):
            found += todo(v, f"{prefix}{i}.")
    elif isinstance(d, str) and "REPLACE-ME" in d:
        found.append(prefix.rstrip("."))
    return found


def deck_identity(path: str | Path | None = None) -> dict:
    """What a deck or a notes document needs to know about the chapter: the
    closing tagline, the line under it, and the mascot. From --chapter, else
    the BNI_CHAPTER environment variable, else BNI's own words - so the deck
    scripts still run for someone trying them out with no chapter set up."""
    import html
    import os
    path = path or os.environ.get("BNI_CHAPTER")
    if not path:
        return {"tagline": "Givers Gain.", "words": "", "mascot": None, "name": ""}
    ch = load(path)
    words = html.unescape(ch.get("chapter.tagline_words") or "").replace(" · ", "  ·  ")
    return {
        "tagline": html.unescape(ch.get("chapter.tagline") or ch.get("chapter.name")),
        "words": words,
        "mascot": ch.asset("brand.mascot"),
        "name": ch.get("chapter.name"),
    }
