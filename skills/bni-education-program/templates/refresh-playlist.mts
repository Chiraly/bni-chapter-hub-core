/**
 * refresh-playlist — add each week's CEU hour to the chapter's Spotify playlist.
 *
 * Runs on Netlify five days before each meeting, early in the chapter's
 * morning (chapter.json spotify.cron overrides when), adding the hour for the
 * COMING meeting. So the week's episodes are already there on the morning
 * the moment is delivered.
 *
 * It ADDS, it does not replace. The playlist accumulates across the term, and
 * members sort by Date Added to find the newest. Nobody loses an hour they were
 * halfway through, a member who joins in November can still work backwards, and
 * there is no window where the playlist and the page disagree about which week
 * is loaded.
 *
 * Episodes already in the playlist are skipped, so a re-run adds nothing and
 * the same episode used by two weeks appears once.
 *
 * The playlist NAME is never touched. Members have it saved; renaming it under
 * them makes a familiar playlist look like a different one.
 *
 * Needs four environment variables, set in the Netlify UI (never in the repo):
 *   SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REFRESH_TOKEN,
 *   SPOTIFY_PLAYLIST_ID
 * Without them it exits quietly, so the site deploys fine before setup is done.
 */
import type { Config } from "@netlify/functions";

const SHOW_ID: string = @@json:show_id@@; // The Official BNI Podcast, by default

/* Links for the notification emails. The playlist one is built from the same
   env var the function writes to, so they cannot drift apart. */
const playlistUrl = () =>
  `https://open.spotify.com/playlist/${process.env.SPOTIFY_PLAYLIST_ID ?? ""}`;
const EDU = `${process.env.URL ?? @@json:fallback_origin@@}/education/`;
const TZ: string = @@json:timezone@@;
const MARKET: string = @@json:market@@;
const COPY: Record<string, string> = @@json:emails@@;
const fill = (s: string, v: Record<string, string | number>) =>
  (s ?? "").replace(/\{(\w+)\}/g, (m, k) => (k in v ? String(v[k]) : m));

type Ep = { n: number; t: string; d: string; u: string };
type Week = { n: number; date: string; title: string; eps: Ep[] };

const chapterToday = () =>
  new Intl.DateTimeFormat("en-CA", {
    timeZone: TZ, year: "numeric", month: "2-digit", day: "2-digit",
  }).format(new Date());

/** The NEXT meeting, not the last one.
 *
 *  The run five days out prepares the coming meeting, so the playlist already holds
 *  that week's hour when the moment is delivered, and keeps it through the
 *  Wednesday after - a seven-day window with two days on the far side of the
 *  session. Loading the meeting that had just passed put the playlist a week
 *  behind on the morning it mattered most.
 */
export function weekToLoad(weeks: Week[], today = chapterToday()): Week | null {
  const upcoming = weeks.find((w) => w.date >= today);
  return upcoming ?? weeks[weeks.length - 1] ?? null;  // term over: hold the last
}

async function accessToken(id: string, secret: string, refresh: string) {
  const r = await fetch("https://accounts.spotify.com/api/token", {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
      Authorization: "Basic " + Buffer.from(`${id}:${secret}`).toString("base64"),
    },
    body: new URLSearchParams({ grant_type: "refresh_token", refresh_token: refresh }),
  });
  if (!r.ok) throw new Error(`token ${r.status}: ${await r.text()}`);
  return (await r.json()).access_token as string;
}

/** Map "Episode 812: ..." -> Spotify episode id, across the whole show. */
async function episodeIndex(token: string) {
  const index = new Map<number, string>();
  let url =
    `https://api.spotify.com/v1/shows/${SHOW_ID}/episodes?market=${MARKET}&limit=50`;
  while (url) {
    const r = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
    if (!r.ok) throw new Error(`episodes ${r.status}: ${await r.text()}`);
    const page = await r.json();
    for (const item of page.items ?? []) {
      const m = /Episode\s+(\d+)\s*:/i.exec(item?.name ?? "");
      if (m && item?.id) index.set(Number(m[1]), item.id);
    }
    url = page.next;
  }
  return index;
}

