"""
build_photo_cache.py — one-time prep of the official BNI photo library.

The supplied album zip is ~594 MB of full-resolution JPEGs, which is far too
heavy to drop into a slide deck. This unpacks it once, downscales to something
sane for projection, and writes contact sheets so the photos can be captioned
into references/photo-index.json.

    python build_photo_cache.py                       # uses the default paths
    python build_photo_cache.py --zip X --out Y

Re-running is cheap: already-converted photos are skipped.
"""
import argparse
import json
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw

# Where the official BNI photo album (downloaded from the Global Brand Hub)
# and the resized library live. Set BNI_PHOTO_LIBRARY to the library folder;
# the zip is expected beside it.
import os
_LIB = Path(os.environ.get("BNI_PHOTO_LIBRARY", "photo-library"))
DEFAULT_ZIP = str(_LIB.parent / "album-d482284769-downloads.zip")
DEFAULT_OUT = str(_LIB)

MAX_W = 1920          # plenty for a 13.3in slide at projector resolution
QUALITY = 82
THUMB_W = 420
SHEET_COLS = 4
SHEET_ROWS = 3


def convert(zf, name, outdir):
    out = outdir / (Path(name).stem + ".jpg")
    if out.exists():
        return out, None
    with zf.open(name) as fh:
        im = Image.open(fh)
        im = im.convert("RGB")
        w, h = im.size
        if w > MAX_W:
            im = im.resize((MAX_W, round(h * MAX_W / w)), Image.LANCZOS)
        im.save(out, "JPEG", quality=QUALITY, optimize=True, progressive=True)
    return out, im.size


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", default=DEFAULT_ZIP)
    ap.add_argument("--out", default=DEFAULT_OUT)
    a = ap.parse_args()

    outdir = Path(a.out)
    (outdir / "sheets").mkdir(parents=True, exist_ok=True)

    zf = zipfile.ZipFile(a.zip)
    names = [n for n in zf.namelist()
             if n.lower().endswith((".jpg", ".jpeg", ".png")) and "/" not in n]
    names.sort()
    print(f"{len(names)} photo(s) in the album")

    manifest = []
    for i, n in enumerate(names, 1):
        out, size = convert(zf, n, outdir)
        im = Image.open(out)
        manifest.append({
            "id": out.stem,
            "file": out.name,
            "w": im.width, "h": im.height,
            "orientation": ("landscape" if im.width > im.height * 1.15
                            else "portrait" if im.height > im.width * 1.15
                            else "square"),
        })
        if i % 10 == 0 or i == len(names):
            print(f"  {i}/{len(names)}")

    # contact sheets, numbered, so each photo can be described and tagged
    per = SHEET_COLS * SHEET_ROWS
    for s in range(0, len(manifest), per):
        batch = manifest[s:s + per]
        th = round(THUMB_W * 0.68)
        pad = 8
        sheet = Image.new("RGB", (SHEET_COLS * THUMB_W + (SHEET_COLS + 1) * pad,
                                  SHEET_ROWS * (th + 22) + (SHEET_ROWS + 1) * pad),
                          (235, 235, 235))
        dr = ImageDraw.Draw(sheet)
        for j, m in enumerate(batch):
            r, c = divmod(j, SHEET_COLS)
            im = Image.open(outdir / m["file"]).convert("RGB")
            im.thumbnail((THUMB_W, th), Image.LANCZOS)
            x = pad + c * (THUMB_W + pad)
            y = pad + r * (th + 22 + pad)
            sheet.paste(im, (x + (THUMB_W - im.width) // 2, y))
            dr.text((x + 3, y + th + 4), f"[{s + j + 1}] {m['id'][:44]}",
                    fill=(20, 20, 20))
        p = outdir / "sheets" / f"sheet-{s // per + 1:02d}.jpg"
        sheet.save(p, "JPEG", quality=88)
        print(f"  sheet -> {p.name}")

    (outdir / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")
    total = sum((outdir / m["file"]).stat().st_size for m in manifest)
    print(f"done: {len(manifest)} photos, {total / 1e6:.0f} MB in {outdir}")


if __name__ == "__main__":
    main()
