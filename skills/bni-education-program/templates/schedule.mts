/**
 * schedule — the one place the chapter's calendar is assembled.
 *
 * WHY THIS EXISTS. The same join used to be written three times: once in the
 * education page, once in the reminder emails, once in the playlist job. Each
 * had its own copy of the date parser, its own fetch of the sheet, and its own
 * idea of which source won. They drifted, which is how the site ended up
 * showing one rotation while the sheet showed another, and how a topic could be
 * right on the page and wrong in the email that went out about it.
 *
 * So: two kinds of thing, joined once, here.
 *
 *   THE CALENDAR is the Google Sheet. One row per meeting: when it is, whether
 *   it is online or at the venue, which moment runs, who presents it, who is
 *   speaking. The coordinators own it and it needs no redeploy.
 *
 *   THE LIBRARY is moments.json in the repo. One entry per education moment:
 *   its one-liner, its deck, its CEU hour. A moment is NOT tied to a date - it
 *   is a thing that can be scheduled, moved, or run again next year.
 *
 * Everything else - both pages and both automations - reads the result of this
 * and does no joining of its own.
 *
 * THE SHEET WINS on anything the sheet has an opinion about: format, topic,
 * presenter, speakers. The library is asked only "what is in this moment".
 * Where the sheet cannot be read at all, the response says so in `source` and
 * the caller falls back to whatever it was built with.
 *
 * A MEETING IS ANY DATED ROW in either the roster tab or the speakers tab.
 * They are two tables about the same thing, keyed on the date, so a date that
 * only one of them knows about is still a meeting rather than a row that
 * quietly vanishes.
 */
import type { Context } from "@netlify/functions";

/* Filled in from the chapter's chapter.json at build time. */
const SHEET: string = @@json:roster_sheet@@;
const TABS: { roster: string; members: string; speakers: string } = @@json:tabs@@;
/* How the chapter meets, and so what a BLANK Format cell means: for a chapter
   that is always hybrid, or always in person, there is nothing to decide and
   an empty cell is not "to be confirmed". Only an alternating chapter has to
   say which it is each week. */
const MODE: string = @@json:mode@@;
const VENUE: string = @@json:venue@@;
const NO_MEETING_WORDS: string[] = @@json:no_meeting_words@@;
const WEEKDAY: string = @@json:weekday@@;
const TZ: string = @@json:timezone@@;
const csvUrl = (gid: string) =>
  `https://docs.google.com/spreadsheets/d/${SHEET}/gviz/tq?tqx=out:csv&gid=${gid}`;

/* The gid, never the tab name. gviz ignores a sheet name it does not recognise
   and silently returns the FIRST tab instead - so a renamed tab would hand us
   the roster and we would cheerfully join it against itself. */

const FALLBACK_ORIGIN = @@json:fallback_origin@@;
const TIMEOUT_MS = 8000;

// ---------------------------------------------------------------- reading ---

/** One CSV parser. There used to be two, plus two ad-hoc regexes. */
export function parseCsv(text: string): string[][] {
  const rows: string[][] = [];
  let row: string[] = [], field = "", quoted = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (quoted) {
      if (c === '"') {
        if (text[i + 1] === '"') { field += '"'; i++; } else quoted = false;
      } else field += c;
    } else if (c === '"') quoted = true;
    else if (c === ",") { row.push(field); field = ""; }
    else if (c === "\n") { row.push(field); rows.push(row); row = []; field = ""; }
    else if (c !== "\r") field += c;
  }
  if (field || row.length) { row.push(field); rows.push(row); }
  return rows;
}

const MONTHS = ["jan", "feb", "mar", "apr", "may", "jun",
                "jul", "aug", "sep", "oct", "nov", "dec"];

/** One date parser. "Tue 29 Sep 2026" -> "2026-09-29".
 *
 *  The sheet's Date column is written for people to read, so it is parsed here
 *  rather than asking anyone to type an ISO date into a spreadsheet. */
export function isoFromSheetDate(s: string): string {
  const m = /(\d{1,2})\s+([A-Za-z]{3,})\s+(\d{4})/.exec(s ?? "");
  if (!m) return "";
  const mo = MONTHS.indexOf(m[2].slice(0, 3).toLowerCase()) + 1;
  if (!mo) return "";
  return `${m[3]}-${String(mo).padStart(2, "0")}-${String(+m[1]).padStart(2, "0")}`;
}

