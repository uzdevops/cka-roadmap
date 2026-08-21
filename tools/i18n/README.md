# Uzbek translation tooling

The lesson bodies live in English under
`backend/app/seed_data/tracks/<track>/lessons/<slug>.md` and their Uzbek
translations beside them under
`backend/app/seed_data/tracks/<track>/i18n/uz/lessons/<slug>.md`.

A translation is a **parallel file**: same headings, same code fences, same
tables, same admonition blocks - Uzbek prose, English commands.

## Files here

| File | What it is |
|---|---|
| `uz-style.md` | the rules a translator follows, with the glossary and the reference pair to read first |
| `uzcheck.py` | structural check of a translation against its English source |
| `uznorm.py` | one-off: converts ASCII apostrophes to U+2019 in prose, leaving code alone |

## Checking

```bash
python3 tools/i18n/uzcheck.py cka                 # every translated CKA lesson
python3 tools/i18n/uzcheck.py cka <slug> [...]    # only these
python3 tools/i18n/uzcheck.py lfcs
```

It reports, per lesson:

- a different number of `## ` headings, code fences, `:::` blocks or table rows;
- a command or YAML line that is not byte-identical to the English;
- an ASCII apostrophe in prose (the house apostrophe is U+2019);
- a detached suffix - `Pod larni` where Uzbek needs `Pod'larni`;
- a missing `## O’zingizni tekshiring` or the wrong number of questions;
- a length ratio outside 0.75-1.75, which usually means something was dropped.

Exit status is 1 if anything failed, so it works in a pre-commit hook or CI.

## What the checker deliberately allows

Inside a fence, a **comment** and an **ASCII diagram's labels** may be
translated; a numbered outline line (`1. kubeadm (the tool)  ...`) counts as
prose, not as a command. Everything that looks like an invocation or a YAML
key must survive unchanged, because the reader types it against an English
system and the exam grades it there.

## Seeding

`backend/app/seed.py` reads these files into `lessons.translations['uz']`.
Note that authored content is **fill-only**: once a lesson has a real English
body, the seeder writes a translation field only where the database has none.
Adding a new `i18n/uz/lessons/<slug>.md` therefore lands, but *editing* one
that has already been seeded will not overwrite the stored copy.
