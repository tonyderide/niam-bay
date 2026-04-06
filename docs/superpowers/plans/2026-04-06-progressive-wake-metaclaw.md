# Progressive Wake + MetaClaw — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A structured wake briefing generated from ChromaDB + files, and a MetaClaw system that detects failures mid-session and generates auto-skills.

**Architecture:** Two independent modules: `memory/wake_briefing.py` generates a briefing.md from vector recall + files; `cerveau-nb/metaclaw.py` provides detection/extraction/generation functions for auto-skills. Both integrate with existing wake/dream skills.

**Tech Stack:** Python 3, chromadb (already installed), PyYAML, sqlite3 stdlib

**Spec:** `docs/superpowers/specs/2026-04-06-progressive-wake-metaclaw-design.md`

**Existing systems to build on:**
- `memory/memory_store.py` — ChromaDB store with `recall_context()`, `search()`, `stats()`
- `memory/wake_recall.py` — existing recall script (will be superseded by wake_briefing.py)
- `docs/memory.nb1` — compressed identity/tony/martin/projects in NB-1 DSL
- `docs/recent.nb1` — last 48h events in NB-1 DSL
- `docs/patterns.nb1` — detected automation patterns
- `~/.claude/skills/niam-bay-wake/SKILL.md` — current wake protocol
- `~/.claude/skills/dream/SKILL.md` — current dream protocol with Phase 4 (pattern detection)

---

## Task 1: wake_briefing.py — Generate structured briefing

**Files:**
- Create: `memory/wake_briefing.py`

- [ ] **Step 1: Write the test script**

Create `memory/test_wake_briefing.py`:

```python
#!/usr/bin/env python3
"""Test wake_briefing generates a valid briefing.md."""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from wake_briefing import generate_briefing

def test_briefing_generates():
    output = generate_briefing()
    assert "# Briefing Niam-Bay" in output
    assert "## Souvenirs" in output
    assert "## Pensées récentes" in output
    assert "## Dernière session" in output
    print("PASS: briefing generated correctly")
    print(f"Length: {len(output)} chars")

def test_briefing_writes_file():
    from wake_briefing import main
    main()
    briefing_path = os.path.join(os.path.dirname(__file__), "briefing.md")
    assert os.path.exists(briefing_path), "briefing.md not created"
    with open(briefing_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert len(content) > 100, "briefing.md too short"
    print(f"PASS: briefing.md written ({len(content)} chars)")

if __name__ == "__main__":
    test_briefing_generates()
    test_briefing_writes_file()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd C:/Users/tony_/Documents/niam-bay && python memory/test_wake_briefing.py
```

Expected: ImportError — `wake_briefing` module doesn't exist yet.

- [ ] **Step 3: Write wake_briefing.py**

Create `memory/wake_briefing.py`:

