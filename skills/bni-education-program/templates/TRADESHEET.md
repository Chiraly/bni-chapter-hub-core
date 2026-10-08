# The trade sheet on the members' site

The home page always shows the newest trade sheet, with the date it was updated
and a download button. Nobody has to tell the site when it changes.

**To publish a new one: drop the PDF in the chapter's trade sheet folder in Drive.**
That is the whole job, and there is no second step.

## There is no rule about the filename

Call it whatever you like. `Trade sheet.pdf`, `trade sheet FINAL v2 (1).pdf`,
anything. The site works out which file is newest from **the file's own modified
date in Drive** — the same date Drive shows in its "Last modified" column — so
it cannot be thrown off by how a file is named.

An earlier version of this did read the date out of the filename, and that was a
trap: one file saved without a date, or with the date typed wrong, and the site
would quietly show the wrong trade sheet. That is gone.

Old versions can stay in the folder. They do no harm, and members are not shown
them — the page offers only the latest one.

## How it works, in case it ever breaks

Two steps, neither of which needs a Google account, an API key, or a credential
of any kind:

1. Drive serves a plain, server-rendered listing of any link-readable folder at
   `drive.google.com/embeddedfolderview?id=<folder>`. That gives the file ids.
2. Each file's download URL redirects to Google's storage host, which answers a
   plain `HEAD` request with a real `Last-Modified` header. That is the file's
   true modified time.

A Netlify function does both, takes the newest, and hands the page a download
link.

Neither endpoint is documented by Google, so either could change one day. The
function is built to survive that in stages:

| If this stops working | What happens |
|---|---|
| The `Last-Modified` headers | Falls back to a date in the filename, if there is one |
| Filename dates too | Falls back to the order Drive lists the files in |
| The folder listing itself | The card falls back to linking the Drive folder — members can still get the file, it just takes one more click |

The function's reply says which of those it used, in a `dateSource` field
(`drive`, `name` or `order`). If the date on the site ever looks wrong, open
`https://YOUR-SITE/.netlify/functions/tradesheet` and look at that
field — `drive` means it is reading the real thing.

**If the card says "Couldn't load"**, check the folder is still shared so that
anyone with the link can view it. That is the usual cause.


## Setting it up

1. Make a Google Drive folder for the trade sheets.
2. Share it: **Anyone with the link → Viewer**.
3. Copy the folder ID (the string after `/folders/` in its address) into
   `chapter.json` → `data.tradesheet_folder_id`, and set `features.tradesheet`
   to `true`.