/** One normaliser, for every join that keys on a name somebody typed. */
export const norm = (s: string) =>
  (s ?? "").trim().toLowerCase().replace(/\s+/g, " ");

/** Header name -> index, so columns can be reordered in the sheet freely. */
function columns(head: string[]): (name: string) => number {
  const lower = head.map((h) => h.trim().toLowerCase());
  return (name: string) => lower.indexOf(name);
}

/* Retried, because one attempt was not enough.

   On the morning of 28 September all three tabs failed at once, the calendar
   came back empty, and the Monday email told both coordinators their roster
   sheet was broken. It was not - Google simply did not answer for a few
   seconds. Reading the same tabs by hand minutes later worked, and has worked
   every time since.

   Three tries with a short backoff. A blip costs a second; a genuine outage
   still gives up, just not on the strength of one request. */
async function tab(gid: string): Promise<string[][] | null> {
  /* No sheet or no gid configured yet. Never ask gviz with an empty gid: it
     silently answers with the FIRST tab, which would then be joined against
     itself as if it were this one. */
  if (!SHEET || !gid) return null;
  for (let attempt = 1; attempt <= 3; attempt++) {
    try {
      const r = await fetch(csvUrl(gid), {
        headers: { "cache-control": "no-cache" },
        signal: AbortSignal.timeout(TIMEOUT_MS),
      });
      if (!r.ok) throw new Error(String(r.status));
      return parseCsv(await r.text()).filter((row) => row.some((c) => c.trim()));
    } catch (e) {
      console.warn(`tab ${gid} attempt ${attempt} failed:`, String(e));
      if (attempt < 3) await new Promise((r) => setTimeout(r, attempt * 400));
    }
  }
  return null;
}

// --------------------------------------------------------------- the shape --

export type Ep = { n: number; t: string; d: string; u?: string; s?: string };

export type Moment = {
  title: string; one?: string; gap?: string; who?: string;
  ceuSecs?: number; eps?: Ep[]; files?: string;
  /** Delivered before the calendar began. Kept so the page can still list it. */
  deliveredOn?: string;
};

export type Meeting = {
  date: string;
  n: number | null;
  fmt: string;
  fmtConfirmed: boolean;
  noMeeting: boolean;
  reason: string;
  note: string;
  title: string;
  one: string;
  gap: string;
  ceuSecs: number;
  eps: Ep[];
  files: string;
  unprepared: boolean;
  who: string;
  confirmed: boolean;
  speakers: string[];
};

/** A coordinator can say "not decided yet" in whatever words come to hand. */
const TBC = /^(tbc|tba|tbd|to be (confirmed|decided|advised)|not decided|presenter.s choice|their choice)$/i;

/** What the sheet's Format column is allowed to say. Anything else is treated
 *  as "not decided", which shows both sets of details rather than guessing. */
const MODE_FMT: Record<string, string> = {
  hybrid: "hybrid", in_person: "in person", online: "online",
};

export function readFormat(raw: string, mode = MODE, venue = VENUE):
    { fmt: string; confirmed: boolean; off: boolean } {
  const v = norm(raw);
  const usual = MODE_FMT[mode];
  if (!v) return usual ? { fmt: usual, confirmed: true, off: false }
                       : { fmt: "", confirmed: false, off: false };
  if (/^no meeting|^none|^off|^public holiday/.test(v))
    return { fmt: "", confirmed: true, off: true };
  if (/^(hybrid|both|in person \+|in person and)/.test(v))
    return { fmt: "hybrid", confirmed: true, off: false };
  if (/^(online|zoom)/.test(v)) return { fmt: "online", confirmed: true, off: false };
  const place = norm(venue).split(" ")[0];
  if (/^(in person|ftf|face|venue)/.test(v) || (place && v.startsWith(place)))
    return { fmt: "in person", confirmed: true, off: false };
  return usual ? { fmt: usual, confirmed: true, off: false }
               : { fmt: "", confirmed: false, off: false };
}

// ----------------------------------------------------------------- joining --

