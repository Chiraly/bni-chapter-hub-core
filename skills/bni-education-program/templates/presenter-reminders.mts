/**
 * presenter-reminders — nudge each week's presenter, and flag unassigned weeks.
 *
 * Runs once a day, early in the chapter's morning. For every week it works out
 * how many days until the meeting and sends a reminder at each stage in
 * chapter.json reminders.stages (by default 14, 7 and 1 days out), plus one on
 * the day the meeting deck is built (education.deck_deadline.days_before) -
 * the last chance to change anything.
 *
 * Both coordinators are copied on every one, so either of them can see at a
 * glance what has gone out and to whom, without asking the other.
 *
 * On the nudge day (Monday by default) it also emails the coordinators a list of unassigned weeks in the
 * next six, so gaps surface early instead of the week before.
 *
 * Every email replies to the coordinators, so "I can't do it" lands with both
 * of them at once.
 *
 * Environment variables (Netlify UI, never the repo):
 *   MAIL_FROM           e.g. BNI Riverside <education@riverside-bni.com.au>
 *                       The domain must be verified with whichever service
 *                       sends the mail (SPF and DKIM), or it lands in spam.
 *   COORDINATORS        comma-separated coordinator addresses
 *
 *   and ONE way of sending:
 *   POSTMARK_TOKEN      a Postmark server API token, or
 *   SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS
 *                       any SMTP service (Google Workspace, Microsoft 365,
 *                       Brevo, Mailgun, SendGrid, your web host...).
 *                       SMTP_PORT 465 = implicit TLS; 587 = STARTTLS.
 *   PRESENTER_EMAILS    JSON mapping presenter NAME -> email, matching the
 *                       Presenter column of the roster sheet, e.g.
 *                       {"Brei Scolaro":"brei@example.com"}
 *                       Week numbers still work as keys, as a fallback.
 *
 * Who presents each week comes from the coordinators' roster sheet, not from
 * weeks.json, so a swap takes effect without a redeploy. Keying the addresses
 * by name rather than by week is what makes that work: move a name to another
 * week in the sheet and the reminders follow it there.
 *
 * Presenter addresses deliberately live in the environment rather than in
 * weeks.json or the sheet, because both of those are served publicly.
 *
 * Idempotency: the thresholds are exact (14 / 7 / 1), and the schedule fires
 * once a day, so each reminder goes once. Manually re-running it on the same
 * day would send again.
 */
import type { Config } from "@netlify/functions";

/* Everything chapter-specific is filled in from chapter.json at build time. */
const TZ: string = @@json:timezone@@;
/* Netlify sets URL to the site's primary address, so when a custom domain
   becomes primary this follows it with no code change. The literal is only
   the local fallback. */
const SITE = process.env.URL ?? @@json:fallback_origin@@;
// The education page moved under /education/ when the members' home page
// went in. weeks.json stays at the site root, where the functions look.
const EDU = `${SITE}/education/`;

// The Education Coordinators' roster sheet. Same sheet the education page
// reads, so the page and these emails can never disagree about who is on.
const ROSTER_ID: string = @@json:roster_sheet@@;
// The editable sheet, for the Monday nudge - the whole point of that email is
// to get somebody assigned, so it should open the place you do that.
const ROSTER_URL = `https://docs.google.com/spreadsheets/d/${ROSTER_ID}/edit`;

// The chapter playlist. Presenters are prompted to point at the QR code on
// their closing slide, so the link belongs in their reminder too.
const PLAYLIST = process.env.SPOTIFY_PLAYLIST_ID
  ? `https://open.spotify.com/playlist/${process.env.SPOTIFY_PLAYLIST_ID}` : "";

/* Days out -> how the reminder says when. The deadline day is the one the
   finished .pptx is due, and that reminder leads with the deadline rather
   than the meeting. Both from chapter.json. */
const STAGES: Record<string, string> = @@json:stages@@;
const DEADLINE_DAY: number = @@json:deadline_days@@;
const NUDGE_DAY: string = @@json:nudge_weekday@@;

/* The wording. Core templates/emails/reminders.json, with the chapter's own
   emails/reminders.json laid over it. {name} is filled in per email. */
