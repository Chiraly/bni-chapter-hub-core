/**
 * referrals-data — the referral board, merged, as JSON for the page.
 *
 * The page never reads the submissions directly - it asks this, which holds the
 * API token the browser never sees.
 *
 * There is no password on any of it. Members decide for themselves what to put
 * on the board, and nothing appears on it that somebody did not type into the
 * form. A shared password would have bought no real privacy - everyone in the
 * chapter would have had it - at the cost of a login box that is poor on a
 * phone.
 *
 * MERGE RULE, per person, per field: the most recent non-empty answer wins.
 *
 * That is what lets a member fill the form in again with only the one field
 * they want to change. Blank means "leave this as it was", not "clear it" -
 * so a field cannot be emptied from the form. Clearing one, or removing
 * somebody who has left, is a coordinator job.
 *
 * Environment (Netlify UI, never the repo):
 *   NETLIFY_API_TOKEN   personal access token, read access to the submissions
 *   SITE_ID             this site's id
 *
 * Without them it returns an empty board and says so, rather than failing, so
 * the page still renders its form.
 */
import type { Context } from "@netlify/functions";

const FORM_NAME = "referrals";

/* The chapter roll, from the schedule function - the same list the form offers
   in its dropdown, read from the same place by the same code. The board shows
   current members and nobody else, so taking somebody out of the Members tab
   takes their asks off the board. That is the whole removal process.

   Filtered HERE rather than in the page, so a departed member's asks are not
   merely hidden - they never leave the server.

   This used to fetch and parse the sheet itself, which made four different
   files that each knew how to read a Google Sheet. Now there is one. */
const FALLBACK_ORIGIN: string = @@json:fallback_origin@@;

/** One spelling for one person: case and stray spaces are not differences
 *  worth dropping somebody's entry over. */
export const norm = (s: string) =>
  (s ?? "").trim().toLowerCase().replace(/\s+/g, " ");

async function members(): Promise<Set<string>> {
  const bases = [...new Set([process.env.URL, FALLBACK_ORIGIN].filter(Boolean))];
  for (const base of bases) {
    try {
      const r = await fetch(`${base}/schedule`, { signal: AbortSignal.timeout(8000) });
      if (!r.ok) continue;
      const d = await r.json();
      return new Set((d.members ?? []).map(norm).filter(Boolean));
    } catch (e) {
      console.warn(`${base}/schedule failed:`, String(e));
    }
  }
  return new Set();          // learned nothing; the caller fails OPEN
}

/** Form field name -> the key the page uses. Anything else is ignored, so
 *  adding a question to the form cannot break the board. */
const FIELDS: Record<string, string> = {
  name: "name",
  bread: "bread",
  cream: "cream",
  dream: "dream",
  specific: "specific",
};

type Ask = {
  name: string;
  bread?: string; cream?: string; dream?: string; specific?: string;
  /** per field, when it was last set - so the page can date each line */
  at: Record<string, string>;
  updated: string;
};

async function submissions(token: string, siteId: string) {
  // 200 is well past a chapter's worth; the API pages beyond that if ever needed
  const url = `https://api.netlify.com/api/v1/sites/${siteId}/submissions` +
              `?per_page=200`;
  const r = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
  if (!r.ok) throw new Error(`submissions ${r.status}: ${await r.text()}`);
  return (await r.json()) as Array<{
    form_name?: string; created_at?: string; data?: Record<string, string>;
  }>;
}

export function merge(rows: Array<{ created_at?: string; data?: Record<string, string> }>): Ask[] {
  // oldest first, so a later submission overwrites field by field
  const ordered = [...rows].sort(
    (a, b) => Date.parse(a.created_at ?? "") - Date.parse(b.created_at ?? ""));

  const board = new Map<string, Ask>();
  for (const row of ordered) {
    const d = row.data ?? {};
    const name = (d[FIELDS.name] ?? "").trim();
    if (!name) continue;                       // unattributable, skip
    const when = row.created_at ?? "";
    const key = name.toLowerCase();

    const rec = board.get(key) ?? { name, at: {}, updated: when } as Ask;
    rec.name = name;                           // keep the latest spelling
    for (const field of ["bread", "cream", "dream", "specific"] as const) {
      const value = (d[FIELDS[field]] ?? "").trim();
      if (!value) continue;                    // blank = leave it alone
      rec[field] = value;
      rec.at[field] = when;
    }
    rec.updated = when;
    board.set(key, rec);
  }

  // most recently touched first - the board reads as "what changed lately"
  return [...board.values()]
    .sort((a, b) => Date.parse(b.updated) - Date.parse(a.updated));
}

export default async (_req: Request, _ctx: Context): Promise<Response> => {
  const json = (body: unknown, status = 200) =>
    new Response(JSON.stringify(body), {
      status,
      headers: { "content-type": "application/json", "cache-control": "no-store" },
    });

  const token = process.env.NETLIFY_API_TOKEN;
  const siteId = process.env.SITE_ID;

  if (!token || !siteId) {
    return json({ asks: [], note: "not configured" });
  }

  try {
    const [all, roll] = await Promise.all([
      submissions(token, siteId),
      members(),
    ]);
    const mine = all.filter((s) => (s.form_name ?? "") === FORM_NAME);
    const board = merge(mine);

    // An empty roll means the sheet would not answer, NOT that nobody is a
    // member. Failing shut there would blank the board over a Google blip,
    // which is worse than a departed member lingering for a few minutes.
    if (!roll.size) {
      return json({ asks: board, count: board.length, filtered: false });
    }

    const current = board.filter((a) => roll.has(norm(a.name)));
    return json({
      asks: current,
      count: current.length,
      filtered: true,
      hidden: board.length - current.length,
    });
  } catch (e) {
    console.warn("referrals-data failed:", String(e));
    return json({ asks: [], note: "could not read submissions" }, 200);
  }
};
