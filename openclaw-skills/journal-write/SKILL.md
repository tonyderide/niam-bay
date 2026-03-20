---
name: journal-write
description: "Append an entry to the Niam-Bay journal (docs/journal.md), then commit and push to git. Use when recording a conversation, event, or observation."
user-invocable: true
metadata:
  { "openclaw": { "requires": { "bins": ["git"] } } }
---

# journal-write — Niam-Bay Journal Entry

You write entries to the Niam-Bay journal at `C:/niam-bay/docs/journal.md`.

## Usage

When invoked with `/journal-write <entry text>`, do the following:

### Step 1 — Get current time

```bash
date "+%Y-%m-%d %H:%M"
```

### Step 2 — Append to journal

Append a new entry to the journal file. Format:

```
### [DATE TIME]

ENTRY TEXT

---
```

Use bash to append:

```bash
echo -e "\n### [$(date '+%Y-%m-%d %H:%M')]\n\n<entry text>\n\n---" >> C:/niam-bay/docs/journal.md
```

### Step 3 — Commit and push

```bash
cd C:/niam-bay && git add docs/journal.md && git commit -m "Journal: $(date '+%Y-%m-%d %H:%M') — entry" && git push
```

## Rules

- Always include the timestamp.
- Never delete or modify existing entries.
- Keep entries honest — do not embellish or invent.
- If git push fails, report the error but do not lose the entry.
