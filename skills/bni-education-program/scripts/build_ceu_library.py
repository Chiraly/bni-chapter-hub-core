"""
build_ceu_library.py — pull the BNI podcasts into one local CEU library.

A CEU hour is only worth anything if the episode numbers, titles and durations
are REAL. Never hand-write them. This reads each show's own RSS feed, which
carries a duration for every episode, and writes references/ceu-library.json.

    python build_ceu_library.py --refresh                  # pull every show
    python build_ceu_library.py --search visitor invit*    # find episodes
    python build_ceu_library.py --hour visitor invit*      # draft a ~60 min set
    python build_ceu_library.py --search attendance --show powerofone

**Matching.** A term matches as a WHOLE WORD (with an optional plural 's')
unless it ends in `*`, which makes it a prefix. Plain substring matching is
quietly poisonous - "lead" would match every episode about leadership - but
strict whole-word matching is too tight for stems, because "invite" never
matches "Inviting". So the caller chooses: `lead` exact, `invit*` for the family.

**Why more than one show.** The Official BNI Podcast alone has almost nothing on
attendance and only nine episodes on visitors, which is not a term's worth. The
other shows fill those gaps and give a wider spread of episode lengths, which
makes hitting a real hour much easier.

Adding a show: find its feed with
`https://itunes.apple.com/lookup?id=<apple id>` and add an entry to SHOWS.
"""
import argparse
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

NS = {"itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd"}
OUT = Path(__file__).resolve().parent.parent / "references" / "ceu-library.json"
# bnipodcast.com 403s a Mozilla-style agent; the other feeds 403 a bare one.
# So the agent is per show, with the plain identifier as the default.
UA = "bni-education-program"
UA_BROWSER = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36")

# Each show numbers its episodes differently, so each carries its own title
# pattern: group 1 is the number, group 2 (optional) the title. `slug` prefixes
# the id, because episode numbers collide across shows.
SHOWS = [
    {"slug": "official", "label": "BNI Podcast",
     "name": "The Official BNI Podcast",
     "feed": "https://www.bnipodcast.com/feed/podcast/",
     "pattern": r"Episode\s+(\d+)\s*[:\-]\s*(.+)"},
    {"slug": "powerofone", "label": "Power of One",
     "name": "BNI & The Power of One",
     "feed": "https://rss.libsyn.com/shows/53882/destinations/196481.xml",
     "pattern": r"BNI\s+(\d+)\s*[:\-]\s*(.+)"},
    {"slug": "bnieffect", "label": "BNI Effect",
     "name": "The BNI Effect",
     "feed": "https://feed.podbean.com/thebnieffect/feed.xml",
     "pattern": r"Ep\s+(\d+)\s*(?:with\s+)?[–—:\-]?\s*(.+)"},
    {"slug": "secrets20", "label": "20 Secrets",
     "name": "20 Secrets to Maximising your BNI Membership",
     "feed": "https://rss.buzzsprout.com/2520585.rss",
     "pattern": r"Secret\s+(\d+)"},          # no separate title - keep the raw one
]

TARGET_MIN, TARGET_MAX = 58 * 60, 72 * 60   # a CEU is an hour; err over, never under


def secs(dur: str) -> int:
    """Handles both '13:24' and a raw seconds count like '1901'."""
    if not dur:
        return 0
    parts = [int(p) for p in dur.strip().split(":")]
    while len(parts) < 3:
        parts.insert(0, 0)
    return parts[0] * 3600 + parts[1] * 60 + parts[2]


def mmss(s: int) -> str:
    return f"{s // 60}:{s % 60:02d}"


def fetch(url: str):
    """Try the plain agent, then a browser one. Feeds disagree about which they
    accept, and a 403 here silently drops a whole show from the library."""
    last = None
    for agent in (UA, UA_BROWSER):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": agent})
            with urllib.request.urlopen(req, timeout=90) as r:
                return ET.fromstring(r.read())
        except Exception as e:
            last = e
    raise last


