# How to write a 3-minute Education Moment

The structure is BNI's own, from *Create a Great Networking Education Moment*
(BNI Global) and the *Creating Education Moments* LTT participant guide (BNI Australia).
Do not invent a different one.

---

## Before you write: answer these five

Straight from the BNI worksheet. If you cannot answer the first one in a single
sentence, you do not have a topic yet.

1. **What is the one thing** you want members to get out of this?
2. How does this topic relate to **business in general**?
3. **Why** is it important for members to know and implement?
4. What might members need to **know in order to implement** it?
5. Where might members find **additional resources**?

## The four steps

| Step | What it does | Roughly |
|---|---|---|
| 1. Relate it to business first | A story or example from ordinary business life. Not BNI yet. | 45–55 s |
| 2. Why this matters | Make them feel the cost of getting it wrong, or the gain of getting it right. | 35–45 s |
| 3. Relate it to BNI | Now land it in this room, this chapter, this meeting. | 45–55 s |
| 4. Resources / wrap up | Where to go next, then the ask, then the tagline. | 25–35 s |

Step 1 is the one people skip, and skipping it is why most education moments die.
Opening with "BNI policy says…" loses the room in four seconds. Opening with "You know
when you ring a tradie and they never call back?" does not.

Interleaved with those four steps, but not replacing them:

- **The visitor beat** — see below. Usually sits between steps 3 and 4.
- **The action ask** — one specific, doable thing, in step 4.

---

## How long it runs

3 minutes. The Education Moment sits at 0:18 in a tightly run agenda and the
President has to take the time back from somewhere.

Timing is declared, not counted. Every slide's notes open with a marker:

```
[0:55-1:35]
```

`deck.save()` checks those markers are contiguous, don't overlap, and finish
between 2:45 and 3:15. Word count tells you nothing here, because the presenter
speaks around the prompts in their own words.

Seven slides at roughly 25 seconds each is the usual shape. Drop a slide before
you crowd one.

## The visitor beat

**Every deck has one.** This is the part that makes these different, and it is not
decoration — a visitor who feels seen is a visitor who comes back.

It does one job, in about 25 seconds: **hand the visitor the part of this week's
idea that is useful in their own business, and say it warmly.**

That is the whole brief. Not a welcome, not a reassurance, not a soft close.

### The rule that matters

**Never reference joining. In either direction.**

Not "if you decide to join". Not "you don't have to decide anything today". Not
"whether or not you ever join". Not "this is what it would cost you". Not even
"come back next month". All of it — including the reassuring half — tells the
visitor you are thinking about converting them, which is the one thing that makes
a room feel like a sales pitch.

The same goes for describing the chapter as a thing being sold: "the actual
product", "worth the visit", "what makes us different from a networking
breakfast". A visitor can see the room. They do not need it sold back to them.

A visitor who gets something genuinely useful and is asked for nothing works out
the rest by themselves. That is the entire mechanism, and naming it breaks it.

### So what goes in it

1. **Something true about their business, not ours.** This week's idea, pointed at
   the work they will go back to this afternoon. Referrals, describing what you do,
   who you have gone quiet on - all of it applies outside this room.
2. **A specific thing to try.** Same shape as the members' ask, sized for someone
   with no BNI context.
3. **Nothing else.** No status, no invitation, no reassurance.

Write it in second person, to them, not about them. Slow down and look at them.

**Register: direct.** Where the moment involves the room's own behaviour, take
responsibility plainly - "if you have been standing on your own, that is on us".
An admission is disarming in a way a welcome never is. Elsewhere, just be useful.

**Do:**
- "You already refer people - your sparkie, your accountant. The gap between a name
  and an introduction is worth knowing wherever you do it."
- "The next ten people worth talking to are already in your phone."
- "If you have spent this morning standing on your own, that is on us, not on you."

**Don't:**
- "You don't have to decide anything today." - the tell. Do not raise it.
- "Whether or not you ever join anything." - the same move, reworded.
- "If you join, this is what the first few months look like."
- "That consistency is the actual product." - do not sell the room to the room.
- Anything that asks them for a decision, an application, or their business card.

**Vary the heading.** The default is *"If you're visiting today…"*. Rotate it so the
regulars don't tune out: *"A word for our visitors"*, *"If this is your first meeting with us"*,
*"Visiting? This bit is for you."*

---

## The close

Two beats, in this order, always:

1. **The action ask** — one thing, this week, specific enough to picture.
   - Good: "Call one visitor from last week. Today, not Friday."
   - Good: "Book one one-to-one with someone whose business you can't yet describe."
   - Bad: "Think about how you can be a better networker." Nobody has ever done this.
2. **The tagline** — the chapter's own, from `chapter.tagline` in its chapter.json (Nexus West's is *Nexus West. Keeping it ELF.* — Easy · Lucrative · Fun).

Say the tagline the same way every week. The whole point of a tagline is that it
becomes the room's, not yours. Within a month the chapter will say it back to you,
and that is when it starts doing its job.

The ask goes on the `action` slide **and** repeats on the `elf_close` slide. Repetition
is not redundancy in a spoken format — people are still writing down the last thing.

---

## Writing the speaker notes

**Notes, not a script.** This is the thing to get right. A member reading 440
written words aloud sounds exactly like a member reading 440 written words
aloud. Give them the structure and the beats, and let them talk.

Every presenter brings their own style and their own stories, and the moment is
better for it. Your job is the shape, not the sentences.

### The shape of one slide's notes

```
[0:15-0:55]
BEAT · the story - business first, no BNI yet

- YOUR example: a time someone sent work away and earned your trust
- If you haven't got one: the plumber who said "not my area, ring Dave"
- Land it: he gave the job away and got everything afterwards
- He wasn't running a strategy

[pause before "who do I ring now?"]
```

Roughly: a timing marker, a one-line statement of what the slide is *for*, three
or four prompts, and a delivery cue. Fifty-odd words a slide. Past that and the
presenter starts reading instead of talking - `deck.save()` warns at 55.

### What to fix and what to leave open

**Prompt for their own material.** Where the moment needs a story, ask for
*theirs* and offer yours as a fallback. `YOUR example:` then
`If you haven't got one:`. A presenter's real story from their own business
beats a better-written one they don't own.

**Keep a handful of lines verbatim.** Some wording carries weight and should not
drift. Mark those `SAY:` and keep them short:

- the ask, so the room hears the same instruction twice
- the tagline - the chapter's `chapter.tagline`

Everything else is theirs.

**Cues in square brackets**, on their own line: `[pause]`, `[look at the
visitors]`, `[wait for hands]`. Never spoken.

**Name real things** in the prompts - a real trade, a real suburb. "A plumber in
Yarraville" prompts a better story than "a service provider".

## Delivery notes worth passing on

- **No handouts** during the moment (Chapter Operations Manual p78) — anything needing
  a response from every member eats the clock. Put it in the dashboard instead.
- Stand where the room can see the screen and you.
- Slides advance on your voice, not the other way around.
- If you are running long, cut the three-up, not the visitor beat.

---

## Quality bar

Before it ships, the moment must pass all of these:

- [ ] One idea, stateable in a single sentence
- [ ] Opens on business, not on BNI
- [ ] 380–470 words of script
- [ ] Has a visitor beat that names a real feeling
- [ ] Has one specific action for this week
- [ ] Ends on the chapter's tagline
- [ ] Every claim is true, and every BNI statistic is sourced
- [ ] A member who has never presented could deliver it from the notes
- [ ] The deck has been rendered and looked at
