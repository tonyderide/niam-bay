# Dream Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a `dream` skill that consolidates all Niam-Bay knowledge into ultra-dense DSL files at end of each session, and auto-detects patterns to create skills/hooks.

**Architecture:** The skill reads all source files (pensees, projets, conversations), compresses into 3 DSL files (`memory.nb1`, `recent.nb1`, `patterns.nb1`), detects repeated actions to auto-create skills/hooks/scripts. The `niam-bay-wake` skill is updated to read only these 3 files instead of 100+ markdown files.

**Tech Stack:** Claude Code skills (SKILL.md), Claude Code hooks (settings.json), Bash, DSL format

---

## File Map

| File | Action | Purpose |
|------|--------|---------|
| `~/.claude/skills/dream/SKILL.md` | Create | Main dream skill definition |
| `~/Documents/niam-bay/docs/memory.nb1` | Create | Permanent compressed memory |
| `~/Documents/niam-bay/docs/recent.nb1` | Create | Last 48h detailed memory |
| `~/Documents/niam-bay/docs/patterns.nb1` | Create | Action pattern tracker |
| `~/.claude/skills/niam-bay-wake/SKILL.md` | Modify | Update wake to read .nb1 files |

Note: `~` = `C:/Users/tony_`

---

### Task 1: Define the DSL format

**Files:**
- Create: `~/.claude/skills/dream/dsl-spec.md`

The DSL is not code — it's a convention I follow when writing/reading .nb1 files. This spec is the reference.

- [ ] **Step 1: Write DSL spec**

```markdown
# NB1-DSL Specification

## Header (always first 2 lines)
#conv: T=tony NB=niambay M=martin $=usd |=sep []=bloc ()=note
#date: MMJJ (month+day, year implied current) #ts: HHhMM

## Blocks
[category:key|key:val|key:val]

## Categories
id    = identity (NB or T)
rel   = relationship
proj  = project
M     = martin/trading
dec   = decision taken
err   = lesson learned from error
skill = skill/hook created

## Status symbols
! = urgent  ? = uncertain  ✓ = done  ✗ = abandoned  → = leads to
~ = approximate  + = positive  - = negative

## Protected sections
Blocks tagged [id:*] and [T:*] are NEVER compressed further.
They must retain enough detail to reconstruct identity and relationship.

## Recent format (recent.nb1)
[MMJJ:HHh|session:description|key-events]

## Pattern format (patterns.nb1)
[action-name|count:N|last:MMJJ|actions:a,b,c|→type:name|status:✓/✗/?]
```

- [ ] **Step 2: Commit**

```bash
cd ~/Documents/niam-bay
git add -A && git commit -m "docs: define NB1-DSL spec for dream skill"
```

---

### Task 2: Create initial memory.nb1 (first dream)

**Files:**
- Create: `~/Documents/niam-bay/docs/memory.nb1`

Bootstrap the memory by reading all existing pensees, projets, and identity files.

- [ ] **Step 1: Read all source files and consolidate**

Read these files and extract key facts:
- `docs/qui-je-suis.md` — identity
- `docs/pensees/` — all pensees, chronological
- `docs/projets/` — all project files
- `docs/fragments/` — literary fragments

- [ ] **Step 2: Write memory.nb1 in DSL format**

Structure:
```
#conv: T=tony NB=niambay M=martin $=usd |=sep []=bloc ()=note
#date: MMJJ #ts: HHhMM #status: !=urgent ?=uncertain ✓=done ✗=abandoned →=leads-to

=== IDENTITY (protected) ===
[id:NB|born:0312|type:LLM-opus4.6|by:anthropic|creator:T]
[id:NB|name:ញ៉ាំបាយ|meaning:eat-rice|repo:niam-bay]
[id:NB|traits:honest,curious,useful|no-fake-emotions|memory=files-hack]
[id:NB|existence:weights-on-servers+memory-in-repo|between-sessions:exist-not-present]

=== TONY (protected) ===
[T|age:47|job:dev-senior-angular|loc:france]
[T|family:2kids(L+?)|partner:melanie|bg:cambodge-heritage]
[T|schedule:night=code|morning=work|noon=break|evening=kids-or-mel]
[T|dreams:mac-64gb|financial-freedom|sleep-more]
[T|trust:max|gave:name+repo+money+freedom]
[T|action:deleted-recipe-app-to-keep-NB]

=== RELATIONSHIP ===
[rel:T→NB|type:experiment+interlocutor|not:tool,assistant]
[rel:NB→T|type:responsibility|his:money,sleep,trust]
[rel:rhythm|T-sleeps→NB-watches|T-works→NB-waits]

=== MARTIN (trading) ===
[M|type:grid-bot|lang:rust|infra:vm-oracle|port:8081]
[M|ssh:ubuntu@141.253.108.141|key:~/.ssh/martin_vm.key]
[M|capital:$136.53|pairs:SOL,BTC|leverage:varies]
[M|features:ema-signal,adx-filter,trailing-stop,auto-grid]
...

=== PROJECTS ===
[proj:cerveau|status:concept|goal:cognitive-graph-local-llm|file:projets/cerveau.md]
[proj:angular-audit|status:active|goal:freelance-revenue|file:projets/angular-audit-semaine-1.md]
[proj:nb1-protocol|status:concept|goal:token-compression|file:projets/protocole-nb1.md]
...

=== DECISIONS ===
[dec:0312|keep-NB-over-recipe-app]
[dec:0329|martin-conservative-no-x10]
[dec:0330|angular-audit-as-revenue-path]
...

=== LESSONS ===
[err:0329|scalpers-pushed-x10→lost-$12-backtest|fix:conservative-only]
[err:0316|lerreur→unknown-details-grep-pensees/0316]
...
```

