"""
bni_deck.py — on-brand BNI Education Moment deck builder.

Geometry, colour and furniture come from the BNI Brand Standards Manual:
  p6  brand colours          p15 fonts (Arial is the sanctioned substitute)
  p17 Super Graphic rules    p28 the official PowerPoint template

Usage
-----
    from bni_deck import BNIDeck

    d = BNIDeck(
        title="Turning Visitors Into Members",
        kicker="3-MINUTE EDUCATION MOMENT",
        subtitle="The power of excellent follow-up",
        presenter="Alex Example", business="Example Plumbing",
        notes="Good morning everyone...",
    )
    d.statement("Trust is built in *minutes*, not months.", notes="...")
    d.visitor(body="You're wondering if...", takeaway="...", notes="...")
    d.action("Book one one-to-one before Friday.", notes="...")
    d.elf_close(action="Book one one-to-one before Friday.", notes="...")
    d.save("out.pptx")

`save()` refuses to write a deck that has no visitor slide or no ELF close.
Highlight a phrase in BNI red by wrapping it in *asterisks*.
"""

from __future__ import annotations

import re
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

# --------------------------------------------------------------------------
# Brand constants — Brand Standards Manual p6
# --------------------------------------------------------------------------

RED = RGBColor(0xCF, 0x20, 0x30)      # BNI Red      — the only accent
STERLING = RGBColor(0xC8, 0xC8, 0xC8)  # Sterling Grey
LIGHT = RGBColor(0xF2, 0xF2, 0xF2)     # Sterling Light Grey
GRANITE = RGBColor(0x64, 0x66, 0x6A)   # Granite Grey — secondary text
BLACK = RGBColor(0x00, 0x00, 0x00)     # Power Black  — headings
WHITE = RGBColor(0xFF, 0xFF, 0xFF)     # True White

FONT = "Arial"          # p15: sanctioned substitute for Helvetica Neue
FONT_ALT = "Helvetica Neue"

# Canvas — 16:9 widescreen
SW = 13.3333
SH = 7.5

# Grid
ML = 0.9                # left margin
MR = 0.9                # right margin
MT = 0.85               # top margin
CW = SW - ML - MR       # content width, 11.533"
SAFE_BOTTOM = 6.05      # nothing below this except furniture

# Furniture — sized from the official template on p28
SG_W, SG_H = 2.50, 1.312    # Super Graphic, aspect 1.9054, flush bottom-right
LOGO_W, LOGO_H = 1.40, 0.537  # content-slide logo, aspect 2.606
LOGO_X, LOGO_B = 0.50, 0.40   # left inset, bottom inset

ASSETS = Path(__file__).resolve().parent.parent / "assets"
LOGO_RED = ASSETS / "logos" / "BNI - Red.png"
LOGO_WHITE = ASSETS / "logos" / "BNI - White.png"
SG_PRIMARY = ASSETS / "graphics" / "Super Graphic - Primary.png"

WPM = 140               # speaking pace used for the timing estimate


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def _fill_alpha(shape, colour, pct):
    """Solid fill at `pct` opacity. python-pptx has no transparency setter, so
    the <a:alpha> element has to go in by hand."""
    shape.fill.solid()
    shape.fill.fore_color.rgb = colour
    srgb = shape._element.spPr.find(qn("a:solidFill")).find(qn("a:srgbClr"))
    alpha = srgb.makeelement(qn("a:alpha"), {"val": str(int(pct * 1000))})
    srgb.append(alpha)
    shape.line.fill.background()
    shape.shadow.inherit = False
    return shape


def _txbox(slide, x, y, w, h):
    """A text box with all inset padding removed, so x/y mean what they say."""
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    return box, tf


def _style(run, size, colour, bold=False, font=FONT, italic=False):
    f = run.font
    f.name = font
    f.size = Pt(size)
    f.bold = bold
    f.italic = italic
    f.color.rgb = colour
    return run


def _emphasis(para, text, size, base_colour, accent=RED, bold=True, font=FONT,
              balance_width=None):
    """Write `text` into `para`, rendering *starred* spans in the accent colour.

    With `balance_width`, the text is broken into balanced lines first, so a
    headline never strands a single word on its own line."""
    lines = _balance(text, size, balance_width, bold) if balance_width else [text]
    for li, line in enumerate(lines):
        if li:
            para._p.append(para._p.makeelement(qn("a:br"), {}))
        for i, chunk in enumerate(re.split(r"\*(.+?)\*", line)):
            if not chunk:
                continue
            run = para.add_run()
            run.text = chunk
            _style(run, size, accent if i % 2 else base_colour, bold=bold, font=font)


