"""
build_dashboard.py - render a chapter's members' site from the core templates
and that chapter's own settings.

    python build_dashboard.py --chapter path/to/chapter.json --out site/ --target netlify
    python build_dashboard.py --chapter chapter.json --out dash.html --target artifact

Pages, one shell:

  /                 home.html       the members' guide
  /meetings/        meetings.html   every date, both sets of details, fees
  /education/       dashboard.html  the term, the decks, the CEU hour, the playlist
  /requests/        referrals.html  the referral board          (features.referral_board)
  /<slug>/          pages/<slug>.html in the chapter folder - the chapter's own

EVERYTHING CHAPTER-SPECIFIC COMES FROM chapter.json. The core carries no
chapter's name, venue, colours or IDs. See references/chapter-config.md.

How a chapter customises, from lightest to heaviest - all of it lives in the
chapter's own folder, so a core update never overwrites it:

  1. chapter.json                settings and feature switches
  2. custom.css, assets/         look
  3. content/<block>.html        replace one named section of a page
     moments.json                the chapter's own moments library
     emails/reminders.json       reword any part of the reminder emails
  4. pages/<slug>.html           whole extra pages, in the shared shell
     functions/*.mts             extra Netlify Functions
  5. overrides/templates/<file>  replace a core template outright. Printed as a
                                 warning on every build, because that file no
                                 longer receives core updates.

Two targets:

  --target artifact   the education page alone, as a fragment; the Artifact host
                      supplies <html>/<head>/<body>. The Spotify embed degrades
                      to a link, because the Artifact CSP blocks third-party frames.
  --target netlify    every page as a complete document, with noindex meta, plus
                      _headers, _redirects, robots.txt and the functions

Brand images are inlined as data URIs so each page is self-contained.
"""
from __future__ import annotations

import argparse
import base64
import html as htmllib
import io
import json
import re
import shutil
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from chapter_config import load, SKILL  # noqa: E402

ROOT = SKILL
TPL = ROOT / "templates"
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip() \
    if (ROOT / "VERSION").exists() else "dev"

CFG = None            # the Chapter, set in main()
OVERRIDDEN: set[str] = set()


# ------------------------------------------------------------ templates ---

def tpl(name: str) -> Path:
    """A core template, unless the chapter has replaced it."""
    own = CFG.dir / "overrides" / "templates" / name
    if own.exists():
        OVERRIDDEN.add(name)
        return own
    return TPL / name


def block(name: str) -> str:
    """One named section of a page. The chapter's content/<name>.html wins;
    otherwise the core's templates/blocks/<name>.html."""
    own = CFG.dir / "content" / f"{name}.html"
    if own.exists():
        return own.read_text(encoding="utf-8")
    core = TPL / "blocks" / f"{name}.html"
    if core.exists():
        return core.read_text(encoding="utf-8")
    raise SystemExit(f"no block called {name!r} in the core or in content/")


# ------------------------------------------------------------ the shell ---

FEATURE_PAGES = [("/", "Home", None), ("/meetings/", "Meetings", None),
                 ("/education/", "Education", None),
                 ("/requests/", "Requests", "referral_board")]


def nav(here: str) -> str:
    items = [(h, l) for h, l, f in FEATURE_PAGES if f is None or CFG.feature(f)]
    items += [(x["href"], x["label"]) for x in CFG.get("site.nav_extra") or []]
    links = "".join(
        f'<a href="{href}"{" aria-current=\"page\"" if href == here else ""}>{label}</a>'
        for href, label in items)
    mark = ""
    if CFG.get("brand.mark_svg"):
        mark = CFG.asset("brand.mark_svg").read_text(encoding="utf-8").strip()
        mark = re.sub(r"<\?xml.*?\?>", "", mark).strip()
    a, b = ((CFG.get("brand.wordmark") or []) + ["", ""])[:2]
    a = a or CFG.get("chapter.name")
    word = f'<b>{htmllib.escape(a)}{f" <span>{htmllib.escape(b)}</span>" if b else ""}</b>'
    return (f'<nav class="nav"><div class="nav-in">'
            f'<a class="brand" href="/">{mark}{word}</a>'
            f'<div class="nav-links">{links}</div></div></nav>')


