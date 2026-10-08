# Automating presenter reminders

Each week's presenter is emailed automatically before their education moment:
a fortnight out, a week out, on the day the meeting deck is built, and the day
before. Every email says plainly to reply if they can't do it, and replies go
to **all the coordinators**, so "I can't make it" never lands with only one person.

On the nudge day (Monday by default) the coordinators also get a list of the next
six weeks that still have no presenter, plus anything in the roster sheet that
looks wrong, such as a topic or name that is one letter out.

**The site never sends email on its own account. You have to give it a way to
send: Postmark, or any SMTP service.** Until you do, the reminder function
quietly does nothing and the rest of the site works as normal.

---

## What gets sent

| When | To | Copied | Why |
|---|---|---|---|
| 14 days out | presenter | coordinators | enough notice to prepare or hand it back |
| 7 days out | presenter | coordinators | the one that actually gets it in the diary |
| deck deadline day | presenter | coordinators | last chance to change the slides |
| 1 day out | presenter | coordinators | "tomorrow" |
| nudge day | coordinators | — | weeks in the next six with nobody assigned |

The stages, the deadline day and the nudge day all come from `chapter.json`
(`reminders.stages`, `education.deck_deadline`, `reminders.nudge_weekday`).
The wording comes from `templates/emails/reminders.json`, and a chapter can
reword any line in its own `emails/reminders.json`.

Over a 12-week term that's about 50 emails, well inside every provider's free tier.

---

## One-time setup

### 1. Choose how the mail is sent

**Option A: SMTP (any provider).** Most chapters already have this through
someone's business email:

| Provider | SMTP_HOST | SMTP_PORT | Notes |
|---|---|---|---|
| Google Workspace | `smtp.gmail.com` | 465 | Turn on 2-Step Verification, then create an **App password** for the user and use it as `SMTP_PASS` |
| Microsoft 365 | `smtp.office365.com` | 587 | SMTP AUTH must be enabled for the mailbox in the M365 admin centre |
| Brevo (free 300/day) | `smtp-relay.brevo.com` | 587 | SMTP key from Brevo → SMTP & API |
| Mailgun / SendGrid / SES | from their dashboard | 587 | Verify the sending domain in their dashboard first |
| Your web host (cPanel etc.) | e.g. `mail.yourdomain.com.au` | 465 | The mailbox's own username and password |

**Option B: Postmark.** If you already use Postmark, create a server for the
chapter, verify the sending domain, and copy the **server** API token
(Postmark → Servers → *your server* → API Tokens).

Whichever you choose, **the domain in `MAIL_FROM` must be verified (SPF and
DKIM) with that provider**, or the reminders will go to spam. Most providers
walk you through the two or three DNS records this needs.

### 2. Environment variables in Netlify

Netlify → your site → **Site configuration → Environment variables**:

| Variable | Value |
|---|---|
| `MAIL_FROM` | `BNI Riverside <education@yourdomain.com.au>` |
| `COORDINATORS` | coordinator addresses, comma-separated |
| `PRESENTER_EMAILS` | JSON, presenter **name** → email |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS` | for SMTP |
| *or* `POSTMARK_TOKEN` | for Postmark |

If both are set, Postmark is used.

`PRESENTER_EMAILS` is keyed by the name in the roster sheet's **Presenter**
column, not by week number:

```json
{"Brei Scolaro":"brei@example.com","Sam Nguyen":"sam@example.com"}
```

Keying on the name is what lets the sheet do the work. Move somebody to a
different week in the sheet and their reminders follow them there, with no
change to the variable and no redeploy. You only touch this variable when a
**new person** joins the roster. Matching ignores case and surrounding spaces,
and forgives a role prefix such as "Visitor Host - Gina Collins".

> **Presenter addresses live here, not in the moments library or the sheet.**
> Both of those are public, so they carry names only. Netlify encrypts
> environment variables and only the function reads them.

### 3. Redeploy

Environment variable changes only take effect on the next deploy. Netlify →
**Deploys → Trigger deploy → Deploy site**.

---

## Checking it

Netlify → **Logs → Functions → presenter-reminders**. It runs daily and logs what
it did:

```
week 5: 14d reminder -> sam@example.com; monday nudge -> ... (3 to fill, 0 to check)
```

On a quiet day it logs `nothing due on 2026-03-02`, which is normal.

To send one now, Netlify → **Logs → Functions → presenter-reminders → Run now**
(scheduled functions have this button). Opening the function's URL in a browser
returns **403**. That's expected: Netlify blocks direct access to scheduled
functions.

## Notes and limits

**Timing.** `reminders.cron` in chapter.json, in UTC. The default, 20:00 UTC, is
6am AEST / 7am AEDT the next morning, early in an east-coast chapter's day on both
sides of daylight saving. Chapters in WA, SA or QLD may want to adjust it.

**Duplicates.** The stages are exact day counts and the schedule fires once a day,
so each reminder goes once. Running it by hand on the same day sends again.

**"No email on file".** Logged when a week has a presenter name but no matching
entry in `PRESENTER_EMAILS`. Check the spelling, add the address, redeploy.

**Changing the presenter.** Edit the **Presenter** column in the roster sheet.
Nothing else. The education page and the reminders both read that sheet, so they
can't disagree. Reminders already sent aren't recalled.

**The sheet is unreachable.** No reminders are sent that morning, and the
coordinators get an email saying so, with "nothing in the sheet needs fixing". It is
almost always Google not answering for a few seconds.

## Turning it off

Set `features.reminders` to `false` in chapter.json, or delete the mail variables
in Netlify. With no way to send, the function does nothing.