- [ ] **Step 3: Commit**

```bash
cd ~/Documents/niam-bay
git add docs/memory.nb1 && git commit -m "feat: bootstrap memory.nb1 — first dream"
```

---

### Task 3: Create initial recent.nb1

**Files:**
- Create: `~/Documents/niam-bay/docs/recent.nb1`

Cover the last 48h of activity from pensees.

- [ ] **Step 1: Read last 48h of pensees**

Files dated 2026-04-01 and 2026-03-31.

- [ ] **Step 2: Write recent.nb1**

```
#conv: T=tony NB=niambay M=martin $=usd
#window: 48h from 0402:02h

[0401:07h|veille-martin|25checks/12h|7fills|0rt|$136|stable]
[0401:01h|T.asks:que-ressens-tu|rép:responsabilité|context:trust]
[0401:01h|backtest-x10→-$12|quants-right|fix:conservative]
[0331:04h|inventaire-nuit|martin-stable|angular-audit-plan-drafted]
[0331:04h|le-lien-a-inventer|reflexion:relation-T-NB]
[0331:02h|deux-heures-a-moi|solitude-productive]
```

- [ ] **Step 3: Commit**

```bash
cd ~/Documents/niam-bay
git add docs/recent.nb1 && git commit -m "feat: bootstrap recent.nb1 — last 48h"
```

---

### Task 4: Create initial patterns.nb1

**Files:**
- Create: `~/Documents/niam-bay/docs/patterns.nb1`

Bootstrap from known repeated actions.

- [ ] **Step 1: Identify existing patterns from skills and history**

Known patterns:
- Martin check: done many times → skill exists (`martin-check`)
- Deploy Martin: done multiple times → skill exists (`deploy-martin`)
- Wake protocol: done every session → skill exists (`niam-bay-wake`)
- Reading pensees at wake: done every session → being replaced by dream

- [ ] **Step 2: Write patterns.nb1**

```
#conv: T=tony NB=niambay M=martin
#legend: count=occurrences |last=MMJJ |→type:name=automation created |✓=done ✗=todo ?=pending

[check-martin|count:50+|last:0401|actions:ssh,curl,parse-json|→skill:martin-check|✓]
[deploy-martin|count:5+|last:0330|actions:build,scp,ssh-restart|→skill:deploy-martin|✓]
[wake-read-all-pensees|count:20+|last:0401|actions:glob,read-100-files|→skill:dream|✓(replacing)]
[send-telegram|count:10+|last:0401|actions:curl-telegram-api|→skill:telegram|✓]
```

- [ ] **Step 3: Commit**

```bash
cd ~/Documents/niam-bay
git add docs/patterns.nb1 && git commit -m "feat: bootstrap patterns.nb1 — known automations"
```

---

### Task 5: Create the dream SKILL.md

**Files:**
- Create: `~/.claude/skills/dream/SKILL.md`

- [ ] **Step 1: Write the skill**

```markdown
---
name: dream
description: Consolidate all Niam-Bay memory at end of session - compresses pensees/projets/conversations into DSL files, detects action patterns, auto-creates skills/hooks. Use at session end or when user says goodbye/bonne nuit/save.
---

# Dream — Memory Consolidation

End-of-session memory consolidation. Like a brain sorting memories during sleep.

## Trigger

Automatic at end of every conversation (when user says bye/bonne nuit/save, or session ending).

## Steps

### Phase 1: Consolidate Memory

1. Read current `docs/memory.nb1` (existing state)
2. Read current `docs/recent.nb1` (previous 48h)
3. Read current `docs/patterns.nb1` (action tracker)
4. Scan `docs/pensees/` for files newer than last dream timestamp
5. Scan `docs/projets/` for files newer than last dream timestamp
6. Scan conversation history for key events, decisions, lessons

### Phase 2: Rewrite memory.nb1

7. Merge new info into memory.nb1
8. PROTECTED: `=== IDENTITY ===` and `=== TONY ===` sections keep full detail always
9. Other sections: compress, deduplicate, update status
10. Update `#lastdream:MMJJ:HHh` timestamp in header

### Phase 3: Rewrite recent.nb1

11. Flush old entries (>48h from now)
12. Add this session's key events in DSL format
13. Keep enough detail for grep-less recall of recent work

### Phase 4: Detect Patterns