/* ---- the chapter roll, from BNI itself -----------------------------------

   BNI is the system of record for who is a member. The Members tab existed
   only because this page renders its list in the browser and a plain fetch
   saw nothing - so the roll was retyped by hand and drifted. It was one name
   out within a week: Melissa Hickson had joined and the site said 41.

   The list does come from the server, just not with the page: the page POSTs
   to a display endpoint and injects the HTML. That POST needs no cookie and
   no session - it needs the right FIELDS, and it returns an empty table
   rather than an error when one is missing, which is what made this look
   impossible at first. `languages` is the one that matters; without it the
   response is a well-formed table with no rows in it.

   Rather than hardcode those fields, the page is read and they are lifted out
   of it. If BNI changes the chapter id, the region, or the widget settings,
   this follows; only a change to the shape of the page itself breaks it, and
   that falls back to the Members tab. */

/* The chapter's member-list page on its BNI regional site, from chapter.json
   (data.bni_member_list_url). Empty turns the BNI roll off and the Members
   tab of the roster sheet is used instead. */
const BNI_PAGE: string = @@json:bni_member_list@@;
const BNI_POST = BNI_PAGE
  ? new URL("/bnicms/v3/frontend/memberlist/display", BNI_PAGE).toString() : "";

/** Pull `var name = <value>;` out of an inline script, quotes and nesting
 *  respected, so a JSON blob with semicolons inside it survives. */
