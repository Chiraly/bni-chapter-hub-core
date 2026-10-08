"""
icon.py — Lucide SVG -> BNI-coloured transparent PNG, for use on slides.

Lucide is ISC-licensed (no attribution required) and its icons are drawn as
`stroke="currentColor"`, so recolouring is a string replace. PyMuPDF does the
rasterising, so there is no new dependency to install.

    from icon import icon
    png = icon("handshake")                  # BNI red, 512px, cached
    png = icon("phone", colour="#FFFFFF")    # white, for the red visitor slide

    python icon.py --list                    # what's bundled
    python icon.py --fetch handshake phone   # add more from the CDN
"""
import argparse
import hashlib
import urllib.request
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parent.parent
SVG_DIR = ROOT / "assets" / "icons-lucide"
CACHE = ROOT / "assets" / "icons-lucide" / ".png-cache"
CDN = "https://cdn.jsdelivr.net/npm/lucide-static@latest/icons/{}.svg"

RED = "#CF2030"
WHITE = "#FFFFFF"
GRANITE = "#64666A"


def fetch(name: str) -> Path:
    """Download one Lucide icon into the bundled set."""
    SVG_DIR.mkdir(parents=True, exist_ok=True)
    dest = SVG_DIR / f"{name}.svg"
    if dest.exists():
        return dest
    req = urllib.request.Request(CDN.format(name),
                                 headers={"User-Agent": "bni-education-program"})
    with urllib.request.urlopen(req, timeout=30) as r:
        if r.status != 200:
            raise FileNotFoundError(f"lucide has no icon called {name!r}")
        dest.write_bytes(r.read())
    return dest


def icon(name: str, colour: str = RED, size: int = 512, stroke: float = 2.0) -> Path:
    """Return a path to a transparent PNG of the named icon in `colour`."""
    svg_path = SVG_DIR / f"{name}.svg"
    if not svg_path.exists():
        svg_path = fetch(name)

    svg = svg_path.read_text(encoding="utf-8")
    svg = svg.replace('stroke="currentColor"', f'stroke="{colour}"')
    if stroke != 2.0:
        svg = svg.replace('stroke-width="2"', f'stroke-width="{stroke}"')

    CACHE.mkdir(parents=True, exist_ok=True)
    key = hashlib.md5(f"{name}{colour}{size}{stroke}".encode()).hexdigest()[:12]
    out = CACHE / f"{name}-{key}.png"
    if out.exists():
        return out

    doc = fitz.open("svg", svg.encode("utf-8"))
    page = doc[0]
    scale = size / max(page.rect.width, page.rect.height)
    page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=True).save(out)
    return out


# A starter set covering the topics an education moment actually needs.
STARTER = """
handshake users user-plus user-check user-round-search contact-round
phone phone-call mail message-circle calendar calendar-check clock timer
target crosshair trending-up trending-down chart-line chart-column award trophy medal
lightbulb graduation-cap book-open headphones mic podcast play-circle
heart heart-handshake gift sparkles star thumbs-up smile party-popper
map-pin compass route footprints door-open key link-2 share-2 network
briefcase building-2 store coins banknote receipt wallet
check check-check circle-check list-checks clipboard-list clipboard-check
repeat refresh-cw rotate-cw arrow-right arrow-up-right move-right
alert-triangle circle-alert octagon-x circle-help info search eye eye-off
sprout tree-pine flame zap battery-charging anchor
coffee utensils hand-heart scale megaphone speech handshake
""".split()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--fetch", nargs="*")
    ap.add_argument("--starter", action="store_true")
    ap.add_argument("--preview", nargs="*")
    a = ap.parse_args()

    if a.list:
        have = sorted(p.stem for p in SVG_DIR.glob("*.svg"))
        print(f"{len(have)} icon(s) bundled")
        for i in range(0, len(have), 6):
            print("  " + "  ".join(f"{n:<22}" for n in have[i:i + 6]))
        return

    names = a.fetch if a.fetch else (STARTER if a.starter else [])
    ok, missing = 0, []
    for n in names:
        try:
            fetch(n)
            ok += 1
        except Exception:
            missing.append(n)
    if names:
        print(f"fetched {ok}/{len(names)} icon(s) into {SVG_DIR}")
        if missing:
            print("  not in lucide: " + ", ".join(missing))

    for n in (a.preview or []):
        print(icon(n))


if __name__ == "__main__":
    main()