/** Every episode URI already in the playlist, so a re-run adds nothing and an
 *  episode shared by two weeks is not added twice. */
async function playlistUris(token: string, playlist: string) {
  const have = new Set<string>();
  let url: string | null =
    `https://api.spotify.com/v1/playlists/${playlist}/tracks` +
    `?market=${MARKET}&limit=100&fields=next,items(track(uri))`;
  while (url) {
    const r: Response = await fetch(url, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!r.ok) throw new Error(`playlist tracks ${r.status}: ${await r.text()}`);
    const page = await r.json();
    for (const item of page.items ?? []) {
      const uri = item?.track?.uri;
      if (uri) have.add(uri);
    }
    url = page.next;
  }
  return have;
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

/** "10:57" -> 657. Durations come from the podcast feed as m:ss or h:mm:ss. */
function secondsOf(d: string): number {
  const parts = (d ?? "").split(":").map(Number);
  if (parts.some(Number.isNaN) || !parts.length) return 0;
  return parts.reduce((total, n) => total * 60 + n, 0);
}

/* Tell the coordinators what happened.
 *
 * Without this the only record is a log line in the Netlify console, which
 * nobody opens on a Thursday morning - so a playlist that quietly failed to
 * update would look exactly like one that worked. The failure case matters more
 * than the success case: episodes missing from Spotify are the thing a
 * coordinator has to act on.
 *
 * Uses the same Postmark server and sender as the presenter reminders. If mail
 * is not configured this does nothing and the run still succeeds - updating the
 * playlist is the job, telling someone about it is a courtesy.
 */
async function notify(subject: string, lines: string[]) {
  const token = process.env.POSTMARK_TOKEN;
  const from = process.env.MAIL_FROM;
  const to = (process.env.COORDINATORS ?? "").split(",")
    .map((s) => s.trim()).filter(Boolean);
  if (!token || !from || !to.length) return;

  /* The same lines carry inline HTML for the html body. For the text part,
     unwrap links to "label: url" before stripping tags - otherwise a link
     collapses to its label and the address is lost, which is worse than no
     link at all. */
  const text = lines
    .map((l) => l.replace(/<a [^>]*href="([^"]+)"[^>]*>(.*?)<\/a>/g, "$2: $1"))
    .map((l) => l.replace(/<[^>]+>/g, ""))
    .join("\n\n");
  const html =
    `<div style="font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;` +
    `font-size:16px;line-height:1.55;color:#121316;max-width:34rem">` +
    lines.map((l) => `<p style="margin:0 0 .8rem">${l}</p>`).join("") +
    `</div>`;

  try {
    const r = await fetch("https://api.postmarkapp.com/email", {
      method: "POST",
      headers: {
        "X-Postmark-Server-Token": token,
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({
        From: from, To: to.join(", "), ReplyTo: to.join(", "),
        Subject: subject, HtmlBody: html, TextBody: text,
        MessageStream: "outbound",
      }),
    });
    if (!r.ok) console.warn(`playlist notification failed: ${r.status}`);
  } catch (e) {
    console.warn("playlist notification failed:", String(e));
  }
}

export default async (): Promise<Response> => {
  const id = process.env.SPOTIFY_CLIENT_ID;
  const secret = process.env.SPOTIFY_CLIENT_SECRET;
  const refresh = process.env.SPOTIFY_REFRESH_TOKEN;
  const playlist = process.env.SPOTIFY_PLAYLIST_ID;

  if (!id || !secret || !refresh || !playlist) {
    // Not an error: the site is expected to deploy before Spotify is wired up.
    return new Response("Spotify not configured - skipping", { status: 200 });
  }

  /* Already joined - the sheet decides which moment runs when, and the
     schedule function is the one place that is worked out. */
  const { meetings } = await fetchSiteJson("/schedule");
  const weeks: Week[] = meetings ?? [];

  const week = weekToLoad(weeks);
  if (!week) return new Response("no weeks defined", { status: 200 });

  const token = await accessToken(id, secret, refresh);
  const index = await episodeIndex(token);

  const found: { uri: string; secs: number }[] = [];
  const missing: number[] = [];
  for (const ep of week.eps) {
    const sid = index.get(ep.n);
    if (sid) found.push({ uri: `spotify:episode:${sid}`, secs: secondsOf(ep.d) });
    else missing.push(ep.n);
  }

  if (!found.length) {
    const msg =
      `no episodes matched for week ${week.n} (wanted ${missing.join(", ")}) - nothing added`;
    await notify(`Playlist NOT updated - week ${week.n}`, [
      `<strong>Nothing was added to the chapter playlist this morning.</strong>`,
      `None of week ${week.n}'s episodes (${missing.join(", ")}) could be found on Spotify. Everything already in the playlist is untouched.`,
      `Every episode is still listed on the <a href="${EDU}">education page</a> with a direct link, so members are not stuck. Worth swapping these numbers for ones Spotify carries.`,
      `<a href="${playlistUrl()}">Open the playlist</a>`,
    ]);
    return new Response(msg, { status: 200 });
  }

  // Skip what is already there. Adding the same episode twice is the obvious
  // failure mode of appending rather than replacing, and it would show up in
  // members' playlists as duplicates they have to scroll past.
  const have = await playlistUris(token, playlist);
  const fresh = found.filter((e) => !have.has(e.uri));
  const already = found.length - fresh.length;

  if (!fresh.length) {
    const msg = `week ${week.n} already in the playlist - nothing to add`;
    console.log(msg);
    return new Response(msg, { status: 200 });
  }

  // POST appends. 100 per request is the API's limit; a week is nowhere near
  // it, but the loop costs nothing and stops this breaking on a long week.
  for (let i = 0; i < fresh.length; i += 100) {
    const batch = fresh.slice(i, i + 100).map((e) => e.uri);
    const post = await fetch(
      `https://api.spotify.com/v1/playlists/${playlist}/tracks`,
      {
        method: "POST",
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify({ uris: batch }),
      },
    );
    if (!post.ok) throw new Error(`add ${post.status}: ${await post.text()}`);
  }

  const msg =
    `week ${week.n} "${week.title}" - ${fresh.length} episode(s) added` +
    (already ? `, ${already} already there` : "") +
    (missing.length ? `, ${missing.length} not found on Spotify: ${missing.join(", ")}` : "");
  console.log(msg);

  const mins = Math.round(fresh.reduce((n, e) => n + e.secs, 0) / 60);
  const total = have.size + fresh.length;
  await notify(
    fill(COPY.playlist_subject, { n: week.n, title: week.title }),
    [
      fill(COPY.playlist_ready, { n: week.n, title: week.title }),
      `${fresh.length} episode${fresh.length === 1 ? "" : "s"}, about ${mins} minutes` +
        (already ? `. ${already} of the week's episodes were already in there` : "") +
        `. The playlist now holds ${total} episode${total === 1 ? "" : "s"} for the term.`,
      `Nothing is removed, so members can still finish an earlier hour. Sorting by <em>Date added</em> puts the newest first.`,
      `<a href="${playlistUrl()}">Open the playlist</a> &nbsp;·&nbsp; <a href="${EDU}">Education page</a>`,
      ...(missing.length
        ? [`<strong>${missing.length} episode${missing.length === 1 ? " was" : "s were"} not found on Spotify</strong> (${missing.join(", ")}), so this week is that much short of the hour. They are still listed on the education page with direct links.`]
        : []),
      `Nothing to do - this is just so you know it ran.`,
    ],
  );
  return new Response(msg, { status: 200 });
};

/* Worked out from meeting.weekday by chapter_config.playlist_cron(): 20:00 UTC
   the evening before, which is 6-7am on an Australian east-coast chapter's
   morning either side of daylight saving. */
export const config: Config = { schedule: "@@cron:playlist@@" };
