# Education Coordinator: how this runs

The whole job in one document. Most of it happens by itself, and the parts that
need a person are marked **you**. Adapted from BNI Nexus West's SOP (v2,
September 2026, Hilary Chapman and Kerry Towndrow) for any chapter using the
BNI Chapter Hub.

Wherever it says "your site", that's your chapter's members' site address.

---

## The short version

| You want to | Do this |
|---|---|
| Change who presents, or which moment runs | **Education roster** tab of the roster sheet |
| Set the weekly speakers | **Speakers** tab |
| Change a meeting's format or date | **Education roster** tab, Format and Date columns |
| Add a member | Nothing. It comes from BNI |
| Publish a new trade sheet | Drop the PDF in the trade sheet folder in Drive |
| Add a new education moment | Ask Claude: it needs a deck, notes and a CEU hour (see CLAUDE-SKILL.md) |
| Add a presenter's email for reminders | `PRESENTER_EMAILS` in Netlify, then trigger a deploy |

Everything above except the last two is live on the site within a couple of
minutes. None of it needs a redeploy.

---

## The members' site

Four pages, all in the menu.

| Page | What's on it |
|---|---|
| **Home** | The chapter goal, the next meeting and the current trade sheet, then the links members ask for |
| **Meetings** | Every date, the details for getting there, the speakers, and the venue fees |
| **Education** | Every week: topic, presenter, slides and notes, the CEU hour, the playlist |
| **Requests** | The referral board: what members are looking for |

Nothing is copied onto the site. It links to Drive, so when anyone updates a deck
it's live immediately.

**The site is not private.** It has no password, and search engines are asked not
to list it, which isn't the same as hidden: anyone with the link can read it. The
referral board says so in as many words, because that's the page where it matters.

---

## How the whole thing fits together

Worth reading once, because everything else follows from it.

**The calendar is the Google Sheet.** One row per meeting: when it is, the format,
which moment runs, who presents it, who's speaking. You own it, and it needs no
redeploy.

**The library is `moments.json`.** One entry per education moment: its one-liner,
its deck, its CEU hour. A moment is **not tied to a date**: it can be scheduled,
moved, or run again next year. The core ships a shared library, and your chapter
can keep its own.

**The schedule joins them**, once, at `your-site/schedule`. Every page and every
automation reads that, so the site, the reminder emails and the playlist can't
disagree with each other.

**The sheet wins** on anything the sheet has an opinion about: format, topic,
presenter, speakers.

---

## The roster sheet

Full detail: `ROSTER-SHEET.md`. In brief:

### Education roster

One row per meeting. **The Date column is the key**: don't reformat it, and check
the year when you add a row.

| Column | What it does |
|---|---|
| **Date** | The key. `Fri 13 Nov 2026` |
| **Format** | `in person`, `online`, `hybrid` or `no meeting`. For a hybrid chapter, blank means "hybrid as usual" |
| **Topic** | Which prepared moment runs. Pick from the dropdown |
| **Presenter** | Who delivers it. Free text, so a guest is fine |
| **Confirmed** | `y` once they've said yes. Adds a green tick |
| **Notes** | For the coordinators. **Not published anywhere** |

**To reorder the moments**, swap the Topic cells between two dates. The topic
carries its whole package (deck, notes and CEU hour), because the podcast episodes
were chosen to match the topic, not the date.

**To let somebody bring their own topic**, type `TBC` or their own title. The deck
drops, but the CEU hour stays.

**Number the weeks however the chapter counts them.** The site works out its own
numbers from the dates.

### Speakers

Date, Speaker 1, Speaker 2, Notes. The names appear in the next-meeting panel and
on the Meetings page. Put a public holiday's name in Notes for a week off.

### Moments: nobody edits it

One formula that lists every prepared moment and which date it's scheduled on. A
blank date is a moment going spare. It refreshes itself.

### Never put email addresses in the sheet

Anything in it is readable by anyone with the link. Addresses live encrypted in
Netlify.

---

## The chapter roll comes from BNI

Nobody maintains a member list. The site reads the real one from your chapter's
page on the regional BNI site on every request: the goal count, the referral-board
names and the presenter-name check all come from it. If BNI can't be reached, the
hidden Members tab is used and `/schedule` says `source: sheet`. Treat that as
something to fix, not something to live with.

---

## Hybrid meetings

For a chapter that meets in the room and on Zoom at the same time. The site
already shows both on every page: the venue and a **Join the Zoom** button, side
by side, labelled **In person + online**.

**Before the meeting (you, or whoever runs the tech):**

- One laptop in the room runs Zoom as **host**, plugged into the projector or
  screen, with the room camera and the **room microphone** (a laptop mic does not
  carry across a function room).
- Make a second person **co-host** and give them the Zoom chat. They watch the
  online members and read questions out.
- **The education moment deck is shared from the host laptop through Zoom's Share
  Screen**, so the room and the online members see the same slide at the same
  time. Don't share it twice.

**During the education moment (the presenter):**

- Face the room camera, not just the people at the tables. The online members
  are half the audience.
- When you ask the room something, ask online too: "and in the chat, ...". The
  co-host reads the answers out.
