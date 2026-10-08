"""
export_notes.py — pull the speaker notes out of a deck into a Word document.

Notes live in the .pptx so the presenter sees them in Presenter View. This writes
the same notes to .docx so they can be printed, emailed, or opened on a phone by
someone who has never heard of markdown - which is everyone in a chapter.

    python export_notes.py deck.pptx              # -> deck-Speaking-Notes.docx
    python export_notes.py deck.pptx --context weeks.json    # adds the header block
    python export_notes.py deck.pptx --md         # also write a .md alongside
    python export_notes.py deck.pptx --out x.docx

These are prompts, not a script. The running time comes from the declared
[m:ss-m:ss] markers, not from counting words.

There is deliberately no separate presenter brief. Seven of the eight things a
brief would say are already here - the one thing, the story prompts, the visitor
beat, the ask, the close, what to prepare, what to cut. Two documents would mean
two things to keep in sync and two things to read at quarter to seven in the
morning. `--context` folds in the rest: the format, the date, and why this week
is in the program at all.
"""
import argparse
import json
import re
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, RGBColor
from pptx import Presentation

# The chapter's closing line, from --chapter or BNI_CHAPTER. Set in main().
TAGLINE = "Givers Gain."

RED = RGBColor(0xCF, 0x20, 0x30)
GRANITE = RGBColor(0x64, 0x66, 0x6A)
BLACK = RGBColor(0x00, 0x00, 0x00)
FONT = "Arial"                      # the BNI brand's own sanctioned substitute


def slide_headline(slide):
    """The biggest run of text on the slide - close enough to a heading."""
    best, size = "", -1
    for sh in slide.shapes:
        if not sh.has_text_frame or not sh.text_frame.text.strip():
            continue
        for p in sh.text_frame.paragraphs:
            for r in p.runs:
                pt = r.font.size.pt if r.font.size else 0
                if pt > size and r.text.strip():
                    best, size = sh.text_frame.text.strip(), pt
    return re.sub(r"\s+", " ", best)


def parse_notes(text):
    """Split one slide's notes into (timing, beat, bullets, cues)."""
    timing, beat, bullets, cues = "", "", [], []
    for line in text.splitlines():
        ln = line.strip()
        if not ln:
            continue
        m = re.fullmatch(r"\[(\d+:\d{2})\s*[-–]\s*(\d+:\d{2})\]", ln)
        if m:
            timing = f"{m.group(1)}–{m.group(2)}"
        elif ln.upper().startswith("BEAT"):
            beat = ln.split("-", 1)[-1].strip() if "-" in ln else ln
        elif ln.startswith(("-", "•")):
            bullets.append(ln.lstrip("-• ").strip())
        elif ln.startswith("[") and ln.endswith("]"):
            cues.append(ln.strip("[]"))
        else:
            bullets.append(ln)
    return timing, beat, bullets, cues


def _run(p, text, size=11, bold=False, italic=False, colour=BLACK):
    r = p.add_run(text)
    r.font.name = FONT
    r.font.size = Pt(size)
    r.bold = bold
    r.italic = italic
    r.font.color.rgb = colour
    return r


def context_for(pptx_path, context_file):
    """Look up this week in the program data, by the Week-NN- folder name."""
    if not context_file:
        return None
    m = re.search(r"Week-(\d+)", str(pptx_path))
    if not m:
        return None
    n = int(m.group(1))
    weeks = json.loads(Path(context_file).read_text(encoding="utf-8"))
    return next((w for w in weeks if w.get("n") == n), None)


