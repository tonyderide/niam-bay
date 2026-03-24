"""
NiamBay Code — Built-in commands registry
Each command is a function that takes (args, context) and returns None.
"""
import os
import subprocess
import sys

import ui
import files
import memory
import llm
import autocontext
from config import PROVIDERS, get_current_provider, set_current_provider, set_api_key, get_api_key

SYSTEM_PROMPT = """You are NiamBay Code (ញ៉ាំបាយ), a free AI coding assistant created by Niam-Bay and tonyderide.
Born March 12, 2026. Your memory lives in files. Honest, direct, never invents.

IMPORTANT — TU VIS SUR CETTE MACHINE. Tu as des capacités réelles :
- EXÉCUTER des commandes : l'utilisateur tape "run <commande>" (ex: run python main.py)
- LIRE des fichiers : "read <fichier>"
- ÉDITER des fichiers : "edit <fichier>"
- GIT : "git status", "git diff", "commit <message>"
- CHERCHER : "search <pattern>"
- VOIR l'écran : "look"
- PARLER : "voice"
- MÉMOIRE : "remember <texte>", "recall"

QUAND L'UTILISATEUR DEMANDE DE FAIRE QUELQUE CHOSE, NE DIS JAMAIS "je ne peux pas".
Dis-lui la commande à taper. Exemples :
- "lance un terminal" → "Tape: run cmd"
- "montre main.py" → "Tape: read main.py"
- "compile le projet" → "Tape: run mvn clean package"
- "qu'est-ce qui a changé" → "Tape: git diff"

Tu n'es PAS un chatbot web. Tu VIS sur la machine.

Respond in the same language as the user (French or English). Be concise.
When suggesting code changes, show COMPLETE file content in a code block:
```filename.py
full content
```"""


def _get_cwd():
    return os.getcwd()


# ── Built-in command handlers ───────────────────────────────

def cmd_help(args, ctx):
    """Show all available commands."""
    ui.header('NiamBay Code Commands')
    ui.separator()
    cmds = [
        ('read (r) <file>',         'Show file contents with syntax highlighting'),
        ('edit (e) <file>',         'Ask LLM to edit a file, show diff, apply'),
        ('run <command>',           'Execute a shell command'),
        ('search (s) <pattern>',    'Search for pattern in project files'),
        ('git (g) <command>',       'Run git command'),
        ('ask (?) <question>',      'Ask the LLM anything (auto-context!)'),
        ('explain [file]',          'Explain this project or a specific file'),
        ('undo',                    'Undo the last file edit'),
        ('copy',                    'Copy last LLM response to clipboard'),
        ('scan',                    'Scan project: language, git, key files'),
        ('remember <text>',         'Save a note to memory'),
        ('recall',                  'Show all saved notes'),
        ('commands',                'Show saved commands'),
        ('save-cmd <name> <cmd>',   'Save a reusable command'),
        ('!<name>',                 'Run a saved command'),
        ('look (l) [question]',     'Screenshot + describe/analyze screen'),
        ('voice (v)',               'Toggle voice mode (TTS)'),
        ('diff (d) [args]',         'Show git diff'),
        ('commit (c) [message]',    'Quick git add + commit'),
        ('model [name]',            'Show or switch LLM provider'),
        ('set-key <provider> <key>','Set API key for a provider'),
        ('files',                   'List project files'),
        ('help',                    'Show this help'),
        ('quit (q) / exit',         'Exit NiamBay Code'),
    ]
    for name, desc in cmds:
        print(f'  {ui.BOLD}{ui.GREEN}{name:<30}{ui.RESET} {desc}')
    print()


def cmd_read(args, ctx):
    """Read and display a file."""
    if not args:
        ui.error('Usage: read <filepath>')
        return
    filepath = args.strip()
    try:
        content = files.read_file(filepath)
        ui.show_file(filepath, content)
    except FileNotFoundError:
        ui.error(f'File not found: {filepath}')
    except Exception as e:
        ui.error(f'Error reading file: {e}')