export function jsVar(html: string, name: string): string {
  const at = html.indexOf(`var ${name} =`);
  if (at < 0) return "";
  let i = html.indexOf("=", at) + 1, depth = 0, quote = "", out = "";
  for (; i < html.length && out.length < 40000; i++) {
    const c = html[i];
    if (quote) {
      out += c;
      if (c === quote && html[i - 1] !== "\\") quote = "";
      continue;
    }
    if (c === "\"" || c === "'") { quote = c; out += c; continue; }
    if (c === "[" || c === "{") depth++;
    if (c === "]" || c === "}") depth--;
    if (c === ";" && depth <= 0) break;
    out += c;
  }
  return out.trim().replace(/^['"]|['"]$/g, "");
}

/** BNI prints some names shouting and some with a stray double space. */
export function tidyName(s: string): string {
  const n = (s ?? "").replace(/\s+/g, " ").trim();
  // Only a name that is ENTIRELY uppercase is re-cased. Touching any other
  // would turn McDonald into Mcdonald, and a wrong name is worse than a loud one.
  if (!/[a-z]/.test(n) && /[A-Z]{2}/.test(n)) {
    return n.toLowerCase().replace(/\b[a-z]/g, (c) => c.toUpperCase());
  }
  return n;
}

export function namesFromMemberList(html: string): string[] {
  return [...html.matchAll(/class="linkone">([^<]+)<\/a>/g)]
    .map((m) => tidyName(m[1])).filter(Boolean);
}

async function bniRoll(): Promise<string[] | null> {
  if (!BNI_PAGE) return null;
  try {
    const pr = await fetch(BNI_PAGE, {
      headers: { "user-agent": "Mozilla/5.0 (compatible; BNIChapterHub/1.0)" },
      signal: AbortSignal.timeout(TIMEOUT_MS),
    });
    if (!pr.ok) throw new Error(`page ${pr.status}`);
    const page = await pr.text();

    // Reassigned after the var, so take the literal that names the chapter.
    const params = (/parameters\s*=\s*"([^"]*chapterName[^"]*)"/
      .exec(page) ?? [])[1];
    const langs = jsVar(page, "languages");
    const mapped = jsVar(page, "mappedWidgetSettings");
    const hidden = (id: string) =>
      (new RegExp(`id=["']${id}["'][^>]*value=["']([^"']*)`).exec(page) ?? [])[1] ?? "";
    if (!params || !langs) throw new Error("page shape changed");

    const body = new URLSearchParams({
      parameters: params, languages: langs, cmsv3: "true",
      website_type: hidden("website_type"), website_id: hidden("website_id"),
      mappedWidgetSettings: mapped, pageMode: "Live_Site",
    });
    const r = await fetch(BNI_POST, {
      method: "POST", body,
      headers: {
        "content-type": "application/x-www-form-urlencoded",
        "x-requested-with": "XMLHttpRequest",
        referer: BNI_PAGE,
      },
      signal: AbortSignal.timeout(TIMEOUT_MS),
    });
    if (!r.ok) throw new Error(`display ${r.status}`);
    const names = namesFromMemberList(await r.text());
    // An empty table is what a rejected call looks like, so treat it as one.
    return names.length ? names : null;
  } catch (e) {
    console.warn("BNI member list unavailable:", String(e));
    return null;
  }
}

/** Edit distance, capped - only used to ask "did you mean". */
export function editDistance(a: string, b: string): number {
  const m = a.length, n = b.length;
  if (!m || !n) return Math.max(m, n);
  let prev = Array.from({ length: n + 1 }, (_, j) => j);
  for (let i = 1; i <= m; i++) {
    const cur = [i];
    for (let j = 1; j <= n; j++) {
      cur[j] = Math.min(prev[j] + 1, cur[j - 1] + 1,
                        prev[j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1));
    }
    prev = cur;
  }
  return prev[n];
}

/** The prepared moment a typed topic was probably meant to be.
 *
 *  Typing a topic is the one move in the coordinators' week that fails
 *  QUIETLY: a title that does not match exactly is treated as "the presenter
 *  is bringing their own", which is a real and wanted case, so it cannot be an
 *  error - but it also drops the deck. A near miss is almost always a typo,
 *  and it should say so. A quarter of the title is a generous allowance for a
 *  dropped word or a stray plural without matching genuinely different names. */
export function nearest(typed: string, titles: string[]): string | null {
  const a = norm(typed);
  let best: string | null = null, score = Infinity;
  for (const title of titles) {
    const d = editDistance(a, norm(title));
    if (d < score) { score = d; best = title; }
  }
  return best && score > 0 && score <= Math.ceil(a.length / 4) ? best : null;
}

/* ---- the library, as a sheet can read it ---------------------------------

   Served as CSV at /moments.csv so the roster sheet can pull it in with one
   IMPORTDATA formula, and the Topic column can then be a dropdown off that
   range. That kills the mistyped-topic problem at the source rather than
   warning about it afterwards.

   It is PUBLISHED into the sheet rather than kept there. A moment carries a
   deck, speaking notes and three to seven podcast episodes with numbers,
   durations and links - a child table, generated from the shows' own feeds.
   None of that is hand-edited, and a spreadsheet is the wrong shape for it.
   So the sheet gets the TITLES, which are the only part anyone schedules by,
   and they arrive already spelled correctly.

   The "Scheduled" column is the cross-link: it says which date each moment is
   running on, straight out of the same join the site uses. A blank one is a
   moment going spare. */

const csvCell = (s: string) => `"${String(s ?? "").replace(/"/g, '""')}"`;

export function momentsCsv(library: Moment[], meetings: Meeting[]): string {
  const when = new Map<string, string>();
  for (const m of meetings) {
    if (m.title && !m.unprepared) when.set(norm(m.title), m.date);
  }
  const rows = library
    .filter((m) => !m.deliveredOn)
    .sort((a, b) => a.title.localeCompare(b.title))
    .map((m) => [
      m.title,
      String((m.eps ?? []).length),
      String(Math.round((m.ceuSecs ?? 0) / 60)),
      m.files ? "yes" : "",
      when.get(norm(m.title)) ?? "",
    ].map(csvCell).join(","));
  return [["Moment", "Episodes", "Minutes", "Deck", "Scheduled"]
            .map(csvCell).join(","), ...rows].join("\n") + "\n";
}

export function build(
  roster: string[][] | null,
  speakers: string[][] | null,
  membersTab: string[][] | null,
  library: Moment[],
  bni: string[] | null = null,
): { meetings: Meeting[]; archive: Moment[]; members: string[];
     memberSource: string; warnings: string[]; problems: string[] } {
  /* Two audiences, and conflating them is what sent that email.

     warnings  things a COORDINATOR can fix in the sheet - a misspelled name,
               a topic that matches nothing, a date with the wrong year. These
               go in the Monday email, because somebody can act on them.

     problems  things that went wrong on OUR side - a tab that would not load,
               BNI not answering. Nobody in the chapter can do anything about
               these, and telling them their sheet is broken when it is not
               costs trust for nothing. They stay visible here. */
  const warnings: string[] = [];
  const problems: string[] = [];

  // Moments, by title. The library answers "what is in this", nothing else.
  const byTitle = new Map(library.filter((m) => m.title).map((m) => [norm(m.title), m]));

  // ---- the speakers tab: date -> names ------------------------------------
  const speakerRows = new Map<string, { names: string[]; note: string }>();
  if (speakers?.length) {
    const col = columns(speakers[0]);
    const iDate = col("date"), iNote = col("notes");
    const iNames = speakers[0]
      .map((h, i) => (/^speaker/i.test(h.trim()) ? i : -1))
      .filter((i) => i >= 0);
    if (iDate < 0 || !iNames.length) {
      problems.push("speakers tab has no Date or Speaker columns");
    } else {
      for (const row of speakers.slice(1)) {
        const date = isoFromSheetDate(row[iDate] ?? "");
        if (!date) continue;
        speakerRows.set(date, {
          names: iNames.map((i) => (row[i] ?? "").trim()).filter(Boolean),
          note: iNote >= 0 ? (row[iNote] ?? "").trim() : "",
        });
      }
    }
  }

  // ---- the roster tab: the meeting itself ---------------------------------
  const meetings = new Map<string, Meeting>();
  const blank = (date: string): Meeting => ({
    date, n: null, fmt: "", fmtConfirmed: false, noMeeting: false, reason: "",
    note: "", title: "", one: "", gap: "", ceuSecs: 0, eps: [], files: "",
    unprepared: false, who: "", confirmed: false, speakers: [],
  });

  if (roster?.length) {
    const col = columns(roster[0]);
    const iDate = col("date"), iFmt = col("format"), iTopic = col("topic");
    const iWho = col("presenter"), iOk = col("confirmed"), iNote = col("notes");
    if (iDate < 0) {
      problems.push("roster tab has no Date column");
    } else {
      for (const row of roster.slice(1)) {
        const date = isoFromSheetDate(row[iDate] ?? "");
        if (!date) continue;
        const m = meetings.get(date) ?? blank(date);

        const f = readFormat(iFmt >= 0 ? (row[iFmt] ?? "") : "");
        m.fmt = f.fmt; m.fmtConfirmed = f.confirmed; m.noMeeting = f.off;

        m.who = iWho >= 0 ? (row[iWho] ?? "").trim() : "";
        m.confirmed = iOk >= 0 && /^(y|yes|true|1|x)$/i.test((row[iOk] ?? "").trim());
        /* The Notes column is where the coordinators write to each other -
           "text to nominate", "needs the projector". Deliberately NOT carried
           into the response: /schedule is public, so publishing it here would
           leave a to-do list in view-source even once no page rendered it.
           Nothing reads it; if something needs to, it can read the sheet. */

        const typed = iTopic >= 0 ? (row[iTopic] ?? "").trim() : "";
        if (m.noMeeting) {
          // The Topic cell is where somebody writes why there is no meeting.
          m.reason = typed.replace(/^no meeting\s*[-–—]\s*/i, "").trim();
          m.title = typed || "No meeting";
          /* A morning off still has a CEU hour - Cup Day has no meeting and
             the credit still counts - so the library is asked even here. */
          const off = byTitle.get(norm(typed));
          if (off) { m.eps = off.eps ?? []; m.ceuSecs = off.ceuSecs ?? 0;
                     m.one = off.one ?? ""; m.gap = off.gap ?? ""; }
        } else if (typed) {
          const found = byTitle.get(norm(typed));
          if (found) {
            m.title = found.title;
            m.one = found.one ?? "";
            m.gap = found.gap ?? "";
            m.ceuSecs = found.ceuSecs ?? 0;
            m.eps = found.eps ?? [];
            m.files = found.files ?? "";
          } else {
            /* A moment nobody has written up - usually the presenter is bringing
               their own on the day. Show what was typed, and drop the DECK: it
               belongs to a different moment and would send them to the wrong
               slides. The CEU HOUR is filled in below from whatever this date
               was prepared with, because an hour of BNI education earns the
               credit whatever the talk turns out to be. */
            m.title = TBC.test(typed) ? "Topic to be confirmed" : typed;
            m.unprepared = true;
            if (!TBC.test(typed)) {
              const meant = nearest(typed, [...byTitle.values()].map((x) => x.title));
              if (meant) {
                warnings.push(`${date}: "${typed}" is not a prepared moment - ` +
                  `did you mean "${meant}"? As typed it loses the deck.`);
              }
            }
          }
        }
        meetings.set(date, m);
      }
    }
  } else {
    problems.push("roster tab could not be read");
  }

  // ---- dates only the speakers tab knows about ----------------------------
  for (const [date, s] of speakerRows) {
    const m = meetings.get(date) ?? blank(date);
    m.speakers = s.names;
    if (!m.note) m.note = s.note;   // public holidays, not private to-dos
    if (!meetings.has(date)) {
      // Not in the roster: a meeting we know about with no moment assigned.
      if (NO_MEETING_WORDS.some((w) => s.note.toLowerCase().includes(w))) {
        m.noMeeting = true; m.fmtConfirmed = true;
        m.reason = s.note; m.title = `No meeting - ${s.note}`;
      } else {
        warnings.push(`${date} is in Speakers but not in the roster`);
      }
    }
    meetings.set(date, m);
  }

  const ordered = [...meetings.values()].sort((a, b) => a.date.localeCompare(b.date));

  /* Week numbers are POSITIONS, not data. The chapter counts its own weeks from
     when it launched, so the sheet says 3..15 where the program says 1..12;
     deriving it here means the two can disagree without anything breaking. */
  let n = 0;
  for (const m of ordered) m.n = m.noMeeting ? null : ++n;

  /* A mistyped year in one Date cell renumbers the whole program, because
     the numbers are positions. "Tue 3 Feb 2026" instead of 2027 put a
     meeting eight months before the rest and made Givers Gain week 2.
     Nothing here drops the row - guessing which date somebody meant is
     worse than showing what they typed - but a gap this large is almost
     always a typo, and it should be visible rather than silently renumbering.
     90 days clears the Christmas break, which is the longest real gap. */
  for (let i = 1; i < ordered.length; i++) {
    const gap = (Date.parse(ordered[i].date) - Date.parse(ordered[i - 1].date))
              / 86400000;
    if (gap > 90) {
      warnings.push(`${ordered[i - 1].date} and ${ordered[i].date} are ` +
        `${Math.round(gap)} days apart - check for a mistyped date`);
    }
  }

  /* An unwritten topic keeps whatever CEU hour this date was prepared with.
     Done after ordering so it can be matched on position, not on a title that
     by definition does not match anything. */
  const prepared = library.filter((m) =>
    !m.deliveredOn && m.eps?.length && !/^no meeting/i.test(m.title));
  for (const m of ordered) {
    if (!m.unprepared || m.eps.length || m.n === null) continue;
    const fallback = prepared[m.n - 1];
    if (fallback) { m.eps = fallback.eps ?? []; m.ceuSecs = fallback.ceuSecs ?? 0; }
  }

  // ---- the chapter roll ---------------------------------------------------
  /* BNI first: it is the system of record, and nobody has to keep it up to
     date by hand. The Members tab is the fallback, and the response says
     which was used so a silent switch to a stale list is visible. */
  let members: string[] = [];
  let memberSource = "none";
  let sheetRoll: string[] = [];
  if (membersTab?.length) {
    const col = columns(membersTab[0]);
    const iName = col("name");
    if (iName < 0) problems.push("members tab has no Name column");
    else sheetRoll = membersTab.slice(1)
      .map((r) => (r[iName] ?? "").trim()).filter(Boolean);
  }
  if (bni?.length) {
    members = bni;
    memberSource = "bni";
    /* There was a warning here comparing the tab with BNI. It made sense
       while the tab was still maintained; now that it is hidden and frozen
       it differs by more names every time somebody joins, and said so every
       Monday. A fallback being out of date is expected, not news. */
  } else {
    members = sheetRoll;
    memberSource = sheetRoll.length ? "sheet" : "none";
    problems.push("BNI member list unavailable - using the Members tab");
  }

  /* A presenter whose name does not match the chapter roll gets NO reminder
     emails - the address is looked up by name, so a typo finds nobody. That
     used to surface only in the Monday nudge, by which time the fortnight and
     one-week reminders had already been missed.

     Only a NEAR miss is flagged. A name that is nothing like a member is a
     guest presenter - Helen Searle is not in the chapter and should not be
     nagged about - whereas one letter out is a typo every time. */
  if (members.length) {
    for (const m of ordered) {
      if (!m.who || m.noMeeting) continue;
      if (members.some((x) => norm(x) === norm(m.who))) continue;
      const meant = nearest(m.who, members);
      if (meant) {
        warnings.push(`${m.date}: presenter "${m.who}" is not on the chapter ` +
          `roll - did you mean "${meant}"? As typed they get no reminders.`);
      }
    }
  }

  const archive = library.filter((m) => m.deliveredOn)
    .sort((a, b) => (b.deliveredOn ?? "").localeCompare(a.deliveredOn ?? ""));

  return { meetings: ordered, archive, members, memberSource, warnings, problems };
}

// ---------------------------------------------------------------- handler ---

async function libraryJson(origin: string): Promise<Moment[]> {
  /* The origin of the request we are answering, first. A draft deploy then
     reads ITS OWN library instead of production's - which is how a preview
     came back saying everything was fine while quietly testing live data.
     DEPLOY_URL looked like the answer and is not set at function runtime. */
  const bases = [...new Set([origin, process.env.URL,
                             FALLBACK_ORIGIN].filter(Boolean))];
  for (const base of bases) {
    try {
      const r = await fetch(`${base}/moments.json`, {
        signal: AbortSignal.timeout(TIMEOUT_MS),
      });
      if (r.ok) return await r.json();
    } catch (e) {
      console.warn(`${base}/moments.json failed:`, String(e));
    }
  }
  return [];
}

/* ---- a sample calendar, before the chapter has a roster sheet -------------

   A brand-new chapter's first deploy has no sheet yet, and a site that says
   "Loading the next meeting" forever looks broken to the people being asked
   to adopt it. So, until data.roster_sheet_id is set: the next twelve
   meetings on the chapter's weekday, with the library's moments in order and
   nobody presenting. Marked `sample` in the response, and the reminder job
   refuses to act on it. The moment a sheet is configured this is never used. */
const DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];

export function sampleRoster(library: Moment[], weekday = WEEKDAY,
                             today = new Intl.DateTimeFormat("en-CA", {
                               timeZone: TZ, year: "numeric", month: "2-digit", day: "2-digit",
                             }).format(new Date())): string[][] {
  const want = DAYS.indexOf(weekday);
  const d = new Date(today + "T00:00:00Z");
  while (d.getUTCDay() !== want) d.setUTCDate(d.getUTCDate() + 1);
  const moments = library.filter((m) => !m.deliveredOn && !/^no meeting/i.test(m.title));
  const rows: string[][] = [["Date", "Format", "Topic", "Presenter", "Confirmed"]];
  for (let i = 0; i < 12; i++) {
    const label = d.toLocaleDateString("en-AU", {
      timeZone: "UTC", weekday: "short", day: "numeric", month: "short", year: "numeric",
    }).replace(/,/g, "");
    rows.push([label, "", moments.length ? moments[i % moments.length].title : "", "", ""]);
    d.setUTCDate(d.getUTCDate() + 7);
  }
  return rows;
}

export default async (req: Request, _ctx: Context): Promise<Response> => {
  const origin = (() => {
    try { return new URL(req.url).origin; } catch { return ""; }
  })();
  const [rosterRead, speakers, membersTab, library, bni] = await Promise.all([
    tab(TABS.roster), tab(TABS.speakers), tab(TABS.members),
    libraryJson(origin), bniRoll(),
  ]);
  const sample = !SHEET;
  const roster = rosterRead ?? (sample ? sampleRoster(library) : null);

  const out = build(roster, speakers, membersTab, library, bni);
  if (sample) {
    out.warnings.unshift("No roster sheet yet: this is a sample calendar. Set " +
      "data.roster_sheet_id in chapter.json to use the chapter's own.");
  }

  /* The sheet asks for this one; everything else wants the JSON.

     Matched on the PATH, not on a query parameter. A Netlify redirect can
     carry ?as=... in its target, but the function still sees the URL the
     browser asked for - so the parameter was never there to read, and
     /moments.csv quietly served JSON. */
  const asked = new URL(req.url);
  if (asked.pathname.endsWith("moments.csv") ||
      asked.searchParams.get("as") === "moments.csv") {
    return new Response(momentsCsv(library, out.meetings), {
      headers: {
        "content-type": "text/csv; charset=utf-8",
        "cache-control": "public, max-age=60, stale-while-revalidate=240",
      },
    });
  }

  return new Response(JSON.stringify({
    generated: new Date().toISOString(),
    source: {
      roster: sample ? "sample" : !!roster, speakers: !!speakers,
      members: out.memberSource, library: library.length > 0,
    },
    ...out,
  }), {
    headers: {
      "content-type": "application/json",
      /* Four tabs and a library, so it is not free. Fresh for two minutes -
         a coordinator wants to see a change quickly - then served instantly
         from the edge while it refreshes behind the request. */
      "cache-control": "public, max-age=60, stale-while-revalidate=240",
    },
  });
};
