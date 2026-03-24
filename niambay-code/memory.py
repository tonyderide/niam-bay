"""
NiamBay Code — Persistent memory (JSON file)
Stores: saved commands, notes, conversation history, project context.
"""
import json
import os
import time
from config import MEMORY_FILE, ensure_config_dir

MAX_HISTORY = 20


def _load():
    """Load memory from disk."""
    ensure_config_dir()
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return _default()


def _default():
    return {
        'notes': [],
        'commands': {},
        'history': [],
        'project_context': {},
    }


def _save(data):
    """Persist memory to disk."""
    ensure_config_dir()
    with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ── Notes ───────────────────────────────────────────────────

def remember(text):
    """Save a note to memory."""
    data = _load()
    data['notes'].append({
        'text': text,
        'time': time.strftime('%Y-%m-%d %H:%M:%S'),
    })
    _save(data)


def recall():
    """Return all notes."""
    return _load().get('notes', [])


# ── Saved commands ──────────────────────────────────────────

def save_command(name, command):
    """Save a reusable command."""
    data = _load()
    data['commands'][name] = command
    _save(data)


def get_command(name):
    """Get a saved command by name."""
    return _load().get('commands', {}).get(name)


def list_commands():
    """Return dict of all saved commands."""
    return _load().get('commands', {})


# ── Conversation history ────────────────────────────────────

def add_history(role, content):
    """Add to conversation history (kept to last MAX_HISTORY exchanges)."""
    data = _load()
    data['history'].append({
        'role': role,
        'content': content,
        'time': time.strftime('%Y-%m-%d %H:%M:%S'),
    })
    # Trim
    if len(data['history']) > MAX_HISTORY * 2:
        data['history'] = data['history'][-(MAX_HISTORY * 2):]
    _save(data)


def get_history():
    """Return conversation history."""
    return _load().get('history', [])


def get_history_for_llm():
    """Return history formatted for LLM messages."""
    hist = get_history()
    messages = []
    for h in hist:
        messages.append({
            'role': h['role'],
            'content': h['content'],
        })
    return messages


# ── Project context ─────────────────────────────────────────

def set_project_context(key, value):
    """Store project context (e.g. file list, project description)."""
    data = _load()
    data['project_context'][key] = value
    _save(data)


def get_project_context():
    """Return project context dict."""
    return _load().get('project_context', {})