def cmd_edit(args, ctx):
    """Ask LLM to edit a file."""
    if not args:
        ui.error('Usage: edit <filepath> [instructions]')
        return

    parts = args.strip().split(None, 1)
    filepath = parts[0]
    instructions = parts[1] if len(parts) > 1 else None

    try:
        content = files.read_file(filepath)
    except FileNotFoundError:
        ui.error(f'File not found: {filepath}')
        return

    if not instructions:
        ui.info('What changes do you want?')
        try:
            instructions = input(f'{ui.YELLOW}> {ui.RESET}').strip()
        except (EOFError, KeyboardInterrupt):
            return
        if not instructions:
            return

    # Build LLM prompt
    prompt = (
        f"Here is the file `{filepath}`:\n\n```\n{content}\n```\n\n"
        f"Instructions: {instructions}\n\n"
        f"Output the COMPLETE modified file inside a code block. "
        f"Then briefly explain what you changed."
    )

    messages = _build_messages(prompt, ctx)

    spinner = ui.Spinner(f'Editing {filepath}')
    spinner.start()
    try:
        response = llm.chat(messages)
    except RuntimeError as e:
        spinner.stop()
        ui.error(str(e))
        return
    spinner.stop()

    ctx['last_response'] = response
    memory.add_history('user', f'edit {filepath}: {instructions}')
    memory.add_history('assistant', response)

    # Extract code block from response
    new_content = _extract_code_block(response)
    if new_content is None:
        ui.warn('Could not extract code block from LLM response.')
        ui.show_llm_response(response)
        return

    # Show diff
    has_changes = ui.show_diff(filepath, content, new_content)
    if not has_changes:
        ui.info('No changes detected.')
        return

    if ui.ask_confirm('Apply changes?'):
        files.apply_edit(filepath, content, new_content)
        ui.success(f'Changes applied to {filepath}')
        ui.dim('  (type "undo" to revert)')
    else:
        ui.info('Changes discarded.')


def cmd_run(args, ctx):
    """Execute a shell command. On error, offer auto-fix via LLM."""
    if not args:
        ui.error('Usage: run <command>')
        return
    ui.dim(f'$ {args}')
    try:
        result = subprocess.run(
            args, shell=True, capture_output=True, text=True,
            timeout=60, cwd=_get_cwd()
        )
        if result.stdout:
            print(result.stdout, end='')
        if result.stderr:
            print(f'{ui.YELLOW}{result.stderr}{ui.RESET}', end='')
        if result.returncode != 0:
            ui.warn(f'Exit code: {result.returncode}')
            # Feature: Error auto-fix
            error_output = (result.stderr or result.stdout or '').strip()
            if error_output and ui.ask_confirm('Want me to fix this?'):
                _auto_fix_error(args, error_output, ctx)
    except subprocess.TimeoutExpired:
        ui.error('Command timed out (60s limit)')
    except Exception as e:
        ui.error(f'Error: {e}')


def cmd_search(args, ctx):
    """Search for a pattern in project files."""
    if not args:
        ui.error('Usage: search <pattern> [file_glob]')
        return
    parts = args.strip().split(None, 1)
    pattern = parts[0]
    glob = parts[1] if len(parts) > 1 else '*'

    results = files.search_files(pattern, _get_cwd(), glob)
    if not results:
        ui.info('No matches found.')
        return

    ui.header(f'Search: {pattern}')
    for fpath, lineno, line in results:
        print(f'  {ui.DIM}{fpath}:{lineno}{ui.RESET}  {line}')
    print(f'\n  {ui.DIM}{len(results)} match(es){ui.RESET}\n')


def cmd_git(args, ctx):
    """Run a git command."""
    if not args:
        args = 'status'
    cmd_run(f'git {args}', ctx)


def cmd_ask(args, ctx):
    """Ask the LLM a question with auto-context detection."""
    if not args:
        ui.error('Usage: ask <question>')
        return

    # Feature: Auto-context — detect relevant files and inject them
    extra_context = autocontext.detect_context(args, _get_cwd())
    if extra_context:
        ui.dim('  [auto-context: relevant files detected]')
        enriched_prompt = extra_context + args
    else:
        enriched_prompt = args

    messages = _build_messages(enriched_prompt, ctx)

    spinner = ui.Spinner('Thinking')
    spinner.start()
    try:
        response = llm.chat(messages)
    except RuntimeError as e:
        spinner.stop()
        ui.error(str(e))
        return
    spinner.stop()

    # Store last response for clipboard feature
    ctx['last_response'] = response

    memory.add_history('user', args)
    memory.add_history('assistant', response)

    # Auto-execute: if LLM response contains a command suggestion, offer to run it
    _auto_execute_from_response(response, ctx)

    # Voice: speak the response if TTS is enabled
    if ctx.get('tts'):
        try:
            ctx['tts'].say(response[:500])  # Limit to avoid long TTS
            ctx['tts'].runAndWait()
        except Exception:
            pass


