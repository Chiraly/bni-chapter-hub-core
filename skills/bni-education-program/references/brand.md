# BNI brand — slide design system

Everything here traces to the *BNI Brand Standards Manual* (page numbers given). When
in doubt, the manual wins. It is in `Brand assets/BNI Brand Standards Manual.pdf`.

---

## Colours (p6)

| Name | Hex | Use |
|---|---|---|
| BNI Red | `CF2030` | the only accent — headings emphasis, visitor slide field, rules |
| Sterling Grey | `C8C8C8` | the Super Graphic's grey sweep; rarely needed directly |
| Sterling Light Grey | `F2F2F2` | the quiet panel in a contrast slide |
| Granite Grey | `64666A` | secondary text — subtitles, support lines, captions |
| Power Black | `000000` | headings and primary text |
| True White | `FFFFFF` | backgrounds, and text on red |

There is no secondary palette. No blues, no greens, no gradients, no drop shadows.
If a slide seems to need another colour, it needs less content instead.

## Type (p15)

Helvetica Neue is the official font. **Arial is the manual's own sanctioned substitute**
and is what these decks use, because it is on every machine that will open them.
The supplied Helvetica Neue OTFs are in `Brand assets/Fonts.zip` if a deck will only
ever be shown from one installed machine — pass `font="Helvetica Neue"` to `BNIDeck`.

Headings are Bold. Body is Regular. Nothing is Light — it dies on a projector.

| Role | Size | Colour |
|---|---|---|
| Title slide headline | 44 | Black (emphasis in Red) |
| Title slide kicker | 14 bold caps | Red |
| Slide heading | 32 | Black |
| Big statement | 40–46 | Black (emphasis in Red) |
| Action ask | 38 | Black |
| Body / support | 17–22 | Granite Grey |
| Visitor slide heading | 30 | White |
| Visitor slide body | 22 | White |
| Presenter footer | 13 | Granite Grey |

## Logo (p8–12)

- Red logo on white. White logo on red or on a photo. Never black on colour.
- Do not stretch, recolour, outline, tint, rotate, add a tagline to, or put anything
  inside the logo. Do not put it in a floating box or on a pattern.
- A chapter name may sit **below** the logo, in Granite Grey, all caps, aligned to the
  logo's width (p9). It never sits beside or inside it.

## Super Graphic (p17)

The red-and-grey swoosh. Rules, verbatim from the manual:

- Its colours never change.
- **Only ever on a white background.** This is why the red visitor slide has no
  Super Graphic — that is correct, not an omission.
- The Primary Super Graphic is **always anchored to the bottom-right corner**, flush
  to both edges.
- It must not touch other elements, apart from minimal white text over the red area.

The Secondary Super Graphic (the square one) anchors top-left. These decks don't use it.

## The official PowerPoint template (p28)

Two layouts, and they are deliberately plain:

- **Title:** white field, BNI logo centred, title beneath in black, Super Graphic
  bottom-right.
- **Content:** white field, small red logo bottom-left, Super Graphic bottom-right.
  Everything else is your content.

That is the whole template. Resist adding header bars, sidebars or footers.

---

## Canvas and grid

13.333 × 7.5 in (16:9). Left and right margins 0.9". Top margin 0.85". Content width
11.533". Nothing below 6.05" except the logo and Super Graphic.

Furniture, sized from p28:
- Super Graphic 2.50 × 1.312", flush to the bottom-right corner
- Content logo 1.40 × 0.537", inset 0.50" left and 0.40" from the bottom

---

## The eight archetypes

All in `scripts/bni_deck.py`. Each takes `notes=` for the speaker script.

| Archetype | When to reach for it | Word budget on screen |
|---|---|---|
| `title_slide` | opens every deck; auto-created | 30 |
| `statement` | one idea, big type. The workhorse — use it most | 28 |
| `photo` | full-bleed official photo, Super Graphic and white logo (p18 Type 1) | 30 |
| `three_up` | exactly three parallel things. Not four, not two | 60 |
| `contrast` | this vs that; before vs after; the grey panel loses, the red panel wins | 62 |
| `visitor` | **mandatory.** Red field, white text | 70 |
| `action` | the one specific thing to do this week | 32 |
| `elf_close` | **mandatory.** The ask, then the tagline | 22 |

Highlight a phrase in BNI Red by wrapping it in `*asterisks*`:

```python
d.statement("Trust is built in *minutes*, not months.")
```

### A typical 3-minute shape

```
title  →  statement (the business hook)  →  contrast or three_up (the why)
       →  statement (the BNI link)  →  visitor  →  action  →  elf_close
```

Seven slides, roughly 25 seconds each. Drop a slide before you crowd one.

---

## Minimalism, concretely

- One idea per slide. If a slide has two, it is two slides — or one of them is cut.
- The slide is not the script. The words on screen are a headline; the sentences live
  in the speaker notes.
- Nobody reads a bullet list while listening to a person. There are no bullet lists in
  this system, and that is on purpose.
- White space is not wasted space. A slide with eight words and a lot of white reads
  as confident. A slide with forty words reads as a document.
- If you are tempted to shrink the type to fit, cut words instead.
