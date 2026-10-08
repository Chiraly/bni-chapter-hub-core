"""
qr.py — QR codes for the closing slide, in BNI red.

Point these at the **dashboard**, not the Spotify playlist. The playlist
deliberately runs a week behind - it flips on Thursday to the hour for the
moment just delivered - so a member scanning on Tuesday morning would get last
week's episodes. The dashboard always shows the current week and links onward
to Spotify for the car.

    from qr import qr
    png = qr("https://open.spotify.com/playlist/your-playlist-id")
"""
import hashlib
from pathlib import Path

import qrcode
from qrcode.image.pil import PilImage

CACHE = Path(__file__).resolve().parent.parent / "assets" / ".qr-cache"
RED = (0xCF, 0x20, 0x30)


def qr(url: str, px: int = 900, colour=RED, border: int = 2) -> Path:
    """A transparent-background QR PNG. Cached by url+colour+size.

    BNI red on white sits around 5:1 contrast, comfortably above what scanners
    need, so the code stays on-brand and still reads. Error correction is set
    high so it survives a projector and a phone camera at an angle.
    """
    CACHE.mkdir(parents=True, exist_ok=True)
    key = hashlib.md5(f"{url}{colour}{px}{border}".encode()).hexdigest()[:12]
    out = CACHE / f"qr-{key}.png"
    if out.exists():
        return out

    q = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10, border=border,
    )
    q.add_data(url)
    q.make(fit=True)
    img = q.make_image(image_factory=PilImage,
                       fill_color=colour, back_color="white").convert("RGB")
    img = img.resize((px, px), 0)          # NEAREST - keeps the modules crisp
    img.save(out)
    return out


if __name__ == "__main__":
    import sys
    for u in sys.argv[1:]:
        p = qr(u)
        print(f"{u}\n  -> {p}")
