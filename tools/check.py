"""
check.py - build every example chapter and fail on anything that would embarrass
a release.

    python tools/check.py

For each examples/<chapter>/chapter.json it builds the site (no live snapshot)
and checks that:
  - the build succeeds (placeholders, feature gates and settings are validated
    by the build itself)
  - no other chapter's details leak into the output - every example lists its
    own giveaway words in examples/<chapter>/check.json under "must_not_contain"
  - the generated functions are free of build tokens

Runs in the release workflow before `stable` is moved, so a release that breaks
a chapter never reaches one.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "skills" / "bni-education-program" / "scripts" / "build_dashboard.py"
OUT = ROOT / ".check"

# Nexus West giveaways (IDs and account details deliberately not listed in a
# public repo). No example other than Nexus may contain them, and the
# core library and templates must not either.
NEXUS = ["Nexus", "Little Ginger", "Akuna", "Keeping it ELF", "Hilary"]


def strip_data(s: str) -> str:
    return re.sub(r"data:[^\"')]+", "", s)


def main() -> int:
    failures = []
    shutil.rmtree(OUT, ignore_errors=True)
    for cfg in sorted((ROOT / "examples").glob("*/chapter.json")):
        name = cfg.parent.name
        out = OUT / name
        r = subprocess.run([sys.executable, str(BUILD), "--chapter", str(cfg),
                            "--out", str(out), "--no-snapshot"],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", env={**os.environ, "PYTHONIOENCODING": "utf-8"})
        if r.returncode:
            failures.append(f"{name}: build failed\n{r.stdout}\n{r.stderr}")
            continue
        extra = cfg.parent / "check.json"
        spec = json.loads(extra.read_text(encoding="utf-8")) if extra.exists() else {}
        banned = spec.get("must_not_contain", NEXUS)
        # Customisation layers that must survive a core change.
        for rel, words in spec.get("must_contain", {}).items():
            f = out / rel
            text = f.read_text(encoding="utf-8") if f.exists() else ""
            for word in words:
                if word not in text:
                    failures.append(f"{name}: expected '{word}' in {rel}")
        for f in list(out.rglob("*.html")) + list(out.rglob("*.mts")) + [out / "public" / "moments.json"]:
            text = strip_data(f.read_text(encoding="utf-8"))
            for word in banned:
                if word.lower() in text.lower():
                    failures.append(f"{name}: '{word}' found in {f.relative_to(out)}")
            if f.suffix == ".mts" and re.search(r"@@[\w:-]+@@", text):
                failures.append(f"{name}: build token left in {f.name}")
        print(f"ok  {name}")

    # The shared library and email copy must be chapter-neutral too.
    for f in [ROOT / "skills/bni-education-program/library/moments.json",
              ROOT / "skills/bni-education-program/templates/emails/reminders.json"]:
        text = f.read_text(encoding="utf-8")
        for word in NEXUS:
            if word.lower() in text.lower():
                failures.append(f"core: '{word}' found in {f.relative_to(ROOT)}")

    shutil.rmtree(OUT, ignore_errors=True)
    if failures:
        print("\nFAILED:\n  " + "\n  ".join(failures))
        return 1
    print("all chapters build cleanly")
    return 0


if __name__ == "__main__":
    sys.exit(main())