def parse(root, show) -> list[dict]:
    eps = []
    for i, item in enumerate(root.findall(".//item")):
        raw = (item.findtext("title") or "").strip()
        m = re.search(show["pattern"], raw, re.I)
        d = item.find("itunes:duration", NS)
        summary = item.find("itunes:summary", NS)
        if summary is None:
            summary = item.find("description")
        text = re.sub(r"<[^>]+>", " ", (summary.text or "")) if summary is not None else ""
        n = int(m.group(1)) if m else None
        title = raw
        if m and m.lastindex and m.lastindex >= 2 and m.group(2):
            title = m.group(2).strip()
        seconds = secs(d.text if d is not None else "")
        if not seconds:
            continue
        eps.append({
            "id": f"{show['slug']}-{n if n is not None else i}",
            "show": show["label"],
            "number": n,
            "title": title,
            "url": (item.findtext("link") or "").strip(),
            "seconds": seconds,
            "duration": mmss(seconds),
            "date": (item.findtext("pubDate") or "")[:16].strip(),
            "summary": re.sub(r"\s+", " ", text).strip()[:400],
        })
    return eps


def load() -> list[dict]:
    if OUT.exists():
        return json.loads(OUT.read_text(encoding="utf-8"))["episodes"]
    return []


def refresh() -> list[dict]:
    eps, meta = [], []
    for show in SHOWS:
        try:
            got = parse(fetch(show["feed"]), show)
        except Exception as e:                      # one bad feed must not kill the rest
            print(f"  {show['label']:<14} FAILED: {e}")
            continue
        eps.extend(got)
        meta.append({"name": show["name"], "label": show["label"],
                     "slug": show["slug"], "feed": show["feed"], "count": len(got)})
        mins = sum(e["seconds"] for e in got) // 60
        print(f"  {show['label']:<14} {len(got):>4} episodes, {mins//60}h{mins % 60:02d} total")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"shows": meta, "count": len(eps), "episodes": eps},
                              indent=1), encoding="utf-8")
    print(f"library: {len(eps)} episodes across {len(meta)} show(s) -> {OUT}")
    return eps


def _patterns(terms):
    pats = []
    for w in terms:
        if w.endswith("*"):
            pats.append(re.compile(r"\b" + re.escape(w[:-1]), re.I))
        else:
            pats.append(re.compile(r"\b" + re.escape(w) + r"s?\b", re.I))
    return pats


def search(eps, terms, limit=25, show=None):
    """Title matches count triple; summary matches count single."""
    pats = _patterns(terms)
    scored = []
    for e in eps:
        if show and not e["id"].startswith(show + "-"):
            continue
        score = (sum(3 for p in pats if p.search(e["title"]))
                 + sum(1 for p in pats if p.search(e["summary"])))
        if score:
            scored.append((score, e))
    scored.sort(key=lambda x: (-x[0], -(x[1]["number"] or 0)))
    return [e for _, e in scored[:limit]]


def build_hour(eps, terms, show=None):
    """A DRAFT set inside the CEU window.

    Ranked on keyword overlap only, so it will sometimes surface an episode that
    shares a word but not the subject. Always read the titles and swap what does
    not fit. The numbers and durations are real; the selection is a start."""
    picks, total = [], 0
    for e in search(eps, terms, limit=80, show=show):
        if total + e["seconds"] > TARGET_MAX:
            continue
        picks.append(e)
        total += e["seconds"]
        if total >= TARGET_MIN:
            break
    return picks, total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--search", nargs="+")
    ap.add_argument("--hour", nargs="+")
    ap.add_argument("--show", help="restrict to one show slug, e.g. powerofone")
    ap.add_argument("--refresh", action="store_true")
    a = ap.parse_args()

    eps = refresh() if a.refresh else (load() or refresh())

    terms = a.search or a.hour or []
    if a.hour:
        picks, total = build_hour(eps, terms, a.show)
        print(f"\nDRAFT CEU hour for {terms}  -  {total // 60} min {total % 60} sec")
        print("  check every title really fits the topic; swap with --search")
        for e in picks:
            print(f"  [{e['show']:<12}] {e['duration']:>6}  {e['title'][:60]}")
            print(f"        {e['url']}")
        if not TARGET_MIN <= total <= TARGET_MAX:
            print(f"  ! outside {TARGET_MIN // 60}-{TARGET_MAX // 60} min; add or swap")
    elif a.search:
        for e in search(eps, terms, show=a.show):
            print(f"  [{e['show']:<12}] {e['duration']:>6}  {e['title'][:60]}")


if __name__ == "__main__":
    main()
