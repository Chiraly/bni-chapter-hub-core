# Setting up your chapter's hub

About an hour for the site itself, plus whatever time your email and Spotify
setup take. You can stop after step 6 and have a working site. The rest switches
on features one at a time.

You'll need a Google account (for the sheet and Drive) and an email address for
Netlify and GitHub. You do **not** need to install anything to get the site live.

---

## 1. Make your chapter repo (5 min)

1. Create a free GitHub account at <https://github.com/signup> if you don't have one.
2. Open <https://github.com/Chiraly/bni-chapter-hub-starter> and click
   **Use this template → Create a new repository**.
3. Name it after your chapter, e.g. `bni-business-by-the-sea-hub`. **Private** is
   fine, and recommended if you will publish venue-fee bank details.

Your repo now holds `chapter.json` and a few empty folders. That's all a chapter
needs: everything else comes from the shared core when the site is built.

> **Business by the Sea:** a filled-in `chapter.json` for your chapter is in the
> core repo at `examples/business-by-the-sea/chapter.json`. Copy its contents over
> the starter's `chapter.json`.

## 2. Fill in chapter.json (15 min)

Edit `chapter.json` on GitHub (click the file, then the pencil icon). At minimum:

- `chapter.name`, `chapter.short_name`, `chapter.tagline`
- `meeting.weekday`, `arrive`, `start`, `mode` (`hybrid` for room + Zoom together)
- `meeting.zoom_url`, `meeting.venue.name` and `address`
- `data.bni_chapter_url` and `data.bni_member_list_url`: your chapter's page on
  the regional BNI site, with `/memberlist` on the end for the second
- `brand.colours` if you want something other than the defaults

Leave `site.origin` as `REPLACE-ME` for now. You'll know the address after step 3.
Every setting is explained in [CHAPTER-CONFIG.md](CHAPTER-CONFIG.md).

Click **Commit changes**.

## 3. Create the Netlify site (10 min)

1. Sign up at <https://app.netlify.com/signup>. **Sign up with GitHub**: it saves
   connecting them later. The free plan is enough.
2. **Add new site → Import an existing project → GitHub**, then authorise Netlify
   and pick your chapter repo.
3. Netlify reads the build settings from the repo's `netlify.toml`. Leave
   everything as it is and click **Deploy**.
4. When it finishes, Netlify shows the site's address, something like
   `https://jolly-otter-123abc.netlify.app`. Rename it under **Site configuration →
   Change site name**, e.g. `bbts-hub` → `https://bbts-hub.netlify.app`.
5. Put that address in `chapter.json` as both `site.origin` and
   `site.fallback_origin`, and commit. Netlify rebuilds by itself on every commit.

**Custom domain (optional).** Netlify → **Domain management → Add a domain**, e.g.
`hub.yourchapter.com.au`, and add the DNS record it shows you at your domain
host. Then change `site.origin` to the custom domain and leave `fallback_origin`
as the `netlify.app` address.

## 4. Copy the roster sheet (10 min)

1. Make a copy of the **Roster sheet template** from the handover folder
   (File → Make a copy) into your chapter's own Drive.
2. **Share → General access → Anyone with the link → Viewer.** The site reads it
   without logging in. Give your coordinators Editor access as normal.
3. Copy the sheet's ID (the long string between `/d/` and `/edit` in its address)
   into `data.roster_sheet_id`.
4. Open each tab and copy the number after `#gid=` in the address bar into
   `data.tabs.roster`, `speakers` and `members`.
5. In the **Moments** tab, cell A1, change the formula to your site's address:
   `=IMPORTDATA("https://bbts-hub.netlify.app/moments.csv")`
6. Fill in a few rows of the **Education roster** tab: Date, Topic (from the
   dropdown), Presenter.

Commit `chapter.json`. Within a couple of minutes of the build, the next meeting
appears on the site. How the sheet works: [ROSTER-SHEET.md](../skills/bni-education-program/templates/ROSTER-SHEET.md).

## 5. Join the update list (2 min)

So your site picks up improvements to the core automatically:

1. Netlify → **Site configuration → Build & deploy → Build hooks → Add build
   hook**. Name it `core-updates`, branch `main`.
2. Send the URL it gives you to Hilary (hilary@seddondigital.com.au). Treat it
   like a password: anyone with it can trigger a rebuild, though not change
   anything.

## 6. Check it (5 min)

Open your site on your phone and check:

- [ ] The home page shows your chapter name, and the next meeting with the right
      day, time, venue and Zoom link
- [ ] `/schedule` on your site shows `"roster": true` under `source`, and your
      members under `members`
- [ ] The Meetings page lists your dates
- [ ] The Education page lists the moments you scheduled
- [ ] A link to the site pasted into WhatsApp shows a preview card