def build_docx(prs, title, runtime, out, ctx=None):
    doc = Document()
    for s in doc.styles:
        try:
            s.font.name = FONT
        except Exception:
            pass

    st = doc.sections[0]
    st.top_margin = st.bottom_margin = Pt(48)
    st.left_margin = st.right_margin = Pt(54)

    p = doc.add_paragraph()
    _run(p, title, size=22, bold=True)
    p = doc.add_paragraph()
    line = f"Speaker notes  ·  {len(prs.slides)} slides  ·  runs {runtime // 60}:{runtime % 60:02d}"
    if ctx:
        when = ctx.get("date", "")
        if when:
            from datetime import date
            y, mo, d = (int(x) for x in when.split("-"))
            when = date(y, mo, d).strftime("%a %d %B")
        bits = [b for b in (f"Week {ctx['n']}", when, ctx.get("fmt", "")) if b]
        line = "  ·  ".join(bits) + "\n" + line
    _run(p, line, size=11, bold=True, colour=RED)

    if ctx:
        p = doc.add_paragraph()
        _run(p, "The one thing.  ", size=11, bold=True)
        _run(p, ctx.get("one", ""), size=11)
        if ctx.get("gap"):
            p = doc.add_paragraph()
            _run(p, "Why this week.  ", size=11, bold=True)
            _run(p, f"It is in the program to shift {ctx['gap'].lower()}.",
                 size=11)

    p = doc.add_paragraph()
    _run(p, "These are speaker notes, not a script. Say it in your own words — "
            "the prompts are the shape, not the sentences. ", size=10, colour=GRANITE)
    _run(p, "SAY:", size=10, bold=True, colour=GRANITE)
    _run(p, " marks the few lines worth keeping word for word. Anything in square "
            "brackets is a cue, not something you say out loud.", size=10,
         colour=GRANITE)

    for i, slide in enumerate(prs.slides, 1):
        text = (slide.notes_slide.notes_text_frame.text.strip()
                if slide.has_notes_slide else "")
        timing, beat, bullets, cues = parse_notes(text)
        head = slide_headline(slide) or "(no text on slide)"

        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(16)
        p.paragraph_format.space_after = Pt(2)
        _run(p, f"Slide {i}", size=9, bold=True, colour=RED)
        if timing:
            _run(p, f"   {timing}", size=9, bold=True, colour=GRANITE)

        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(4)
        _run(p, head, size=13, bold=True)

        if beat:
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(6)
            _run(p, beat, size=10, italic=True, colour=GRANITE)

        for b in bullets:
            p = doc.add_paragraph(style="List Bullet")
            p.paragraph_format.space_after = Pt(2)
            # keep SAY: and YOUR: prompts visually distinct
            m = re.match(r"(SAY:|YOUR [^:]*:)\s*(.*)", b)
            if m:
                _run(p, m.group(1) + " ", size=11, bold=True, colour=RED)
                _run(p, m.group(2), size=11)
            else:
                _run(p, b, size=11)

        for c in cues:
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Pt(18)
            p.paragraph_format.space_after = Pt(2)
            _run(p, f"[{c}]", size=10, italic=True, colour=RED)

    doc.add_page_break()
    p = doc.add_paragraph()
    _run(p, "Before you present", size=14, bold=True)
    for line in [
        "Talk it through once out loud, timed. If you run over, cut a slide.",
        "Bring your own examples. Prompts marked YOUR are the ones to make yours.",
        "The visitor slide matters most. Slow down and look at them.",
        f"Finish on the tagline the same way every week: {TAGLINE}",
        "If the meeting is running late, cut a middle slide. Never cut the visitor beat.",
        "No visitors this morning? Run the visitor slide anyway - the habit is being "
        "taught to the room, not performed for guests.",
        "Nerves are normal. It is three minutes, the room is on your side, and every "
        "person listening has done it. Reading straight from these prompts is fine.",
    ]:
        p = doc.add_paragraph(style="List Bullet")
        p.paragraph_format.space_after = Pt(3)
        _run(p, line, size=11)

    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(18)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _run(p, TAGLINE, size=12, bold=True)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _run(p, "Easy  ·  Lucrative  ·  Fun", size=9, bold=True, colour=RED)

    doc.save(str(out))


def build_md(prs, title, runtime, out):
    lines = [f"# {title} — speaker notes", "",
             f"**{len(prs.slides)} slides · runs {runtime // 60}:{runtime % 60:02d}**",
             "", "These are speaker notes, not a script. Say it in your own words.",
             "", "---", ""]
    for i, slide in enumerate(prs.slides, 1):
        notes = (slide.notes_slide.notes_text_frame.text.strip()
                 if slide.has_notes_slide else "")
        lines += [f"## Slide {i} — {slide_headline(slide) or '(no text)'}", "",
                  notes or "_(no notes)_", ""]
    out.write_text("\n".join(lines), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pptx")
    ap.add_argument("--out")
    ap.add_argument("--md", action="store_true", help="also write a .md alongside")
    ap.add_argument("--context", help="weeks.json, for the format/date/why header")
    ap.add_argument("--chapter", help="the chapter's chapter.json (or set BNI_CHAPTER)")
    a = ap.parse_args()

    global TAGLINE
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from chapter_config import deck_identity
    TAGLINE = deck_identity(a.chapter)["tagline"]

    src = Path(a.pptx)
    out = Path(a.out) if a.out else src.with_name(src.stem + "-Speaking-Notes.docx")
    prs = Presentation(str(src))
    title = slide_headline(prs.slides[0]) if len(prs.slides) else src.stem

    runtime = 0
    for slide in prs.slides:
        if not slide.has_notes_slide:
            continue
        m = re.search(r"\[(\d+):(\d{2})\s*[-–]\s*(\d+):(\d{2})\]",
                      slide.notes_slide.notes_text_frame.text)
        if m:
            runtime = max(runtime, int(m.group(3)) * 60 + int(m.group(4)))

    build_docx(prs, title, runtime, out, context_for(src, a.context))
    print(f"-> {out}  (runs {runtime // 60}:{runtime % 60:02d})")
    if a.md:
        md = out.with_suffix(".md")
        build_md(prs, title, runtime, md)
        print(f"-> {md}")


if __name__ == "__main__":
    main()
