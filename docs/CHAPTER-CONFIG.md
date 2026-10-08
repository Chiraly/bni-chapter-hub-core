# chapter.json: every setting

Your chapter's site is built entirely from `chapter.json` in your chapter repo.
Anything you leave out uses the core default (in
`skills/bni-education-program/config/chapter.defaults.json`), so a new setting
added to the core never breaks an older chapter.

The build prints `TODO:` for every value still saying `REPLACE-ME`, and `note:`
for any setting it doesn't recognise (usually a typo).

Values marked **HTML** may contain simple tags like `<b>` and entities like
`&mdash;`.

---

## chapter

| Setting | Example | What it does |
|---|---|---|
| `name` **required** | `"BNI Business by the Sea"` | Everywhere: page titles, footer, link previews, emails |
| `short_name` **required** | `"Business by the Sea"` | Where the full name is too long |
| `region` | `"Melbourne West and Geelong"` | Reference only, for now |
| `lede` HTML | `"A hybrid chapter on the Williamstown waterfront..."` | The intro under the name on the home page |
| `tagline` | `"Business by the Sea. Givers Gain."` | The closing line of every deck, the speaking notes and the reminder emails |
| `tagline_words` HTML | `"Easy &middot; Lucrative &middot; Fun"` | Optional second line under the tagline |
| `contact_name` | `"Lisa"` or `"the Education Coordinator"` | Who members are told to ask ("tell Lisa") |
| `maintained_by` | `"Maintained by the Leadership Team"` | Footer line |

## site

| Setting | What it does |
|---|---|
| `origin` **required** | The site's address, e.g. `https://bbts.bnimwg.com.au` (a subdomain of the region's domain, see SETUP-GUIDE step 3) or `https://bbts-hub.netlify.app`. Used for link previews |
| `fallback_origin` | The site's `*.netlify.app` address. The functions use it while a new custom domain's certificate is being issued |
| `nav_extra` | Extra menu items: `[{"href": "/visitors/", "label": "Visitors"}]` |
| `footer_links` | `[{"label": "...", "href": "..."}]`. Defaults to your BNI chapter page |

## brand

| Setting | What it does |
|---|---|
| `wordmark` | Two-part name in the nav: `["Business", "by the Sea"]`. The second part is greyed |
| `mark_svg` | Small SVG mark before the wordmark. Optional |
| `lockup` | Footer logo (PNG/SVG). Defaults to the BNI logo |
| `lockup_white` | White logo for link-preview cards. **PNG.** Defaults to the white BNI logo |
| `favicon_svg`, `favicon_png` | Browser tab and phone home-screen icons |
| `mascot` | Optional image on each deck's closing slide |
| `colours.primary` | Nav mark, badges, link-preview background |
| `colours.accent`, `colours.accent_ink` | Buttons, eyebrows, links (`_ink` is the darker hover/text shade) |
| `colours.*_dark` | The same three for dark mode. Lighter versions of the same colours |
| `colours.goal_band`, `goal_band_dark`, `goal_bar` | The chapter-goal band |

The Education page always uses **BNI red** for its own accents. It is BNI's
content, and BNI's brand rules apply to it.

## meeting

| Setting | What it does |
|---|---|
| `weekday` **required** | `"Friday"`. Drives "Next Friday", the deadline day and the playlist day |
| `arrive`, `start` **required** | `"6:30am"`, `"6:45am"`. Shown on every page |
| `timezone` | `"Australia/Melbourne"`. The site's clock always runs on chapter time |
| `handover_hour` | `10`. The hour (24h, chapter time) on meeting day when the site moves on to next week |
| `mode` **required** | `hybrid` (room and Zoom together), `alternating` (one or the other each week, set in the roster), `in_person`, `online` |
| `summary` HTML | The one-line description on the Meetings page. Written for you from the other settings if you leave it out |
| `zoom_url` | Required unless `in_person` |
| `venue.name`, `venue.short`, `venue.address` | Required unless `online`. `short` is used in tables ("Seaview") |
| `venue.maps_url` | Optional. Built from the name and address if left out |
| `venue.parking` HTML | Optional parking note under the venue |
| `tbc_note` HTML | Extra line when some weeks' format is still to be confirmed (alternating chapters) |
| `no_meeting_words` | Words in a Speakers-tab note that mark a date as "no meeting" |

## goal (shown when `features.goal` is on)

| Setting | What it does |
|---|---|
| `members` | Target member count, e.g. `50` |
| `date` | `"2027-06-30"`. Counts down in chapter time |

The current count is the real member list from BNI.

## fees (shown when `features.fees` is on)

