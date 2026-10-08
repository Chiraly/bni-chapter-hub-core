---
name: bni-education-program
description: Build a BNI chapter's Networking Education Moment program — a term-long plan driven by the chapter's own Traffic Lights gaps, plus on-brand PowerPoint decks, speaker notes, a verified CEU podcast hour per week, and a member dashboard. Use whenever someone asks for a BNI education moment, education moments, a chapter education plan or roster, an Education Coordinator program, a networking education segment, a 3-minute education moment, CEU podcast picks for a chapter, or a BNI education dashboard. Also trigger on "education moment for [topic]", "what should we teach the chapter", "our visitor conversion is low, what education moment", "BNI education roster", "CEU hour", or any mention of the Chapter Traffic Lights / Power of One report in a training context. Australian BNI chapters are the default context. Do NOT use for BNI weekly presentations (60-second infomercials), Feature Presentations, or general business training that is not BNI.
---

# BNI Education Moment Program

Builds and runs a chapter's Networking Education Moment program end to end.

**Source:** the `bni-chapter-hub-core` repo (Hilary Chapman, Seddon Digital), shared by
every chapter that runs a BNI Chapter Hub. Installed as the `bni-chapter-hub` plugin.

---

## First: which chapter?

Everything chapter-specific (name, meeting day and time, venue, Zoom, tagline,
mascot, colours, sheet and folder IDs) lives in **that chapter's `chapter.json`**,
in its chapter repo. Never hard-code a chapter's details into a deck, a script or
a template.

