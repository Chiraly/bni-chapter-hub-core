"""build_blank_template.py - an empty, on-brand deck for a member to fill in.

The program supplies a finished deck for every week, but members write their
own moments too, and a blank BNI-branded 16:9 deck with the structure already
in it is the difference between "I'll have a go" and "I wouldn't know where to
start".

Every slide carries placeholder copy that says what belongs there and roughly
how much of it, plus speaker notes with the timing marker for that beat. The
placeholders are deliberately written as instructions rather than lorem ipsum,
so a half-finished deck still reads as half-finished rather than as nonsense.

The visitor beat and the ELF close are already in place, because bni_deck.py
refuses to save a deck without them - and because they are the two things
people leave out.

    python build_blank_template.py --out "Blank-Education-Moment-Template.pptx"
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bni_deck import BNIDeck                                   # noqa: E402

# Set from the chapter's chapter.json in main(). The deadline is the
# chapter's, not BNI's: one deck is built for the whole meeting, so a late
# file means it does not go in.
PLAYLIST = ""
DEADLINE = ("Send the finished .pptx to the Vice President by 12pm on the "
            "day the meeting deck is built.")
CHAPTER = None


def build(out: Path):
    d = BNIDeck(
        title="Your Title Goes Here",
        subtitle="One line that says what the idea is",
        chapter=CHAPTER,        # tagline and mascot
        notes="\n".join([
            "[0:00-0:15]",
            "BEAT - set up. Open with a question they answer in their own head.",
            "- Replace every placeholder in this deck, then delete nothing else",
            "- Keep one idea per slide. If a slide needs two, it needs to be two",
            f"- {DEADLINE}",
            "- These notes are the shape of the talk. Write your own words over them",
        ]),
    )

    d.statement(
        "The one sentence you want\nthe room to remember.",
        support="Say the idea plainly, then stop. This is the slide people "
                "will quote back at you.",
        notes="\n".join([
            "[0:15-0:55]",
            "BEAT - the hook. Why this matters, before any how.",
            "- Say the idea in one sentence",
            "- YOUR example: the moment you learned this, or saw it work",
            "- [pause] Let it land before you move on",
            "- Land it: name the cost of not doing it",
        ]),
    )

    d.contrast(
        "Two ways to do the same thing",
        left=("The common way",
              "What most people do, and why it quietly does not work. "
              "Be specific - a real habit, not a straw man."),
        right=("The better way",
               "What to do instead. It has to be something they could "
               "genuinely do this week."),
        notes="\n".join([
            "[0:55-1:35]",
            "BEAT - the contrast. Same effort, different result.",
            "- Walk both panels. Do not read them out",
            "- The first is what they are doing now. Say it without judgement",
            "- [pause] Ask: which one sounds like your last month?",
            "- Land it: the difference is the habit, not the effort",
        ]),
    )

    d.columns(
        "Three things that make it work",
        [("First", "A short label, then one line. Twelve words is plenty."),
         ("Second", "If you only have two, use two - the heading must match "
                    "the count."),
         ("Third", "Up to five columns fit, but three is almost always right.")],
        notes="\n".join([
            "[1:35-2:10]",
            "BEAT - make it usable. Three things, said plainly.",
            "- Roughly a line each. Do not elaborate on all three",
            "- Pick one to give an example for. Leave the others bare",
            "- Land it: they should be able to repeat these back",
        ]),
    )

    d.visitor(
        "Name the thing a visitor is actually feeling right now, before you "
        "tell them anything. They gave up a Tuesday morning on somebody's "
        "invitation and they are working out whether this room is for them.",
        takeaway="Then give them the one thing this idea is worth to them this "
                 "week, whatever they decide about BNI.",
        notes="\n".join([
            "[2:10-2:35]",
            "BEAT - the visitor beat. The 25 seconds that matter most.",
            "[stop. look at the visitors, not the members. slow right down.]",
            "- Say what they are feeling before you say anything useful",
            "- Give them something they can use today",
            "- No visitors this morning? Run it anyway - you are teaching the room",
        ]),
    )

    d.action(
        "One specific thing to do\nthis week.",
        detail="Never vague, never plural. A member should be able to do it "
               "before Friday and know whether they did.",
        notes="\n".join([
            "[2:35-2:50]",
            "BEAT - one ask.",
            "- SAY: the ask, in one sentence, word for word",
            "- Make it small enough that nobody has an excuse",
            "- [pause] If it cannot be done by Friday, it is the wrong ask",
        ]),
    )

    d.elf_close(
        action="Repeat the ask here, in the same words.",
        qr_url=PLAYLIST,
        qr_label="Chapter playlist",
        notes="\n".join([
            "[2:50-3:00]",
            "BEAT - close. Same words every week, so the room learns to say it back.",
            "- One line that ties the idea to the ask",
            "- Point at the QR: that is the chapter Spotify playlist, this week's hour",
            f"- SAY: {d.TAGLINE}",
            "- Thanks everyone.",
        ]),
    )

    out.parent.mkdir(parents=True, exist_ok=True)
    # strict=False: the placeholders run slightly over the word budgets on
    # purpose, because they are instructions. A real deck should pass strict.
    d.save(out, strict=False)          # save() prints the path and the timings


def main():
    global PLAYLIST, DEADLINE, CHAPTER
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="Blank-Education-Moment-Template.pptx")
    ap.add_argument("--chapter", help="the chapter's chapter.json (or set BNI_CHAPTER)")
    a = ap.parse_args()
    import os
    CHAPTER = a.chapter or os.environ.get("BNI_CHAPTER")
    if CHAPTER:
        from chapter_config import load
        ch = load(CHAPTER)
        PLAYLIST = ch.get("spotify.playlist_url") or ""
        dl = ch.deadline()
        DEADLINE = (f"Send the finished .pptx to {dl['who']} by {dl['time']} on the "
                    f"{dl['weekday']} before you present.")
    build(Path(a.out))


if __name__ == "__main__":
    main()