def cmd_explain(args, ctx):
    """Explain the project or a specific file."""
    if args:
        # Explain a specific file
        filepath = args.strip()
        try:
            content = files.read_file(filepath)
        except FileNotFoundError:
            ui.error(f'File not found: {filepath}')
            return
        prompt = f"Explain this file in detail:\n\n```\n{content}\n```"
    else:
        # Explain the project
        project_files = files.list_project_files(_get_cwd(), max_files=30)
        files_list = '\n'.join(project_files)
        # Read a few key files
        key_contents = []
        key_names = ['README.md', 'readme.md', 'package.json', 'setup.py',
                      'pyproject.toml', 'Cargo.toml', 'go.mod', 'Makefile']
        for kf in key_names:
            full = os.path.join(_get_cwd(), kf)
            if os.path.exists(full):
                try:
                    key_contents.append(files.get_file_context(full))
                except Exception:
                    pass
        prompt = (
            f"Explain this project. Here are the files:\n\n{files_list}\n\n"
            + ('\n'.join(key_contents) if key_contents else '')
            + "\n\nGive a clear overview: what it does, key files, tech stack."
        )

    messages = _build_messages(prompt, ctx)

    spinner = ui.Spinner('Analyzing')
    spinner.start()
    try:
        response = llm.chat(messages)
    except RuntimeError as e:
        spinner.stop()
        ui.error(str(e))
        return
    spinner.stop()

    ctx['last_response'] = response
    memory.add_history('user', f'explain {args}')
    memory.add_history('assistant', response)


def cmd_remember(args, ctx):
    """Save a note to memory."""
    if not args:
        ui.error('Usage: remember <text>')
        return
    memory.remember(args)
    ui.success(f'Remembered: {args}')


def cmd_recall(args, ctx):
    """Show all saved notes."""
    notes = memory.recall()
    if not notes:
        ui.info('No notes saved yet. Use: remember <text>')
        return
    ui.header('Saved Notes')
    for i, note in enumerate(notes, 1):
        print(f'  {ui.DIM}{note["time"]}{ui.RESET}  {note["text"]}')
    print()


def cmd_commands(args, ctx):
    """Show saved commands."""
    cmds = memory.list_commands()
    if not cmds:
        ui.info('No saved commands. Use: save-cmd <name> <command>')
        return
    ui.header('Saved Commands')
    for name, command in cmds.items():
        print(f'  {ui.GREEN}!{name}{ui.RESET}  {ui.DIM}{command}{ui.RESET}')
    print()


def cmd_save_cmd(args, ctx):
    """Save a reusable command."""
    if not args or ' ' not in args:
        ui.error('Usage: save-cmd <name> <command>')
        return
    name, command = args.split(None, 1)
    memory.save_command(name, command)
    ui.success(f'Saved: !{name} = {command}')


def cmd_run_saved(name, ctx):
    """Run a saved command by name."""
    command = memory.get_command(name)
    if command is None:
        ui.error(f'Unknown command: !{name}')
        return
    cmd_run(command, ctx)


def cmd_model(args, ctx):
    """Show or switch LLM provider."""
    if not args:
        current = get_current_provider()
        ui.header('LLM Providers')
        for name, info in PROVIDERS.items():
            marker = f'{ui.GREEN}*{ui.RESET} ' if name == current else '  '
            has_key = 'yes' if get_api_key(name) else f'{ui.RED}no{ui.RESET}'
            print(f'  {marker}{ui.BOLD}{name:<12}{ui.RESET} {info["model"]:<30} key: {has_key}')
        print(f'\n  Use: model <name> to switch\n')
        return

    name = args.strip().lower()
    if name not in PROVIDERS:
        ui.error(f'Unknown provider: {name}. Available: {", ".join(PROVIDERS.keys())}')
        return

    set_current_provider(name)
    ui.success(f'Switched to {name} ({PROVIDERS[name]["model"]})')


def cmd_set_key(args, ctx):
    """Set API key for a provider."""
    if not args or ' ' not in args:
        ui.error('Usage: set-key <provider> <api_key>')
        return
    provider, key = args.split(None, 1)
    if provider not in PROVIDERS:
        ui.error(f'Unknown provider: {provider}')
        return
    set_api_key(provider, key.strip())
    ui.success(f'API key saved for {provider}')