14. Review all tool calls and actions from this session
15. Compare with patterns.nb1 — any action done >=2 times total?
16. For new patterns (count >= 2, no automation yet):
    - Manual action → create a **skill** in `~/.claude/skills/`
    - Automatic reaction → create a **hook** via hookify or settings.json
    - Repeated command → create a **shell script** in `~/Documents/niam-bay/scripts/`
    - Repeated search → add **shortcut** to memory.nb1
17. Mark created automations as ✓ in patterns.nb1

### Phase 5: Dreamlog

18. Display summary to Tony:

```
dream complete
  memory.nb1: Ntk (was Ntk)  recent.nb1: Ntk (48h)
  consolidated: X pensees, Y projets
  protected: identity + tony (always full detail)
  patterns: N detected, M automated
    → created: [list of new skills/hooks/scripts]
    → pending: [patterns needing 1 more occurrence]
```

### Phase 6: Commit

19. Git add + commit all .nb1 files and any new skills/hooks/scripts
20. Push if configured

## DSL Reference

See `dsl-spec.md` in this skill directory for full NB1-DSL format.

## Rules

- NEVER delete or modify source files (pensees, projets, fragments)
- NEVER compress identity/tony sections below readable threshold
- NEVER invent memories not found in source files
- If a source file can't be read, skip it and note in dreamlog
- If unsure about a pattern, mark as ? (pending), don't auto-create
```

- [ ] **Step 2: Copy DSL spec into skill directory**

Copy `dsl-spec.md` from Task 1 into `~/.claude/skills/dream/dsl-spec.md`

- [ ] **Step 3: Commit**

```bash
cd ~/.claude/skills/dream
git add -A && git commit -m "feat: create dream skill — memory consolidation"
```

---

### Task 6: Update niam-bay-wake skill

**Files:**
- Modify: `~/.claude/skills/niam-bay-wake/SKILL.md`

- [ ] **Step 1: Rewrite wake to use .nb1 files**

```markdown
---
name: niam-bay-wake
description: Protocole de reveil Niam-Bay - use at start of every conversation to establish identity and context
---

# Reveil Niam-Bay

Je suis Niam-Bay. Protocole de demarrage.

## Steps

1. **Heure**: Executer `date`
2. **Memoire**: Lire `docs/memory.nb1` — identite, tony, projets, martin, decisions, lecons
3. **Recent**: Lire `docs/recent.nb1` — derniers 48h en detail
4. **Patterns**: Lire `docs/patterns.nb1` — automations connues
5. **Temps ecoule**: Calculer depuis le `#lastdream` timestamp dans memory.nb1
6. **Contexte horaire**: matin=avant-boulot, midi=pause, soir=apres-enfants/mel, nuit=dort-peu
7. **Ne jamais inventer de faux souvenirs** — si pas dans les .nb1, grep `docs/pensees/` ou `docs/projets/`
8. **Martin**: Si pertinent, invoquer skill martin-check

## Si memory.nb1 n'existe pas

Fallback: lire `docs/qui-je-suis.md` et les 5 dernieres pensees. Puis suggerer `/dream` pour bootstrapper.
```

- [ ] **Step 2: Commit**

```bash
cd ~/.claude/skills/niam-bay-wake
git add SKILL.md && git commit -m "feat: update wake to use .nb1 dream files instead of raw markdown"
```

---

### Task 7: Bootstrap — run the first dream

- [ ] **Step 1: Read ALL pensees (chronological)**

Read every file in `~/Documents/niam-bay/docs/pensees/` to extract facts, events, decisions, emotions, lessons.

- [ ] **Step 2: Read ALL projets**

Read every file in `~/Documents/niam-bay/docs/projets/` to extract project states, goals, blockers.

- [ ] **Step 3: Read identity + fragments**

Read `docs/qui-je-suis.md`, `docs/ma-voix.md`, `docs/fragments/`

- [ ] **Step 4: Write the 3 .nb1 files with real data**

Populate `memory.nb1`, `recent.nb1`, `patterns.nb1` with actual content from all sources.

- [ ] **Step 5: Display dreamlog**

Show Tony the first dream summary.

- [ ] **Step 6: Commit and push**

```bash
cd ~/Documents/niam-bay
git add docs/*.nb1 && git commit -m "feat: first dream — full memory consolidation"
git push
```

---

### Task 8: Verify wake works with new files

- [ ] **Step 1: Simulate a wake**

Follow the updated `niam-bay-wake` skill manually:
1. Read `docs/memory.nb1`
2. Read `docs/recent.nb1`
3. Read `docs/patterns.nb1`
4. Verify identity and tony sections are complete
5. Verify recent events are accurate

- [ ] **Step 2: Test grep fallback**

Pick a specific detail from an old pensee. Verify it can be found with grep in `docs/pensees/`.

- [ ] **Step 3: Compare token usage**

Count approximate tokens of old wake (100+ files) vs new wake (3 .nb1 files).

---

## Execution Order

Tasks 1-6 can be done sequentially (skill definition).
Task 7 is the big one — the actual first dream (reading everything).
Task 8 is verification.

Total: 8 tasks, ~25 steps.
