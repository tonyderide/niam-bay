#!/usr/bin/env python3
"""
MetaClaw — Détection d'échecs et génération d'auto-skills.

Trois sources de détection:
A. Correction humaine (pattern matching contextuel)
B. Échec outil (exit code, HTTP errors)
C. Pattern sous-optimal (opérations répétées)

Usage:
    from metaclaw import detect_correction, detect_tool_failure, detect_suboptimal
    from metaclaw import create_auto_skill, promote_skill
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
    """
    has_negative = bool(NEGATIVE_WORDS.search(human_message))
    has_action_ref = bool(ACTION_REFS.search(human_message))

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
    r"panic|PANIC|traceback|Traceback)"
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


def create_auto_skill(lesson: dict, skills_dir: str = None, session_id: str = None) -> str:
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
        session_id: optional session identifier

    Returns:
        path to created file
    """
    target_dir = Path(skills_dir) if skills_dir else SKILLS_DIR
    target_dir.mkdir(parents=True, exist_ok=True)

    slug = _slugify(lesson["rule"][:50])
    filename = f"auto-{slug}.md"
    filepath = target_dir / filename

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
        "session_origin": session_id,
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
    """Change the status of an auto-skill (draft -> active -> proven)."""
    _update_frontmatter(skill_path, {"status": new_status})


def increment_activation(skill_path: str) -> None:
    """Increment the activation counter and update last_used."""
    fm = _parse_frontmatter(skill_path)
    _update_frontmatter(skill_path, {
        "activations": fm.get("activations", 0) + 1,
        "last_used": datetime.now().strftime("%Y-%m-%d"),
    })


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
    """List all auto-skills, optionally filtered by status."""
    target_dir = Path(skills_dir) if skills_dir else SKILLS_DIR
    if not target_dir.exists():
        return []

    results = []
    for f in target_dir.glob("auto-*.md"):
        fm = _parse_frontmatter(str(f))
        if status and fm.get("status") != status:
            continue

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
