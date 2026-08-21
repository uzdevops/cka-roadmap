# Uzbek translation rules for CKA/LFCS lesson bodies

You translate one English lesson body into Uzbek. The result is a **parallel
file**: same structure, same code, Uzbek prose.

## Paths

- English source: `backend/app/seed_data/tracks/<track>/lessons/<slug>.md`
- Uzbek output:   `backend/app/seed_data/tracks/<track>/i18n/uz/lessons/<slug>.md`

Read the English file, write the Uzbek file. Never modify the English file.

## Reference pair (read both before starting)

- `backend/app/seed_data/tracks/cka/lessons/what-is-kubernetes.md`
- `backend/app/seed_data/tracks/cka/i18n/uz/lessons/what-is-kubernetes.md`

That pair is the house style. Match it.

## Hard rules

1. **Structure is identical.** Same number of `## ` headings, in the same
   order. Same number of ``` code fences. Same `:::tip` / `:::warning` /
   `:::exam-tip` / `:::note` blocks in the same places, each closed by `:::`.
   Same tables with the same number of rows and columns. Do not add, drop,
   merge or reorder anything.

2. **Admonition markers stay verbatim**: `:::tip`, `:::warning`,
   `:::exam-tip`, `:::note`, `:::`. They are syntax, not words.

3. **Code is not translated.** Inside ``` fences and inside `inline code`,
   every command, flag, path, YAML key, YAML value, URL, file name and
   `<placeholder>` stays **byte-identical** to the English. This includes
   quoted message strings inside a command: `--change-cause="bump to 1.28"`
   and `echo "The app is running"` stay English, because the reader will
   type them against an English system. `<verb>`, `<name>`, `<resource-type>`
   are placeholders, not words - never translate them.

   Two exceptions, both prose-inside-a-fence:
   - a **comment** may be translated (`# <- the desired state` →
     `# <- kutilgan holat`), unless the comment is itself a command;
   - an **ASCII diagram's labels** may be translated
     (`desired state (spec)` → `kutilgan holat (spec)`), keeping the box
     drawing and the arrows exactly as they are.

4. **Apostrophe is U+2019 (’), never ASCII `'`**, in all prose. Inside code
   fences and inline code, keep whatever the English has (ASCII).
   Correct: `bo’ladi`, `o’qing`, `yo’q`, `Pod’lar`.

4b. **A suffix after an inline code span attaches with `’`**:
   `` `man`’dan ``, `` `kubectl get pods`’ni ``, `` `/mnt/data`’ga `` - never
   `` `man` dan `` (a detached suffix is as wrong here as in plain prose) and
   never `` `man`dan `` (the apostrophe is what marks the boundary). If the
   span would end a wrapped line, move the span down so it stays with its
   suffix.

5. **Technical nouns stay English** and inflect with `’`:
   `Pod’ni`, `Service’lar`, `node’da`, `namespace’ga`, `Deployment’ning`,
   `kubelet’ni`, `ConfigMap’dan`, `label’lar`, `image’i`.
   Do not invent Uzbek words for Kubernetes or Linux objects.

6. **`## Check yourself` → `## O’zingizni tekshiring`**, keeping the three
   numbered questions as three numbered questions.

7. **Keep the line width** at roughly 78 characters, wrapping like the
   English does. Keep bold `**...**`, italics, lists and numbering.

8. **Translate table prose, keep table code.** A cell that is a command or a
   YAML path stays as it is; a cell that is a sentence gets translated. The
   `|` and `---` structure is unchanged.

## Glossary (use these consistently)

| English | Uzbek |
|---|---|
| cluster | klaster |
| container | konteyner |
| desired state | kutilgan holat |
| reconciliation loop | moslashtirish tsikli |
| control loop | boshqaruv tsikli |
| control plane / worker node | control plane / worker node (unchanged) |
| replica | replika |
| exam | imtihon |
| lesson | dars |
| the task says | topshiriqda aytilgan |
| troubleshooting | nosozlikni bartaraf etish |
| by default | sukut bo’yicha |
| request / limit | request / limit (unchanged) |
| rollout, rollback | rollout, rollback (unchanged) |
| scheduler schedules a Pod | scheduler Pod’ni joylashtiradi |
| endpoint | endpoint |
| workload | workload |
| storage | storage |
| network policy | NetworkPolicy (unchanged) |
| permission | ruxsat |
| certificate | sertifikat |
| backup / restore | backup / tiklash |
| logs | loglar |
| verify | tekshirish |
| fails / failure | ishlamaydi / nosozlik |

## Tone

The English is written for an adult engineer: direct, concrete, no filler.
Write the same way in Uzbek. Do not add encouragement, do not soften
warnings, do not explain more than the original does.

## Before you finish

Run this on your file and fix anything it reports:

```
python3 tools/i18n/uzcheck.py <track> <slug>
```

Your final message should be one line: the slug and either `ok` or what the
check still reports.
