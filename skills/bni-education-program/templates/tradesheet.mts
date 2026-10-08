/**
 * tradesheet — the newest trade sheet in a Drive folder, with no credential.
 *
 * Somebody drops a new PDF in the folder and the site picks it up. Nothing to
 * redeploy, nobody to tell, and NOTHING TO NAME CORRECTLY.
 *
 * How it manages that without a Google API key, in two parts:
 *
 *   1. WHICH FILES ARE THERE. Drive serves `embeddedfolderview` as plain
 *      server-rendered HTML for any folder that is readable by anyone with the
 *      link, and every entry carries its file id.
 *
 *   2. HOW OLD EACH ONE IS. The download URL redirects to Google's storage
 *      host, which answers a plain HEAD with a real `Last-Modified` header.
 *      That is the file's actual modified time - the same instant Drive shows
 *      in its own "Last modified" column - so it needs no API key and no
 *      cooperation from whoever uploaded the file.
 *
 * That second part is the point. An earlier version of this read the date out
 * of the filename, which meant a trade sheet uploaded as "trade sheet FINAL
 * v2.pdf" was invisible to it, and one misdated in the name would outrank the
 * real newest. People will not always name files correctly, and they should
 * not have to. The file's own timestamp cannot be got wrong.
 *
 * The filename date survives only as a fallback, for the case where Drive
 * stops answering HEAD at all. Order of preference, most to least trusted:
 *
 *      drive  - Last-Modified from Drive. What we want.
 *      name   - a date in the filename. Only if NO file gave a Drive time.
 *      order  - the order Drive listed them. Only if nothing else worked.
 *
 * The response says which one was used, in `dateSource`, so a wrong-looking
 * date on the site can be diagnosed without guessing.
 *
 * If anything about that page changes, this returns the folder link instead of
 * nothing, so the section degrades to "here is the folder" rather than
 * vanishing.
 */
import type { Context } from "@netlify/functions";

const FOLDER_ID: string = @@json:tradesheet_folder@@;
const FOLDER_URL = `https://drive.google.com/drive/folders/${FOLDER_ID}`;

/** The chapter's own timezone. A file uploaded at 9am in Melbourne is 23:00
 *  UTC the day before, and showing yesterday's date would be its own bug. */
const TZ: string = @@json:timezone@@;

/** Drive is usually quick, but one slow file should not hold up the page. */
const HEAD_TIMEOUT_MS = 6000;

const MONTHS = ["jan", "feb", "mar", "apr", "may", "jun",
                "jul", "aug", "sep", "oct", "nov", "dec"];

type Entry = { id: string; name: string };
export type Source = "drive" | "name" | "order";

const downloadUrl = (id: string) =>
  `https://drive.google.com/uc?export=download&id=${id}`;

/** Pull {id, name} pairs out of the folder view's markup. */
export function parseFolder(html: string): Entry[] {
  const out: Entry[] = [];
  // <div class="flip-entry" id="entry-FILEID" ... >…<div class="flip-entry-title">NAME</div>
  const re = /flip-entry"\s+id="entry-([A-Za-z0-9_-]+)"[\s\S]*?flip-entry-title"[^>]*>([^<]+)</g;
  let m: RegExpExecArray | null;
  while ((m = re.exec(html))) {
    out.push({ id: m[1], name: m[2].trim() });
  }
  return out;
}

/** The fallback only: "…-Trade-Sheet-22-Sep-2026.pdf" -> a sortable stamp.
 *  0 when the name carries no date, which is a perfectly normal filename. */
export function dateFromName(name: string): number {
  const m = /(\d{1,2})[-_ ]([A-Za-z]{3,})[-_ ](\d{4})/.exec(name ?? "");
  if (!m) return 0;
  const mo = MONTHS.indexOf(m[2].slice(0, 3).toLowerCase());
  if (mo < 0) return 0;
  return Date.UTC(Number(m[3]), mo, Number(m[1]));
}

