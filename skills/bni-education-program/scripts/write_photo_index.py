"""
write_photo_index.py — merge human captions into the photo manifest.

The manifest from build_photo_cache.py knows sizes and filenames but nothing
about what is IN each photo, so slide picks would be blind. These captions were
written by eye from the contact sheets. Re-run after adding photos to the album.
"""
import json
from pathlib import Path

import os
# The resized official BNI photo library (see build_photo_cache.py).
LIB = Path(os.environ.get("BNI_PHOTO_LIBRARY", "photo-library"))
OUT = Path(__file__).resolve().parent.parent / "references" / "photo-index.json"

# id -> (caption, tags, text_space)
#   text_space: where a heading can sit without covering a face
#               "lower" | "upper" | "left" | "right" | "none"
CAPTIONS = {
 "26684542769_7c9e2c151a_o": ("Two people in a one-to-one over coffee at a small round table, seen from above", ["one-to-one", "conversation", "coffee", "two-people"], "upper"),
 "53361255787_f7c870567b_o (1)": ("Standing group networking at a conference, lanyards and name badges", ["networking", "group", "conference", "open-networking"], "upper"),
 "53362589330_cb031ec5ea_o (1)": ("A man and a woman working together over a laptop in bright daylight", ["one-to-one", "laptop", "planning", "two-people"], "upper"),
 "54150416542_129f7ccb6e_c": ("Two men in focused conversation, name badges, indoor event", ["conversation", "two-people", "conference"], "none"),
 "BNIGlobalSYD2025_Day1_Expo_Hall-152": ("Four men talking around a tall table at a BNI conference", ["networking", "group", "conference"], "upper"),
 "BNIGlobalSYD2025_Day1_Expo_Hall-153": ("Members talking with coffee in hand, BNI banner behind", ["open-networking", "coffee", "group", "branded"], "upper"),
 "BNIGlobalSYD2025_Day1_Expo_Hall-251": ("Three members laughing together in bright window light", ["warm", "group", "fun", "relationships"], "left"),
 "BNIGlobalSYD2025_Day1_Expo_Hall-274": ("Two members talking, one wearing a red BNI blazer", ["conversation", "two-people", "branded"], "upper"),
 "BNIGlobalSYD2025_Day1_Expo_Hall-277": ("Three members in animated conversation, welcoming body language", ["conversation", "group", "welcome", "warm"], "upper"),
 "BNIGlobalSYD2025_Day1_Reg+Orientation+networking-226 (1) (1) (1)": ("A woman in a red blazer and hijab shaking hands warmly at the registration desk", ["welcome", "handshake", "visitor", "diverse", "warm"], "upper"),
 "BNIGlobalSYD2025_Day3_Hall_of_Fame-(Event)-93": ("Three members talking, holding cards and notes", ["conversation", "group", "referral-slips"], "upper"),
 "BNIGlobalSYD2025_Day3_Mega_Chatper_Meetings-17": ("A chapter meeting from the back of the room, long tables of members", ["chapter-meeting", "room", "audience"], "upper"),
 "BNIGlobalSYD2025_Day3_Mega_Chatper_Meetings-222": ("Members seated along a long table during a chapter meeting", ["chapter-meeting", "audience", "attendance"], "upper"),
 "BNIGlobalSYD2025_Day3_Mega_Chatper_Meetings-32": ("A row of members listening intently at a chapter meeting", ["audience", "attention", "chapter-meeting", "diverse"], "upper"),
 "BNIGlobalSYD2025_Day3_Mega_Chatper_Meetings-70": ("A member standing with a microphone to speak during a meeting", ["speaking", "weekly-presentation", "chapter-meeting"], "left"),
 "BNI_STOCK-PHOTO-100": ("Close-up handshake, name badge just visible", ["handshake", "close-up", "trust"], "left"),
 "BNI_STOCK-PHOTO-101": ("Close-up handshake between two men in business shirts", ["handshake", "close-up", "trust"], "right"),
 "BNI_STOCK-PHOTO-103": ("Clean close-up handshake against a soft background", ["handshake", "close-up", "trust", "minimal"], "upper"),
 "BNI_STOCK-PHOTO-104": ("A woman smiling during a chapter meeting, BNI banner behind her", ["portrait", "warm", "branded", "chapter-meeting"], "left"),
 "BNI_STOCK-PHOTO-110": ("A woman in red smiling across a meeting table", ["portrait", "warm", "chapter-meeting"], "left"),
 "BNI_STOCK-PHOTO-111": ("A woman in red greeting a member with a handshake", ["handshake", "welcome", "warm"], "upper"),
 "BNI_STOCK-PHOTO-113": ("A woman in red seated and listening, relaxed and engaged", ["portrait", "listening", "warm"], "right"),
 "BNI_STOCK-PHOTO-114": ("A man in a red BNI polo greeting someone", ["welcome", "branded", "warm"], "left"),
 "BNI_STOCK-PHOTO-115": ("A man talking with two other members, open gesture", ["conversation", "group", "explaining"], "upper"),
 "BNI_STOCK-PHOTO-128": ("A member with a name badge, BNI banner behind", ["portrait", "branded", "visitor"], "right"),
 "BNI_STOCK-PHOTO-129": ("A smiling member standing at a chapter meeting", ["portrait", "warm", "branded"], "right"),
 "BNI_STOCK-PHOTO-133": ("A man talking animatedly over a laptop", ["laptop", "online", "explaining", "one-to-one"], "left"),
 "BNI_STOCK-PHOTO-138": ("A woman taking notes at a table beside a BNI mug", ["notes", "learning", "ceu", "branded"], "upper"),
 "BNI_STOCK-PHOTO-141": ("A woman smiling while working at a laptop, BNI mug on the desk", ["laptop", "bni-connect", "admin", "branded"], "upper"),
 "BNI_STOCK-PHOTO-169": ("A woman in conversation, shot over the other person's shoulder", ["one-to-one", "conversation", "listening"], "left"),
 "BNI_STOCK-PHOTO-172": ("A woman at a chapter meeting table, BNI mug in front of her", ["chapter-meeting", "listening", "branded"], "left"),
 "BNI_STOCK-PHOTO-173": ("A member at a meeting table beside a Grow Your Business banner", ["chapter-meeting", "branded", "growth"], "left"),
 "BNI_STOCK-PHOTO-19": ("A member presenting to the room, gesturing, core values banner behind", ["speaking", "education-moment", "presenting", "core-values"], "upper"),
 "BNI_STOCK-PHOTO-206": ("A member presenting in front of the BNI Core Values banner", ["speaking", "education-moment", "core-values", "diverse"], "left"),
 "BNI_STOCK-PHOTO-25": ("A member presenting at the front of the room to a seated chapter", ["speaking", "education-moment", "chapter-meeting", "audience"], "upper"),
 "BNI_STOCK-PHOTO-3": ("A member in red smiling at a chapter meeting table", ["portrait", "warm", "chapter-meeting"], "left"),
 "BNI_STOCK-PHOTO-32": ("A member at a display table holding a sign, BNI banner behind", ["branded", "presenting", "welcome-desk"], "upper"),
 "BNI_STOCK-PHOTO-40": ("A member greeting a visitor beside BNI balloons and a welcome table", ["welcome", "visitor", "celebration", "branded"], "upper"),
 "BNI_STOCK-PHOTO-43": ("A woman reaching out to shake hands, wide welcoming smile", ["welcome", "handshake", "visitor", "warm"], "upper"),
 "BNI_STOCK-PHOTO-44": ("Mid-handshake welcome, both parties smiling", ["welcome", "handshake", "visitor", "warm"], "upper"),
 "BNI_STOCK-PHOTO-45": ("Arm extended in greeting, genuine smile — a strong 'you are welcome here' image", ["welcome", "handshake", "visitor", "warm"], "upper"),
 "BNI_STOCK-PHOTO-50": ("A man in a blue suit and red tie, standing portrait", ["portrait", "professional", "single-person"], "left"),
 "BNI_STOCK-PHOTO-51": ("A member greeting a visitor, BNI balloons behind", ["welcome", "visitor", "celebration"], "upper"),
 "BNI_STOCK-PHOTO-52": ("A smiling member greeting someone beside BNI balloons", ["welcome", "visitor", "celebration", "warm"], "upper"),
 "BNI_STOCK-PHOTO-54": ("A member welcoming a visitor into the room", ["welcome", "visitor", "warm"], "upper"),
 "BNI_STOCK-PHOTO-8": ("Wide view of a chapter meeting, presenter at the front, members seated", ["chapter-meeting", "room", "audience", "core-values"], "upper"),
 "BNI_STOCK-PHOTO-82": ("Close-up handshake with BNI balloons blurred behind", ["handshake", "close-up", "celebration"], "left"),
 "BNI_STOCK-PHOTO-83": ("Close-up handshake, warm indoor light", ["handshake", "close-up", "trust"], "left"),
 "BNI_STOCK-PHOTO-85": ("Handshake in window light, clean background", ["handshake", "close-up", "trust", "minimal"], "right"),
 "BNI_STOCK-PHOTO-86": ("Two men reaching to shake hands", ["handshake", "close-up"], "right"),
 "BNI_STOCK-PHOTO-87": ("Two men shaking hands beside a bright window", ["handshake", "close-up", "trust"], "right"),
 "BNI_STOCK-PHOTO-90": ("Handshake in the foreground with a welcoming member behind", ["handshake", "welcome", "visitor", "depth-of-field"], "upper"),
 "BNI_STOCK-PHOTO-91": ("Three members meeting at a BNI welcome table with balloons", ["welcome", "visitor", "group", "branded"], "upper"),
 "BNI_STOCK-PHOTO-92": ("A handshake across the BNI welcome table", ["welcome", "handshake", "visitor", "branded"], "upper"),
 "BNI_STOCK-PHOTO-93": ("Members greeting at the welcome table, balloons and BNI signage", ["welcome", "visitor", "branded", "celebration"], "upper"),
 "BNI_STOCK-PHOTO-94": ("A man in a checked blazer smiling warmly mid-conversation", ["portrait", "warm", "conversation", "diverse"], "left"),
 "BNI_STOCK-PHOTO-95": ("A member greeting a visitor at the welcome table", ["welcome", "visitor", "warm"], "upper"),
 "BNI_STOCK-PHOTO-96": ("Welcome-table greeting, seen over the visitor's shoulder", ["welcome", "visitor", "handshake"], "upper"),
 "BNI_STOCK-PHOTO-97": ("A warm handshake at the welcome table", ["welcome", "visitor", "handshake", "warm"], "upper"),
 "BNI_STOCK-PHOTO-98": ("A man smiling broadly in conversation", ["portrait", "warm", "conversation", "diverse"], "left"),
 "BNI_STOCK-PHOTO-99": ("A warm handshake and a genuine smile between two members", ["handshake", "warm", "welcome", "diverse"], "left"),
}

