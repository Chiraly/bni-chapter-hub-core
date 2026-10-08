# BNI Chapter Hub (core)

A members' website and education program kit for BNI chapters: the next
meeting, the education program with verified CEU podcast hours, the referral
board, the trade sheet, automated presenter reminders and a chapter Spotify
playlist. It also includes the Claude skill that builds the education moments.

Built for **BNI Nexus West** by Hilary Chapman (Seddon Digital), and shared so any
chapter can run its own.

**New here? Read [docs/START-HERE.md](docs/START-HERE.md).**

## This repo vs your chapter's repo

This is the **shared core**: templates, automations, the moments library, the
Claude skill and the docs. Chapters don't edit it. Each chapter has its own small
repo, made from
[bni-chapter-hub-starter](https://github.com/Chiraly/bni-chapter-hub-starter),
holding only its `chapter.json` and its own content. Netlify fetches this core on
every build, so improvements reach every chapter.

```
docs/                          start here, setup, settings, customising, SOP, emails
skills/bni-education-program/  the Claude skill, the site templates and functions
  config/                      chapter.defaults.json - every setting and its default
  library/                     the shared moments library
  templates/                   pages, blocks, emails, Netlify Functions, setup guides
  scripts/                     build_dashboard.py, bni_deck.py and friends
examples/                      example chapters, built by tools/check.py on every release
tools/check.py                 build every example and fail on leaks or breakage
.github/workflows/release.yml  publish a release → move `stable` → rebuild every chapter
.claude-plugin/                makes this repo a Claude Code plugin marketplace
```

## Branches

- `main`: development
- `stable`: what chapters build from and what the plugin installs. Moved by
  publishing a GitHub Release. See [docs/RELEASING.md](docs/RELEASING.md).

## Credits and brand

BNI names, logos, brand assets and the GAINS worksheet belong to BNI Global LLC
and are used under BNI's brand standards for internal chapter education. Icons are
[Lucide](https://lucide.dev) (ISC). Podcast data comes from the Official BNI
Podcast's public feed.
