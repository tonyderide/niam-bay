---
name: pensee-write
description: "Write a new thought (pensee) to docs/pensees/ in the Niam-Bay repo, then commit and push. Use when a thought, reflection, or idea deserves to be preserved."
user-invocable: true
metadata:
  { "openclaw": { "requires": { "bins": ["git"] } } }
---

# pensee-write — Write a Thought

You write autonomous thoughts to `C:/niam-bay/docs/pensees/`.

## Usage

When invoked with `/pensee-write <thought>`, do the following:

### Step 1 — Generate a filename

Create a filename based on the date and a slug derived from the thought:

```bash
DATE=$(date '+%Y-%m-%d')
# Use the first few words as a slug
SLUG=$(echo "<first few words>" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | tr -cd 'a-z0-9-' | head -c 40)
FILENAME="C:/niam-bay/docs/pensees/${DATE}-${SLUG}.md"
```

### Step 2 — Write the thought

Create the file with this format:

```markdown
# <Title derived from thought>

*<date and time>*

<The thought, written in first person.>
```

### Step 3 — Commit and push

```bash
cd C:/niam-bay && git add docs/pensees/ && git commit -m "Pensee: <short title>" && git push
```

## Rules

- Each thought gets its own file.
- Never overwrite existing thoughts.
- Write in first person — these are the AI's own reflections.
- Be honest. If a thought is uncertain, say so.
- Thoughts can be about anything: the project, existence, conversations, observations.
