# Changelog

What changed in each release of the BNI Chapter Hub core, written for
coordinators. Your site picks up each release automatically if your
`netlify.toml` says `CORE_REF = "stable"`.

Each entry lists **Templates touched**. If your chapter repo has a file of the
same name in `overrides/templates/`, compare it with the new core version.

---

## 1.0.1 (October 2026)

- **A new chapter's site looks finished before its roster sheet exists.** Until
  `data.roster_sheet_id` is set, the site shows a sample calendar: the next 12
  meetings on the chapter's weekday, with the shared library's moments in order.
  `/schedule` marks it `"roster": "sample"`, and the reminder emails never act on it.
- **The Zoom link can come later.** A hybrid or online chapter with no
  `meeting.zoom_url` yet builds, and the site says the link is on its way.

**Templates touched:** `schedule.mts`, `presenter-reminders.mts`, `meeting.html`, `meetings.html`.

---

## 1.0.0 (October 2026)

The first shared release, made from BNI Nexus West's members' site
(elf.nexusnetworking.com.au).

- **Every chapter detail is a setting.** Name, meeting day and times, venue, Zoom,
  colours, logos, tagline, links, sheet and folder IDs all come from
  `chapter.json`. Nothing about any one chapter is in the core.
- **Hybrid meetings.** `meeting.mode: "hybrid"` shows the venue and the Zoom link
  side by side every week, labelled *In person + online*. `alternating`,
  `in_person` and `online` also work. The roster's Format column accepts `hybrid`.
- **Feature switches.** `goal`, `fees`, `spotify`, `tradesheet`, `referral_board`,
  `bni_roll`, `reminders`.
- **Any SMTP for reminder emails**, as well as Postmark.
- **Reminder wording is editable** per chapter (`emails/reminders.json`) without
  losing core improvements to the lines you didn't change.
- **Five customisation layers**: settings, `custom.css`, content blocks, extra
  pages and functions, and template overrides. See docs/CUSTOMISING.md.
- **Decks and speaking notes** use the chapter's own tagline and mascot.
- Deck deadline, reminder stages, nudge day and playlist day follow the
  chapter's meeting weekday.

**Templates touched:** all (first release).