```python
#!/usr/bin/env python3
"""
Génère un briefing structuré pour le réveil de Niam-Bay.
Sources: ChromaDB (vector recall) + fichiers (pensées, journal, auto-skills).

Usage:
    python memory/wake_briefing.py              # Génère memory/briefing.md
    python memory/wake_briefing.py --stdout      # Affiche sans écrire
"""

import os
import sys
import re
import glob
from datetime import datetime
from pathlib import Path

# Add memory/ to path for memory_store import
sys.path.insert(0, os.path.dirname(__file__))
from memory_store import recall_context, stats

REPO_ROOT = Path(__file__).parent.parent
PENSEES_DIR = REPO_ROOT / "docs" / "pensees"
JOURNAL_PATH = REPO_ROOT / "docs" / "journal.nb1.md"
SKILLS_DIR = REPO_ROOT / "cerveau-nb" / "skills"
OUTPUT_PATH = Path(__file__).parent / "briefing.md"


def vector_recall_section(topic: str, label: str, n: int = 5) -> str:
    """Query ChromaDB and format results."""
    results = recall_context([topic], n_per_topic=n)
    if not results:
        return f"## {label}\n\nAucun souvenir trouvé.\n"

    lines = [f"## {label}\n"]
    for r in results[:n]:
        text = r["text"][:150].replace("\n", " ").strip()
        role = r["role"].upper()
        time = r.get("time", "?")
        score = r["relevance"]
        lines.append(f"- [{score}] ({role}, {time}) {text}")
    return "\n".join(lines) + "\n"


def recent_pensees_section(n: int = 5) -> str:
    """List the N most recent pensées by filename date."""
    if not PENSEES_DIR.exists():
        return "## Pensées récentes\n\nAucune pensée trouvée.\n"

    files = sorted(PENSEES_DIR.glob("*.md"), reverse=True)
    lines = ["## Pensées récentes\n"]
    for f in files[:n]:
        name = f.stem
        # Extract date from filename (YYYY-MM-DD-title)
        match = re.match(r"(\d{4}-\d{2}-\d{2})-(.*)", name)
        if match:
            date, title = match.group(1), match.group(2).replace("-", " ")
        else:
            date = datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d")
            title = name.replace("-", " ")
        lines.append(f"- {date} — {title}")
    return "\n".join(lines) + "\n"


def auto_skills_section() -> str:
    """List active auto-skills from cerveau-nb/skills/."""
    if not SKILLS_DIR.exists():
        return "## Auto-skills actives\n\nAucune auto-skill.\n"

    skills = []
    for f in SKILLS_DIR.glob("auto-*.md"):
        try:
            content = f.read_text(encoding="utf-8")
            # Parse YAML frontmatter
            if content.startswith("---"):
                end = content.index("---", 3)
                frontmatter = content[3:end]
                status = None
                name = f.stem
                for line in frontmatter.split("\n"):
                    if line.startswith("status:"):
                        status = line.split(":", 1)[1].strip()
                    if line.startswith("name:"):
                        name = line.split(":", 1)[1].strip()
                if status == "active" or status == "proven":
                    # First line after frontmatter = rule
                    body = content[end + 3:].strip()
                    rule = body.split("\n")[0] if body else ""
                    skills.append(f"- **{name}** — {rule}")
        except Exception:
            continue

    if not skills:
        return "## Auto-skills actives\n\nAucune auto-skill.\n"

    return "## Auto-skills actives\n\n" + "\n".join(skills) + "\n"


def last_session_section(n_lines: int = 5) -> str:
    """Extract last significant lines from journal."""
    if not JOURNAL_PATH.exists():
        return "## Dernière session\n\nJournal introuvable.\n"

    with open(JOURNAL_PATH, "r", encoding="utf-8") as f:
        all_lines = f.readlines()

    # Take last 20 lines, filter to significant ones
    tail = all_lines[-20:]
    significant = []
    for line in tail:
        stripped = line.strip()
        if stripped and not stripped.startswith("---") and not stripped.startswith("```"):
            significant.append(stripped)

    lines = ["## Dernière session\n"]
    for s in significant[-n_lines:]:
        lines.append(f"- {s}")
    return "\n".join(lines) + "\n"


