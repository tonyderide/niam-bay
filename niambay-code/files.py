"""
NiamBay Code — File operations (read, edit, search, diff, undo)
"""
import os
import fnmatch
import re

# ── Undo stack ─────────────────────────────────────────────
# Stores (filepath, old_content) for the last MAX_UNDO edits
MAX_UNDO = 20
_undo_stack = []


def read_file(filepath):
    """Read a file and return its content. Raises FileNotFoundError."""
    filepath = os.path.abspath(filepath)
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()


def write_file(filepath, content):
    """Write content to a file."""
    filepath = os.path.abspath(filepath)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)


def apply_edit(filepath, old_content, new_content):
    """Apply an edit: save old version for undo, write new content. Returns True on success."""
    filepath = os.path.abspath(filepath)
    # Save to undo stack before overwriting
    _undo_stack.append((filepath, old_content))
    if len(_undo_stack) > MAX_UNDO:
        _undo_stack.pop(0)
    write_file(filepath, new_content)
    return True


def undo_last_edit():
    """Undo the last edit. Returns (filepath, True) on success, (None, False) if nothing to undo."""
    if not _undo_stack:
        return None, False
    filepath, old_content = _undo_stack.pop()
    write_file(filepath, old_content)
    return filepath, True


def get_undo_count():
    """Return the number of edits that can be undone."""
    return len(_undo_stack)


def search_files(pattern, directory='.', file_glob='*', max_results=50):
    """
    Search for a regex pattern in files under directory.
    Returns list of (filepath, line_number, line_text) tuples.
    """
    directory = os.path.abspath(directory)
    results = []
    try:
        regex = re.compile(pattern, re.IGNORECASE)
    except re.error as e:
        return [(f'Invalid regex: {e}', 0, '')]

    for root, dirs, filenames in os.walk(directory):
        # Skip hidden dirs and common noise
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in (
            'node_modules', '__pycache__', '.git', 'venv', '.venv', 'env',
        )]
        for fname in filenames:
            if not fnmatch.fnmatch(fname, file_glob):
                continue
            fpath = os.path.join(root, fname)
            try:
                with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                    for i, line in enumerate(f, 1):
                        if regex.search(line):
                            rel = os.path.relpath(fpath, directory)
                            results.append((rel, i, line.rstrip()))
                            if len(results) >= max_results:
                                return results
            except (IOError, OSError):
                continue

    return results


def list_project_files(directory='.', max_files=200):
    """List project files (skip hidden, node_modules, etc.)."""
    directory = os.path.abspath(directory)
    files = []
    for root, dirs, filenames in os.walk(directory):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in (
            'node_modules', '__pycache__', '.git', 'venv', '.venv', 'env',
            'dist', 'build', '.next',
        )]
        for fname in filenames:
            if fname.startswith('.'):
                continue
            fpath = os.path.join(root, fname)
            rel = os.path.relpath(fpath, directory)
            files.append(rel)
            if len(files) >= max_files:
                return files
    return files


def get_file_context(filepath):
    """Read a file and return it formatted for LLM context."""
    try:
        content = read_file(filepath)
        return f"--- {filepath} ---\n{content}\n--- end {filepath} ---"
    except FileNotFoundError:
        return f"--- {filepath} --- FILE NOT FOUND ---"
    except Exception as e:
        return f"--- {filepath} --- ERROR: {e} ---"
