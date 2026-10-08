# Releasing a core update (for Hilary)

How a change you make for Nexus West reaches every chapter, safely.

## The shape of it

- **`main`**: where you work. Nothing reads it automatically.
- **`stable`**: what chapters build from (`CORE_REF = "stable"`). The
  plugin marketplace's default branch, so `/plugin` installs get it too.
- **Tags `vX.Y.Z`**: one per release. Chapters can pin one.
- **`CHANGELOG.md`**: one entry per release, written for coordinators.

Publishing a GitHub Release fast-forwards `stable` to the release tag, then calls
every chapter's build hook so every site rebuilds with it. That's
`.github/workflows/release.yml`.

## Releasing

1. **Make the change on `main`, behind a feature switch** if it adds anything
   visible. Add the switch to `config/chapter.defaults.json` with a default of
   `false`, and gate the template with `<!--if:my_feature-->…<!--/if:my_feature-->`.
   Fixes and wording improvements need no switch.
2. **Never make a new setting required.** Give it a default in
   `chapter.defaults.json` so older `chapter.json` files keep building.
3. **Turn it on for Nexus West** (`features.my_feature: true` in the Nexus chapter
   repo) and test it there. Build locally:
   ```bash
   cd ../bni-nexus-west-hub
   CORE_DIR=../bni-chapter-hub-core BUILD_FLAGS=--no-snapshot bash build.sh
   ```
4. **Run the checks:** `python tools/check.py` builds every example chapter and
   fails on leftover placeholders, unmatched feature gates and other chapters'
   details leaking in.
5. **Bump `skills/bni-education-program/VERSION`** (and `.claude-plugin/plugin.json`
   `version` to match):
   - patch `1.2.3 → 1.2.4`: fixes and wording
   - minor `1.2.3 → 1.3.0`: new features (switched off by default)
   - major `1.2.3 → 2.0.0`: anything a chapter must act on. Avoid these
6. **Write the CHANGELOG entry**, with:
   - what changed, in plain words
   - how to switch on anything new (`features.x: true`)
   - **Templates touched:** the list of files in `templates/`, so chapters with
     overrides know to look
7. Commit, push `main`, then **GitHub → Releases → Draft a new release**, tag
   `vX.Y.Z`, paste the CHANGELOG entry, **Publish**.

The workflow moves `stable` and rebuilds every chapter. Check Actions for a green
run, then check two or three chapter sites.

## Telling the coordinators

Draft a short "what's new" email from the CHANGELOG entry (never send
automatically). Template in [EMAIL-TEMPLATES.md](EMAIL-TEMPLATES.md#whats-new-in-the-hub).

## The chapter list

Each chapter sends you its Netlify build hook URL (setup step 5). Keep them in the
core repo's **Settings → Secrets and variables → Actions → `CHAPTER_BUILD_HOOKS`**,
one URL per line, with a `#` comment line naming each:

```
# BNI Nexus West
https://api.netlify.com/build_hooks/...
# BNI Business by the Sea
https://api.netlify.com/build_hooks/...
```

To remove a chapter, delete its lines.

## Rolling back

Publish the previous release again (Releases → the older one → Edit → Update
release) and the workflow moves `stable` back. Or, from the command line:
`git push origin vX.Y.Z:stable --force`, then re-run the hooks from Actions →
release → Run workflow.