/** The file's real modified time, straight from Drive. 0 if it won't say.
 *
 *  A HEAD is enough - we never download the 3MB body just to read a header. */
export async function modifiedAt(id: string): Promise<number> {
  try {
    const r = await fetch(downloadUrl(id), {
      method: "HEAD",
      redirect: "follow",
      signal: AbortSignal.timeout(HEAD_TIMEOUT_MS),
    });
    if (!r.ok) return 0;
    const at = Date.parse(r.headers.get("last-modified") ?? "");
    return Number.isFinite(at) ? at : 0;
  } catch {
    return 0;                       // timeout, network, anything - just fall back
  }
}

/** Given the files and their Drive times, pick the newest and say how we knew.
 *
 *  Split out from the handler so it can be exercised with fabricated inputs -
 *  including the ones that matter, like a file misdated in its name. */
export function pickNewest(
  files: Entry[], driveTimes: number[],
): { file: Entry; at: number; source: Source } | null {
  if (!files.length) return null;

  // 1. Drive's own timestamps, if it gave us any at all.
  if (driveTimes.some((t) => t > 0)) {
    let best = 0;
    for (let i = 1; i < files.length; i++) {
      if (driveTimes[i] > driveTimes[best]) best = i;
    }
    return { file: files[best], at: driveTimes[best], source: "drive" };
  }

  // 2. Drive is not answering. Fall back to a date in the name, if there is one.
  const nameTimes = files.map((f) => dateFromName(f.name));
  if (nameTimes.some((t) => t > 0)) {
    let best = 0;
    for (let i = 1; i < files.length; i++) {
      if (nameTimes[i] > nameTimes[best]) best = i;
    }
    return { file: files[best], at: nameTimes[best], source: "name" };
  }

  // 3. Nothing to go on. Give them a file rather than nothing, and say so.
  return { file: files[0], at: 0, source: "order" };
}

const label = (at: number) =>
  at > 0
    ? new Date(at).toLocaleDateString("en-AU", {
        timeZone: TZ, day: "numeric", month: "long", year: "numeric",
      })
    : "";

export default async (_req: Request, _ctx: Context): Promise<Response> => {
  const json = (body: unknown) =>
    new Response(JSON.stringify(body), {
      headers: {
        "content-type": "application/json",
        /* Freshness, and why these numbers.

           stale-while-revalidate was a DAY. Each Netlify edge node caches separately,
           so a new trade sheet showed on some nodes and not others for up to 24 hours
           - which is exactly what 'I added it and it is not showing' looked like. The
           SOP promises about five minutes, so the cache should too.

           Nobody waits either way: with stale-while-revalidate the edge answers
           instantly from its last copy and refreshes behind the request. The only
           cost of a short window is more background invocations, which are cheap. */
        "cache-control":
          "public, max-age=60, stale-while-revalidate=240",
      },
    });

  try {
    const r = await fetch(
      `https://drive.google.com/embeddedfolderview?id=${FOLDER_ID}#list`);
    if (!r.ok) throw new Error(`folder ${r.status}`);

    const files = parseFolder(await r.text())
      .filter((f) => /\.pdf$/i.test(f.name));
    if (!files.length) throw new Error("no PDFs found in the folder");

    // All at once - a folder of these is small, and they are independent.
    const driveTimes = await Promise.all(files.map((f) => modifiedAt(f.id)));

    const best = pickNewest(files, driveTimes)!;

    return json({
      name: best.file.name,
      dateLabel: label(best.at),
      dateSource: best.source,
      download: downloadUrl(best.file.id),
      view: `https://drive.google.com/file/d/${best.file.id}/view`,
      folder: FOLDER_URL,
      count: files.length,
    });
  } catch (e) {
    console.warn("tradesheet lookup failed:", String(e));
    return json({ folder: FOLDER_URL, note: String(e) });
  }
};