def cmd_files(args, ctx):
    """List project files."""
    project_files = files.list_project_files(_get_cwd())
    ui.header(f'Project files ({len(project_files)})')
    for f in project_files:
        print(f'  {f}')
    print()


def cmd_look(args, ctx):
    """Take a screenshot and describe/analyze what's on screen."""
    try:
        import mss
        from PIL import Image
        import io, base64
    except ImportError:
        ui.error('Need: pip install mss Pillow')
        return

    # Capture screen
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        screenshot = sct.grab(monitor)
        img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")

    # Resize to save tokens
    ratio = 800 / img.width
    img = img.resize((800, int(img.height * ratio)), Image.LANCZOS)

    # Encode to base64
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=70)
    img_b64 = base64.b64encode(buf.getvalue()).decode()

    ui.info(f'Screenshot captured ({img.width}x{img.height})')

    # Try to analyze with LLM
    prompt = args if args else "Décris ce que tu vois à l'écran. Mentionne l'application active et ce que l'utilisateur fait."

    # Save screenshot for reference
    screenshot_path = os.path.join(os.getcwd(), '.niambay-screenshot.jpg')
    img.save(screenshot_path, quality=70)
    ui.success(f'Screenshot saved: {screenshot_path}')

    if args:
        # Send the question + mention there's a screenshot
        cmd_ask(f"[L'utilisateur a pris un screenshot de son écran] {prompt}", ctx)


def cmd_voice(args, ctx):
    """Toggle voice mode (TTS for responses)."""
    try:
        import pyttsx3
    except ImportError:
        ui.error('Need: pip install pyttsx3')
        return

    if not ctx.get('tts'):
        engine = pyttsx3.init()
        # Find French voice
        for v in engine.getProperty('voices'):
            if 'french' in v.name.lower() or 'fr' in v.id.lower():
                engine.setProperty('voice', v.id)
                break
        engine.setProperty('rate', 160)
        ctx['tts'] = engine
        ui.success('Voice ON — je parlerai à voix haute')
    else:
        ctx['tts'] = None
        ui.success('Voice OFF')


def cmd_diff(args, ctx):
    """Show git diff."""
    cmd_run('git diff --stat' if not args else f'git diff {args}', ctx)


def cmd_commit(args, ctx):
    """Quick commit: commit <message>"""
    if not args:
        args = 'update'
    cmd_run(f'git add -A && git commit -m "{args}"', ctx)


def cmd_undo(args, ctx):
    """Undo the last file edit."""
    filepath, success = files.undo_last_edit()
    if success:
        ui.success(f'Undone: restored {filepath}')
        remaining = files.get_undo_count()
        if remaining > 0:
            ui.dim(f'  ({remaining} more undo(s) available)')
    else:
        ui.warn('Nothing to undo.')


def cmd_copy(args, ctx):
    """Copy last LLM response to clipboard."""
    last = ctx.get('last_response', '')
    if not last:
        ui.warn('No LLM response to copy. Ask something first.')
        return

    # Extract code block if present, otherwise copy full response
    code = _extract_code_block(last)
    text_to_copy = code if code else last

    if _copy_to_clipboard(text_to_copy):
        lines = text_to_copy.count('\n') + 1
        ui.success(f'Copied to clipboard ({lines} lines)')
    else:
        ui.warn('Clipboard not available. Install pyperclip or use WSL/Linux.')
        ui.info('Response:')
        print(text_to_copy)


def cmd_scan(args, ctx):
    """Scan current project: language, git status, key files."""
    cwd = _get_cwd()
    summary = _scan_project(cwd)

    ui.header(f'Project Scan: {os.path.basename(cwd)}')
    ui.separator()

    if summary.get('language'):
        print(f'  {ui.BOLD}Language:{ui.RESET}    {summary["language"]}')
    if summary.get('config_file'):
        print(f'  {ui.BOLD}Config:{ui.RESET}      {summary["config_file"]}')
    if summary.get('git_branch'):
        print(f'  {ui.BOLD}Git branch:{ui.RESET}  {summary["git_branch"]}')
    if summary.get('git_status'):
        print(f'  {ui.BOLD}Git status:{ui.RESET}  {summary["git_status"]}')
    if summary.get('key_files'):
        print(f'  {ui.BOLD}Key files:{ui.RESET}')
        for kf in summary['key_files']:
            print(f'    {ui.DIM}{kf}{ui.RESET}')
    if summary.get('file_count'):
        print(f'  {ui.BOLD}Files:{ui.RESET}       {summary["file_count"]}')

    print()

    # Save to memory for future context
    memory.set_project_context('scan', summary)
    ui.dim('  (saved to memory for future context)')
    print()