def theme_css() -> str:
    """The chapter's colours, laid over the core palette. The variable names
    are historical: --nx-navy is the chapter's primary, --nx-orange its accent."""
    c = CFG.get("brand.colours")
    light = (f"--nx-navy:{c['primary']}; --nx-orange:{c['accent']};"
             f" --nx-orange-ink:{c['accent_ink']};")
    dark = (f"--nx-navy:{c['primary_dark']}; --nx-orange:{c['accent_dark']};"
            f" --nx-orange-ink:{c['accent_ink_dark']};")
    goal = (f".goal{{--goal-bg:{c['goal_band']}; --goal-rule:{c['accent']};"
            f" --goal-bar:{c['goal_bar']}}}")
    goal_dark = f"--goal-bg:{c['goal_band_dark']}; --goal-rule:{c['accent_dark']}"
    return (f"\n/* chapter theme, from chapter.json */\n:root{{{light}}}\n"
            f"@media (prefers-color-scheme:dark){{:root:not([data-theme=\"light\"]){{{dark}}}"
            f" :root:not([data-theme=\"light\"]) .goal{{{goal_dark}}}}}\n"
            f":root[data-theme=\"dark\"]{{{dark}}}\n{goal}\n"
            f":root[data-theme=\"dark\"] .goal{{{goal_dark}}}\n")


def page_meta() -> dict:
    name = CFG.get("chapter.name")
    return {
        "/": {"blurb": f"What's on at {name}, what to listen to, and where to find it.",
              "card_sub": "For members", "card": "og.png"},
        "/education/": {
            "blurb": "Every week of the term: the topic, who's presenting, the "
                     "slides and notes, and the hour of podcast that earns your CEU.",
            "card_sub": "Education program", "card": "og-education.png"},
        "/meetings/": {
            "blurb": f"When and where {name} meets: every date of the term "
                     "and the details for getting there.",
            "card_sub": "Meetings", "card": "og.png"},
        # No preview card of its own - a link pasted into a chat should not
        # advertise what is behind it.
        "/requests/": {"blurb": "", "card_sub": "For members", "card": "og.png"},
    }


# Every function the core can ship, and the feature that switches it on.
# schedule is the join everything else reads, so it is always on.
FUNCTIONS = {
    "schedule.mts": None,
    "refresh-playlist.mts": "spotify",
    "presenter-reminders.mts": "reminders",
    "referrals-data.mts": "referral_board",
    "tradesheet.mts": "tradesheet",
}
RETIRED = ("weeks.json",)

HEAD = """<!doctype html>
<html lang="en-AU">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<meta name="theme-color" content="{theme}">
<meta name="generator" content="BNI Chapter Hub {version}">
{favicon_tags}
<title>{title}</title>
<meta name="description" content="{description}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{site_name}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:url" content="{page_url}">
<meta property="og:image" content="{og_image}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<style>html{{color-scheme:light dark}}body{{margin:0}}img{{max-width:100%}}
[hidden]{{display:none!important}}</style>
</head>
<body>
"""

ROBOTS = "User-agent: *\nDisallow: /\n"

# Written into the build output so it works the same from a git-connected
# Netlify build (where netlify.toml is the chapter repo's own) and from a CLI
# deploy. Rewrites, not redirects: the paths stay tidy in the address bar.
REDIRECTS = """/requests/data   /.netlify/functions/referrals-data   200
/schedule        /.netlify/functions/schedule         200
/moments.csv     /.netlify/functions/schedule?as=moments.csv   200
"""

NETLIFY_TOML = """# Written by build_dashboard.py for a CLI deploy. A git-connected chapter
# repo has its own netlify.toml, and this file is not written over it.
[build]
  publish = "public"
  functions = "netlify/functions"

[build.environment]
  NODE_VERSION = "20"
"""

PACKAGE_JSON = {
    "name": "bni-chapter-hub-site",
    "private": True,
    "description": "Dependencies for the chapter hub's Netlify Functions.",
    "dependencies": {"@netlify/functions": "^2.8.2", "nodemailer": "^6.9.16"},
}

HEADERS = """/*
  X-Robots-Tag: noindex, nofollow, noarchive
  Referrer-Policy: strict-origin-when-cross-origin
  X-Content-Type-Options: nosniff
"""


