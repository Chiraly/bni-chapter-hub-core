# BNI Chapter Hub: start here

A members' website and education program kit for a BNI chapter. It was built
for BNI Nexus West (elf.nexusnetworking.com.au) and is now shared so any chapter
can run its own copy.

## What your chapter gets

**A members' site** with four pages, phone-friendly:

- **Home**: the next meeting (Zoom link, venue, or both for a hybrid chapter),
  the current trade sheet, the chapter goal, and the links members always ask for.
- **Meetings**: every date, who's speaking, how to get there, venue fees.
- **Education**: every week's education moment, with the topic, presenter,
  slides and speaking notes, and a verified one-hour podcast list that earns a CEU.
- **Requests**: a referral board where members post bread-and-butter, cream and
  dream referrals.

**Automations** that run by themselves:

- Presenter reminder emails a fortnight, a week, the deck-deadline day and the day
  before, plus a weekly "weeks still to fill" email to the coordinators.
- A chapter Spotify playlist that gains each week's CEU hour automatically.
- The member list, read live from your chapter's BNI page, so nobody maintains one.
- The newest trade sheet, picked up from a Drive folder.

**A Claude skill** (`bni-education-program`) that plans a term of education
moments from your chapter's Traffic Lights gaps and builds each week's on-brand
deck, speaking notes and CEU hour.

**Email templates and an SOP** for the Education Coordinator.

## What it costs

Nothing, for a chapter of normal size:

| Service | What for | Cost |
|---|---|---|
| Netlify | Hosting the site and running the automations | Free tier |
| GitHub | Holding your chapter's settings | Free |
| Google Sheets / Drive | The roster, the decks, the trade sheet | What you already have |
| Spotify | The playlist (optional) | Free account works |
| Email sending (SMTP or Postmark) | Presenter reminders (optional) | Your existing email, or a free tier |
| Claude | Building the education program | Your Claude plan |

## How it fits together

```
 bni-chapter-hub-core  (shared, maintained by Hilary Chapman / Seddon Digital)
   the site templates, the automations, the moments library, the Claude skill
          │  fetched fresh on every build, so improvements reach every chapter
          ▼
 your chapter repo  (yours: settings + your own logo, content and pages)
   chapter.json, assets/, content/, pages/
          │  Netlify builds it
          ▼
 your members' site  ◄── reads live ──  your roster Google Sheet
                                         your BNI chapter page (member list)
                                         your trade-sheet Drive folder
```

**You own your chapter repo and your Netlify site.** Nobody else can change your
site. When the core gets an improvement, your site is rebuilt with it
automatically, unless you have pinned a version (see CUSTOMISING.md).

## Where to go next

| You are | Read |
|---|---|
| Setting up a new chapter's site | [SETUP-GUIDE.md](SETUP-GUIDE.md) (about an hour) |
| Changing what the site says or looks like | [CHAPTER-CONFIG.md](CHAPTER-CONFIG.md), then [CUSTOMISING.md](CUSTOMISING.md) |
| The Education Coordinator, week to week | [EDUCATION-COORDINATOR-SOP.md](EDUCATION-COORDINATOR-SOP.md) |
| Sending the chapter emails | [EMAIL-TEMPLATES.md](EMAIL-TEMPLATES.md) |
| Using Claude to build the program | [CLAUDE-SKILL.md](CLAUDE-SKILL.md) |
| Hilary, shipping an update to all chapters | [RELEASING.md](RELEASING.md) |

## Who to ask

Hilary Chapman, Seddon Digital: hilary@seddondigital.com.au. If you've built
something other chapters would want, send it over and it can go into the core
for everyone.
