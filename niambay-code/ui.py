"""
NiamBay Code — Terminal UI (colors, formatting, diff display)
ANSI codes — works on Windows 10+ and Linux.
"""
import os
import sys
import platform

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

# ── ANSI codes ──────────────────────────────────────────────
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


def color(text, *codes):
    return ''.join(codes) + str(text) + RESET


def red(t):      return color(t, RED)
def green(t):    return color(t, GREEN)
def yellow(t):   return color(t, YELLOW)
def blue(t):     return color(t, BLUE)
def cyan(t):     return color(t, CYAN)
def magenta(t):  return color(t, MAGENTA)
def bold(t):     return color(t, BOLD)
def dim(t):      return color(t, DIM)
def bold_cyan(t): return color(t, BOLD, CYAN)


# ── High-level UI ───────────────────────────────────────────

def banner():
    """Print startup banner."""
    lines = [
        '',
        f'  {BOLD}{CYAN}{"=" * 39}{RESET}',
        f'  {BOLD}{CYAN}\u2551  NIAM-BAY CODE  \u1789\u17D2\u1789\u17B6\u17C6\u178F\u17B6\u1799       \u2551{RESET}',
        f'  {BOLD}{CYAN}\u2551  Free AI Coding Assistant       \u2551{RESET}',
        f'  {BOLD}{CYAN}{"=" * 39}{RESET}',
        '',
    ]
    print('\n'.join(lines))


def prompt():
    """Return the REPL prompt string."""
    return f'{BOLD}{GREEN}nb> {RESET}'


def info(msg):
    print(f'{CYAN}{msg}{RESET}')


def success(msg):
    print(f'{GREEN}{msg}{RESET}')


def warn(msg):
    print(f'{YELLOW}{msg}{RESET}')


def error(msg):
    print(f'{RED}{msg}{RESET}')


def header(msg):
    print(f'\n{BOLD}{msg}{RESET}')


def separator(char='\u2500', width=50):
    print(f'{DIM}{char * width}{RESET}')


def show_file(filepath, content):
    """Display file contents with line numbers."""
    header(f'  {filepath}')
    separator()
    lines = content.split('\n')
    width = len(str(len(lines)))
    for i, line in enumerate(lines, 1):
        num = str(i).rjust(width)
        print(f'  {DIM}{num}{RESET}  {line}')
    separator()
    print()


def show_diff(filepath, old_content, new_content):
    """Display a colored unified diff."""
    import difflib
    old_lines = old_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)
    diff = difflib.unified_diff(old_lines, new_lines, fromfile=filepath, tofile=filepath, lineterm='')

    header(f'  {filepath}')
    separator()

    has_diff = False
    for line in diff:
        has_diff = True
        line = line.rstrip('\n')
        if line.startswith('+++') or line.startswith('---'):
            print(f'  {BOLD}{line}{RESET}')
        elif line.startswith('@@'):
            print(f'  {MAGENTA}{line}{RESET}')
        elif line.startswith('+'):
            print(f'  {GREEN}{line}{RESET}')
        elif line.startswith('-'):
            print(f'  {RED}{line}{RESET}')
        else:
            print(f'  {line}')

    if not has_diff:
        info('  (no changes)')

    separator()
    print()
    return has_diff


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
