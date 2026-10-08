# Imagery

Minimalist BNI slides need far less imagery than instinct suggests. The default answer
is a typographic slide. Reach down this ladder only when a picture genuinely earns its
place.

---

## The ladder

### 1. The official BNI photo library — first choice for people

61 photos, downscaled and indexed. Index at `references/photo-index.json`; files at
the folder named by the `BNI_PHOTO_LIBRARY` environment variable (build it from BNI's official album with `scripts/build_photo_cache.py`).

Each entry has a caption, tags, and `text_space` — where a heading can sit without
covering a face. Search the tags rather than guessing filenames:

```python
import json
idx = json.load(open("references/photo-index.json"))
picks = [p for p in idx["photos"] if "welcome" in p["tags"] and p["text_space"] == "upper"]
```

Strong for: welcome and handshake moments, chapter meetings, open networking, members
presenting, one-to-ones.

**Known gaps** (listed in the index, so don't force a bad fit): no phone calls, no
referral slips in close-up, no outdoor or Australian settings, no BNI Connect screens,
effectively no portrait orientation. When the library has nothing, go typographic.

> These are photographs of real people at real BNI events. Never present them as this
> chapter's own members, and never generate lookalikes.

### 2. BNI brand graphics

The seven core-value icons in `assets/icons-bni/` (red and white versions) and the
Super Graphics in `assets/graphics/`. Use the official core-value icons whenever a
slide is *about* a core value — they are recognisable and members have seen them.

### 3. Lucide icons — the everyday workhorse

ISC licensed, no attribution, 86 bundled and any other pullable from the CDN.

```python
from icon import icon
p = icon("handshake")                     # BNI red, 512px
p = icon("phone", colour="#FFFFFF")       # white, for the red visitor slide
```

```bash
python scripts/icon.py --list
python scripts/icon.py --fetch calendar-heart
```

**Style rule.** The BNI core-value icons are solid; Lucide is line. Never put both
styles on one slide. Pick one language per deck.

### 4. Recraft — rarely, and check the cost first

For abstract or metaphorical art where no photo or icon will do.

> **Cost warning.** `vector_illustration` costs roughly **80 credits per image**. Two
> images emptied a 180-credit balance during this skill's build. Check
> `mcp__recraft__get_user` before generating, and prefer `digital_illustration` or
> `realistic_image` (raster), which are far cheaper.

House style, if you do use it:

> flat minimal vector, crimson red #CF2030 with mid grey and white only, plain white
> background, generous negative space, simple geometric shapes, no text, no logos

**Watch out:** the word "elf" reliably produces Christmas imagery, and red pointed
shapes on a head read as a devil rather than an elf. If you need a simple flat mark,
hand-authoring the SVG is faster, free, exactly on-brand, and easier to correct — which
is how `assets/mascot/` was made.

**Never generate:** the BNI logo or anything logo-like; photoreal people presented as
BNI members; anything that could pass as an official BNI asset.

### 5. Free stock photography

When the official library has a genuine gap. Pexels and Unsplash both allow free
commercial use without attribution. If a search is needed, hand the user two or three
candidate links rather than picking blind — a wrong stock photo is worse than none.
Anything chosen must match the BNI photo style (p20): professional, warm, well lit,
shallow depth of field, real-looking people.

### 6. No image

Often the right answer. A `statement` slide with eight words and a lot of white space
looks more confident than a mediocre photo with a caption. In a 3-minute talk the
audience should be looking at the speaker most of the time anyway.

---

## Using a photo well

`d.photo(image, heading=..., caption=...)` gives the p18 "Image with SG 1" treatment:
full bleed, Super Graphic bottom-right, white logo top-left, and a soft dark scrim
behind the heading so white text stays readable.

- Check `text_space` before choosing where the heading goes. Text over a face is the
  single most common way these slides go wrong.
- One photo per deck, at most two. A deck of photos is a slideshow, not an argument.
- Never stretch. `photo()` covers and centre-crops, which is correct.
- Never put a photo behind body text — only behind a short heading with the scrim.

## Attribution

BNI photography and graphics: internal chapter use. Lucide: ISC, licence bundled at
`assets/icons-lucide/LICENSE`. Recraft output: generated for this chapter's use.
Free stock: record the source URL in the program folder even where attribution is not
required, so it can be traced later.