Before building anything, find the chapter's `chapter.json`: ask for the chapter
repo folder if it isn't the working directory. Then either pass `--chapter
path/to/chapter.json` to the scripts or set `BNI_CHAPTER` to that path for the
session. A chapter with no hub yet can still get decks: the scripts fall back to
BNI's own "Givers Gain." tagline. Offer to set up a `chapter.json` from the
starter (see `docs/SETUP-GUIDE.md` in the core repo).

---

## What this is for

The Education Coordinator must deliver a 3–5 minute Networking Education Moment at
*every* weekly meeting, planned a month ahead, aimed at the chapter's actual gaps
(Chapter Operations Manual p78). This skill turns "our visitor conversion is 8%" into
a term of dated topics, decks, scripts, presenters and CEU listening.

Two non-negotiables, because they are what makes these decks different:

1. **Every deck has a visitor beat.** A slide that speaks directly to visitors, names
   what they are actually feeling, and gives them something they can use whether or
   not they ever join.
2. **Every deck ends the same way.** A specific action for this week, then the
   chapter's own tagline, `chapter.tagline` in its chapter.json (for Nexus West:
   **Nexus West. Keeping it ELF.**, *Easy · Lucrative · Fun*).

`scripts/bni_deck.py` refuses to save a deck missing either one.

---

## Workflow

### Phase 1 — Diagnose

Ask for the chapter's **Chapter Traffic Lights** and **Member Traffic Lights (Power of
One)** reports. Accept a pasted table, CSV, PDF or screenshot. If they aren't available,
run the interview in `references/diagnostics.md` instead — do not guess.

Also establish: chapter name, size, number of weeks, term start date, season, how many
members joined in the last 3 months, and anything the President has flagged.

Read `references/diagnostics.md`. Produce a **gap analysis**: which metrics are red or
amber, what that means behaviourally, and which gaps the education program can actually
move. Be honest about the ones it can't.

### Phase 2 — Set goals

Read `references/program-design.md`. Write 2–4 training goals, each with a measurable
outcome, a target date and the report it will be read from. Ask the user to confirm
before building — the goals shape every week that follows.

### Phase 3 — Plan the term

Choose topics from the topic banks, weighted by the gap analysis and shaped by the
Australian calendar (EOFY, Christmas, the January restart, school terms). Produce
`Education-Program-Plan.md`: week number, date, topic, the one thing, which gap it
serves, and a suggested presenter type.

Topic banks, loaded as needed:
- `references/topics-growth.md` — visitors, invitations, conversion, chapter growth
- `references/topics-referrals.md` — referrals vs leads, asks, weekly presentations, TYFCB
- `references/topics-engagement.md` — attendance, one-to-ones, retention, CEUs
- `references/topics-core-seasonal.md` — core values, Givers Gain, seasonal moments

### Phase 4 — Build each week

Read `references/education-moment-method.md` before writing a single word, then for
each week produce:

| File | What it is |
|---|---|
| `<slug>.pptx` | 5–7 slides, built with `scripts/bni_deck.py` |
| `<slug>-Speaking-Notes.docx` | prompts and beats, timing markers, delivery cues |
| `<slug>-CEU-Hour.md` | ~60 min of verified podcast, matched to the topic |

**There is no separate presenter brief.** Seven of the eight things a brief would
carry are already in the speaker notes - the one thing, the story prompts, the
visitor beat, the ask, the close, what to prepare, what to cut. Run
`export_notes.py --context weeks.json` and the rest folds into the header: the
week, the date, the meeting format, and why the topic is in the program. One
document per week, because two would need keeping in sync and nobody reads two
at quarter to seven in the morning.

Imagery: read `references/imagery.md` and follow the ladder. Photos of people come
from the official library — never generate them.

CEU: read `references/ceu-podcasts.md`. **Never invent an episode number, title or
duration.** Use `scripts/build_ceu_library.py --hour <terms>`.

### Phase 5 — The members' site

The site is the chapter's BNI Chapter Hub. It's built from the chapter repo, not
from here:

- **New moments** go into the chapter repo's `moments.json` (start from this
  skill's `library/moments.json` if the chapter has none). Same shape as the
  library entries: `title`, `one`, `gap`, `ceuSecs`, `eps`, `files` (the week's
  Drive folder). Add the dates and presenters to the **roster sheet**, not to
  `moments.json`.
- **Commit** the chapter repo and Netlify rebuilds the site. To preview first:
  `CORE_DIR=<core repo> BUILD_FLAGS=--no-snapshot bash build.sh` in the chapter repo.
- Settings and customisation: `docs/CHAPTER-CONFIG.md` and `docs/CUSTOMISING.md`
  in the core repo. The automations (reminders, playlist, trade sheet) are set up
  per `templates/REMINDERS-SETUP.md`, `SPOTIFY-SETUP.md`, `TRADESHEET.md`.

For a one-off Artifact preview of the education page:
`scripts/build_dashboard.py --chapter chapter.json --out dash.html --target artifact`.
Read `references/dashboard.md` for how the page is meant to behave.

---

## Always verify by looking

python-pptx will happily write a deck with text running off the slide. Render and look
at every deck before calling it done:

```bash
pwsh scripts/render_preview.ps1 -Pptx out.pptx -OutDir preview
python scripts/contact_sheet.py preview sheet.png
```

Then read `sheet.png`. Check: Super Graphic bottom-right on every white slide, logo
placed, only brand colours, nothing overflowing, no slide over its word budget.

`deck.save()` prints warnings for script length and on-slide word count. Do not ignore
them — a 3-minute slot is 3 minutes.

---

## Scripts

| Script | Purpose |
|---|---|
| `bni_deck.py` | the deck builder — 8 archetypes, brand geometry, validation |
| `render_preview.ps1` | .pptx → PNGs via PowerPoint COM, for visual QA |
| `contact_sheet.py` | tile those PNGs into one image to look at |
| `icon.py` | Lucide SVG → BNI-red transparent PNG |
| `build_ceu_library.py` | refresh the podcast library; search; build a CEU hour |
| `build_dashboard.py` | render the members' site from a chapter.json (Netlify or Artifact) |
| `chapter_config.py` | load and validate a chapter.json over the core defaults |
| `spotify_auth.py` | one-time: get a Spotify refresh token for playlist automation |
| `export_notes.py` | pull speaker notes out of a deck into a printable script |
| `build_photo_cache.py` | one-time: unpack and downscale the official photo album |
| `write_photo_index.py` | merge captions into the photo manifest |

## House rules

- **Australian English and Australian context.** "Organise", "recognise", "one-to-one".
  Money in AUD. EOFY is 30 June. Don't say "fall" or "Main Street".
- **3 minutes is 3 minutes** — 380–470 spoken words. Anything longer steals from the
  meeting and the President will have to cut you off.
- **One idea per moment.** If it needs two ideas, it is two weeks.
- Written for a **nervous member**, not a trainer. Short sentences, plain words,
  a story they can actually tell.
- Never invent BNI statistics, policies or podcast episodes. Cite the source or leave
  it out. Global BNI stats change — look them up.
- The mascot is **internal chapter education material only** (Brand Standards p12).

## Before delivering

If the `ai-writing-signs` skill is available, run its self-check after this skill's own checklist. It works on the habits that make copy read as machine output: generic in place of specific, analysis tails, borrowed authority, promotional drift, contrast theatre, and formatting in place of thought. Fix the habit underneath; swapping synonyms only hides it.
