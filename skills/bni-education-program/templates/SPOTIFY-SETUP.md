# Automating the chapter Spotify playlist

Once set up, each week's CEU hour is added to the chapter's playlist five days
before the meeting (a Thursday for a Tuesday chapter, a Sunday for a Friday one).
Nothing to remember, nothing to do each week.

**How it behaves.** The hour for the *coming* meeting is added early that
morning, so the episodes are there before the moment is delivered. To run it on
another day, set `spotify.cron` in chapter.json (UTC).

**It adds, it never removes.** The playlist grows across the term and members sort
by *Date added* to find the newest. Somebody halfway through last week's hour does
not lose it, and somebody who joins in November can work backwards through the
whole term.

Episodes already in the playlist are skipped, so a re-run adds nothing and an
episode used by two different weeks appears once.

The playlist **name never changes** — members have it saved, and renaming it makes
a familiar playlist look like a new one.

**The coordinators get an email** each time it runs, saying what was added. The
one that matters is the failure email: if none of the week's episodes can be found
on Spotify, nothing is added and you are told, rather than the run failing
silently.

---

## One-time setup (about ten minutes)

This part only you can do — changing your playlist needs your Spotify
authorisation, and the credentials must never go in the repo or into a chat.

### 1. Create a Spotify app

At <https://developer.spotify.com/dashboard> → **Create app**.

- **App name:** anything, e.g. `BNI Riverside playlist`
- **Redirect URI:** `http://127.0.0.1:8888/callback`
  Type it exactly. Spotify rejects `localhost` — it must be the numeric loopback.
- **API:** tick *Web API*

Then open the app's **Settings** and copy the **Client ID** and **Client secret**.

### 2. Get a refresh token

On your own machine:

```bash
python scripts/spotify_auth.py --client-id YOUR_ID --client-secret YOUR_SECRET
```

Your browser opens, you click **Agree**, and the terminal prints the four values
to set next. The refresh token does not expire.

### 3. Put them in Netlify

Netlify → the project → **Project configuration → Environment variables**.
Add all four:

| Variable | Value |
|---|---|
| `SPOTIFY_CLIENT_ID` | from step 1 |
| `SPOTIFY_CLIENT_SECRET` | from step 1 |
| `SPOTIFY_REFRESH_TOKEN` | from step 2 |
| `SPOTIFY_PLAYLIST_ID` | `0OzCqqMEiCMbLcFTS885RF` |

Netlify encrypts these. They are never in the repository.

### 4. Redeploy

```bash
netlify deploy --prod --dir <site-folder>
```

The function is deployed either way — **before** the variables are set it exits
quietly and does nothing, so the site is safe to publish before you get to this.

---

## Checking it

Netlify → **Logs → Functions → refresh-playlist**. A successful run logs something like:

```
week 1 "Givers Gain, Literally" - 5 episode(s) added
```

To run it now rather than waiting for Thursday, use the Netlify UI:
**Logs → Functions → refresh-playlist → Run**. Opening the function's URL in a
browser returns **403** — that is normal and not a fault. Netlify blocks direct
HTTP access to scheduled functions so they can only fire on their schedule.

To try it locally before deploying, with the four variables in a local `.env`:

```bash
netlify functions:invoke refresh-playlist
```

## What can go wrong

**"Spotify not configured - skipping"** — one of the four variables is missing or
misspelt. Check for stray spaces.

**"no episodes matched"** — none of the week's episodes were found on Spotify, so
nothing was added and everything already in the playlist is untouched. You get an
email saying so. Usually means an episode number in `weeks.json` doesn't match
Spotify's title format.

**Some episodes missing** — named in the email and the log. Older episodes
occasionally aren't on Spotify even though they're on bnipodcast.com. Swap them in
the week's CEU hour, or accept that week being short of the hour; the education
page still lists all of them with direct links.

**Token errors after changing your Spotify password** — passwords don't invalidate
refresh tokens, but removing the app from your account does. Re-run step 2.

## Turning it off

Delete `SPOTIFY_REFRESH_TOKEN` in Netlify. The function goes back to doing nothing,
and the playlist keeps everything already in it.


---

## Turning it on in chapter.json

Once the four variables are set in Netlify:

```json
"spotify": { "playlist_url": "https://open.spotify.com/playlist/YOUR_ID" },
"features": { "spotify": true }
```

then commit. The playlist appears on the Education page, the presenter emails
link it, and the weekly job starts. Use the same playlist ID in
`SPOTIFY_PLAYLIST_ID` and in `playlist_url`.
