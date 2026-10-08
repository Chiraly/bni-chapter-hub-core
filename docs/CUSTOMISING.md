# Making the site your chapter's own

Everything you customise lives in **your chapter repo**. The shared core never
writes to it, so a core update can't undo your changes. There are five layers,
from lightest to heaviest. Use the lightest one that does the job, because the
heavier layers take more looking after.

| Layer | Where | Keeps getting core updates? |
|---|---|---|
| 1. Settings | `chapter.json` | Yes |
| 2. Look | `custom.css`, `assets/` | Yes |
| 3. Content | `content/*.html`, `moments.json`, `emails/reminders.json` | Yes, apart from the block you replaced |
| 4. Extras | `pages/*.html`, `functions/*.mts` | Yes. They're additions |
| 5. Override | `overrides/templates/*` | **No**, not for the file you replaced |

---

## 1. Settings: chapter.json

Names, times, venue, Zoom, colours, links, home-page cards, and switching whole
features on and off. Covers most of what a chapter wants.
See [CHAPTER-CONFIG.md](CHAPTER-CONFIG.md).

## 2. Look: custom.css and assets/

Add `custom.css` at the top of your repo. It loads after the core's styles on
every page, so anything in it wins:

```css
/* Rounder buttons, and a sea-green accent on the home page only */
.btn { border-radius: 999px; }
body:has(.cards) { --accent: #1B7F79; --accent-ink: #145F5B; }
```

Logos, favicon and mascot go in `assets/` and are pointed at from `chapter.json`
→ `brand`. See `assets/README.md` in your repo.

## 3. Content: replace one section

**A page section.** Create `content/<block>.html` to replace that section only:

| Block | Where |
|---|---|
| `home-hero` | Heading and intro on the home page |
| `home-extra` | Between the home-page cards and "BNI's own tools" (empty by default) |
| `venue-fees` | Venue fees on the Meetings page |
| `deck-deadline` | The "send your .pptx by..." paragraphs on the Education page |

Copy the core's version from `skills/bni-education-program/templates/blocks/`
as a starting point. Example `content/home-extra.html`:

```html
<p class="eyebrow">Visitors this month</p>
<div class="how">
  <p><b>Visitor day is Friday 20 November.</b> Bring one person who'd benefit
     from a room full of referrals. Breakfast is on the chapter.</p>
</div>
```

**Your own moments library.** Put `moments.json` in your repo and it replaces the
core's shared library. Start from a copy of the core's
(`skills/bni-education-program/library/moments.json`) and add your own. The
Claude skill writes new entries in the right shape for you.

**Reminder email wording.** Put `emails/reminders.json` in your repo with only the
keys you want to change:

```json
{
  "cant_make_it": "<strong>Can't make it?</strong> Reply to this email or text Lisa on 0400 000 000 as early as you can."
}
```

The full list of keys and the core wording is in
`skills/bni-education-program/templates/emails/reminders.json`.

## 4. Extras: new pages and functions

**A new page.** `pages/visitors.html` becomes `/visitors/`, in the same header,
nav and footer as the rest. Add it to the menu in `chapter.json`:

```json
"site": { "nav_extra": [ { "href": "/visitors/", "label": "Visitors" } ] }
```

A starting template:

```html
<title>@@chapter@@ — Visitors</title>
<style>
  :root{--accent:var(--nx-orange); --accent-ink:var(--nx-orange-ink)}
</style>

@@nav@@
@@clock@@
@@meeting@@

<div class="wrap">
  <p class="eyebrow">Visiting</p>
  <h2>Your first morning at @@chapter_short@@</h2>
  <div class="how">
    <p>We meet every @@weekday@@ at @@start@@. Be there by @@arrive@@.</p>
  </div>
@@footer@@
</div>
```

`@@meeting@@` drops in the live next-meeting panel. Remove it (and `@@clock@@`) if
the page doesn't need it.

**A new automation.** Put a Netlify Function in `functions/`, e.g.
`functions/visitor-followup.mts`. It is deployed with the core's. A file with the
same name as a core function *replaces* it, and the build warns you.

## 5. Override: replace a core template

The escape hatch. `overrides/templates/home.html` replaces the core's `home.html`
completely, and the same goes for any file in `skills/bni-education-program/templates/`.

The cost: **that file stops receiving core updates.** Every build lists the files
you have overridden, and every core release's CHANGELOG lists the templates it
touched. When one of yours appears there, compare and copy the change across.

Before overriding, ask whether a content block, a setting or `custom.css` would
do. If none would, tell Hilary: it may be worth adding a block or a setting to the
core so nobody needs to override.

---

## Getting core updates

Your `netlify.toml` says which version of the core to build with:

```toml
CORE_REF = "stable"    # always the latest release (recommended)
CORE_REF = "v1.3.0"    # pinned
```

On `stable`, you get each release automatically. Hilary's release pipeline
rebuilds every chapter on the update list (setup step 5). Pin a version if
you're mid-term and want nothing to change, then move to `stable` when you're
ready. What changed in each release, and anything you need to do, is in
[CHANGELOG.md](../CHANGELOG.md).

New features arrive **switched off** for existing chapters unless they're
harmless. The CHANGELOG says which `features` setting turns each one on.

## Sharing something back

If you build something other chapters would want, such as a page, a block, an
automation or a better email, send it to Hilary as a pull request on the core
repo, or just email the files. It goes into the core behind a `features` switch,
so every chapter can turn it on.
