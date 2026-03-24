"""
NiamBay Code -- Terminal UI (colors, formatting, diff display, spinner, syntax highlighting)
ANSI codes -- works on Windows 10+ and Linux. Pure stdlib.
"""
import os
import sys
import platform
import threading
import time
import re

# Enable ANSI and UTF-8 on Windows 10+
if platform.system() == 'Windows':
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        pass
    # Force UTF-8 output
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# -- ANSI codes --------------------------------------------------------
RESET   = '\033[0m'
BOLD    = '\033[1m'
DIM     = '\033[2m'
ITALIC  = '\033[3m'
UNDER   = '\033[4m'

RED     = '\033[31m'
GREEN   = '\033[32m'
YELLOW  = '\033[33m'
BLUE    = '\033[34m'
MAGENTA = '\033[35m'
CYAN    = '\033[36m'
WHITE   = '\033[37m'

BG_RED    = '\033[41m'
BG_GREEN  = '\033[42m'
BG_YELLOW = '\033[43m'
BG_BLUE   = '\033[44m'

# Bright variants
BR_BLACK  = '\033[90m'  # bright black = gray


def color(text, *codes):
    return ''.join(codes) + str(text) + RESET


def red(t):      return color(t, RED)
def green(t):    return color(t, GREEN)
def yellow(t):   return color(t, YELLOW)
def blue(t):     return color(t, BLUE)
def cyan(t):     return color(t, CYAN)
def magenta(t):  return color(t, MAGENTA)
def bold(t):     return color(t, BOLD)
def dim(t):      print(f'{DIM}{t}{RESET}')
def dim_str(t):  return color(t, DIM)
def bold_cyan(t): return color(t, BOLD, CYAN)


# -- Spinner -----------------------------------------------------------

class Spinner:
    """Animated braille spinner that runs in a background thread."""
    _FRAMES = list('\u280b\u2819\u2839\u2838\u283c\u2834\u2826\u2827\u2807\u280f')

    def __init__(self, message='Thinking'):
        self._message = message
        self._stop_event = threading.Event()
        self._thread = None

    def start(self):
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._spin, daemon=True)
        self._thread.start()

    def _spin(self):
        i = 0
        while not self._stop_event.is_set():
            frame = self._FRAMES[i % len(self._FRAMES)]
            sys.stdout.write(f'\r  {CYAN}{frame} {self._message}...{RESET}  ')
            sys.stdout.flush()
            i += 1
            self._stop_event.wait(0.08)
        # Clear the spinner line
        sys.stdout.write('\r' + ' ' * 60 + '\r')
        sys.stdout.flush()

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=1)


# -- Syntax highlighting (basic, stdlib only) --------------------------

# Keywords per file extension family
_PY_KEYWORDS = {
    'def', 'class', 'import', 'from', 'return', 'if', 'elif', 'else',
    'for', 'while', 'try', 'except', 'finally', 'with', 'as', 'yield',
    'raise', 'pass', 'break', 'continue', 'lambda', 'and', 'or', 'not',
    'in', 'is', 'None', 'True', 'False', 'async', 'await', 'global',
    'nonlocal', 'del', 'assert',
}

_JS_KEYWORDS = {
    'function', 'const', 'let', 'var', 'return', 'if', 'else', 'for',
    'while', 'class', 'import', 'export', 'from', 'new', 'this', 'async',
    'await', 'try', 'catch', 'finally', 'throw', 'switch', 'case', 'break',
    'continue', 'default', 'typeof', 'instanceof', 'null', 'undefined',
    'true', 'false', 'yield', 'of', 'in',
}

_GENERIC_KEYWORDS = _PY_KEYWORDS | _JS_KEYWORDS


def _get_keywords_for_file(filepath):
    """Pick keyword set based on file extension."""
    ext = os.path.splitext(filepath)[1].lower()
    if ext in ('.py', '.pyw'):
        return _PY_KEYWORDS
    if ext in ('.js', '.ts', '.jsx', '.tsx', '.mjs', '.cjs'):
        return _JS_KEYWORDS
    return _GENERIC_KEYWORDS