const COPY: Record<string, string> = @@json:emails@@;
const fill = (s: string, v: Record<string, string | number>) =>
  (s ?? "").replace(/\{(\w+)\}/g, (m, k) => (k in v ? String(v[k]) : m));

/** The plain-text twin of an HTML snippet, so the copy is written once. */
export function plain(html: string): string {
  return (html ?? "")
    .replace(/<br\s*\/?>/gi, "\n").replace(/<\/p>\s*/gi, "\n\n")
    .replace(/<a [^>]*href="([^"]*)"[^>]*>([^<]*)<\/a>/gi, "$2 ($1)")
    .replace(/<[^>]+>/g, "")
    .replace(/&mdash;/g, "-").replace(/&middot;/g, "-").replace(/&nbsp;/g, " ")
    .replace(/&ldquo;|&rdquo;/g, '"').replace(/&amp;/g, "&").replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">").replace(/[ \t]+\n/g, "\n").replace(/\n{3,}/g, "\n\n")
    .replace(/[ \t]{2,}/g, " ").trim();
}

type Ep = { n: number; t: string; d: string };
type Week = {
  n: number; date: string; title: string; who: string; one: string; gap: string;
  ceuSecs: number; eps: Ep[];
  // the week's Google Drive folder, holding the deck and the speaker notes
  files?: string;
};

const chapterToday = () =>
  new Intl.DateTimeFormat("en-CA", {
    timeZone: TZ, year: "numeric", month: "2-digit", day: "2-digit",
  }).format(new Date());

const isNudgeDay = () =>
  new Intl.DateTimeFormat("en-AU", { timeZone: TZ, weekday: "short" })
    .format(new Date()).startsWith(NUDGE_DAY.slice(0, 3));

/** Midnight UTC for a YYYY-MM-DD string. Date.UTC months are 0-indexed, which
 *  is easy to get wrong: the error cancels out inside one month and only shows
 *  up across a month boundary, where it silently skips a reminder. */
function utcDay(iso: string): number {
  const [y, m, d] = iso.split("-").map(Number);
  return Date.UTC(y, m - 1, d);
}

/** Whole days from today (chapter time) to a YYYY-MM-DD meeting date. */
export function daysUntil(date: string, today: string): number {
  return Math.round((utcDay(date) - utcDay(today)) / 86_400_000);
}

const prettyDate = (iso: string) =>
  new Date(iso + "T00:00:00Z").toLocaleDateString("en-AU", {
    timeZone: "UTC", weekday: "long", day: "numeric", month: "long",
  });

const esc = (s: string) =>
  s.replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]!));