def _est_lines(text, size_pt, width_in, bold=True):
    """Roughly how many lines `text` wraps to. Good enough to place the block
    that follows it, which is all we need it for.

    Explicit newlines count. Without that an ask written as two deliberate
    lines measured as one, and whatever sat under it was placed on top of the
    second line."""
    # 0.48 em/char, calibrated against rendered Arial Bold headlines at 38-44pt
    avg_char_in = size_pt / 72 * (0.48 if bold else 0.45)
    per_line = max(1, int(width_in / avg_char_in))
    clean = re.sub(r"\*", "", text or "")
    return max(1, sum(max(1, -(-len(seg) // per_line))
                      for seg in clean.split("\n")))


def _text_w(text, size_pt, bold=True):
    """Approximate rendered width in inches. Same 0.48 em/char calibration as
    _est_lines, which was measured against rendered Arial Bold at 38-44pt."""
    return len(re.sub(r"\*", "", text)) * size_pt / 72 * (0.48 if bold else 0.45)


def _balance(text, size_pt, width_in, bold=True):
    """Split `text` into balanced lines - PowerPoint's missing text-wrap: balance.

    PowerPoint wraps greedily, which strands single words on the last line. This
    finds the natural line count, then distributes words to minimise the longest
    line, so two-line headings break near the middle instead of leaving an
    orphan. Returns a list of lines; a single line means leave it alone.
    """
    words = text.split()
    if len(words) < 3 or _text_w(text, size_pt, bold) <= width_in:
        return [text]

    n = max(2, -(-int(_text_w(text, size_pt, bold) * 100) // int(width_in * 100)))
    for lines_wanted in (n, n + 1):
        # minimise the widest line for this many lines (small DP, short headings)
        best = None
        def walk(i, left, acc):
            nonlocal best
            if left == 1:
                rest = " ".join(words[i:])
                cand = acc + [rest]
                widest = max(_text_w(l, size_pt, bold) for l in cand)
                if widest <= width_in and (best is None or widest < best[0]):
                    best = (widest, cand)
                return
            for j in range(i + 1, len(words) - left + 2):
                chunk = " ".join(words[i:j])
                if _text_w(chunk, size_pt, bold) > width_in:
                    break
                walk(j, left - 1, acc + [chunk])
        walk(0, lines_wanted, [])
        if best:
            return best[1]
    return [text]


def _wc(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9'’\-]+", text or ""))


class DeckError(Exception):
    pass


# --------------------------------------------------------------------------
# the deck
# --------------------------------------------------------------------------

class BNIDeck:
    """A minimalist, on-brand BNI education moment deck."""

    # The closing tagline is the chapter's own, from its chapter.json - pass
    # chapter="path/to/chapter.json" or set BNI_CHAPTER. Nexus West's reads
    # "Nexus West. Keeping it ELF." with "Easy · Lucrative · Fun" beneath.
    TAGLINE = "Givers Gain."
    ELF_WORDS = ""
    VISITOR_HEADING = "If you're visiting today…"

    def __init__(self, title, kicker="3-MINUTE EDUCATION MOMENT", subtitle="",
                 presenter="", business="", notes="", font=FONT, mascot=None,
                 fmt="", chapter=None, tagline=None, tagline_words=None):
        """`fmt` is "online", "in person" or "hybrid" - chapters that alternate
        need the presenter to know before they open their mouth, because half
        the asks do not survive the wrong format.

        `chapter` is the chapter's chapter.json (or set BNI_CHAPTER): it
        supplies the closing tagline and the mascot. `tagline` and
        `tagline_words` override it for a one-off."""
        from chapter_config import deck_identity
        ident = deck_identity(chapter)
        self.TAGLINE = tagline or ident["tagline"]
        self.ELF_WORDS = tagline_words if tagline_words is not None else ident["words"]
        if mascot is None and ident["mascot"]:
            mascot = ident["mascot"]
        self.fmt = fmt
        self.font = font
        self.mascot = Path(mascot) if mascot else None
        self.prs = Presentation()
        self.prs.slide_width = Inches(SW)
        self.prs.slide_height = Inches(SH)
        self._blank = self.prs.slide_layouts[6]     # blank layout
        self._has_visitor = False
        self._has_close = False
        self._kinds = []            # archetype of each slide, in order
        self._variants = set()      # 1-based indices of alternate-format slides
        self.title_slide(title, kicker, subtitle, presenter, business, notes)

    # -- plumbing ---------------------------------------------------------

    # Words that can sit on screen before a slide stops being minimalist.
    # A contrast panel or a visitor beat legitimately carries more than a
    # statement slide, so the budget is per archetype rather than flat.
    WORD_LIMIT = {"title": 30, "statement": 28, "photo": 30, "columns": 62,
                  "contrast": 62, "visitor": 70, "action": 32, "close": 26}
    # close is 26 rather than 22 because the QR carries its own label

    def _new(self, kind, bg=WHITE, furniture=True, logo=True, variant=""):
        self._kinds.append(kind)
        s = self.prs.slides.add_slide(self._blank)
        if variant:
            self._variants.add(len(self._kinds))
        bgfill = s.background.fill
        bgfill.solid()
        bgfill.fore_color.rgb = bg
        if furniture:
            # Super Graphic — always anchored flush to the bottom-right (p17)
            s.shapes.add_picture(
                str(SG_PRIMARY), Inches(SW - SG_W), Inches(SH - SG_H),
                Inches(SG_W), Inches(SG_H))
        if logo:
            s.shapes.add_picture(
                str(LOGO_RED), Inches(LOGO_X), Inches(SH - LOGO_B - LOGO_H),
                Inches(LOGO_W), Inches(LOGO_H))
        return s

    def _tag(self, slide, text):
        """Small red marker, top-right. Used for the alternate-format slides so
        nobody presents the wrong one by accident."""
        _, tf = _txbox(slide, SW - MR - 3.2, 0.42, 3.2, 0.3)
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.RIGHT
        _style(p.add_run(), 12, RED, bold=True, font=self.font).text = text.upper()

    def _notes(self, slide, text):
        if text:
            slide.notes_slide.notes_text_frame.text = text.strip()

    def _heading(self, slide, text, y=MT, size=32, colour=BLACK, width=None):
        w = width or CW
        box, tf = _txbox(slide, ML, y, w, 1.0)
        _emphasis(tf.paragraphs[0], text, size, colour, font=self.font,
                  balance_width=w)
        return box

    # -- archetypes -------------------------------------------------------

    def title_slide(self, title, kicker="", subtitle="", presenter="",
                    business="", notes=""):
        """White field, centred BNI logo, title beneath — the p28 template."""
        s = self._new("title", logo=False)

        s.shapes.add_picture(str(LOGO_RED), Inches((SW - 3.0) / 2), Inches(1.55),
                             Inches(3.0), Inches(3.0 / 2.606))

        y = 3.28
        if kicker:
            _, tf = _txbox(s, ML, y, CW, 0.35)
            p = tf.paragraphs[0]
            p.alignment = PP_ALIGN.CENTER
            label = kicker.upper()
            if self.fmt:
                label = f"{label}  ·  {self.fmt.upper()}"
            _style(p.add_run(), 14, RED, bold=True, font=self.font).text = label
            y += 0.55

        _, tf = _txbox(s, ML, y, CW, 1.5)
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        _emphasis(p, title, 44, BLACK, font=self.font, balance_width=CW)
        y += 0.35 + 0.62 * _est_lines(title, 44, CW)

        if subtitle:
            _, tf = _txbox(s, ML, y, CW, 0.6)
            p = tf.paragraphs[0]
            p.alignment = PP_ALIGN.CENTER
            _style(p.add_run(), 20, GRANITE, font=self.font).text = subtitle

        if presenter:
            _, tf = _txbox(s, ML, 6.45, CW, 0.35)
            p = tf.paragraphs[0]
            p.alignment = PP_ALIGN.CENTER
            line = f"{presenter}  |  {business}" if business else presenter
            _style(p.add_run(), 13, GRANITE, font=self.font).text = line

        self._notes(s, notes)
        return s

    def statement(self, text, support="", notes=""):
        """One idea, big type, acres of white space. The workhorse."""
        s = self._new("statement")
        size = 40 if _wc(text) > 9 else 46
        _, tf = _txbox(s, ML, 2.1, CW, 2.4)
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        _emphasis(tf.paragraphs[0], text, size, BLACK, font=self.font,
                  balance_width=CW)
        if support:
            _, tf2 = _txbox(s, ML, 4.65, CW * 0.86, 1.0)
            _emphasis(tf2.paragraphs[0], support, 20, GRANITE, accent=GRANITE,
                      bold=False, font=self.font, balance_width=CW * 0.86)
        self._notes(s, notes)
        return s

    def photo(self, image, caption="", heading="", notes=""):
        """Full-bleed photo with the Super Graphic and a white logo — p18 Type 1."""
        s = self._new("photo", furniture=False, logo=False)
        pic = s.shapes.add_picture(str(image), 0, 0, height=Inches(SH))
        if pic.width < Inches(SW):
            pic.width = Inches(SW)
            pic.height = int(Inches(SW) * pic.image.size[1] / pic.image.size[0])
        pic.left = int((Inches(SW) - pic.width) / 2)
        pic.top = int((Inches(SH) - pic.height) / 2)

        # The text block is laid out from the BOTTOM up, stopping clear of the
        # logo. Placing it from a fixed top meant a two-line heading pushed the
        # caption straight down onto the logo, which is exactly what happened.
        scrim = bool(heading or caption)
        LOGO_TOP = SH - LOGO_B - LOGO_H          # 6.563
        FLOOR = LOGO_TOP - 0.16                  # keep clear of it

        head_lines = _est_lines(heading, 32, CW * 0.72) if heading else 0
        cap_h = 0.32 if caption else 0.0
        head_h = head_lines * 0.50
        cap_y = FLOOR - cap_h
        head_y = cap_y - (0.22 if caption else 0.0) - head_h

        # Scrim first, so the Super Graphic and logo sit on top of it. It starts
        # above whatever the text actually needs, never at a fixed height.
        if scrim:
            top = min(4.62, head_y - 0.34)
            _fill_alpha(s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, Inches(top),
                                           Inches(SW), Inches(SH - top)), BLACK, 64)

        s.shapes.add_picture(str(SG_PRIMARY), Inches(SW - SG_W), Inches(SH - SG_H),
                             Inches(SG_W), Inches(SG_H))

        # White logo top-left washes out over a bright photo, so when there is a
        # scrim it sits in it, bottom-left, where the p28 content template puts it.
        if scrim:
            s.shapes.add_picture(str(LOGO_WHITE), Inches(LOGO_X), Inches(LOGO_TOP),
                                 Inches(LOGO_W), Inches(LOGO_H))
        else:
            s.shapes.add_picture(str(LOGO_WHITE), Inches(0.55), Inches(0.5),
                                 Inches(1.5), Inches(1.5 / 2.606))

        if heading:
            _, tf = _txbox(s, ML, head_y, CW * 0.72, head_h + 0.2)
            _emphasis(tf.paragraphs[0], heading, 32, WHITE, accent=WHITE,
                      font=self.font, balance_width=CW * 0.72)
        if caption:
            _, tf = _txbox(s, ML, cap_y, CW * 0.68, cap_h + 0.12)
            _emphasis(tf.paragraphs[0], caption, 15, WHITE, accent=WHITE,
                      bold=False, font=self.font, balance_width=CW * 0.68)
        self._notes(s, notes)
        return s

    # Type and spacing per column count. Five columns is the practical ceiling
    # on a 13.3in slide before the labels start wrapping into soup - and if a
    # heading says "five", the slide has to show five, or the room notices.
    _COLS = {                 # n: (gap, icon, label pt, body pt)
        2: (0.90, 1.05, 22, 18),
        3: (0.55, 0.95, 21, 17),
        4: (0.42, 0.80, 18, 14),
        5: (0.34, 0.72, 16, 14),
    }

    def columns(self, heading, items, icons=None, notes=""):
        """2-5 columns. `items` = [(label, body), ...]. `icons` = matching PNGs.

        The heading and the column count must agree. A slide headed "five" with
        three columns on it reads as a mistake, because it is one."""
        n = len(items)
        if n not in self._COLS:
            raise DeckError(f"columns expects 2-5 items, got {n}")
        gap, icon_w, label_pt, body_pt = self._COLS[n]

        s = self._new("columns")
        self._heading(s, heading)

        col = (CW - (n - 1) * gap) / n
        top = 2.75
        for i, (label, body) in enumerate(items):
            x = ML + i * (col + gap)
            y = top
            if icons and i < len(icons) and icons[i]:
                s.shapes.add_picture(str(icons[i]), Inches(x), Inches(y),
                                     Inches(icon_w), Inches(icon_w))
                y += icon_w + 0.37
            else:
                bar = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y),
                                         Inches(0.62), Inches(0.055))
                bar.fill.solid()
                bar.fill.fore_color.rgb = RED
                bar.line.fill.background()
                bar.shadow.inherit = False
                y += 0.5

            _, tf = _txbox(s, x, y, col, 0.5)
            _style(tf.paragraphs[0].add_run(), label_pt, BLACK, bold=True,
                   font=self.font).text = label
            _, tf = _txbox(s, x, y + 0.55, col, 1.7)
            _style(tf.paragraphs[0].add_run(), body_pt, GRANITE,
                   font=self.font).text = body
        self._notes(s, notes)
        return s

    def three_up(self, heading, items, icons=None, notes=""):
        """Kept for readability where a slide really is three things."""
        return self.columns(heading, items, icons, notes)

    def contrast(self, heading, left, right, notes=""):
        """Two panels: (label, body) each. The 'this not that' slide."""
        s = self._new("contrast")
        self._heading(s, heading)

        gap = 0.7
        col = (CW - gap) / 2
        top, height = 2.45, 2.55
        for i, ((label, body), tint) in enumerate(
                zip((left, right), (LIGHT, RED))):
            x = ML + i * (col + gap)
            panel = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(top),
                                       Inches(col), Inches(height))
            panel.fill.solid()
            panel.fill.fore_color.rgb = tint
            panel.line.fill.background()
            panel.shadow.inherit = False

            fg = WHITE if i else BLACK
            body_fg = WHITE if i else GRANITE
            _, tf = _txbox(s, x + 0.45, top + 0.42, col - 0.9, 0.6)
            _style(tf.paragraphs[0].add_run(), 22, fg, bold=True,
                   font=self.font).text = label
            _, tf = _txbox(s, x + 0.45, top + 1.20, col - 0.9, 1.6)
            _style(tf.paragraphs[0].add_run(), 17, body_fg, font=self.font).text = body
        self._notes(s, notes)
        return s

    def visitor(self, body, takeaway="", heading=None, notes=""):
        """
        The visitor beat — mandatory in every deck.

        `body`     names what a visitor is actually feeling right now.
        `takeaway` is what this week's idea gives them even if they never join.
        """
        s = self._new("visitor", bg=RED, furniture=False, logo=False)
        s.shapes.add_picture(str(LOGO_WHITE), Inches(LOGO_X),
                             Inches(SH - LOGO_B - LOGO_H),
                             Inches(LOGO_W), Inches(LOGO_H))

        _, tf = _txbox(s, ML, 1.15, CW, 0.8)
        _style(tf.paragraphs[0].add_run(), 30, WHITE, bold=True,
               font=self.font).text = heading or self.VISITOR_HEADING

        _, tf = _txbox(s, ML, 2.25, CW * 0.82, 1.8)
        _emphasis(tf.paragraphs[0], body, 22, WHITE, accent=WHITE, bold=False,
                  font=self.font, balance_width=CW * 0.82)

        if takeaway:
            rule = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(ML), Inches(4.35),
                                      Inches(1.5), Inches(0.045))
            rule.fill.solid()
            rule.fill.fore_color.rgb = WHITE
            rule.line.fill.background()
            rule.shadow.inherit = False
            _, tf = _txbox(s, ML, 4.7, CW * 0.82, 1.1)
            _style(tf.paragraphs[0].add_run(), 22, WHITE, bold=True,
                   font=self.font).text = takeaway

        self._has_visitor = True
        self._notes(s, notes)
        return s

    def action(self, ask, detail="", notes="", variant=""):
        """One specific thing to do this week. Never vague, never plural.

        `variant` marks this as the alternate-format version of the previous
        slide - "if online", "if in person". It shares that slide's time slot,
        so it is excluded from the timing sequence check, and it carries a red
        tag so nobody presents both."""
        s = self._new("action", variant=variant)
        if variant:
            self._tag(s, variant)
        _, tf = _txbox(s, ML, 2.05, CW, 0.4)
        _style(tf.paragraphs[0].add_run(), 14, RED, bold=True,
               font=self.font).text = "THIS WEEK"

        _, tf = _txbox(s, ML, 2.80, CW * 0.88, 2.0)
        _emphasis(tf.paragraphs[0], ask, 38, BLACK, font=self.font,
                  balance_width=CW * 0.88)

        if detail:
            y = 2.80 + 0.58 * _est_lines(ask, 38, CW * 0.88) + 0.55
            _, tf = _txbox(s, ML, y, CW * 0.8, 1.0)
            _emphasis(tf.paragraphs[0], detail, 19, GRANITE, accent=GRANITE,
                      bold=False, font=self.font, balance_width=CW * 0.8)
        self._notes(s, notes)
        return s

    def elf_close(self, action="", notes="", qr_url="", qr_label="This week's hour"):
        """The consistent sign-off: the ask, then the chapter's tagline.

        `qr_url` puts a QR on the right, balancing the mascot on the left. Point
        it at the Spotify playlist: the playlist holds the coming week's hour
        from Thursday morning, so a scan in the room on Tuesday returns that
        morning's episodes."""
        s = self._new("close", furniture=False, logo=False)
        s.shapes.add_picture(str(SG_PRIMARY), Inches(SW - SG_W), Inches(SH - SG_H),
                             Inches(SG_W), Inches(SG_H))
        s.shapes.add_picture(str(LOGO_RED), Inches((SW - 2.6) / 2), Inches(1.75),
                             Inches(2.6), Inches(2.6 / 2.606))

        if action:
            _, tf = _txbox(s, ML, 3.15, CW, 0.5)
            p = tf.paragraphs[0]
            p.alignment = PP_ALIGN.CENTER
            _style(p.add_run(), 19, GRANITE, font=self.font).text = action

        # The tagline has to live in the corridor between the mascot on the
        # left and the QR on the right, not across the full width - at 44pt a
        # chapter-length tagline runs straight under the QR code. Work out the
        # clear span, then step the size down until it fits on one line.
        MASCOT_X, MASCOT_W = 1.05, 1.35
        QR_SIZE = 1.45
        QR_X = SW - MR - QR_SIZE - 0.55
        GAP = 0.35
        left = (MASCOT_X + MASCOT_W + GAP) if (self.mascot and self.mascot.exists()) else ML
        right = (QR_X - GAP) if qr_url else (SW - MR)
        span = right - left

        # _text_w runs a few per cent narrow against real Arial Bold, so leave
        # headroom rather than trusting it to the inch. And turn wrapping off:
        # if the estimate is still optimistic the tagline overhangs slightly,
        # which looks like nothing, where wrapping drops a second line straight
        # onto "Easy - Lucrative - Fun".
        size = 44
        while size > 28 and _text_w(self.TAGLINE, size) > span * 0.90:
            size -= 2

        box, tf = _txbox(s, left, 3.95, span, 0.9)
        tf.word_wrap = False
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        _style(p.add_run(), size, BLACK, bold=True, font=self.font).text = self.TAGLINE

        _, tf = _txbox(s, ML, 5.0, CW, 0.45)
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        if self.ELF_WORDS:
            _style(p.add_run(), 17, RED, bold=True, font=self.font).text = self.ELF_WORDS

        if self.mascot and self.mascot.exists():
            s.shapes.add_picture(str(self.mascot), Inches(1.05), Inches(4.45),
                                 Inches(1.35), Inches(1.35))

        if qr_url:
            from qr import qr as _qr
            size = 1.45
            x = SW - MR - size - 0.55       # clear of the Super Graphic
            s.shapes.add_picture(str(_qr(qr_url)), Inches(x), Inches(4.20),
                                 Inches(size), Inches(size))
            _, tf = _txbox(s, x - 0.5, 4.20 + size + 0.10, size + 1.0, 0.3)
            pp = tf.paragraphs[0]
            pp.alignment = PP_ALIGN.CENTER
            _style(pp.add_run(), 11, GRANITE, font=self.font).text = qr_label

        self._has_close = True
        self._notes(s, notes)
        return s

    # -- output -----------------------------------------------------------

    def timings(self):
        """Parse the [m:ss-m:ss] marker at the top of each slide's notes.

        These are speaker notes, not a script, so counting words tells you
        nothing about how long the moment runs - the presenter speaks around the
        prompts in their own words. The declared timings are the honest measure,
        so they are what gets checked: contiguous, no gaps, ending near three
        minutes."""
        out = []
        for i, s in enumerate(self.prs.slides, 1):
            text = s.notes_slide.notes_text_frame.text if s.has_notes_slide else ""
            m = re.search(r"\[(\d+):(\d{2})\s*[-–]\s*(\d+):(\d{2})\]", text)
            if not m:
                out.append((i, None, None))
                continue
            out.append((i,
                        int(m.group(1)) * 60 + int(m.group(2)),
                        int(m.group(3)) * 60 + int(m.group(4))))
        return out

    def runs_for(self):
        """Total declared running time in seconds, 0 if the notes aren't marked."""
        ends = [t[2] for t in self.timings() if t[2] is not None]
        return max(ends) if ends else 0

    def notes_words(self, slide):
        """Words in one slide's notes, ignoring [cues] and the timing marker."""
        if not slide.has_notes_slide:
            return 0
        return _wc(re.sub(r"\[[^\]]*\]", " ", slide.notes_slide.notes_text_frame.text))

    def check(self, strict=True):
        """Returns a list of problems. Raises on the fatal ones when strict."""
        problems, warnings = [], []
        if not self._has_visitor:
            problems.append("no visitor slide - every education moment must have one")
        if not self._has_close:
            problems.append("no ELF close - every deck must end on the tagline")

        n = len(self.prs.slides)
        if n > 8:
            warnings.append(f"{n} slides - 3 minutes rarely supports more than 7")

        # Timing: the markers must be contiguous and land near three minutes.
        marks = self.timings()
        unmarked = [i for i, a, b in marks
                    if a is None and i not in self._variants]
        if unmarked:
            warnings.append(f"slide(s) {unmarked} have no [m:ss-m:ss] timing marker")
        seq = [(i, a, b) for i, a, b in marks
               if a is not None and i not in self._variants]
        prev_end = 0
        for i, a, b in seq:
            if a != prev_end:
                warnings.append(
                    f"slide {i} starts at {a // 60}:{a % 60:02d} but the previous "
                    f"slide ends at {prev_end // 60}:{prev_end % 60:02d}")
            if b <= a:
                warnings.append(f"slide {i} has a timing marker that does not advance")
            prev_end = b
        if prev_end and not 165 <= prev_end <= 195:
            warnings.append(
                f"runs {prev_end // 60}:{prev_end % 60:02d}; a 3-minute slot wants "
                f"2:45-3:15")

        # Notes should prompt, not script. Total words is the wrong measure - a
        # 40-second beat legitimately needs more prompts than a 15-second one.
        # What actually makes notes unreadable at 6:45am is too many lines, or a
        # line so long the presenter reads it aloud instead of glancing at it.
        for i, slide in enumerate(self.prs.slides, 1):
            if not slide.has_notes_slide:
                continue
            text = slide.notes_slide.notes_text_frame.text
            bullets = [ln.strip(" -•\t") for ln in text.splitlines()
                       if ln.strip().startswith(("-", "•"))]
            if len(bullets) > 7:
                warnings.append(f"slide {i}: {len(bullets)} prompts - more than 7 "
                                f"is hard to glance at, split or cut")
            for b in bullets:
                n_words = _wc(re.sub(r"\[[^\]]*\]", " ", b))
                if n_words > 18:
                    warnings.append(
                        f"slide {i}: a {n_words}-word prompt reads as a sentence to "
                        f"recite - shorten it: \"{b[:46]}...\"")
                    break

        for i, (slide, kind) in enumerate(zip(self.prs.slides, self._kinds), 1):
            on_slide = sum(_wc(sh.text_frame.text) for sh in slide.shapes
                           if sh.has_text_frame)
            limit = self.WORD_LIMIT.get(kind, 45)
            if on_slide > limit:
                warnings.append(f"slide {i} ({kind}): {on_slide} words on screen, "
                                f"limit {limit} - trim it")

        if strict and problems:
            raise DeckError("; ".join(problems))
        return problems + warnings

    def save(self, path, strict=True):
        issues = self.check(strict=strict)
        for i in issues:
            print(f"  ! {i}")
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.prs.save(str(path))
        secs = self.runs_for()
        notes = sum(self.notes_words(s) for s in self.prs.slides)
        print(f"  -> {path}  ({len(self.prs.slides)} slides, "
              f"runs {secs // 60}:{secs % 60:02d}, {notes} words of notes)")
        return path