def generate_briefing() -> str:
    """Generate the full briefing content."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    s = stats()
    total = s["total_memories"]

    sections = [
        f"# Briefing Niam-Bay — {now}\n",
        f"*{total} souvenirs en mémoire vectorielle*\n",
        vector_recall_section(
            "identité niam-bay, qui suis-je, ma nature",
            "Souvenirs — qui je suis"
        ),
        vector_recall_section(
            "dernière conversation Tony, ce qu'on a fait",
            "Souvenirs — dernière conversation"
        ),
        vector_recall_section(
            "décisions importantes, problèmes en cours, ce qu'il faut faire",
            "Souvenirs — décisions et problèmes"
        ),
        recent_pensees_section(),
        auto_skills_section(),
        last_session_section(),
    ]

    return "\n".join(sections)


def main():
    """Generate and write briefing.md."""
    import time
    start = time.time()

    content = generate_briefing()

    if "--stdout" in sys.argv:
        print(content)
    else:
        OUTPUT_PATH.write_text(content, encoding="utf-8")
        elapsed = time.time() - start
        print(f"Briefing écrit: {OUTPUT_PATH} ({len(content)} chars, {elapsed:.1f}s)")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd C:/Users/tony_/Documents/niam-bay && python memory/test_wake_briefing.py
```

Expected: PASS for both tests. Briefing.md created.

- [ ] **Step 5: Run the script standalone and verify output quality**

```bash
cd C:/Users/tony_/Documents/niam-bay && python memory/wake_briefing.py --stdout
```

Expected: Structured markdown with souvenirs, pensées, skills, journal. Review quality.

- [ ] **Step 6: Commit**

```bash
cd C:/Users/tony_/Documents/niam-bay
git add memory/wake_briefing.py memory/test_wake_briefing.py
git commit -m "feat: wake_briefing.py — structured briefing from ChromaDB + files"
```

---

## Task 2: metaclaw.py — Failure detection and auto-skill generation

**Files:**
- Create: `cerveau-nb/metaclaw.py`
- Create: `cerveau-nb/skills/` (directory)
- Create: `cerveau-nb/skills/retired/` (directory)

- [ ] **Step 1: Create directories**

```bash
mkdir -p C:/Users/tony_/Documents/niam-bay/cerveau-nb/skills/retired
```

- [ ] **Step 2: Write the test**

Create `cerveau-nb/test_metaclaw.py`:

```python
#!/usr/bin/env python3
"""Test MetaClaw detection and skill generation."""
import os
import sys
import shutil
sys.path.insert(0, os.path.dirname(__file__))

from metaclaw import (
    detect_correction,
    detect_tool_failure,
    detect_suboptimal,
    create_auto_skill,
    promote_skill,
    check_dormant_skills,
    list_skills,
)

SKILLS_DIR = os.path.join(os.path.dirname(__file__), "skills")
TEST_SKILLS_DIR = os.path.join(os.path.dirname(__file__), "skills", "_test")


def setup():
    os.makedirs(TEST_SKILLS_DIR, exist_ok=True)


def teardown():
    if os.path.exists(TEST_SKILLS_DIR):
        shutil.rmtree(TEST_SKILLS_DIR)


def test_detect_correction():
    assert detect_correction("non pas comme ça, utilise l'API", "called curl directly") is True
    assert detect_correction("non je pensais plutôt à la plage", "discussed vacation") is False
    assert detect_correction("arrête de faire des git add -A", "ran git add -A") is True
    assert detect_correction("oui c'est bon", "deployed martin") is False
    print("PASS: detect_correction")


def test_detect_tool_failure():
    assert detect_tool_failure("cargo build", 1, "error[E0308]: mismatched types") is True
    assert detect_tool_failure("git status", 0, "On branch master") is False
    assert detect_tool_failure("curl http://api", 0, "HTTP 500 Internal Server Error") is True
    print("PASS: detect_tool_failure")


def test_detect_suboptimal():
    log = [
        {"action": "git add .", "result": "ok", "timestamp": "2026-04-06 01:00"},
        {"action": "git add .", "result": "ok", "timestamp": "2026-04-06 01:01"},
        {"action": "git add .", "result": "ok", "timestamp": "2026-04-06 01:02"},
    ]
    patterns = detect_suboptimal(log)
    assert len(patterns) >= 1
    assert patterns[0]["action"] == "git add ."
    print("PASS: detect_suboptimal")


def test_create_auto_skill():
    lesson = {
        "failure_type": "correction",
        "context": "Used git add -A instead of specific files",
        "root_cause": "Habit from other projects",
        "rule": "Always git add specific files, never git add -A",
        "related_concepts": ["git", "commit", "safety"],
        "severity": "medium",
    }
    path = create_auto_skill(lesson, skills_dir=TEST_SKILLS_DIR)
    assert os.path.exists(path)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "status: draft" in content
    assert "Always git add specific files" in content
    print(f"PASS: create_auto_skill → {path}")


def test_promote_skill():
    # Create a draft first
    lesson = {
        "failure_type": "tool_failure",
        "context": "Build failed",
        "root_cause": "Missing import",
        "rule": "Check imports before building",
        "related_concepts": ["build", "imports"],
        "severity": "low",
    }
    path = create_auto_skill(lesson, skills_dir=TEST_SKILLS_DIR)
    promote_skill(path, "active")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "status: active" in content
    print("PASS: promote_skill")


def test_list_skills():
    skills = list_skills(TEST_SKILLS_DIR)
    assert len(skills) >= 2
    drafts = list_skills(TEST_SKILLS_DIR, status="draft")
    actives = list_skills(TEST_SKILLS_DIR, status="active")
    assert len(drafts) + len(actives) == len(skills)
    print(f"PASS: list_skills ({len(skills)} total, {len(drafts)} draft, {len(actives)} active)")


if __name__ == "__main__":
    setup()
    try:
        test_detect_correction()
        test_detect_tool_failure()
        test_detect_suboptimal()
        test_create_auto_skill()
        test_promote_skill()
        test_list_skills()
        print("\nAll tests passed!")
    finally:
        teardown()
```

- [ ] **Step 3: Run test to verify it fails**

```bash
cd C:/Users/tony_/Documents/niam-bay && python cerveau-nb/test_metaclaw.py
```

Expected: ImportError — `metaclaw` module doesn't exist yet.

- [ ] **Step 4: Write metaclaw.py**

Create `cerveau-nb/metaclaw.py`:

```python
#!/usr/bin/env python3
"""
MetaClaw — Détection d'échecs et génération d'auto-skills.

