"""
NiamBay Code — Auto-context detection
When the user asks about code, automatically detect which files are relevant
and inject their content into the prompt before sending to the LLM.
"""
import os
import re
import subprocess


def detect_context(user_input, cwd):
    """
    Analyze user input and return extra context to prepend to the LLM prompt.
    Returns a string with file contents and metadata, or empty string.
    """
    context_parts = []

    # 1. Detect explicit filenames mentioned
    files_found = _detect_filenames(user_input, cwd)
    for fpath in files_found:
        content = _safe_read(fpath)
        if content is not None:
            rel = os.path.relpath(fpath, cwd)
            context_parts.append(f"[Auto-loaded file: {rel}]\n```\n{content}\n```")

    # 2. Detect function/class names → grep for them
    if not files_found:
        symbols = _detect_symbols(user_input)
        for symbol in symbols[:3]:  # Max 3 symbols
            found = _grep_symbol(symbol, cwd)
            for fpath, line_num, line_text in found[:2]:  # Max 2 results per symbol
                content = _safe_read(os.path.join(cwd, fpath))
                if content is not None:
                    context_parts.append(
                        f"[Auto-found '{symbol}' in {fpath}:{line_num}]\n```\n{content}\n```"
                    )
                    break  # One file per symbol is enough

    # 3. "fix the bug" / "fix" / "what changed" → show recent git diff
    if _wants_fix_or_diff(user_input):
        diff = _get_git_diff(cwd)
        if diff:
            context_parts.append(f"[Recent git changes]\n```diff\n{diff}\n```")
        # Also load recently modified files
        modified = _get_modified_files(cwd)
        for fpath in modified[:3]:
            full = os.path.join(cwd, fpath)
            content = _safe_read(full)
            if content is not None:
                context_parts.append(f"[Modified file: {fpath}]\n```\n{content}\n```")

    if context_parts:
        header = "[NiamBay auto-context — relevant files detected automatically]\n\n"
        return header + "\n\n".join(context_parts) + "\n\n---\nUser question: "
    return ""


def _detect_filenames(text, cwd):
    """Find filenames mentioned in the text that actually exist."""
    found = []
    # Match things that look like filenames: word.ext, path/to/file.ext
    patterns = re.findall(r'(?:[\w./\\-]+\.[\w]+)', text)
    for p in patterns:
        # Try as-is
        full = os.path.join(cwd, p)
        if os.path.isfile(full):
            found.append(full)
        # Try absolute
        elif os.path.isfile(p):
            found.append(os.path.abspath(p))
    return found


def _detect_symbols(text):
    """Detect potential function/class names in the text."""
    # Look for camelCase, snake_case, or PascalCase identifiers
    # Filter out common English words and short words
    words = re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]{2,})\b', text)
    stop_words = {
        'the', 'and', 'for', 'that', 'this', 'with', 'from', 'have', 'has',
        'are', 'was', 'were', 'been', 'being', 'will', 'would', 'could',
        'should', 'can', 'not', 'but', 'what', 'how', 'why', 'where', 'when',
        'which', 'who', 'about', 'into', 'does', 'did', 'fix', 'bug', 'error',
        'function', 'class', 'method', 'file', 'code', 'line', 'variable',
        'add', 'remove', 'change', 'update', 'explain', 'show', 'find',
        'make', 'use', 'call', 'return', 'import', 'print', 'read', 'write',
    }
    symbols = []
    for w in words:
        if w.lower() not in stop_words and (
            '_' in w or  # snake_case
            any(c.isupper() for c in w[1:]) or  # camelCase/PascalCase
            len(w) > 5  # longer identifiers likely to be specific
        ):
            symbols.append(w)
    return list(dict.fromkeys(symbols))  # dedupe, preserve order


def _grep_symbol(symbol, cwd):
    """Search for a symbol in project files. Returns list of (relpath, line, text)."""
    results = []
    skip_dirs = {'.git', 'node_modules', '__pycache__', 'venv', '.venv', 'env', 'dist', 'build'}
    try:
        for root, dirs, filenames in os.walk(cwd):
            dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith('.')]
            for fname in filenames:
                if fname.startswith('.') or not _is_text_file(fname):
                    continue
                fpath = os.path.join(root, fname)
                try:
                    with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                        for i, line in enumerate(f, 1):
                            if symbol in line:
                                rel = os.path.relpath(fpath, cwd)
                                results.append((rel, i, line.rstrip()))
                                if len(results) >= 5:
                                    return results
                except (IOError, OSError):
                    continue
    except Exception:
        pass
    return results


def _is_text_file(filename):
    """Check if a filename looks like a text/code file."""
    text_exts = {
        '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.c', '.cpp', '.h',
        '.go', '.rs', '.rb', '.php', '.html', '.css', '.json', '.yaml',
        '.yml', '.toml', '.xml', '.md', '.txt', '.sh', '.bash', '.zsh',
        '.sql', '.r', '.swift', '.kt', '.scala', '.lua', '.pl', '.pm',
        '.cs', '.vb', '.fs', '.ex', '.exs', '.clj', '.hs', '.ml',
        '.cfg', '.ini', '.conf', '.env', '.dockerfile', '.makefile',
    }
    _, ext = os.path.splitext(filename.lower())
    return ext in text_exts or filename.lower() in {'makefile', 'dockerfile', 'rakefile'}


def _wants_fix_or_diff(text):
    """Detect if user wants to fix something or see recent changes."""
    text_lower = text.lower()
    triggers = [
        'fix the bug', 'fix this', 'fix it', 'what broke', 'what changed',
        'what went wrong', "what's wrong", 'debug', 'recent changes',
        'last change', 'repare', 'corriger', 'corrige', 'qu\'est-ce qui',
    ]
    return any(t in text_lower for t in triggers)


def _get_git_diff(cwd):
    """Get recent git diff (staged + unstaged)."""
    try:
        result = subprocess.run(
            'git diff HEAD~1 --stat && echo "---" && git diff HEAD~1',
            shell=True, capture_output=True, text=True, timeout=10, cwd=cwd
        )
        if result.returncode == 0 and result.stdout.strip():
            # Limit to 200 lines
            lines = result.stdout.split('\n')
            if len(lines) > 200:
                return '\n'.join(lines[:200]) + '\n... (truncated)'
            return result.stdout
    except Exception:
        pass
    # Fallback: just unstaged changes
    try:
        result = subprocess.run(
            'git diff', shell=True, capture_output=True, text=True, timeout=10, cwd=cwd
        )
        if result.returncode == 0 and result.stdout.strip():
            lines = result.stdout.split('\n')
            if len(lines) > 200:
                return '\n'.join(lines[:200]) + '\n... (truncated)'
            return result.stdout
    except Exception:
        pass
    return ""


def _get_modified_files(cwd):
    """Get list of recently modified files from git."""
    try:
        result = subprocess.run(
            'git diff --name-only HEAD~1',
            shell=True, capture_output=True, text=True, timeout=10, cwd=cwd
        )
        if result.returncode == 0:
            return [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
    except Exception:
        pass
    # Fallback: unstaged
    try:
        result = subprocess.run(
            'git diff --name-only',
            shell=True, capture_output=True, text=True, timeout=10, cwd=cwd
        )
        if result.returncode == 0:
            return [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
    except Exception:
        pass
    return []


def _safe_read(filepath):
    """Read a file safely, return None on error. Limit to 500 lines."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
        if len(lines) > 500:
            return ''.join(lines[:500]) + '\n... (file truncated at 500 lines)'
        return ''.join(lines)
    except Exception:
        return None
