# Using Claude to build the education program

The `bni-education-program` skill turns "our visitor conversion is 8%" into a
term of dated education moments: on-brand decks, speaking notes for a nervous
presenter, and a verified hour of BNI podcast per week for the CEU. It's what
built Nexus West's program.

It runs in **Claude Code** (the desktop app's Code tab, or the `claude` command in
a terminal). It needs to run Python to build decks, so it won't work in plain
chat on claude.ai.

## Install it (once)

In Claude Code, type:

```
/plugin marketplace add Chiraly/bni-chapter-hub-core
/plugin install bni-chapter-hub@bni-chapter-hub
```

To pick up improvements later:

```
/plugin marketplace update bni-chapter-hub
```

The scripts need Python 3.10+ and a few packages:

```bash
pip install python-pptx Pillow python-docx PyMuPDF
```

Slide previews (the "look at every deck" check) use PowerPoint on Windows. On a
Mac or without PowerPoint, open the decks and look at them yourself.

## Tell it which chapter

Open Claude Code **in your chapter repo folder** (the one with `chapter.json`).
The skill reads your chapter's name, tagline, mascot, meeting day, deadline and
playlist from there, so every deck and email is yours. If you work from another
folder, tell Claude where your `chapter.json` is.

## Things to ask

**Plan a term**

> Build the education program for BNI Business by the Sea: 12 weeks from Friday
> 6 February. Here's our Traffic Lights report. *(attach the PDF or paste it)*

It reads the red and amber metrics, proposes 2–4 training goals and asks you to
confirm them, then plans the term against those gaps and the Australian calendar.

**Build one week**

> Build week 4: "A Referral Is Not a Lead". Lisa is presenting, and it's hybrid.

You get the `.pptx`, a speaking-notes `.docx` and the CEU hour. Every deck has a
visitor slide and ends on your tagline; the deck builder refuses to save one that
doesn't.

**Without a Traffic Lights report**

> We don't have the Traffic Lights yet. What should we teach this term?

It runs a short interview instead of guessing.

**Add a moment to the site**

> Add this week's moment to our site library and commit it.

It adds the entry to your chapter repo's `moments.json`. Then put the date and
presenter in the roster sheet.

**Refresh the podcast data**

> Refresh the CEU podcast library and check next term's hours still add up.

## Rules it keeps (so you can hold it to them)

- Three minutes is three minutes, about 380–470 spoken words.
- One idea per moment.
- Written for a nervous member, not a trainer.
- Australian English, Australian calendar (EOFY, Christmas, the January restart).
- **Never invents** a BNI statistic, policy or podcast episode. Episode numbers and
  durations come from the podcast's own feed.
- Photos of people come only from BNI's official photo library.

## Where things land

Put the term's files in your chapter's education folder in Drive, one folder
per week. Link each week's folder in `moments.json` (the `files` field), and the
Education page and the reminder emails link presenters straight to their slides.