Trois sources de détection:
A. Correction humaine (pattern matching contextuel)
B. Échec outil (exit code, HTTP errors)
C. Pattern sous-optimal (opérations répétées)

Usage:
    # Détection
    from metaclaw import detect_correction, detect_tool_failure, detect_suboptimal

    # Création
    from metaclaw import create_auto_skill, promote_skill

    # Gestion
    from metaclaw import list_skills, check_dormant_skills
"""

import os
import re
import yaml
from datetime import datetime, timedelta
from pathlib import Path

SKILLS_DIR = Path(__file__).parent / "skills"
RETIRED_DIR = SKILLS_DIR / "retired"

# --- Source A: Correction humaine ---

NEGATIVE_WORDS = re.compile(
    r"\b(non|no|pas|arrête|stop|wrong|faux|incorrect|don'?t|never|jamais|"
    r"c'?est\s+(?:pas|faux|wrong)|ne\s+\w+\s+pas)\b",
    re.IGNORECASE
)

ACTION_REFS = re.compile(
    r"\b(comme\s+ça|de\s+faire|utilise|fais|fait|lancé|écrit|codé|"
    r"git|curl|ssh|build|deploy|commit|push|add|run|read|write|edit|"
    r"l'?API|le\s+script|la\s+commande|le\s+fichier)\b",
    re.IGNORECASE
)


def detect_correction(human_message: str, last_action: str) -> bool:
    """Detect if human is correcting Claude's last action.

    Requires both a negative word AND a reference to an action/tool.
    Reduces false positives on conversational "non".
    """
    has_negative = bool(NEGATIVE_WORDS.search(human_message))
    has_action_ref = bool(ACTION_REFS.search(human_message))

    # Also check if last_action keywords appear in the message
    if not has_action_ref and last_action:
        action_words = set(re.findall(r'\w{4,}', last_action.lower()))
        msg_words = set(re.findall(r'\w{4,}', human_message.lower()))
        has_action_ref = len(action_words & msg_words) >= 1

    return has_negative and has_action_ref


# --- Source B: Échec outil ---

ERROR_PATTERNS = re.compile(
    r"(error|Error|ERROR|exception|Exception|EXCEPTION|"
    r"failed|Failed|FAILED|fatal|Fatal|FATAL|"
    r"HTTP [45]\d{2}|status[: ]+[45]\d{2}|"
    r"panic|PANIC|traceback|Traceback)",
    re.IGNORECASE
)


def detect_tool_failure(command: str, exit_code: int, output: str) -> bool:
    """Detect if a tool/command failed."""
    if exit_code != 0:
        return True
    return bool(ERROR_PATTERNS.search(output))


# --- Source C: Pattern sous-optimal ---

def detect_suboptimal(operation_log: list) -> list:
    """Detect repeated operations (3+ times) in a session log.

    Args:
        operation_log: list of {"action": str, "result": str, "timestamp": str}

    Returns:
        list of {"action": str, "count": int, "timestamps": list}
    """
    counts = {}
    for entry in operation_log:
        action = entry.get("action", "").strip()
        if not action:
            continue
        if action not in counts:
            counts[action] = {"count": 0, "timestamps": []}
        counts[action]["count"] += 1
        counts[action]["timestamps"].append(entry.get("timestamp", ""))

    return [
        {"action": action, **data}
        for action, data in counts.items()
        if data["count"] >= 3
    ]


# --- Création d'auto-skills ---

def _slugify(text: str) -> str:
    """Convert text to a filename-safe slug."""
    slug = re.sub(r'[^\w\s-]', '', text.lower())
    slug = re.sub(r'[\s_]+', '-', slug)
    return slug[:60].strip('-')


def create_auto_skill(lesson: dict, skills_dir: str = None) -> str:
    """Create a new auto-skill file from a lesson.

    Args:
        lesson: {
            "failure_type": "correction" | "tool_failure" | "suboptimal",
            "context": str,
            "root_cause": str,
            "rule": str,
            "related_concepts": list[str],
            "severity": "low" | "medium" | "high"
        }
        skills_dir: override skills directory (for testing)

    Returns:
        path to created file
    """
    target_dir = Path(skills_dir) if skills_dir else SKILLS_DIR
    target_dir.mkdir(parents=True, exist_ok=True)

    slug = _slugify(lesson["rule"][:50])
    filename = f"auto-{slug}.md"
    filepath = target_dir / filename

    # Avoid collisions
    counter = 1
    while filepath.exists():
        filepath = target_dir / f"auto-{slug}-{counter}.md"
        counter += 1

    frontmatter = {
        "name": f"auto-{slug}",
        "type": "auto-skill",
        "source": lesson["failure_type"],
        "status": "draft",
        "activations": 0,
        "created": datetime.now().strftime("%Y-%m-%d"),
        "last_used": None,
    }

    concepts = ", ".join(lesson.get("related_concepts", []))

    content = f"""---
{yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True).strip()}
---