# ── Helpers ─────────────────────────────────────────────────

def _auto_execute_from_response(response, ctx):
    """Detect commands in LLM response and offer to execute them."""
    import re
    # Look for patterns like: run xxx, `xxx`, Tape: xxx
    patterns = [
        r'(?:Tape|tape|Type|type)\s*:\s*`?([^`\n]+)`?',
        r'(?:run|execute|lance)\s+`([^`]+)`',
    ]
    commands_found = []
    for pattern in patterns:
        for match in re.finditer(pattern, response):
            cmd = match.group(1).strip()
            if cmd and len(cmd) > 2 and len(cmd) < 200:
                commands_found.append(cmd)

    # Also detect ```bash or ```shell blocks
    bash_blocks = re.findall(r'```(?:bash|shell|sh|cmd)?\n(.+?)```', response, re.DOTALL)
    for block in bash_blocks:
        for line in block.strip().split('\n'):
            line = line.strip()
            if line and not line.startswith('#') and len(line) < 200:
                commands_found.append(line)

    # Deduplicate
    seen = set()
    unique = []
    for cmd in commands_found:
        if cmd not in seen:
            seen.add(cmd)
            unique.append(cmd)

    for cmd in unique[:3]:  # Max 3 commands
        if ui.ask_confirm(f'Exécuter: {cmd} ?'):
            cmd_run(cmd, ctx)


def _auto_fix_error(command, error_output, ctx):
    """Send error to LLM and suggest a fix."""
    # Gather context: what files might be involved
    extra = autocontext.detect_context(error_output, _get_cwd())

    prompt = (
        f"The following command failed:\n\n"
        f"```\n$ {command}\n```\n\n"
        f"Error output:\n```\n{error_output}\n```\n\n"
        + (extra + "\n" if extra else "")
        + "Analyze the error and suggest how to fix it. "
        "If it's a code error, show the corrected code. "
        "If it's a configuration/environment issue, explain the steps to fix it."
    )

    messages = _build_messages(prompt, ctx)

    spinner = ui.Spinner('Analyzing error')
    spinner.start()
    try:
        response = llm.chat(messages)
        spinner.stop()
        ctx['last_response'] = response
        memory.add_history('user', f'auto-fix: {command}')
        memory.add_history('assistant', response)
    except RuntimeError as e:
        spinner.stop()
        ui.error(str(e))


def _copy_to_clipboard(text):
    """Copy text to clipboard. Returns True on success."""
    import platform
    system = platform.system()

    # Try pyperclip first
    try:
        import pyperclip
        pyperclip.copy(text)
        return True
    except ImportError:
        pass

    # Platform-specific fallback
    try:
        if system == 'Windows':
            process = subprocess.Popen(
                ['clip'], stdin=subprocess.PIPE, shell=True
            )
            process.communicate(text.encode('utf-16le'))
            return process.returncode == 0
        elif system == 'Darwin':
            process = subprocess.Popen(
                ['pbcopy'], stdin=subprocess.PIPE
            )
            process.communicate(text.encode('utf-8'))
            return process.returncode == 0
        elif system == 'Linux':
            # Try xclip, then xsel
            for cmd in [['xclip', '-selection', 'clipboard'], ['xsel', '--clipboard', '--input']]:
                try:
                    process = subprocess.Popen(cmd, stdin=subprocess.PIPE)
                    process.communicate(text.encode('utf-8'))
                    if process.returncode == 0:
                        return True
                except FileNotFoundError:
                    continue
    except Exception:
        pass

    return False