**The site is now live.** Everything below is optional, one feature at a time.

---

## 7. Referral board (5 min)

1. Netlify → your site → **Forms → Enable form detection**, then trigger a
   deploy. New Netlify sites have this switched off, and until it's on, posts go
   nowhere.

To *show* the posts on the board:

2. Netlify → your avatar → **User settings → Applications → Personal access
   tokens → New access token**. Name it `referral board`.
3. Netlify → your site → **Site configuration → Environment variables**, add:
   - `NETLIFY_API_TOKEN`: the token
   - `SITE_ID`: from **Site configuration → General → Site details → Site ID**
4. **Deploys → Trigger deploy → Deploy site.**

Submissions also appear in Netlify → **Forms**, and you can turn on email
notifications for new posts there.

## 8. Presenter reminder emails (20 min, plus DNS time)

**You must set up a way to send email.** The site has no email account of its own.
Use SMTP from your existing business email (Google Workspace, Microsoft 365,
your web host) or a sending service (Brevo, Mailgun, Postmark).

Make sure the sending domain has SPF and DKIM set up with that provider, or the
reminders will land in spam. Then add these in Netlify → Environment variables:

| Variable | Example |
|---|---|
| `MAIL_FROM` | `BNI Business by the Sea <education@yourdomain.com.au>` |
| `COORDINATORS` | `lisa@example.com, paul@example.com` |
| `PRESENTER_EMAILS` | `{"Lisa Guglielmino":"lisa@example.com"}` |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS` | from your provider |

Trigger a deploy. Full details, provider settings and troubleshooting:
[REMINDERS-SETUP.md](../skills/bni-education-program/templates/REMINDERS-SETUP.md).

## 9. Spotify playlist (15 min)

1. Create a playlist in Spotify, e.g. "BNI Business by the Sea: CEU hours".
2. Follow [SPOTIFY-SETUP.md](../skills/bni-education-program/templates/SPOTIFY-SETUP.md)
   to create a Spotify app and get a refresh token (needs Python on your computer,
   one command).
3. Add the four `SPOTIFY_*` variables in Netlify.
4. In `chapter.json`, set `spotify.playlist_url` and `features.spotify: true`.
   Commit.

## 10. Trade sheet (5 min)

1. Make a Drive folder for trade sheet PDFs and share it: **Anyone with the link →
   Viewer**.
2. Put its ID in `data.tradesheet_folder_id`, set `features.tradesheet: true`.
   Commit.
3. Drop a PDF in. The newest one always shows on the home page.

## 11. Chapter goal and venue fees

Set `goal.members` and `goal.date`, and/or the `fees` section, then turn on
`features.goal` / `features.fees`. See [CHAPTER-CONFIG.md](CHAPTER-CONFIG.md).

---

## Environment variables: the full list

All set in Netlify → Site configuration → Environment variables. After changing
any of them, **Deploys → Trigger deploy**.

| Variable | Used by | Secret? |
|---|---|---|
| `NETLIFY_API_TOKEN`, `SITE_ID` | Referral board | token yes |
| `MAIL_FROM`, `COORDINATORS`, `PRESENTER_EMAILS` | Reminders | addresses: keep private |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS` | Reminders (SMTP) | password yes |
| `POSTMARK_TOKEN` | Reminders (Postmark, instead of SMTP) | yes |
| `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`, `SPOTIFY_REFRESH_TOKEN`, `SPOTIFY_PLAYLIST_ID` | Playlist | yes, apart from the playlist ID |

Never put any of these in `chapter.json`, the roster sheet, or a chat. They belong
in Netlify only.

## Previewing changes on your own computer (optional)

If you'd rather see a change before committing it, install
[Git](https://git-scm.com), [Python 3.12+](https://python.org) and
[Node 20+](https://nodejs.org), clone both your chapter repo and the core repo
side by side, then from your chapter repo:

```bash
pip install -r requirements.txt
CORE_DIR=../bni-chapter-hub-core bash build.sh
npx netlify-cli dev
```

`netlify dev` serves the site with its functions at <http://localhost:8888>.

## When something goes wrong

| Symptom | Look at |
|---|---|
| Deploy failed | Netlify → Deploys → the failed deploy → log. The build prints which setting is missing or mistyped |
| "Loading the next meeting..." never goes away | `/schedule` on your site. Check `problems`. Usually the sheet isn't shared "anyone with the link", or a gid is wrong |
| Member count is 0 | `data.bni_member_list_url`, which must end in `/memberlist`. `/schedule` → `source.members` says `bni` or `sheet` |
| No reminders | Netlify → Logs → Functions → presenter-reminders |
| Changed an environment variable and nothing happened | Trigger a deploy. Variables only apply from the next deploy |