def data_uri(path: Path, width: int) -> str:
    if path.suffix.lower() == ".svg":
        return "data:image/svg+xml;base64," + base64.b64encode(path.read_bytes()).decode()
    im = Image.open(path).convert("RGBA")
    if im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


# ------------------------------------------------------------- snapshot ---

SNAPSHOT = "[]"
SNAPSHOT_MEMBERS = "[]"


def snapshot() -> tuple[str, str]:
    """The resolved calendar as the live site currently sees it, inlined so a
    page paints the next meeting immediately. Best effort: the first deploy
    has no /schedule to ask yet, and an empty snapshot just means the page
    fetches before it paints. Never recomputed here - one join, in the
    schedule function."""
    import time
    import urllib.request
    origin = CFG.get("site.origin").rstrip("/")
    d = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(f"{origin}/schedule?b={time.time()}",
                                        timeout=20) as r:
                got = json.loads(r.read().decode("utf-8"))
            if got.get("meetings"):
                d = got
                break
            print(f"     snapshot: attempt {attempt + 1} came back empty, retrying")
        except Exception as e:
            print(f"     snapshot: attempt {attempt + 1} failed ({e})")
        time.sleep(2)
    if d is None:
        print("     snapshot: unavailable; pages will fetch before painting")
        return ("[]", "[]")
    meetings = d.get("meetings", [])
    weeks = sorted(
        meetings + [{**m, "archive": True, "date": m.get("deliveredOn", "")}
                    for m in d.get("archive", [])],
        key=lambda w: w.get("date") or "")
    members = d.get("members", [])
    print(f"     snapshot: {len(meetings)} meetings, {len(members)} members")
    return (json.dumps(weeks, ensure_ascii=False, separators=(",", ":")),
            json.dumps(members, ensure_ascii=False, separators=(",", ":")))


# --------------------------------------------------------------- tokens ---