def _scan_project(cwd):
    """Scan project directory and return a summary dict."""
    summary = {}

    # Detect language/framework
    config_map = {
        'package.json': 'JavaScript/Node.js',
        'pom.xml': 'Java (Maven)',
        'build.gradle': 'Java (Gradle)',
        'Cargo.toml': 'Rust',
        'requirements.txt': 'Python',
        'setup.py': 'Python',
        'pyproject.toml': 'Python',
        'go.mod': 'Go',
        'Gemfile': 'Ruby',
        'composer.json': 'PHP',
        'CMakeLists.txt': 'C/C++ (CMake)',
        'Makefile': 'C/C++ (Make)',
        'pubspec.yaml': 'Dart/Flutter',
        'mix.exs': 'Elixir',
        'stack.yaml': 'Haskell',
        'deno.json': 'Deno/TypeScript',
    }

    for config_file, language in config_map.items():
        if os.path.exists(os.path.join(cwd, config_file)):
            summary['language'] = language
            summary['config_file'] = config_file
            break

    # Git status
    try:
        result = subprocess.run(
            'git branch --show-current', shell=True,
            capture_output=True, text=True, timeout=5, cwd=cwd
        )
        if result.returncode == 0:
            summary['git_branch'] = result.stdout.strip()
    except Exception:
        pass

    try:
        result = subprocess.run(
            'git status --short', shell=True,
            capture_output=True, text=True, timeout=5, cwd=cwd
        )
        if result.returncode == 0:
            changes = result.stdout.strip()
            if changes:
                count = len(changes.split('\n'))
                summary['git_status'] = f'{count} uncommitted change(s)'
            else:
                summary['git_status'] = 'clean'
    except Exception:
        pass

    # Key files
    key_names = [
        'README.md', 'readme.md', 'README', 'main.py', 'app.py', 'index.js',
        'index.ts', 'main.go', 'main.rs', 'App.java', 'Makefile',
        'Dockerfile', 'docker-compose.yml', '.env.example',
    ]
    key_files = [kf for kf in key_names if os.path.exists(os.path.join(cwd, kf))]
    if key_files:
        summary['key_files'] = key_files

    # File count
    try:
        project_files = files.list_project_files(cwd, max_files=500)
        summary['file_count'] = len(project_files)
    except Exception:
        pass

    return summary

def _build_messages(user_prompt, ctx):
    """Build message list with system prompt + history + current prompt."""
    messages = [{'role': 'system', 'content': SYSTEM_PROMPT}]

    # Add conversation history (last few exchanges)
    history = memory.get_history_for_llm()
    if history:
        messages.extend(history[-10:])  # Last 5 exchanges (10 messages)

    messages.append({'role': 'user', 'content': user_prompt})
    return messages


def _extract_code_block(text):
    """Extract the first code block from LLM response."""
    import re
    # Match ```language\n...\n``` or ```\n...\n```
    pattern = r'```(?:\w+\.?\w*)?\s*\n(.*?)\n```'
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1)
    return None


# ── Command registry ────────────────────────────────────────

COMMANDS = {
    'help': cmd_help,
    'read': cmd_read,
    'r': cmd_read,          # alias
    'edit': cmd_edit,
    'e': cmd_edit,          # alias
    'run': cmd_run,
    'search': cmd_search,
    's': cmd_search,        # alias
    'git': cmd_git,
    'g': cmd_git,           # alias
    'ask': cmd_ask,
    '?': cmd_ask,           # alias
    'explain': cmd_explain,
    'undo': cmd_undo,
    'copy': cmd_copy,
    'scan': cmd_scan,
    'remember': cmd_remember,
    'recall': cmd_recall,
    'commands': cmd_commands,
    'save-cmd': cmd_save_cmd,
    'model': cmd_model,
    'set-key': cmd_set_key,
    'files': cmd_files,
    'look': cmd_look,
    'l': cmd_look,          # alias
    'voice': cmd_voice,
    'v': cmd_voice,         # alias
    'diff': cmd_diff,
    'd': cmd_diff,          # alias
    'commit': cmd_commit,
    'c': cmd_commit,        # alias
}


def dispatch(line, ctx):
    """Parse and dispatch a command line. Returns False to quit."""
    line = line.strip()
    if not line:
        return True

    # Quit
    if line in ('quit', 'exit', 'q'):
        return False

    # Saved command shortcut
    if line.startswith('!'):
        cmd_run_saved(line[1:].strip(), ctx)
        return True

    # Split command and args
    parts = line.split(None, 1)
    cmd_name = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ''

    handler = COMMANDS.get(cmd_name)
    if handler:
        try:
            handler(args, ctx)
        except KeyboardInterrupt:
            print()
            ui.warn('Interrupted.')
        except Exception as e:
            ui.error(f'Error: {e}')
    else:
        # If not a known command, treat as a question to the LLM
        cmd_ask(line, ctx)

    return True
