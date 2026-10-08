# Education moment emails

There are two kinds:

1. **Automatic**: the presenter reminders the site sends by itself. You set them
   up once (needs SMTP, see below) and never write them again.
2. **Sent by a person**: the chapter announcements and one-to-one notes below.
   Copy, fill in the `[brackets]`, send. Paste them into Gmail, Outlook or BNI
   Connect, or into WhatsApp with the subject line removed.

---

## 1. The automatic presenter reminders

| When | Subject |
|---|---|
| 14 days out | *Your BNI education moment in a fortnight: [title]* |
| 7 days out | *Your BNI education moment in one week: [title]* |
| Deck deadline day | *Your BNI education moment on [weekday]: [title]*. Leads with "Changing the slides? Today is the day." |
| 1 day out | *Your BNI education moment tomorrow: [title]* |
| Monday | To coordinators: *3 education weeks to fill, and 1 thing to check* |

Each one carries the topic, the date, the one thing to land, a link to the
presenter's own slides and notes, the playlist, the deadline rule and a "can't make
it? just reply" line. Replies go to the coordinators.

**These need email sending set up. The site has no email account of its own.**
Give it SMTP details from your business email (Google Workspace, Microsoft 365,
your web host) or a sending service (Brevo, Mailgun, Postmark), with SPF and DKIM
set up on the sending domain so they don't land in spam. Step by step:
`skills/bni-education-program/templates/REMINDERS-SETUP.md`.

**To reword them**, put the lines you want to change in your chapter repo's
`emails/reminders.json`. The full wording, line by line, is in
`skills/bni-education-program/templates/emails/reminders.json`.

---

## 2. Emails a person sends

### Term launch: to the whole chapter

**Subject:** This term's education moments, and where to find them

> Hi everyone,
>
> Our education moments for [term, e.g. Term 1, February to April] are planned,
> and everything is in one place: **[site address]/education/**
>
> For every week you'll find the topic, who's presenting, the slides and notes,
> and an hour of BNI podcast picked to match the topic. Listen to the hour and
> that's a CEU. [The episodes go into our chapter Spotify playlist each week:
> save it once and it keeps up on its own.]
>
> This term we're working on **[goal 1, e.g. converting more visitors]** and
> **[goal 2]**, because that's where our Traffic Lights say we have the most to
> gain.
>
> **Want to present one?** Reply and tell me which week. Delivering one teaches
> you far more than sitting through it, and the slides and notes are done for you.
>
> CEUs don't log themselves: BNI Connect → Reports → CEU, about a minute.
>
> [Name]
> Education Coordinator, [chapter name]

### Asking someone to present: one-to-one

**Subject:** Would you deliver the education moment on [date]?

> Hi [first name],
>
> Would you be up for delivering our education moment on **[weekday date]**? The
> topic is **[title]**: [the one thing, in one sentence].
>
> It's three minutes, and it's ready to go. The slides and speaking notes are
> written, with timings and story prompts, and you just bring one example of your
> own. I asked you because [the honest reason, e.g. you're the one who actually
> brings visitors].
>
> If you say yes, the site sends you a reminder a fortnight out, a week out and
> the day before, with a link to your slides. If something comes up, just reply
> to any of them.
>
> Can you let me know by [date]?
>
> [Name]

### The night before: to the whole chapter (optional)

**Subject:** Tomorrow: [title]

> Hi everyone,
>
> Tomorrow [first name of presenter] is delivering **[title]**. [One sentence on
> why it matters, e.g. Most referrals die because nobody asked one more
> question.]
>
> We're [in the room at [venue] / on Zoom / in the room and on Zoom]. Be there by
> **[arrive time]**: [site address]
>
> The hour of podcast for this week is already in the playlist, if you'd like a
> head start on the CEU.
>
> See you there,
> [Name]

### After the meeting: to the whole chapter

**Subject:** This week's education moment: the one thing, and your CEU hour

> Hi everyone,
>
> Thanks [presenter first name] for this morning's moment, **[title]**.
>
> **The one thing:** [the one thing]
> **This week's ask:** [the action from the closing slide]
>
> Missed it, or want it again? The slides, the notes and the hour of podcast that
> earns you a CEU are here: [site address]/education/
>
> Log your CEU in BNI Connect → Reports → CEU once you've listened.
>
> [Name]

### Thank you: to the presenter

**Subject:** Thank you for this morning

> Hi [first name],
>
> Thank you for this morning. [One specific thing that landed, e.g. The story
> about the plumber who sent the wrong referral got the biggest nod of the
> morning.]
>
> If you'd like it, I'd love to put you down for another one next term.
>
> [Name]

### Monthly CEU nudge: to the whole chapter

**Subject:** Your CEUs for [month]

> Hi everyone,
>
> A quick one: CEUs are one of the five Power of One KPIs, and nobody logs them
> for you.
>
> Every week's education moment comes with about an hour of BNI podcast, and that
> hour is a CEU. They're all here, newest first: [site address]/education/
>
> BNI Connect → Reports → CEU. It takes about a minute.
>
> [Name]

### Welcoming a new member to the hub

**Subject:** Everything for members, in one place

> Hi [first name], welcome to [chapter name].
>
> Save this on your phone: **[site address]**
>
> It has the next meeting (with the Zoom link and the venue), the trade sheet, the
> referral board where members post what they're looking for, and every
> education moment with its slides and podcast hour.
>
> Add your own referral request on the Requests page when you're ready. You'll be
> in the name list once BNI has you on the chapter roll.
>
> [Name]

### What's new in the hub: core updates, to coordinators

For Hilary, when a release goes out (see RELEASING.md). Draft only, never sent
automatically.

**Subject:** BNI Chapter Hub [version]: what's new

> Hi all,
>
> Your members' site has just been updated to [version]. Nothing for you to do
> unless you want the new bits:
>
> - **[Change 1]**: [what it does for members]. Already on.
> - **[Change 2]**: [what it does]. Switch it on with `features.[name]: true` in
>   your `chapter.json`.
>
> If you've replaced any templates (overrides), check: this release touched
> [templates].
>
> Full notes: [link to the CHANGELOG]
>
> Hilary