def esc(s) -> str:
    """&, <, > and the double quote - enough for text and for a double-quoted
    attribute, without turning every apostrophe into &#x27;."""
    return (str(s if s is not None else "").replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def mode_label() -> str:
    return {"alternating": "alternating between Zoom and the venue",
            "hybrid": "in the room and on Zoom at the same time",
            "in_person": "in person", "online": "on Zoom"}[CFG.get("meeting.mode")]


def summary() -> str:
    s = CFG.get("meeting.summary")
    if s:
        return s
    m = CFG.get("meeting")
    where = m["venue"]["short"] or m["venue"]["name"]
    return {
        "alternating": f"Every {m['weekday']}, {m['start']}, alternating between "
                       f"Zoom and {where}. Be there by {m['arrive']} either way.",
        "hybrid": f"Every {m['weekday']}, {m['start']}, at {where} and on Zoom at "
                  f"the same time &mdash; come in person or join online. Be there by "
                  f"{m['arrive']}.",
        "in_person": f"Every {m['weekday']}, {m['start']}, at {where}. Be there by "
                     f"{m['arrive']}.",
        "online": f"Every {m['weekday']}, {m['start']}, on Zoom. Be there by "
                  f"{m['arrive']}.",
    }[m["mode"]]


def maps_url() -> str:
    v = CFG.get("meeting.venue")
    if v.get("maps_url"):
        return v["maps_url"]
    from urllib.parse import quote_plus
    return ("https://www.google.com/maps/search/?api=1&query="
            + quote_plus(f"{v['name']} {v['address']}"))


def spotify_html(embed: bool) -> str:
    url = CFG.get("spotify.playlist_url")
    if not url:
        return ""
    if not embed:
        return (f'<a class="btn primary playfall" href="{esc(url)}" target="_blank"'
                ' rel="noopener">Open the chapter playlist in Spotify</a>')
    pid = url.split("?")[0].rstrip("/").rsplit("/", 1)[-1]
    return (f'<iframe class="embed" title="{esc(CFG.get("chapter.name"))} chapter playlist"'
            f' src="https://open.spotify.com/embed/playlist/{pid}"'
            ' loading="lazy" allow="clipboard-write; encrypted-media; fullscreen;'
            ' picture-in-picture"></iframe>')


BUILTIN_CARDS: dict = {}


def builtin_cards() -> dict:
    name = esc(CFG.get("chapter.name"))
    return {
        "requests": {
            "feature": "referral_board", "title": "Referral requests",
            "href": "/requests/", "primary": True, "button": "Open the board",
            "text": "What everyone is actually looking for &mdash; bread and butter, "
                    "cream, dream, and anyone in particular. Post yours, and read the "
                    "rest before you go out for the week. Nothing is compulsory: put "
                    "up as much or as little as you like."},
        "education": {
            "title": "Education program", "href": "/education/", "primary": True,
            "button": "Open the program",
            "text": "Every week: the topic, who's presenting, the slides and notes, "
                    "and the hour of podcast that earns your CEU."
                    + (" The chapter playlist is on that page."
                       if CFG.feature("spotify") else "")},
        "ceu": {
            "title": "Log your CEUs", "href": "https://www.bniconnectglobal.com/",
            "link_title": False, "button": "BNI Connect",
            "text": "One hour of BNI education is one CEU, and CEUs are one of the five "
                    "Power of One KPIs. Nobody logs them for you &mdash; it's Reports "
                    "&rarr; CEU in BNI Connect, and it takes about a minute."},
        "gains": {
            "title": "The GAINS sheet", "href": CFG.get("education.gains_pdf"),
            "external": False, "button": "Download the worksheet",
            "text": "BNI's own worksheet for a one-to-one &mdash; goals, accomplishments, "
                    "interests, networks, skills. One per person, dated, so you can see "
                    "how old what you know about somebody is. It is the difference "
                    "between a coffee and a one-to-one they remember."},
        "chapter_page": {
            "title": "Our chapter page", "href": CFG.get("data.bni_chapter_url"),
            "link_title": False, "button": "BNI chapter page",
            "text": f"The public page for {name} &mdash; the member list and the "
                    "visitor booking form. This is the link to send someone you're "
                    "inviting."},
    }


DEFAULT_CARDS = [{"builtin": b} for b in
                 ("requests", "education", "ceu", "gains", "chapter_page")]


def card(c: dict) -> str:
    """One card on the home page. Built-ins are the core's own; anything else
    is the chapter's, straight from chapter.json home.cards."""
    if "builtin" in c:
        b = BUILTIN_CARDS.get(c["builtin"])
        if b is None:
            raise SystemExit(f"home.cards: no built-in card called {c['builtin']!r}")
        if b.get("feature") and not CFG.feature(b["feature"]):
            return ""
        c = {**b, **{k: v for k, v in c.items() if k != "builtin"}}
    href = c.get("href") or ""
    ext = c.get("external", href.startswith("http"))
    tgt = ' target="_blank" rel="noopener"' if ext else ""
    title = (f'<a href="{esc(href)}"{tgt}>{c["title"]}</a>'
             if href and c.get("link_title", True) else c["title"])
    btn = (f'<a class="btn{" primary" if c.get("primary") else ""} go" href="{esc(href)}"{tgt}>'
           f'{c.get("button", "Open")}</a>' if href else "")
    return (f'\n    <div class="card">\n      <h3>{title}</h3>\n      <p>{c.get("text", "")}</p>\n'
            f'      {btn}\n    </div>')


def footer_links() -> str:
    links = list(CFG.get("site.footer_links") or [])
    if not links and CFG.get("data.bni_chapter_url"):
        links = [{"label": "Our chapter page", "href": CFG.get("data.bni_chapter_url")}]
    return "".join(f'<a href="{esc(l["href"])}" target="_blank" rel="noopener">'
                   f'{esc(l["label"])}</a>' for l in links)


def fees_rows() -> str:
    f = CFG.get("fees")
    rows = [("Account name", f.get("account_name")), ("BSB", f.get("bsb")),
            ("Account", f.get("account_number")), ("Reference", f.get("reference"))]
    if not f.get("account_number"):
        return ""
    return "".join(f"<tr><td>{a}</td><td><b>{esc(b)}</b></td></tr>" for a, b in rows if b)


def tokens(embed: bool = True) -> dict:
    """Every @@name@@ a template may use, in one flat table - so a template
    author can see the whole vocabulary in one place. Documented in
    references/chapter-config.md."""
    m = CFG.get("meeting")
    v = m["venue"]
    dl = CFG.deadline()
    mascot = CFG.asset("brand.mascot")
    return {
        "chapter": esc(CFG.get("chapter.name")),
        "chapter_short": esc(CFG.get("chapter.short_name")),
        "lede": CFG.get("chapter.lede"),
        "contact": esc(CFG.get("chapter.contact_name")),
        "maintained_by": esc(CFG.get("chapter.maintained_by")),
        "tagline": esc(CFG.get("chapter.tagline")),
        "weekday": esc(m["weekday"]),
        "zoom": esc(m.get("zoom_url", "")),
        "venue_name": esc(v.get("name", "")),
        "venue_short": esc(v.get("short") or v.get("name", "")),
        "venue_address": esc(v.get("address", "")),
        "venue_maps": esc(maps_url()),
        "parking": v.get("parking", ""),
        "arrive": esc(m["arrive"]),
        "start": esc(m["start"]),
        "mode": m["mode"],
        "mode_label": mode_label(),
        "meeting_summary": summary(),
        "tbc_note": m.get("tbc_note", ""),
        "spotify": spotify_html(embed),
        "playlist_url": esc(CFG.get("spotify.playlist_url") or ""),
        "playlist_day": CFG.playlist_day(),
        "gains": esc(CFG.get("education.gains_pdf") or ""),
        "goal_members": str(CFG.get("goal.members") or 0),
        "goal_date": esc(CFG.get("goal.date") or ""),
        "template_pptx": esc(CFG.get("education.template_pptx") or ""),
        "template_pptx_button": (f'<a class="btn primary" href="{esc(CFG.get("education.template_pptx"))}"'
                                 ' target="_blank" rel="noopener">Template (PowerPoint)</a>'
                                 if CFG.get("education.template_pptx") else ""),
        "template_canva": (f'<a class="btn" href="{esc(CFG.get("education.template_canva"))}"'
                           ' target="_blank" rel="noopener">Template (Canva)</a>'
                           if CFG.get("education.template_canva") else ""),
        "deadline_who": esc(dl["who"]),
        "deadline_time": esc(dl["time"]),
        "deadline_weekday": dl["weekday"],
        "education_folder": esc(CFG.get("data.education_folder_url") or ""),
        "fees_summary": CFG.get("fees.summary") or "",
        "fees_rows": fees_rows(),
        "fees_note": CFG.get("fees.note") or "",
        "footer_links": footer_links(),
        "home_cards": "".join(card(c) for c in (CFG.get("home.cards") or DEFAULT_CARDS)),
        "mascot": data_uri(mascot, 160) if mascot else "",
        "lockup": data_uri(CFG.asset("brand.lockup"), 260),
        "logo": data_uri(ROOT / "assets" / "logos" / "BNI - Red.png", 320),
        "sg": data_uri(ROOT / "assets" / "graphics" / "Super Graphic - Primary.png", 560),
        # JS-safe copies, for templates that read settings in a <script>
        "json_meeting": json.dumps({
            "weekday": m["weekday"], "mode": m["mode"], "arrive": m["arrive"],
            "start": m["start"], "zoom": m.get("zoom_url", ""),
            "venue": v.get("name", ""), "venueShort": v.get("short") or v.get("name", ""),
            "address": v.get("address", ""), "maps": maps_url(),
            "parking": v.get("parking", ""),
        }, ensure_ascii=False),
        "json_timezone": json.dumps(m["timezone"]),
        "json_handover": json.dumps(m.get("handover_hour", 10)),
        "json_education_folder": json.dumps(CFG.get("data.education_folder_url") or ""),
        "json_listen": json.dumps(
            ([["Chapter Spotify playlist", CFG.get("spotify.playlist_url")]]
             if CFG.feature("spotify") and CFG.get("spotify.playlist_url") else [])
            + [["bnipodcast.com", "https://www.bnipodcast.com/"],
               ["YouTube", "https://www.youtube.com/@TheOfficialBNIPodcast"]]),
    }


IF_RE = re.compile(r"<!--if:(!?)(\w+)-->(.*?)<!--/if:\1\2-->", re.S)
MODES = ("hybrid", "alternating", "in_person", "online")


def gate(html: str, where: str = "") -> str:
    """<!--if:spotify--> ... <!--/if:spotify--> keeps its contents only when
    the feature is on; <!--if:!spotify--> ... <!--/if:!spotify--> only when
    it is off. Meeting modes (hybrid, alternating, in_person, online) work
    the same way."""
    def keep(m):
        neg, name, body = m.group(1), m.group(2), m.group(3)
        on = (CFG.get("meeting.mode") == name) if name in MODES else CFG.feature(name)
        return body if on != bool(neg) else ""
    prev = None
    while prev != html:                      # nested gates
        prev, html = html, IF_RE.sub(keep, html)
    stray = re.findall(r"<!--/?if:!?\w+-->", html)
    if stray:
        raise SystemExit(f"{where}: unmatched feature gate(s): {sorted(set(stray))}")
    return html


def render(template: Path, here: str, embed: bool = True) -> str:
    html = template.read_text(encoding="utf-8")

    # the shell, inlined once per page
    css = tpl("site.css").read_text(encoding="utf-8") + theme_css()
    custom = CFG.dir / "custom.css"
    if custom.exists():
        css += "\n/* chapter custom.css */\n" + custom.read_text(encoding="utf-8")
    html = html.replace("<style>", "<style>\n" + css + "\n", 1)
    html = html.replace("@@nav@@", nav(here))
    for part in ("clock", "meeting", "goal", "footer"):
        html = html.replace(f"@@{part}@@", tpl(f"{part}.html").read_text(encoding="utf-8"))
    html = re.sub(r"@@block:([\w-]+)@@", lambda m: block(m.group(1)), html)
    html = gate(html, template.name)

    html = html.replace("@@weeks@@", SNAPSHOT).replace("@@roll@@", SNAPSHOT_MEMBERS)
    t = tokens(embed)
    # Two passes: a block or a setting can itself contain a token.
    for _ in range(2):
        html = re.sub(r"@@(\w+)@@", lambda m: t.get(m.group(1), m.group(0)), html)
    left = re.findall(r"@@[\w:-]+@@", html)
    if left:
        raise SystemExit(f"{template.name}: unsubstituted placeholder(s): {sorted(set(left))}")
    return html


def favicon_tags() -> str:
    tags = []
    if CFG.get("brand.favicon_svg"):
        svg = CFG.asset("brand.favicon_svg").read_bytes()
        tags.append('<link rel="icon" href="data:image/svg+xml;base64,'
                    f'{base64.b64encode(svg).decode()}" type="image/svg+xml">')
    png = CFG.asset("brand.favicon_png")
    if png:
        uri = data_uri(png, 180)
        if not CFG.get("brand.favicon_svg"):
            tags.append(f'<link rel="icon" href="{uri}" type="image/png">')
        tags.append(f'<link rel="apple-touch-icon" href="{uri}">')
    return "\n".join(tags)


def document(html: str, fallback: str, here: str = "/") -> tuple[str, str]:
    """Split the <title> out of a fragment and wrap it as a whole document."""
    m = re.search(r"<title>(.*?)</title>\s*", html, re.S)
    title = m.group(1).strip() if m else fallback
    if m:
        html = html[:m.start()] + html[m.end():]
    meta = page_meta()
    page = meta.get(here, meta["/"])
    origin = CFG.get("site.origin").rstrip("/")
    head = HEAD.format(
        title=title, description=esc(page["blurb"]), page_url=origin + here,
        og_image=f"{origin}/{page['card']}", site_name=esc(CFG.get("chapter.name")),
        theme=CFG.get("brand.colours.primary"), favicon_tags=favicon_tags(),
        version=VERSION)
    return head + html + "\n</body>\n</html>\n", title


# ------------------------------------------------------------ functions ---

def emails() -> dict:
    """The reminder emails' wording: the core's, with the chapter's own
    emails/reminders.json laid over it key by key."""
    core = json.loads((TPL / "emails" / "reminders.json").read_text(encoding="utf-8"))
    own_path = CFG.dir / "emails" / "reminders.json"
    if own_path.exists():
        own = json.loads(own_path.read_text(encoding="utf-8"))
        core.update({k: v for k, v in own.items() if not k.startswith("_")})
    dl = CFG.deadline()
    fill = {
        "chapter": CFG.get("chapter.name"), "chapter_short": CFG.get("chapter.short_name"),
        "tagline": CFG.get("chapter.tagline") or CFG.get("chapter.name"),
        "tagline_words": CFG.get("chapter.tagline_words") or "",
        "contact": CFG.get("chapter.contact_name"), "weekday": CFG.weekday,
        "deadline_who": dl["who"], "deadline_time": dl["time"],
        "deadline_weekday": dl["weekday"], "playlist_day": CFG.playlist_day(),
    }
    out = {}
    for k, v in core.items():
        if k.startswith("_"):
            continue
        if isinstance(v, list):
            v = "\n".join(v)
        for name, val in fill.items():
            v = v.replace("{{" + name + "}}", str(val))
        out[k] = v
    return out


def function_tokens() -> dict:
    """What the .mts files are told about the chapter. Each is a JSON literal,
    dropped in where the function used to have a hard-coded constant."""
    dl = CFG.deadline()
    stages = {int(k): v for k, v in (CFG.get("reminders.stages") or {}).items()}
    stages.setdefault(dl["days"], f"on {CFG.weekday}")
    j = lambda x: json.dumps(x, ensure_ascii=False)
    return {
        "@@json:timezone@@": j(CFG.get("meeting.timezone")),
        "@@json:origin@@": j(CFG.get("site.origin").rstrip("/")),
        "@@json:fallback_origin@@": j((CFG.get("site.fallback_origin")
                                       or CFG.get("site.origin")).rstrip("/")),
        "@@json:roster_sheet@@": j(CFG.get("data.roster_sheet_id") or ""),
        "@@json:tabs@@": j(CFG.get("data.tabs")),
        "@@json:tradesheet_folder@@": j(CFG.get("data.tradesheet_folder_id") or ""),
        "@@json:bni_member_list@@": j(CFG.get("data.bni_member_list_url")
                                      if CFG.feature("bni_roll") else ""),
        "@@json:show_id@@": j(CFG.get("spotify.show_id")),
        "@@json:market@@": j(CFG.get("spotify.market")),
        "@@json:stages@@": j({str(k): v for k, v in sorted(stages.items(), reverse=True)}),
        "@@json:deadline_days@@": j(dl["days"]),
        "@@json:nudge_weekday@@": j(CFG.get("reminders.nudge_weekday") or "Mon"),
        "@@json:emails@@": j(emails()),
        "@@json:mode@@": j(CFG.get("meeting.mode")),
        "@@json:venue@@": j(CFG.get("meeting.venue.name") or ""),
        "@@json:no_meeting_words@@": j(CFG.get("meeting.no_meeting_words")),
        "@@json:chapter@@": j(CFG.get("chapter.name")),
        "@@json:weekday@@": j(CFG.weekday),
        "@@json:playlist_day@@": j(CFG.playlist_day()),
        "@@cron:playlist@@": CFG.playlist_cron(),
        "@@cron:reminders@@": CFG.get("reminders.cron"),
    }


def write_functions(funcs: Path):
    ft = function_tokens()
    wanted = {}
    for name, feature in FUNCTIONS.items():
        if feature is None or CFG.feature(feature):
            text = tpl(name).read_text(encoding="utf-8")
            for k, v in ft.items():
                text = text.replace(k, v)
            left = re.findall(r"@@[\w:-]+@@", text)
            if left:
                raise SystemExit(f"{name}: unsubstituted placeholder(s): {sorted(set(left))}")
            wanted[name] = text
    own = CFG.dir / "functions"
    if own.is_dir():
        for f in sorted(own.glob("*.mts")) + sorted(own.glob("*.ts")):
            if f.name in wanted:
                OVERRIDDEN.add(f"functions/{f.name}")
            wanted[f.name] = f.read_text(encoding="utf-8")

    # Anything this build no longer writes must not survive from an earlier one:
    # a stale function keeps running on its schedule long after it was dropped.
    if funcs.exists():
        for stale in funcs.rglob("*"):
            if stale.is_file() and stale.name not in wanted:
                stale.unlink()
    funcs.mkdir(parents=True, exist_ok=True)
    for name, text in wanted.items():
        (funcs / name).write_text(text, encoding="utf-8")
    return sorted(wanted)


# ----------------------------------------------------------------- main ---

def main():
    global CFG, SNAPSHOT, SNAPSHOT_MEMBERS, BUILTIN_CARDS
    try:                                    # Windows consoles default to cp1252
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--chapter", required=True, help="the chapter's chapter.json")
    ap.add_argument("--weeks", help="the moments library. Default: moments.json "
                                    "beside chapter.json, else the core's")
    ap.add_argument("--out", required=True,
                    help="file for --target artifact, directory for --target netlify")
    ap.add_argument("--target", choices=["artifact", "netlify"], default="netlify")
    ap.add_argument("--no-snapshot", action="store_true",
                    help="skip reading the live /schedule (first deploy, offline)")
    a = ap.parse_args()

    CFG = load(a.chapter)
    BUILTIN_CARDS = builtin_cards()
    print(f"   {CFG.get('chapter.name')} - BNI Chapter Hub {VERSION}")

    weeks = Path(a.weeks) if a.weeks else (
        CFG.dir / "moments.json" if (CFG.dir / "moments.json").exists()
        else ROOT / "library" / "moments.json")
    out = Path(a.out)

    if not a.no_snapshot:
        SNAPSHOT, SNAPSHOT_MEMBERS = snapshot()

    if a.target == "artifact":
        html = render(tpl("dashboard.html"), "/education/", embed=False)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html, encoding="utf-8")
        print(f"-> {out}  ({len(html) // 1024} KB, fragment for Artifact)")
        return

    public = out / "public"
    funcs = out / "netlify" / "functions"
    public.mkdir(parents=True, exist_ok=True)
    for name in RETIRED:
        stale = public / name
        if stale.exists():
            stale.unlink()

    pages = [("/", "home.html", CFG.get("chapter.name")),
             ("/meetings/", "meetings.html", f"{CFG.get('chapter.name')} - Meetings"),
             ("/education/", "dashboard.html", "Chapter Education Program")]
    if CFG.feature("referral_board"):
        pages.append(("/requests/", "referrals.html", "Referral requests"))
    elif (public / "requests").exists():
        shutil.rmtree(public / "requests")

    written = []
    for here, name, fallback in pages:
        doc, title = document(render(tpl(name), here), fallback, here)
        dest = public / here.strip("/") / "index.html" if here != "/" else public / "index.html"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(doc, encoding="utf-8")
        written.append((here, title))

    # The chapter's own pages, in the same shell.
    own_pages = CFG.dir / "pages"
    if own_pages.is_dir():
        for f in sorted(own_pages.glob("*.html")):
            here = f"/{f.stem}/"
            doc, title = document(render(f, here), f.stem.replace("-", " ").title(), here)
            dest = public / f.stem / "index.html"
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(doc, encoding="utf-8")
            written.append((here, title))

    # og:image has to be a real URL, so these are the only image files.
    from build_og_image import build as build_og
    for card_name, sub in {p["card"]: p["card_sub"] for p in page_meta().values()}.items():
        build_og(public / card_name, title=CFG.get("chapter.name"), sub=sub,
                 lockup=CFG.asset("brand.lockup_white"),
                 bg=CFG.get("brand.colours.primary"), edge=CFG.get("brand.colours.accent"))

    (public / "robots.txt").write_text(ROBOTS, encoding="utf-8")
    (public / "_headers").write_text(HEADERS, encoding="utf-8")
    (public / "_redirects").write_text(REDIRECTS, encoding="utf-8")
    (public / "moments.json").write_text(weeks.read_text(encoding="utf-8"), encoding="utf-8")
    if not (out / "netlify.toml").exists():
        (out / "netlify.toml").write_text(NETLIFY_TOML, encoding="utf-8")
    if not (out / "package.json").exists():
        (out / "package.json").write_text(json.dumps(PACKAGE_JSON, indent=2) + "\n",
                                          encoding="utf-8")

    fn_names = write_functions(funcs)

    print(f"-> {out}/")
    for here, title in written:
        print(f"     {here:<14} {title!r}")
    for f in fn_names:
        print(f"     netlify/functions/{f}")
    off = [k for k, v in (CFG.get("features") or {}).items() if not v]
    if off:
        print(f"   features off: {', '.join(off)}")
    if OVERRIDDEN:
        print("   WARNING: this chapter replaces these core files, which therefore")
        print("   no longer receive core updates - check the CHANGELOG for each release:")
        for o in sorted(OVERRIDDEN):
            print(f"     - {o}")


if __name__ == "__main__":
    main()
