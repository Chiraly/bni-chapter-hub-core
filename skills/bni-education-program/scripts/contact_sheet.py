"""
contact_sheet.py — tile rendered slide PNGs into one image for visual QA.

    python contact_sheet.py preview/ sheet.png [--cols 2] [--scale 0.5] [--only 1,3,4]

Pairs with render_preview.ps1. Looking at the slides is the only way to catch
text overflow, collisions and awkward wraps, so this is part of every build.
"""
import argparse
import re
import sys
from pathlib import Path

from PIL import Image


def slide_no(p: Path) -> int:
    m = re.search(r"(\d+)", p.stem)
    return int(m.group(1)) if m else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("indir")
    ap.add_argument("outfile")
    ap.add_argument("--cols", type=int, default=2)
    ap.add_argument("--scale", type=float, default=0.5)
    ap.add_argument("--only", default="", help="comma-separated slide numbers")
    a = ap.parse_args()

    files = sorted(Path(a.indir).glob("*.PNG"), key=slide_no)
    files += [f for f in sorted(Path(a.indir).glob("*.png"), key=slide_no)
              if f not in files]
    if a.only:
        want = {int(x) for x in a.only.split(",")}
        files = [f for f in files if slide_no(f) in want]
    if not files:
        sys.exit(f"no PNGs in {a.indir}")

    ims = [Image.open(f).convert("RGB") for f in files]
    w, h = ims[0].size
    pad, cols = 14, a.cols
    rows = -(-len(ims) // cols)
    sheet = Image.new("RGB", (cols * w + (cols + 1) * pad,
                              rows * h + (rows + 1) * pad), (190, 190, 190))
    for i, im in enumerate(ims):
        r, c = divmod(i, cols)
        sheet.paste(im.resize((w, h)), (pad + c * (w + pad), pad + r * (h + pad)))

    if a.scale != 1:
        sheet = sheet.resize((int(sheet.width * a.scale),
                              int(sheet.height * a.scale)), Image.LANCZOS)
    Path(a.outfile).parent.mkdir(parents=True, exist_ok=True)
    sheet.save(a.outfile)
    print(f"{len(ims)} slide(s) -> {a.outfile} {sheet.size}  "
          f"[{', '.join(str(slide_no(f)) for f in files)}]")


if __name__ == "__main__":
    main()