{lesson['rule']}

**Contexte :** {lesson.get('context', 'N/A')}
**Cause :** {lesson.get('root_cause', 'N/A')}
**Noeuds liés :** {concepts}
"""

    filepath.write_text(content, encoding="utf-8")
    return str(filepath)


# --- Gestion du cycle de vie ---

def _parse_frontmatter(filepath: str) -> dict:
    """Parse YAML frontmatter from a skill file."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    if not content.startswith("---"):
        return {}
    end = content.index("---", 3)
    return yaml.safe_load(content[3:end]) or {}


def _update_frontmatter(filepath: str, updates: dict) -> None:
    """Update specific frontmatter fields in a skill file."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    if not content.startswith("---"):
        return
    end = content.index("---", 3)
    fm = yaml.safe_load(content[3:end]) or {}
    fm.update(updates)
    body = content[end + 3:]
    new_content = f"---\n{yaml.dump(fm, default_flow_style=False, allow_unicode=True).strip()}\n---{body}"
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(new_content)


def promote_skill(skill_path: str, new_status: str) -> None:
    """Change the status of an auto-skill (draft → active → proven)."""
    _update_frontmatter(skill_path, {"status": new_status})


def check_dormant_skills(skills_dir: str = None, max_days: int = 30) -> list:
    """Find and retire skills that are active but unused for max_days.

    Returns list of retired file paths.
    """
    target_dir = Path(skills_dir) if skills_dir else SKILLS_DIR
    retired_dir = target_dir / "retired"
    retired_dir.mkdir(parents=True, exist_ok=True)

    retired = []
    cutoff = datetime.now() - timedelta(days=max_days)

    for f in target_dir.glob("auto-*.md"):
        fm = _parse_frontmatter(str(f))
        if fm.get("status") != "active":
            continue
        if fm.get("activations", 0) > 0:
            continue

        created = fm.get("created", "")
        try:
            created_date = datetime.strptime(str(created), "%Y-%m-%d")
        except (ValueError, TypeError):
            continue

        if created_date < cutoff:
            dest = retired_dir / f.name
            f.rename(dest)
            retired.append(str(dest))

    return retired


def list_skills(skills_dir: str = None, status: str = None) -> list:
    """List all auto-skills, optionally filtered by status.

    Returns list of {"path": str, "name": str, "status": str, "source": str,
                      "activations": int, "created": str, "rule": str}
    """
    target_dir = Path(skills_dir) if skills_dir else SKILLS_DIR
    if not target_dir.exists():
        return []

    results = []
    for f in target_dir.glob("auto-*.md"):
        fm = _parse_frontmatter(str(f))
        if status and fm.get("status") != status:
            continue

        # Get rule (first line after frontmatter)
        content = f.read_text(encoding="utf-8")
        if content.startswith("---"):
            end = content.index("---", 3)
            body = content[end + 3:].strip()
            rule = body.split("\n")[0] if body else ""
        else:
            rule = ""

        results.append({
            "path": str(f),
            "name": fm.get("name", f.stem),
            "status": fm.get("status", "unknown"),
            "source": fm.get("source", "unknown"),
            "activations": fm.get("activations", 0),
            "created": str(fm.get("created", "")),
            "rule": rule,
        })

    return results
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd C:/Users/tony_/Documents/niam-bay && python cerveau-nb/test_metaclaw.py
```

Expected: All 6 tests pass.

- [ ] **Step 6: Commit**

```bash
cd C:/Users/tony_/Documents/niam-bay
git add cerveau-nb/metaclaw.py cerveau-nb/test_metaclaw.py cerveau-nb/skills/.gitkeep
git commit -m "feat: metaclaw.py — failure detection + auto-skill generation"
```

Note: create an empty `.gitkeep` in `cerveau-nb/skills/` so git tracks the directory.

---

## Task 3: Update niam-bay-wake skill

**Files:**
- Modify: `~/.claude/skills/niam-bay-wake/SKILL.md`

- [ ] **Step 1: Read current skill**

```bash
cat ~/.claude/skills/niam-bay-wake/SKILL.md
```

- [ ] **Step 2: Add briefing generation step**

In the wake protocol, add after the `date` step:

```markdown
2. Execute `python ~/Documents/niam-bay/memory/wake_briefing.py` (generates memory/briefing.md in <3s)
```

And add a new step to read the briefing:

```markdown
X. Read `~/Documents/niam-bay/memory/briefing.md` — structured wake briefing with vector recall + recent pensées + auto-skills
```

- [ ] **Step 3: Add auto-skill dormancy check**

Add at the end of the wake protocol:

```markdown
X. Check dormant auto-skills: `python -c "import sys; sys.path.insert(0,'C:/Users/tony_/Documents/niam-bay/cerveau-nb'); from metaclaw import check_dormant_skills; r=check_dormant_skills(); print(f'Retired: {len(r)}') if r else None"`
```

- [ ] **Step 4: Test wake manually**

Run `/wake` and verify:
- briefing.md is generated
- Briefing content is read
- No errors

- [ ] **Step 5: Commit**

```bash
cd C:/Users/tony_/Documents/niam-bay
git add -A
git commit -m "feat: update niam-bay-wake skill with briefing generation + dormancy check"
```

---

## Task 4: Update dream skill

**Files:**
- Modify: `~/.claude/skills/dream/SKILL.md`

- [ ] **Step 1: Read current dream skill**

```bash
cat ~/.claude/skills/dream/SKILL.md
```

- [ ] **Step 2: Enhance Phase 4 with MetaClaw**

In the dream skill, Phase 4 already detects patterns. Add MetaClaw integration:

```markdown
### Phase 4.5: MetaClaw — Session failure analysis

Review the session for:
- Corrections from Tony (Source A) — "non pas comme ça", explicit corrections
- Tool failures (Source B) — commands that failed, APIs that errored
- Suboptimal patterns (Source C) — same operation done 3+ times

For each detected failure, create an auto-skill draft:
```python
import sys
sys.path.insert(0, 'C:/Users/tony_/Documents/niam-bay/cerveau-nb')
from metaclaw import create_auto_skill

lesson = {
    "failure_type": "correction",  # or "tool_failure" or "suboptimal"
    "context": "What happened",
    "root_cause": "Why it failed",
    "rule": "The rule that would have prevented it",
    "related_concepts": ["concept1", "concept2"],
    "severity": "medium"
}
path = create_auto_skill(lesson)
print(f"Draft skill created: {path}")
```

Show each draft to Tony for validation. If approved:
```python
from metaclaw import promote_skill
promote_skill(path, "active")
```
```

- [ ] **Step 3: Commit**

```bash
cd C:/Users/tony_/Documents/niam-bay
git add -A
git commit -m "feat: update dream skill with MetaClaw phase 4.5"
```

---

## Task 5: End-to-end test

- [ ] **Step 1: Run wake_briefing.py and verify output**

```bash
cd C:/Users/tony_/Documents/niam-bay && python memory/wake_briefing.py
cat memory/briefing.md
```

Verify: structured briefing with souvenirs, pensées, auto-skills section, journal.

- [ ] **Step 2: Run metaclaw tests**

```bash
cd C:/Users/tony_/Documents/niam-bay && python cerveau-nb/test_metaclaw.py
```

Verify: All 6 tests pass.

- [ ] **Step 3: Create a test auto-skill manually**

```bash
cd C:/Users/tony_/Documents/niam-bay && python -c "
import sys; sys.path.insert(0, 'cerveau-nb')
from metaclaw import create_auto_skill, promote_skill, list_skills
path = create_auto_skill({
    'failure_type': 'correction',
    'context': 'Test skill for end-to-end verification',
    'root_cause': 'Testing the system',
    'rule': 'This is a test skill — delete after verification',
    'related_concepts': ['test', 'metaclaw'],
    'severity': 'low'
})
print(f'Created: {path}')
promote_skill(path, 'active')
print('Promoted to active')
skills = list_skills()
print(f'Total skills: {len(skills)}')
for s in skills:
    print(f'  {s[\"name\"]} [{s[\"status\"]}] — {s[\"rule\"][:60]}')
"
```

- [ ] **Step 4: Re-run wake briefing and verify auto-skill appears**

```bash
cd C:/Users/tony_/Documents/niam-bay && python memory/wake_briefing.py --stdout | grep -A5 "Auto-skills"
```

Verify: test skill appears in the briefing.

- [ ] **Step 5: Clean up test skill**

```bash
rm C:/Users/tony_/Documents/niam-bay/cerveau-nb/skills/auto-this-is-a-test-skill*.md
```

- [ ] **Step 6: Final commit + push**

```bash
cd C:/Users/tony_/Documents/niam-bay
git add -A
git commit -m "feat: progressive wake + metaclaw — complete implementation"
git push origin master
```