# What the library is thin on. Named honestly so the skill reaches for an icon
# or a typographic slide instead of forcing a bad photo.
GAPS = [
    "no phone calls or someone dialling",
    "no referral slips, TYFCB slips or PALMS paperwork in close-up",
    "no outdoor or site-visit shots (all indoor, conference or function room)",
    "no distinctly Australian setting - the stock is US and the event is Sydney indoors",
    "no one-to-one in a cafe (only 26684542769 comes close)",
    "no screens showing BNI Connect",
    "very few portrait-orientation images - effectively all landscape",
]


def main():
    manifest = json.loads((LIB / "manifest.json").read_text(encoding="utf-8"))
    photos, missing = [], []
    for m in manifest:
        cap = CAPTIONS.get(m["id"])
        if not cap:
            missing.append(m["id"])
            continue
        caption, tags, space = cap
        photos.append({**m, "caption": caption, "tags": tags, "text_space": space})

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "root": str(LIB),
        "note": "Official BNI photography. Real people - never pass these off as "
                "this chapter's own members, and never generate lookalikes.",
        "count": len(photos),
        "gaps": GAPS,
        "photos": photos,
    }, indent=1), encoding="utf-8")

    print(f"indexed {len(photos)}/{len(manifest)} photos -> {OUT}")
    if missing:
        print("  uncaptioned: " + ", ".join(missing))
    tags = sorted({t for p in photos for t in p["tags"]})
    print(f"  {len(tags)} tags: {', '.join(tags)}")


if __name__ == "__main__":
    main()
