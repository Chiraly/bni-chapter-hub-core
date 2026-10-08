# The member dashboard

One link a member can open on a phone in a car park at 6:40am and immediately see: what
this week's education moment is, who is presenting it, where the deck is, and what to
listen to for the CEU.

Published as an Artifact. `templates/dashboard.html` is the starting point.

---

## How the chapter actually works

This shapes the whole design:

- **The Education Coordinator assigns presenters.** Not self-service. The schedule is
  set by one person and published.
- **Members log their own CEUs in BNI Connect.** The dashboard does not track listening
  and must not pretend to — a tick box that saves nothing is worse than no tick box.

So the page is **read-mostly**: data baked in, republished when the schedule changes.
No sign-in, nothing to save, nothing to break.

If the coordinator later wants to reassign presenters without re-running the skill,
load `artifact-capabilities` and add a `db`-backed edit mode. Keep the read path
working unchanged if you do — most viewers will never edit anything.

---

## What goes on it

1. **Masthead** — chapter name, term, meeting day and time. BNI logo, Super Graphic
   anchored bottom-right per brand.
2. **This week** — the panel that carries the page. Week number, date, topic, the one
   thing in plain language, presenter, which gap it serves, and links to the deck,
   notes and brief.
3. **This week's CEU hour** — numbered episodes with real durations, one line each on
   why it is there, and a running total badge. Then where else to listen.
4. **The term** — every week as a compact ledger row: number, topic, date, presenter,
   gap, and a status chip (Delivered / This week / Upcoming). Numbering is legitimate
   here because weeks genuinely are a sequence.
5. **What we're aiming at** — the training goals with their measures, so members can
   see why these topics and not others.
6. **CEUs** — one hour = 1 CEU, and a plain instruction to log it in BNI Connect.
7. **Footer** — the chapter's name, its links and its logo, from chapter.json

---

## Linking to the files

**Link to the week's Google Drive folder. Never copy files into the site.**

One link per week, straight to that week's folder. When anyone updates a deck or
a set of notes it is live immediately - no rebuild, no redeploy, nothing for the
Education Coordinator to remember. Hosting the files on Netlify would mean a
redeploy every time somebody else edited something, which is exactly the kind of
standing chore this program exists to avoid.

**The site is a members' resource, not a visitor one.** Its URL is not on the
slides and not on the QR. That is what makes the Drive links safe: nobody is
pointing a room full of visitors at the speaker notes.

The QR on the closing slide goes to the **chapter Spotify playlist** - the thing
that is genuinely for everyone in the room.

Embedded audio is not an option either way: the artifact CSP blocks media from
non-allowlisted hosts, so an `<audio>` tag pointed at a podcast MP3 fails
silently. Link to the episode page, which carries the player and the transcript.

## Design notes

- **Type is the brand face**: `"Helvetica Neue", Helvetica, Arial, sans-serif`. No
  second family — hierarchy comes from weight, scale, case and letter-spacing, which is
  the Swiss idiom Helvetica belongs to and keeps the page unmistakably BNI.
- **Red is the only accent.** Semantic green appears once, on the CEU total. Everything
  else is neutral.
- **Only "this week" reads as a card.** If every block has a border and a shadow, the
  hierarchy flattens and nothing leads.
- `font-variant-numeric: tabular-nums` on week numbers, dates and durations.
- **Both themes.** Every colour is a token declared in bare `:root`, redefined under
  `prefers-color-scheme: dark` (guarded `:root:not([data-theme="light"])`) and again
  under `:root[data-theme="dark"]`. The red lifts to `#F2455A` on dark so it keeps
  contrast without glowing.
- **Mobile first.** Members open this on a phone. Test at 375px before anything wider.

## Hosting

Two targets, one template, via `scripts/build_dashboard.py`:

- `--target artifact` writes a fragment; the Artifact host supplies the skeleton.
- `--target netlify` writes a whole Netlify project - `public/` plus `netlify.toml`
  and the scheduled functions.

**Netlify is usually the better home.** An Artifact needs viewers to sign in to
claude.ai; a Netlify URL just opens. For thirty business owners at 6:40am that
difference matters. Deploy with `noindex` in both a meta tag and an `X-Robots-Tag`
header, so the link works for anyone who has it without turning up in search.

> Deploy from the folder containing `netlify.toml`, **never** with `--dir`. The
> flag overrides the config: the site publishes one level deep and the scheduled
> functions are silently skipped. This is not obvious from the CLI output.

### Which week is "this week"

Computed in the browser from the meeting dates, pinned to the chapter's timezone
rather than the viewer's device, comparing plain `YYYY-MM-DD` strings so daylight
saving is a non-issue. Nothing to republish week to week, and it works identically
on any host. "This week" is the first meeting that has not passed, held through the
day after so a Tuesday afternoon does not jump ahead.

### Scheduled functions

- `refresh-playlist` loads the coming Tuesday's CEU hour into the chapter Spotify
  playlist each Thursday morning, so the playlist matches the moment on the day it
  is delivered and holds for two days after. Never renames the playlist; members
  have it saved. See `templates/SPOTIFY-SETUP.md`.
- `presenter-reminders` emails each presenter 14, 7 and 1 days out, copying the
  coordinators on the last one, plus a Monday list of unassigned weeks. See
  `templates/REMINDERS-SETUP.md`.

Both exit quietly when their environment variables are absent, so the site can be
deployed long before either is configured.

> **Never put email addresses in `weeks.json`.** It is served publicly. Presenter
> addresses belong in an encrypted Netlify environment variable that only the
> function reads. Names on the page are a judgement call for the chapter; addresses
> are not.

## Honesty

If you publish a preview with placeholder weeks or presenters, **say so on the page**.
A dashboard that looks like the real roster but is not will get someone turning up
expecting to present. Mark example data clearly and remove the notice once the real
program is in.

Never put a CEU episode on the page that has not come from the verified library.
