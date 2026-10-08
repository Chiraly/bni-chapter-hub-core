"""build_og_image.py - the card that shows when someone shares the site link.

Without this, pasting the address into WhatsApp or a chapter chat gives a bare
URL and nothing else. Members share this link with each other, so it is worth
looking like something.

1200x630 is the size every platform crops from. It cannot be a data URI the way
the rest of the site's images are - og:image has to be a real, absolute URL -
so this writes a file that build_dashboard.py drops into the site root.

    python build_og_image.py --out og.png
"""
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
LOCKUP = ROOT / "assets" / "logos" / "BNI - White.png"

W, H = 1200, 630
NAVY = (26, 39, 68)
ORANGE = (212, 88, 42)
WHITE = (255, 255, 255)
MUTED = (168, 180, 204)

# Arial is the BNI brand's own sanctioned substitute and is on every Windows
# machine; the fallbacks keep this working elsewhere.
FONTS = [
    ("C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/arial.ttf"),
    ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
     "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
]


def fonts(bold_px, reg_px):
    for bold, reg in FONTS:
        if Path(bold).exists():
            return ImageFont.truetype(bold, bold_px), ImageFont.truetype(reg, reg_px)
    return ImageFont.load_default(), ImageFont.load_default()


def _rgb(hexstr, fallback):
    if not hexstr:
        return fallback
    h = hexstr.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def build(out: Path, title="BNI Chapter", sub="Education program",
          lockup: Path | None = None, bg: str = "", edge: str = ""):
    """The chapter's primary colour behind, its accent along the bottom edge,
    its white lockup top left. All three come from chapter.json."""
    im = Image.new("RGB", (W, H), _rgb(bg, NAVY))
    d = ImageDraw.Draw(im)

    # the accent edge, the one bit of a palette that reads at thumbnail size
    d.rectangle([0, H - 14, W, H], fill=_rgb(edge, ORANGE))

    lock = Image.open(lockup or LOCKUP).convert("RGBA")
    lw = 300
    lock = lock.resize((lw, round(lock.height * lw / lock.width)), Image.LANCZOS)
    im.paste(lock, (90, 96), lock)

    big, reg = fonts(76, 38)
    y = 96 + lock.height + 54
    d.text((90, y), title, font=big, fill=WHITE)
    y += big.getbbox(title)[3] + 26
    d.text((90, y), sub, font=reg, fill=MUTED)

    out.parent.mkdir(parents=True, exist_ok=True)
    im.save(out, "PNG", optimize=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="og.png")
    ap.add_argument("--title", default="BNI Chapter")
    ap.add_argument("--sub", default="Education program")
    a = ap.parse_args()
    build(Path(a.out), a.title, a.sub)


if __name__ == "__main__":
    main()