async function send(opts: {
  to: string[]; cc?: string[]; replyTo: string[]; subject: string;
  html: string; text: string;
}) {
  /* Postmark if there is a token, otherwise plain SMTP. Either way the sending
     domain has to be verified (SPF and DKIM) or the mail lands in spam. */
  if (process.env.POSTMARK_TOKEN) {
    const r = await fetch("https://api.postmarkapp.com/email", {
      method: "POST",
      headers: {
        "X-Postmark-Server-Token": process.env.POSTMARK_TOKEN,
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({
        From: process.env.MAIL_FROM,
        To: opts.to.join(", "),
        Cc: opts.cc?.length ? opts.cc.join(", ") : undefined,
        ReplyTo: opts.replyTo.join(", "),
        Subject: opts.subject,
        HtmlBody: opts.html,
        TextBody: opts.text,
        MessageStream: "outbound",
      }),
    });
    if (!r.ok) throw new Error(`postmark ${r.status}: ${await r.text()}`);
    return;
  }
  const { createTransport } = await import("nodemailer");
  const port = Number(process.env.SMTP_PORT ?? 587);
  const mailer = createTransport({
    host: process.env.SMTP_HOST, port, secure: port === 465,
    auth: { user: process.env.SMTP_USER, pass: process.env.SMTP_PASS },
  });
  await mailer.sendMail({
    from: process.env.MAIL_FROM,
    to: opts.to.join(", "),
    cc: opts.cc?.length ? opts.cc.join(", ") : undefined,
    replyTo: opts.replyTo.join(", "),
    subject: opts.subject, html: opts.html, text: opts.text,
  });
}

const mailerConfigured = () =>
  Boolean(process.env.POSTMARK_TOKEN ||
          (process.env.SMTP_HOST && process.env.SMTP_USER && process.env.SMTP_PASS));

function reminderBody(w: Week, when: string, coordinators: string[], days = 0) {
  /* The deck is built for them and already lodged, so there is nothing to
     send. The deadline only bites if they change it. The deadline-day
     reminder is the one that says "today". */
  const lastChance = days === DEADLINE_DAY;
  const v = {
    when, title: esc(w.title), n: w.n, date: prettyDate(w.date), one: esc(w.one ?? ""),
    files: w.files ?? "", edu: EDU, playlist: PLAYLIST,
  };
  const f = (k: string) => fill(COPY[k], v);
  const box = (inner: string) =>
    `<p style="margin:0 0 1.1rem;padding:.8rem .9rem;background:#F6F6F8;border-left:3px solid #CF2030">${inner}</p>`;
  const para = (inner: string, style = "") =>
    `<p style="margin:0 0 1.1rem${style}">${inner}</p>`;

  const parts = [
    `<p style="font-size:13px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#CF2030;margin:0 0 .5rem">${f("reminder_kicker")}</p>`,
    `<h2 style="margin:0 0 .35rem;font-size:22px;line-height:1.25">${esc(w.title)}</h2>`,
    para(f("reminder_meta"), ";color:#64666A"),
    w.one ? para(f("reminder_one_thing")) : "",
    w.files ? para(f("reminder_files")) : "",
    para(f("reminder_notes")),
    PLAYLIST ? para(f("reminder_playlist"), ";color:#64666A;font-size:14px") : "",
    box(f(lastChance ? "deadline_today" : "deadline_normal")),
    box(f("cant_make_it")),
    `<p style="margin:1.5rem 0 0;color:#64666A;font-size:14px">${f("signoff")}</p>`,
  ].filter(Boolean);

  const html = `
<div style="font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;font-size:16px;line-height:1.55;color:#121316;max-width:34rem">
  ${parts.join("\n  ")}
</div>`.trim();
  const text = parts.map(plain).filter(Boolean).join("\n\n");
  return { html, text };
}

/** Sent only when the calendar could not be read, so reminders were skipped.
 *  Deliberately calm: nothing in the sheet needs fixing, and saying it does
 *  sends two people looking for a fault that is not there. */
function outageBody(problems: string[]) {
  const what = problems.map((p) => esc(p)).join("<br>") || "the schedule could not be read";
  const html = `
<div style="font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;font-size:16px;line-height:1.55;color:#121316;max-width:34rem">
  ${COPY.outage_body}
  <p style="margin:0 0 1rem;color:#64666A;font-size:14px">What it reported:<br>${what}</p>
  <p style="margin:0;color:#64666A;font-size:14px">${COPY.outage_footer}</p>
</div>`.trim();
  const text = [plain(COPY.outage_body), "What it reported:\n" + plain(what),
                plain(COPY.outage_footer)].join("\n\n");
  return { html, text };
}

function unassignedBody(weeks: Week[], checks: string[] = []) {
  const rows = weeks.map((w) =>
    `<tr><td style="padding:.3rem .9rem .3rem 0;color:#64666A;white-space:nowrap">Week ${w.n} &middot; ${prettyDate(w.date)}</td><td style="padding:.3rem 0"><strong>${esc(w.title)}</strong>${w.who ? `<br><span style="color:#B2451F">named as &ldquo;${esc(w.who)}&rdquo; &mdash; no address on file, check the spelling</span>` : ""}</td></tr>`,
  ).join("");
  const html = `
<div style="font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;font-size:16px;line-height:1.55;color:#121316;max-width:34rem">
  ${weeks.length ? `
  <p style="margin:0 0 1rem">${weeks.length} week${weeks.length === 1 ? "" : "s"}
     in the next six ${weeks.length === 1 ? "needs" : "need"} attention &mdash;
     nobody assigned, or a name that finds no address:</p>
  <table style="border-collapse:collapse;margin:0 0 1.2rem">${rows}</table>` : ""}
  ${checks.length ? `
  <p style="margin:0 0 .6rem"><strong>Worth a look in the roster sheet:</strong></p>
  <ul style="margin:0 0 1.2rem;padding-left:1.1rem;color:#B2451F">
    ${checks.map((c) => `<li style="margin:0 0 .4rem">${esc(c)}</li>`).join("")}
  </ul>
  <p style="margin:0 0 1.1rem;color:#64666A;font-size:14px">
    These are spotted automatically by comparing the sheet with the chapter
    roll and the list of prepared moments. A name or topic that is one letter
    out still looks right in the sheet, but finds nothing.</p>` : ""}
  <p style="margin:0 0 1.1rem">${fill(COPY.nudge_open_roster, { roster: ROSTER_URL })}</p>
  ${weeks.length ? `<p style="margin:0;color:#64666A;font-size:14px">
    Reminders only go out once a week has someone assigned, so these are the ones
    to fill first. A week also lands here if the name in the sheet has no email
    address on file &mdash; usually a spelling that doesn't match.</p>` : ""}
</div>`.trim();
  const text = (weeks.length
    ? `${weeks.length} week(s) in the next six need attention - nobody assigned, or a name that finds no address:\n\n`
    : ``)
    + weeks.map((w) => `  Week ${w.n} - ${prettyDate(w.date)} - ${w.title}${w.who ? ` - named as \"${w.who}\", no address on file` : ""}`).join("\n")
    + (checks.length
        ? (weeks.length ? `\n\n` : ``) + `Worth a look in the roster sheet:\n`
          + checks.map((c) => `  - ${c}`).join("\n")
        : ``)
    + `\n\nOpen the roster sheet: ${ROSTER_URL}`
    + `\nPut a full name in the Presenter column and everything follows.`
    + (weeks.length
        ? `\n\nReminders only go out once a week has someone assigned. A week also
lands here if the name in the sheet has no email address on file.`
        : ``);
  return { html, text };
}

/* The site's own data, fetched over the network because that is the only way a
   function can read a published file.
 *
 * process.env.URL is whatever Netlify considers primary, which flips to a new
 * custom domain the moment it is configured - before Let's Encrypt has issued
 * the certificate for it. In that window a fetch to the primary URL fails the
 * TLS handshake and takes the whole run down with it. So: try primary, and fall
 * back to the netlify.app address, which always has a valid certificate.
 */
const FALLBACK_ORIGIN: string = @@json:fallback_origin@@;

async function fetchSiteJson(path: string): Promise<any> {
  const bases = [...new Set([process.env.URL, FALLBACK_ORIGIN].filter(Boolean))];
  let last: unknown;
  for (const base of bases) {
    try {
      const r = await fetch(`${base}${path}`);
      if (!r.ok) throw new Error(`${path} ${r.status}`);
      return await r.json();
    } catch (e) {
      last = e;
      console.warn(`${base}${path} failed, trying next:`, String(e));
    }
  }
  throw new Error(`could not read ${path}: ${String(last)}`);
}

export default async (): Promise<Response> => {
  const from = process.env.MAIL_FROM;
  const coordinators = (process.env.COORDINATORS ?? "")
    .split(",").map((s) => s.trim()).filter(Boolean);

  if (!mailerConfigured() || !from || !coordinators.length) {
    return new Response("reminders not configured - skipping", { status: 200 });
  }

  let emails: Record<string, string> = {};
  try {
    emails = JSON.parse(process.env.PRESENTER_EMAILS ?? "{}");
  } catch {
    return new Response("PRESENTER_EMAILS is not valid JSON", { status: 500 });
  }

  /* The calendar, already assembled: the roster sheet joined to the moments
     library, once, by the schedule function. This used to fetch weeks.json and
     the sheet and do that join itself, which is how an email could go out
     naming a topic the page had already moved. */
  const { meetings, warnings, problems, source } =
    await fetchSiteJson("/schedule");
  const checks: string[] = warnings ?? [];
  const weeks: Week[] = meetings ?? [];

  /* An unreadable roster means an EMPTY calendar, and an empty calendar means
     this loop finds nobody due a reminder and cheerfully sends nothing. That
     is the quiet half of what went wrong on 28 September: the coordinators got
     an alarming email, and any presenter due a reminder that morning got
     nothing at all, with no sign either had happened.

     So: refuse to act on a calendar we could not read, and say so plainly to
     the two people who need to know reminders did not go out. It is not their
     sheet, and the message says so. */
  const calendarUnreadable = source?.roster === false || !weeks.length;
  if (calendarUnreadable) {
    const { html, text } = outageBody(problems ?? []);
    await send({
      to: coordinators, replyTo: coordinators,
      subject: COPY.outage_subject,
      html, text,
    });
    return new Response(
      `calendar unreadable - skipped: ${(problems ?? []).join("; ")}`,
      { status: 200 });
  }

  // Addresses are matched on the name in the Presenter column, case- and
  // space-insensitively, so "brei scolaro" in the env still finds "Brei Scolaro".
  const byName = new Map(
    Object.entries(emails).map(([k, v]) => [k.trim().toLowerCase(), v]));

  /* Role prefixes creep into the Presenter column - "Visitor Host - Gina
     Collins" instead of "Gina Collins" - and used to mean that week silently
     got no reminder. Try the whole string first, then whatever follows the
     last dash. That is still an exact match on a full name, so it forgives the
     prefix without ever guessing from a partial one: a genuine typo in the
     name itself still finds nobody, and surfaces in the Monday nudge. */
  const addressFor = (w: Week) => {
    const raw = (w.who ?? "").trim();
    const look = (s: string) => byName.get(s.trim().toLowerCase());
    const afterDash = raw.split(/\s+[-–—]\s+/).pop() ?? raw;
    return look(raw) ?? look(afterDash) ?? emails[String(w.n)];
  };

  const today = chapterToday();
  const done: string[] = [];

  for (const w of weeks) {
    const days = daysUntil(w.date, today);
    const when = STAGES[String(days)];
    if (!when) continue;

    const to = addressFor(w);
    if (!to) {
      done.push(`week ${w.n}: ${days}d out, no email on file for "${w.who}"`);
      continue;
    }

    const { html, text } = reminderBody(w, when, coordinators, days);
    await send({
      to: [to],
      cc: coordinators,                 // both coordinators see every reminder
      replyTo: coordinators,
      subject: fill(COPY.reminder_subject, { when, title: w.title }),
      html, text,
    });
    done.push(`week ${w.n}: ${days}d reminder -> ${to}`);
  }

  if (isNudgeDay()) {
    const soon = weeks.filter((w) => {
      const d = daysUntil(w.date, today);
      // A week counts as unassigned if the sheet names nobody, or names
      // somebody with no address on file, or still holds a placeholder role.
      return d > 0 && d <= 42 &&
        (!w.who || !addressFor(w) || /^(tbc|unassigned)$/i.test(w.who.trim()));
    });
    /* The schedule spots things nobody would otherwise see: a topic that
       nearly matches a prepared one, a presenter a letter off the chapter
       roll, a date typed with the wrong year. Those used to sit in a JSON
       field that only I ever opened. Monday morning, in front of the two
       people who can fix them, is where they are worth something. */
    if (soon.length || checks.length) {
      const { html, text } = unassignedBody(soon, checks);
      const bits: string[] = [];
      if (soon.length) {
        bits.push(`${soon.length} education week${soon.length === 1 ? "" : "s"} to fill`);
      }
      if (checks.length) {
        bits.push(`${checks.length} thing${checks.length === 1 ? "" : "s"} to check`);
      }
      await send({
        to: coordinators, replyTo: coordinators,
        subject: bits.join(", and "),
        html, text,
      });
      done.push(`monday nudge -> ${coordinators.join(", ")} ` +
                `(${soon.length} to fill, ${checks.length} to check)`);
    }
  }

  const msg = done.length ? done.join("; ") : `nothing due on ${today}`;
  console.log(msg);
  return new Response(msg, { status: 200 });
};

/* chapter.json reminders.cron. The default, 20:00 UTC daily, is 6am AEST /
   7am AEDT the next morning - early in an east-coast Australian chapter's day
   on both sides of daylight saving. */
export const config: Config = { schedule: "@@cron:reminders@@" };