def _highlight_line(line, keywords):
    """Apply basic syntax highlighting to a single line of code."""
    # If the (stripped) line is a comment, color the whole thing dim
    stripped = line.lstrip()
    if stripped.startswith('#') or stripped.startswith('//'):
        return f'{DIM}{line}{RESET}'

    result = []
    i = 0
    length = len(line)

    while i < length:
        ch = line[i]

        # Strings (single and double quotes)
        if ch in ('"', "'"):
            quote = ch
            # Check for triple quotes
            if line[i:i+3] in ('"""', "'''"):
                end = line.find(line[i:i+3], i + 3)
                if end == -1:
                    result.append(f'{GREEN}{line[i:]}{RESET}')
                    i = length
                else:
                    result.append(f'{GREEN}{line[i:end+3]}{RESET}')
                    i = end + 3
            else:
                j = i + 1
                while j < length:
                    if line[j] == '\\':
                        j += 2
                        continue
                    if line[j] == quote:
                        j += 1
                        break
                    j += 1
                result.append(f'{GREEN}{line[i:j]}{RESET}')
                i = j
            continue

        # Inline comment
        if ch == '#' or (ch == '/' and i + 1 < length and line[i+1] == '/'):
            result.append(f'{DIM}{line[i:]}{RESET}')
            i = length
            continue

        # Numbers (standalone digits)
        if ch.isdigit() and (i == 0 or not line[i-1].isalnum()):
            j = i
            while j < length and (line[j].isdigit() or line[j] in '.xXabcdefABCDEF_'):
                j += 1
            result.append(f'{YELLOW}{line[i:j]}{RESET}')
            i = j
            continue

        # Words (identifiers / keywords)
        if ch.isalpha() or ch == '_':
            j = i
            while j < length and (line[j].isalnum() or line[j] == '_'):
                j += 1
            word = line[i:j]
            if word in keywords:
                result.append(f'{CYAN}{word}{RESET}')
            else:
                result.append(word)
            i = j
            continue

        result.append(ch)
        i += 1

    return ''.join(result)


# -- High-level UI ----------------------------------------------------

def banner():
    """Print startup banner with box-drawing characters."""
    title = '\u25c6 NIAM-BAY CODE  \u1789\u17d2\u1789\u17b6\u17c6\u178f\u17b6\u1799'
    subtitle = 'Free AI Coding Assistant'
    inner_w = 36
    lines = [
        '',
        f'  {BOLD}{CYAN}\u2554{"="*inner_w}\u2557{RESET}',
        f'  {BOLD}{CYAN}\u2551{RESET}   {BOLD}{WHITE}{title}{RESET}{" " * (inner_w - len(title) - 3)}{BOLD}{CYAN}\u2551{RESET}',
        f'  {BOLD}{CYAN}\u2551{RESET}   {subtitle}{" " * (inner_w - len(subtitle) - 3)}{BOLD}{CYAN}\u2551{RESET}',
        f'  {BOLD}{CYAN}\u255a{"="*inner_w}\u255d{RESET}',
        '',
    ]
    print('\n'.join(lines))


def prompt():
    """Return the REPL prompt string."""
    return f'{BOLD}{GREEN}\u25b6 nb> {RESET}'


def status_bar(provider='?', memory_count=0, history_count=0, cwd=''):
    """Print a status bar at the bottom of the screen."""
    short_cwd = cwd
    # Shorten the cwd if it's too long
    if len(short_cwd) > 30:
        short_cwd = '...' + short_cwd[-27:]
    parts = [
        f'{BOLD}{provider}{RESET}',
        f'mem:{memory_count}',
        f'hist:{history_count}',
        short_cwd,
    ]
    bar = f'{DIM}[{"] [".join(parts)}]{RESET}'
    print(f'  {bar}')


def info(msg):
    print(f'{CYAN}{msg}{RESET}')


def success(msg):
    print(f'{GREEN}\u2714 {msg}{RESET}')


def warn(msg):
    print(f'{YELLOW}\u26a0 {msg}{RESET}')


def error(msg):
    print(f'{RED}\u2716 {msg}{RESET}')


def header(msg):
    print(f'\n{BOLD}{msg}{RESET}')


