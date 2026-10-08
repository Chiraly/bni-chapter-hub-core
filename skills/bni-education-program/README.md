# bni-education-program

Builds a BNI chapter's Networking Education Moment program: a term of dated topics
driven by the chapter's own Traffic Lights gaps, on-brand PowerPoint decks with speaking
notes, a verified CEU podcast hour per week, and a member dashboard.

**Say something like:** *"Build the education program for BNI Riverside — 12 weeks
starting 10 February, here's our Traffic Lights report."*

---

## Where it lives

In the `bni-chapter-hub-core` repo, shared by every chapter running a BNI Chapter
Hub, and installed as the `bni-chapter-hub` Claude Code plugin. Each chapter's own
details come from its `chapter.json`. See `docs/CLAUDE-SKILL.md` in the core repo.

## Requirements

Python 3.10+ with `python-pptx`, `Pillow`, `python-docx` and `PyMuPDF`
(`pip install python-pptx Pillow python-docx PyMuPDF`).
PowerPoint is needed only for rendering slide previews (`render_preview.ps1`), which is
part of the QA step. No npm, no API keys.

Recraft and web access are optional. The skill works without either.

## One-time setup on a new machine

```bash
python scripts/build_photo_cache.py    # unpack + downscale the 594 MB photo album
python scripts/write_photo_index.py    # merge captions into the index
python scripts/icon.py --starter       # fetch the Lucide icon set
python scripts/build_ceu_library.py --refresh
```

Set `BNI_PHOTO_LIBRARY` to where the photo cache should live (a shared drive
folder is best, so it only needs building once for everyone).

## Where the work lands

```
<the chapter's education Drive folder>\Programs\<Chapter> - <Term>\
  Education-Program-Plan.md
  Week-01-<slug>\  <slug>.pptx  -Speaking-Notes.md  -Presenter-Brief.md  -CEU-Hour.md
  ...
  dashboard.html          (published as an Artifact)
```

## The two things that are never optional

Every deck has a **visitor beat** and ends on **the chapter's tagline** (from its
chapter.json). `bni_deck.py` refuses to save one that doesn't.

## Sources

Built from BNI's own material, all in this folder:
the *Brand Standards Manual*, the *Chapter Operations Manual 2026 (BNI Australia)*, the
*Creating Education Moments* Leadership Team Training participant guide, and
*Create a Great Networking Education Moment*.

Podcast data comes from the Official BNI Podcast's public RSS feed. Icons are Lucide
(ISC). The mascot is hand-drawn for internal chapter education use only — the Brand
Standards Manual (p12) does not permit derivative BNI branding in public-facing
material.
