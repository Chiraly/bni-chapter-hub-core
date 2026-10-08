# The CEU hour

Every week of the program comes with about an hour of listening matched to that week's
topic. One hour of qualifying BNI education = **1 CEU**, and CEUs are one of the five
Power of One KPIs (Chapter Operations Manual p111).

Members log their own CEUs in **BNI Connect**. The dashboard does not track them — it
just makes the hour easy to find and press play on.

---

## The rule that matters

**Never write an episode number, title or duration from memory.** Nothing destroys
trust in a resource faster than a link to an episode that does not exist, or a "15
minute" episode that runs 42. Every entry must come from the library, which comes from
the podcast's own feed.

```bash
python scripts/build_ceu_library.py --refresh            # pull the feed
python scripts/build_ceu_library.py --search visitor     # find candidates
python scripts/build_ceu_library.py --hour visitor invite follow up
```

`--hour` assembles episodes into a set landing between 55 and 65 minutes and prints
real numbers, durations and URLs. Take those verbatim.

The feed carries the most recent **300 episodes** (currently 678–977) with an exact
`<itunes:duration>` for each. Older episodes still exist on bnipodcast.com; if you want
one, open its page and read the duration off it. Do not estimate.

---

## Where members listen

Give every week's list on all four, because members are not all the same:

| Route | Why it's there |
|---|---|
| **The dashboard** | Primary. No app, no account, no searching — the week's episodes in order with a play control. |
| **bnipodcast.com** | The canonical source. Free, no login, and **every episode has a full transcript**, which matters for members who would rather read or who are hard of hearing. |
| **Spotify** — [the show](https://open.spotify.com/show/11B5zbsY9tEP4iPbHHX5iq) | What most members already have. Podcasts play in full on the free tier. Add the week's episodes to the chapter playlist. |
| **YouTube** — [@TheOfficialBNIPodcast](https://www.youtube.com/@TheOfficialBNIPodcast) | The zero-sign-up fallback, works on any device. |

Also on Apple Podcasts, Podbean and TuneIn if someone asks.

---

## Building a good hour

**Composition.** Episodes run 12–16 minutes, so four is usually an hour. Aim for:

- **2 episodes dead-on the topic** — these do the work
- **1 adjacent episode** that comes at it differently, or is a member story
- **1 short foundational episode** — a Givers Gain, Power of One or core-values classic

Order them so the hour builds: the clearest one first, the most challenging one last.

**Say why each one is there.** A bare list gets ignored. One line per episode — "this
is the one that explains why the follow-up call beats the email" — is the difference
between a list and a recommendation.

**Watch the total.** 55–65 minutes. Under 55 and it is not a CEU. Well over 65 and
members quietly do none of it.

**Don't repeat inside a term.** Track what has already been used. An episode reused in
week 11 that was in week 3 reads as filler.

---

## Beyond the podcast

The hour does not have to be four podcast episodes.

- **BNI Academy** — free to members, courses count. A 20-minute module plus three
  episodes is a good hour, and it gets members into the Academy, which most never open.
- **Chapter and regional trainings**, Members Success Programs, and the Leadership Team
  Trainings all count.
- **The chapter's own Spotify playlist** — if the chapter already curates one, add the
  week's episodes to it rather than competing with it.

Check what the region counts before promising a member it qualifies. When unsure, say
"check with the Education Coordinator" rather than inventing a rule.

---

## The week's CEU file

```markdown
# Week 7 CEU hour — Referrals vs Leads
**Total 58 min · 1 CEU · log it in BNI Connect**

### 1. Episode 812 — The Difference Between a Referral and a Lead (14:02)
The cleanest explanation of the distinction. Start here.
https://www.bnipodcast.com/...

### 2. ...

**Also on:** [Spotify playlist](...) · [YouTube](...) · [bnipodcast.com](...)
**Logging it:** BNI Connect → Reports → CEU. One hour listened = 1 CEU.
```

Keep it to one screen. Members read this on a phone in a car park.