def separator(char='\u2500', width=50):
    print(f'{DIM}{char * width}{RESET}')


def show_file(filepath, content):
    """Display file contents with line numbers and syntax highlighting."""
    keywords = _get_keywords_for_file(filepath)
    header(f'  {filepath}')
    separator()
    lines = content.split('\n')
    width = len(str(len(lines)))
    for i, line in enumerate(lines, 1):
        num = str(i).rjust(width)
        highlighted = _highlight_line(line, keywords)
        print(f'  {DIM}{num}{RESET}  {highlighted}')
    separator()
    print()


def show_diff(filepath, old_content, new_content):
    """Display a colored diff with box-drawing frame."""
    import difflib
    old_lines = old_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)
    diff = list(difflib.unified_diff(old_lines, new_lines, fromfile=filepath, tofile=filepath, lineterm=''))

    if not diff:
        info('  (no changes)')
        return False

    # Pretty header
    bar_w = 50
    title = f' {filepath} '
    pad = bar_w - len(title) - 1
    if pad < 1:
        pad = 1
    print(f'\n  {DIM}\u250c\u2500{BOLD}{WHITE}{title}{RESET}{DIM}{"\u2500" * pad}{RESET}')

    for line in diff:
        line = line.rstrip('\n')
        if line.startswith('+++') or line.startswith('---'):
            continue  # Skip redundant header lines
        if line.startswith('@@'):
            print(f'  {DIM}\u2502{RESET} {MAGENTA}{line}{RESET}')
        elif line.startswith('+'):
            print(f'  {DIM}\u2502{RESET} {GREEN}{line}{RESET}')
        elif line.startswith('-'):
            print(f'  {DIM}\u2502{RESET} {RED}{line}{RESET}')
        else:
            print(f'  {DIM}\u2502{RESET} {line}')

    print(f'  {DIM}\u2514{"\u2500" * bar_w}{RESET}\n')
    return True


def ask_confirm(question='Apply?', options='y/n'):
    """Ask yes/no confirmation. Returns True for yes."""
    try:
        answer = input(f'{YELLOW}{question} [{options}] {RESET}').strip().lower()
        return answer in ('y', 'yes')
    except (EOFError, KeyboardInterrupt):
        print()
        return False


def show_llm_response(text):
    """Print LLM response in cyan."""
    print()
    for line in text.split('\n'):
        print(f'  {CYAN}{line}{RESET}')
    print()


def show_table(headers, rows):
    """Simple table display."""
    if not rows:
        return
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(widths):
                widths[i] = max(widths[i], len(str(cell)))

    hline = '  ' + '  '.join(h.ljust(widths[i]) for i, h in enumerate(headers))
    print(f'{BOLD}{hline}{RESET}')
    print(f'  {DIM}{"  ".join("\u2500" * w for w in widths)}{RESET}')
    for row in rows:
        line = '  ' + '  '.join(str(cell).ljust(widths[i]) for i, cell in enumerate(row))
        print(line)
    print()


# -- Multiline input ---------------------------------------------------

def read_multiline_input(first_line):
    """
    Detect and handle multiline input.
    Triggers:
      - Line ends with backslash: continuation mode (strip backslash, prompt for more)
      - Line starts or contains ```: collect until closing ```
    Returns the complete input string.
    """
    # Triple backtick mode
    if '```' in first_line:
        lines = [first_line]
        # If the line both opens and closes triple backticks, just return it
        count = first_line.count('```')
        if count >= 2:
            return first_line
        # Collect until closing ```
        try:
            while True:
                more = input(f'{DIM}...{RESET} ')
                lines.append(more)
                if '```' in more:
                    break
        except (EOFError, KeyboardInterrupt):
            pass
        return '\n'.join(lines)

    # Backslash continuation mode
    if first_line.endswith('\\'):
        lines = [first_line[:-1]]  # strip trailing backslash
        try:
            while True:
                more = input(f'{DIM}...{RESET} ')
                if more.endswith('\\'):
                    lines.append(more[:-1])
                else:
                    lines.append(more)
                    break
        except (EOFError, KeyboardInterrupt):
            pass
        return '\n'.join(lines)

    # Single line, no special handling
    return first_line
