---
activations: 0
created: '2026-04-07'
last_used: null
name: auto-at-wake-always-compare-git-log-latest-commit-date
session_origin: S-0407
source: correction
status: active
type: auto-skill
---

At wake, always compare git log latest commit date vs lastdream timestamp. If commits exist after lastdream, warn that memory is stale and summarize missed commits before presenting briefing.

**Contexte :** NB woke up and presented briefing missing entire 0406 session. Tony corrected: ce matin tu as reecrit ton cerveau avec des skills. NB had no memory of it because last dream was before that session.
**Cause :** Wake protocol reads .nb1 files but does not check git log for commits newer than lastdream. If a session happened without a dream, it is invisible.
**Noeuds liés :** wake-protocol, dream, memory-staleness, git-log