| Setting | What it does |
|---|---|
| `summary` HTML | e.g. `"<b>$60 a month, due on the 5th.</b> It covers the room and breakfast."` |
| `account_name`, `bsb`, `account_number`, `reference` | The bank table. Leave `account_number` empty to hide the table |
| `note` HTML | Anything after the table |

**The site is public.** Anyone with the link can read the fees section. Only
publish account details the chapter is happy to have public.

## data

| Setting | What it does |
|---|---|
| `roster_sheet_id` | The roster Google Sheet's ID. See `ROSTER-SHEET.md` |
| `tabs.roster`, `tabs.speakers`, `tabs.members` | Each tab's gid |
| `tradesheet_folder_id` | Public Drive folder holding the trade sheet PDFs |
| `education_folder_url` | Drive folder holding the decks and notes |
| `bni_chapter_url` | Your chapter's public BNI page |
| `bni_member_list_url` | Your chapter's `.../memberlist` page on the BNI regional site. The member count, the referral-board names and the presenter-name check all come from it |

## spotify (when `features.spotify` is on)

| Setting | What it does |
|---|---|
| `playlist_url` | The chapter playlist. Embedded on the Education page |
| `show_id` | The podcast episodes are drawn from. Default: The Official BNI Podcast |
| `market` | `"AU"` |
| `cron` | When the weekly job runs, in UTC. Worked out from `meeting.weekday` if left out |

## education

| Setting | What it does |
|---|---|
| `gains_pdf` | The GAINS worksheet link. Defaults to BNI's |
| `template_pptx`, `template_canva` | The blank deck for members writing their own moment |
| `deck_deadline.days_before` | Days before the meeting that the meeting deck is built (Friday meeting, `3` = Tuesday) |
| `deck_deadline.time`, `deck_deadline.who` | `"12pm"`, `"the Vice President"` |

## reminders

| Setting | What it does |
|---|---|
| `cron` | When the reminder job runs, UTC. Default `0 20 * * *` (6–7am east-coast time) |
| `stages` | `{"14": "in a fortnight", "7": "in one week", "1": "tomorrow"}`. The deadline day is added automatically |
| `nudge_weekday` | `"Mon"`. The day coordinators get the "weeks to fill" email |

## home

`cards`: the cards on the home page, in order. Built-ins: `requests`,
`education`, `ceu`, `gains`, `chapter_page`. Your own:

```json
{ "title": "Member contact list", "href": "https://...", "button": "Open the list",
  "text": "Every member in one place...", "primary": false }
```

A built-in can be tweaked: `{ "builtin": "chapter_page", "button": "Visit" }`.

## features

All `true`/`false`:

| Feature | Turns on | Needs |
|---|---|---|
| `goal` | The chapter-goal band | `goal` settings |
| `fees` | Venue fees on the Meetings page | `fees` settings |
| `spotify` | The playlist on the Education page, and the weekly playlist job | Spotify setup, see `SPOTIFY-SETUP.md` |
| `tradesheet` | The trade-sheet card on the home page | `data.tradesheet_folder_id` |
| `referral_board` | The Requests page | `NETLIFY_API_TOKEN` and `SITE_ID` in Netlify |
| `bni_roll` | Reading the member list from BNI | `data.bni_member_list_url` |
| `reminders` | The presenter reminder emails | SMTP or Postmark, see `REMINDERS-SETUP.md` |

New core features arrive switched **off** for existing chapters unless they are
harmless, and the CHANGELOG says how to switch them on.

---

## Tokens you can use in content blocks and extra pages

`@@chapter@@` `@@chapter_short@@` `@@tagline@@` `@@contact@@` `@@weekday@@`
`@@arrive@@` `@@start@@` `@@zoom@@` `@@venue_name@@` `@@venue_short@@`
`@@venue_address@@` `@@venue_maps@@` `@@parking@@` `@@meeting_summary@@`
`@@mode_label@@` `@@playlist_url@@` `@@playlist_day@@` `@@gains@@`
`@@deadline_who@@` `@@deadline_time@@` `@@deadline_weekday@@`
`@@education_folder@@` `@@goal_members@@` `@@goal_date@@`

Page furniture: `@@nav@@` `@@clock@@` `@@meeting@@` (the next-meeting panel)
`@@goal@@` `@@footer@@`.

Show something only when a feature is on: `<!--if:spotify--> ... <!--/if:spotify-->`.
Only when it is off: `<!--if:!spotify--> ... <!--/if:!spotify-->`. Meeting modes work
the same way: `<!--if:hybrid--> ... <!--/if:hybrid-->`.