- The visitor beat counts double: visitors online are easiest to lose. Name them
  if the co-host has their names.
- If you point at a QR code on the closing slide, leave it up for five seconds.
  Online members can scan it off their own screen.

**When the format changes for one week** (venue closed, everyone online), put
`online` in that week's Format cell. The site switches every page to the Zoom
details, and the reminder emails go out as normal.

---

## The weekly rhythm

| When | What happens | Who |
|---|---|---|
| Five days before | The coming meeting's CEU hour is **added** to the Spotify playlist, and the coordinators get an email | automatic |
| A fortnight before | Presenter gets "you're on in a fortnight" | automatic |
| A week before | Presenter gets "one week to go" | automatic |
| Deck deadline day | Presenter gets the last-chance email. The meeting deck is built that afternoon | automatic |
| Nudge day (Monday) | Anything needing attention comes to the coordinators | automatic |
| Day before | Presenter gets "tomorrow" | automatic |
| Meeting day | The moment is delivered | presenter |
| Meeting day, 10am | The site moves that week into the delivered list | automatic |

**The only recurring human job is reading the Monday email and acting on it.**

### The deck deadline, and who it applies to

**Presenters don't have to send anything.** Every deck is built ahead and already
with whoever builds the meeting deck. If the presenter is happy with it, they turn
up and deliver it. The deadline only bites if:

1. **the presenter changes the deck**: the changed `.pptx` is theirs to send by
   the deadline, or
2. **a member writes their own moment**: same deadline, same reason.

The deadline-day email says exactly this, so you shouldn't have to.

---

## The Monday email

It goes to the coordinators, only when there's something to say. Two halves:

**Weeks to fill**: anything in the next six weeks with nobody assigned, or with a
name that has no email address on file.

**Things to check**: problems spotted by comparing the sheet against the chapter
roll and the moments library:

- a **presenter** a letter or two off a real member: *"did you mean Gina Collins?"*
- a **topic** a letter or two off a prepared moment, which would lose the deck
- a **date** typed with the wrong year, which would renumber the whole program

Only near misses are flagged. A name nothing like a member is a guest presenter.

---

## Asking someone to present

Ask at least three weeks out, and say what the topic is when you ask. A member who
delivers an education moment learns it far better than one who sits through it, so
spread it around rather than presenting them all yourself. Template:
EMAIL-TEMPLATES.md → *Asking someone to present*.

Match the topic to whoever the room finds credible on it. The member who actually
brings visitors should be the one talking about inviting.

Keep one deck you could deliver cold, for the morning somebody doesn't show.

---

## A member wants to write their own

Point them at the blank template (linked on the Education page). It has seven
on-brand slides, each with a prompt saying what belongs there. The three rules
people get wrong:

1. **Three minutes is shorter than you think.** Talk it through out loud against a
   timer. If it runs over, cut a slide.
2. **Every moment has something for visitors**: a red slide near the end naming
   what a visitor is actually feeling, and giving them something worth having
   whether or not they ever join.
3. **It ends on the chapter's tagline.**

---

## CEUs

One hour of BNI education is one CEU, and CEUs are one of the five Power of One KPIs.

**Episode numbers and durations come from each show's own feed. Never type one in
from memory.** A wrong number sends a member hunting for an episode that doesn't
exist, and they stop trusting the whole list.

Members log their own CEUs in BNI Connect under Reports → CEU. Coordinators don't
log them and can't see them. Say so often: people assume it's automatic.

---

## When something looks wrong

| Symptom | Cause |
|---|---|
| A presenter got no email | Their name in the sheet has no `PRESENTER_EMAILS` entry. Check the spelling: Monday's email will have named it |
| The site shows the wrong topic or presenter | The sheet is believed. Check the sheet first |
| A week shows "Topic to be confirmed" | The Topic cell holds something that isn't a prepared moment |
| The whole program is renumbered | A Date cell with the wrong year |
| Member count looks wrong | Open `your-site/schedule` and check `source` says `bni` |
| Nothing added to the playlist | Netlify → Logs → Functions → refresh-playlist. You should also have had an email |
| Trade sheet shows the wrong file | Open `your-site/.netlify/functions/tradesheet` and check `dateSource` says `drive` |
| Emails not sending at all | Netlify → Logs → Functions → presenter-reminders. Usually the SMTP details |
| Changed a Netlify setting and nothing happened | Environment changes need a redeploy: Deploys → Trigger deploy |

`your-site/schedule` is the diagnostic. Its `warnings` list is what Monday's email
is built from, and `source` says where each piece of data came from.

---

## Handing the role on

Whoever takes it over needs, in this order:

1. Edit access to the roster sheet and the chapter's education Drive folder.
2. Their address added to `COORDINATORS` (and yours removed), then a deploy.
   If the chapter keeps its keys in Doppler, change it there and Doppler updates
   Netlify.
3. Access to the Netlify site, the chapter's GitHub repo and, if used, the
   chapter's Doppler workplace.
4. This document, read once through.

The program itself (topics, decks, notes and CEU hours) is built by the Claude
skill `bni-education-program`. See CLAUDE-SKILL.md. The next coordinator doesn't
have to build a term by hand, and shouldn't.
