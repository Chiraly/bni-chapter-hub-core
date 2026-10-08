# The roster sheet

One Google Sheet is the chapter's calendar. The Education Coordinators edit it,
and the site, the reminder emails and the playlist job all read it. Change
something in it and everything follows within a couple of minutes. There's no
rebuild, no redeploy and nobody to ask.

Start from the blank template in the handover kit (`Roster sheet template`), or
build it from the description below.

---

## Tabs

The site finds each tab by its **gid**, the number after `#gid=` in the address
bar when that tab is open. Put the three gids in `chapter.json` → `data.tabs`,
and the sheet's ID (the long string between `/d/` and `/edit`) in
`data.roster_sheet_id`.

> Always the gid, never the tab name. Google answers a request for an unknown
> name by silently returning the first tab instead.

### Education roster (`data.tabs.roster`)

One row per meeting. **The Date column is the key**: everything joins on it.

| Column | What it does |
|---|---|
| **Date** | The key. `Fri 13 Nov 2026`, or any date Sheets understands. Check the year |
| **Format** | `online`, `in person`, `hybrid`, or `no meeting`. What blank means depends on `meeting.mode`: for a hybrid, in-person or online chapter, blank means "as usual"; for an alternating chapter, blank means "to be confirmed", and the site shows both sets of details |
| **Topic** | Which prepared moment runs. Make it a dropdown off the Moments tab (below) |
| **Presenter** | Who delivers it. Free text, so a guest is fine |
| **Confirmed** | `y` once they have said yes. This adds a green tick |
| **Notes** | For the coordinators. **Not published anywhere** |

Header names matter (case doesn't); column order doesn't.

To reorder the moments, swap the Topic cells between two dates. The topic carries
its whole package: deck, notes and CEU hour.

To let somebody bring their own topic, type `TBC` or their own title. The deck
drops, because it belongs to a different moment, but the CEU hour stays.

### Speakers (`data.tabs.speakers`)

| Column | What it does |
|---|---|
| **Date** | Same key as the roster |
| **Speaker 1**, **Speaker 2**, ... | Any column whose header starts with "Speaker" |
| **Notes** | Public. Put the public-holiday name here for a no-meeting week |

A date that appears here but not in the roster is still treated as a meeting.

### Members (`data.tabs.members`), usually hidden

One column, **Name**. A fallback only: the chapter roll is read from the BNI
regional website (`data.bni_member_list_url`) on every request. If BNI cannot
be reached, this tab is used instead.

### Moments: never edit it

One formula, in cell A1:

```
=IMPORTDATA("https://YOUR-SITE/moments.csv")
```

It lists every prepared moment and which date it is scheduled on, so a blank in
that column is a moment going spare. Point the roster's Topic column at
`Moments!A2:A` as a dropdown (Data → Data validation → Dropdown from a range), set
to **show a warning** rather than reject, so a guest's own title is still allowed.

---

## Sharing

The sheet must be readable by **anyone with the link** (Share → General access →
Anyone with the link → Viewer). The site reads it from Google with no login.
Coordinators get Editor access as normal.

## Never put email addresses in this sheet

Anything in it is readable by anyone with the link. Presenter addresses live
encrypted in Netlify (`PRESENTER_EMAILS`). See [REMINDERS-SETUP.md](REMINDERS-SETUP.md).

## Checking it

Open `https://YOUR-SITE/schedule`. That is the joined calendar exactly as the site
sees it. `warnings` lists near-miss names and topics; `problems` lists anything that
could not be read; `source` says where each piece came from.
