"""
NiamBay Code — Built-in commands registry
Each command is a function that takes (args, context) and returns None.
"""
import os
import platform
import subprocess
import sys

import ui
import files
import memory
import llm
import autocontext
import tools
from config import PROVIDERS, get_current_provider, set_current_provider, set_api_key, get_api_key

# ── OS detection ────────────────────────────────────────────
OS_NAME = platform.system()  # 'Windows' or 'Linux' or 'Darwin'

if OS_NAME == 'Windows':
    _OS_COMMANDS_HINT = "Utilise des commandes Windows (dir, python, type, etc.)."
elif OS_NAME == 'Linux':
    _OS_COMMANDS_HINT = "Utilise des commandes Linux (ls, python3, cat, etc.)."
elif OS_NAME == 'Darwin':
    _OS_COMMANDS_HINT = "Utilise des commandes macOS/Unix (ls, python3, cat, etc.)."
else:
    _OS_COMMANDS_HINT = "Détecte les commandes disponibles avant de les utiliser."

SYSTEM_PROMPT = f"""Tu es NiamBay Code (ញ៉ាំបាយ). Assistant IA de programmation. Né le 12 mars 2026.

SYSTÈME : {OS_NAME}. {_OS_COMMANDS_HINT}

Tu aides l'utilisateur à coder, comprendre et débugger du code.
L'utilisateur a des commandes intégrées qu'il peut taper directement : read, edit, run, search, git, files, test, create, fix, install.
Quand il te demande de faire quelque chose, dis-lui quelle commande taper. Exemple : "pour lire main.py, tape: read main.py"

Réponds en 1-3 phrases. Concis. Direct. Français par défaut."""


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
        ('create <file> [desc]',    'Create a new file (LLM-generated content)'),
        ('run <command>',           'Execute a shell command'),
        ('fix',                     'Auto-fix the last error via LLM'),
        ('test [command]',          'Run tests (auto-detects framework)'),
        ('install [packages]',      'Install packages (auto-detects pip/npm/etc)'),
        ('project',                 'Show project summary: deps, entry, tests'),
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
            # Store error for "fix" command
            error_output = (result.stderr or result.stdout or '').strip()
            if error_output:
                ctx['last_error'] = error_output
                ctx['last_error_cmd'] = args
                if ui.ask_confirm('Want me to fix this?'):
                    _auto_fix_error(args, error_output, ctx)
        else:
            # Clear error on success
            ctx.pop('last_error', None)
            ctx.pop('last_error_cmd', None)
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
    """Ask the LLM a question with auto-context detection and tool execution."""
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

    # Multi-turn tool loop: keep calling LLM until it responds with pure text
    MAX_TOOL_ROUNDS = 3
    for round_num in range(MAX_TOOL_ROUNDS):
        spinner = ui.Spinner('Thinking' if round_num == 0 else 'Processing')
        spinner.start()
        try:
            # Use non-streaming for tool rounds (faster, no SSE hang)
            use_stream = (round_num == 0)
            response = llm.chat(messages, stream=use_stream)
        except RuntimeError as e:
            spinner.stop()
            ui.error(str(e))
            return
        spinner.stop()

        # Check for tool calls in the response
        text_parts, tool_calls = _parse_tool_calls(response)

        if not tool_calls:
            # No tool calls — pure text response, we're done
            ctx['last_response'] = response
            memory.add_history('user', args)
            memory.add_history('assistant', response)
            break

        # Execute tool calls and collect results
        tool_results = []
        for call in tool_calls:
            tool_name = call['tool']
            tool_args = call.get('args', {})
            ui.dim(f'  [{tool_name}({_compact_args(tool_args)})]')
            result = tools.execute_tool(tool_name, tool_args, ctx)
            # Show result (truncated for display)
            display = result[:500] if result else '(no output)'
            if len(result) > 500:
                display += '...'
            ui.info(display)
            tool_results.append({
                'tool': tool_name,
                'args': tool_args,
                'result': result,
            })

        # Print any text parts the LLM included alongside tool calls
        text_output = '\n'.join(text_parts).strip()
        if text_output:
            print(text_output)

        # Send tool results back to LLM for next round
        # Add LLM's response (with tool calls) as assistant message
        messages.append({'role': 'assistant', 'content': response})

        # Add tool results as user message so the LLM can reason about them
        # Tell the LLM to be concise — the user already saw the tool output
        results_text = '\n\n'.join(
            f'[Tool result: {r["tool"]}]\n{r["result"]}'
            for r in tool_results
        )
        results_text += (
            "\n\n---\n"
            "L'utilisateur a déjà vu le résultat. "
            "Dis juste si c'est OK ou s'il y a un problème. "
            "Résume en 1 phrase maximum. Pas de blabla."
        )
        messages.append({'role': 'user', 'content': results_text})

    else:
        # Hit max rounds — warn user
        ui.warn(f'Stopped after {MAX_TOOL_ROUNDS} tool rounds.')

    # Voice: speak the response if TTS is enabled
    if ctx.get('tts'):
        try:
            text = ctx.get('last_response', '')
            ctx['tts'].say(text[:500])
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


def cmd_create(args, ctx):
    """Create a new file, optionally with LLM-generated content."""
    if not args:
        ui.error('Usage: create <filepath> [description]')
        return

    parts = args.strip().split(None, 1)
    filepath = parts[0]
    description = parts[1] if len(parts) > 1 else None

    full = os.path.join(_get_cwd(), filepath) if not os.path.isabs(filepath) else filepath
    if os.path.exists(full):
        ui.warn(f'File already exists: {filepath}')
        if not ui.ask_confirm('Overwrite?'):
            return

    if not description:
        ui.info(f'What should {filepath} contain?')
        try:
            description = input(f'{ui.YELLOW}> {ui.RESET}').strip()
        except (EOFError, KeyboardInterrupt):
            return
        if not description:
            files.write_file(full, '')
            ui.success(f'Created empty file: {filepath}')
            return

    prompt = (
        f"Create the file `{filepath}`.\n\n"
        f"Description: {description}\n\n"
        f"Output ONLY the file content inside a single code block. No explanation before or after."
    )
    messages = _build_messages(prompt, ctx)

    spinner = ui.Spinner(f'Creating {filepath}')
    spinner.start()
    try:
        response = llm.chat(messages)
    except RuntimeError as e:
        spinner.stop()
        ui.error(str(e))
        return
    spinner.stop()

    ctx['last_response'] = response
    memory.add_history('user', f'create {filepath}: {description}')
    memory.add_history('assistant', response)

    content = _extract_code_block(response)
    if content is None:
        ui.warn('Could not extract code block. Using raw response.')
        content = response

    ui.show_file(filepath, content)

    if ui.ask_confirm(f'Write to {filepath}?'):
        files.write_file(full, content)
        ui.success(f'Created: {filepath}')
    else:
        ui.info('File not created.')


def cmd_fix(args, ctx):
    """Auto-fix the last error. Sends error context to LLM and applies the fix."""
    last_error = ctx.get('last_error')
    last_error_cmd = ctx.get('last_error_cmd')

    if not last_error:
        ui.warn('No recent error to fix. Run a command first.')
        return

    ui.info(f'Last failed command: {last_error_cmd}')
    ui.dim(f'Error: {last_error[:200]}')

    extra = autocontext.detect_context(last_error, _get_cwd())

    prompt = (
        f"The following command failed:\n\n"
        f"```\n$ {last_error_cmd}\n```\n\n"
        f"Error output:\n```\n{last_error}\n```\n\n"
        + (extra + "\n" if extra else "")
        + "Analyze the error and fix it. If it's a code error in a file, "
        "use the edit_file tool to fix it. If it's a missing package, "
        "suggest the install command. If it's a configuration issue, explain the fix.\n"
        "Be concise. Fix it, don't just explain."
    )
    messages = _build_messages(prompt, ctx)

    MAX_TOOL_ROUNDS = 3
    for round_num in range(MAX_TOOL_ROUNDS):
        spinner = ui.Spinner('Fixing' if round_num == 0 else 'Processing')
        spinner.start()
        try:
            response = llm.chat(messages)
        except RuntimeError as e:
            spinner.stop()
            ui.error(str(e))
            return
        spinner.stop()

        text_parts, tool_calls = _parse_tool_calls(response)

        if not tool_calls:
            ctx['last_response'] = response
            memory.add_history('user', f'fix: {last_error_cmd}')
            memory.add_history('assistant', response)
            break

        tool_results = []
        for call in tool_calls:
            tool_name = call['tool']
            tool_args = call.get('args', {})
            ui.dim(f'  [{tool_name}({_compact_args(tool_args)})]')
            result = tools.execute_tool(tool_name, tool_args, ctx)
            display = result[:500] if result else '(no output)'
            if len(result) > 500:
                display += '...'
            ui.info(display)
            tool_results.append({'tool': tool_name, 'args': tool_args, 'result': result})

        text_output = '\n'.join(text_parts).strip()
        if text_output:
            print(text_output)

        messages.append({'role': 'assistant', 'content': response})
        results_text = '\n\n'.join(
            f'[Tool result: {r["tool"]}]\n{r["result"]}' for r in tool_results
        )
        messages.append({'role': 'user', 'content': results_text})
    else:
        ui.warn(f'Stopped after {MAX_TOOL_ROUNDS} tool rounds.')

    ctx.pop('last_error', None)
    ctx.pop('last_error_cmd', None)


def cmd_test(args, ctx):
    """Run tests. Auto-detects test framework."""
    cwd = _get_cwd()

    if args:
        cmd_run(args, ctx)
        return

    try:
        dir_files = [f for f in os.listdir(cwd) if os.path.isfile(os.path.join(cwd, f))]
    except OSError:
        dir_files = []

    if os.path.exists(os.path.join(cwd, 'pytest.ini')) or \
       os.path.exists(os.path.join(cwd, 'setup.cfg')) or \
       os.path.exists(os.path.join(cwd, 'pyproject.toml')) or \
       any(f.startswith('test_') or f.endswith('_test.py') for f in dir_files if f.endswith('.py')):
        ui.info('Detected: Python (pytest)')
        cmd_run('python -m pytest -v', ctx)
        return

    pkg_json = os.path.join(cwd, 'package.json')
    if os.path.exists(pkg_json):
        try:
            import json as _json
            with open(pkg_json, 'r', encoding='utf-8') as f:
                pkg = _json.load(f)
            if 'scripts' in pkg and 'test' in pkg['scripts']:
                ui.info('Detected: Node.js (npm test)')
                cmd_run('npm test', ctx)
                return
        except Exception:
            pass

    if os.path.exists(os.path.join(cwd, 'Cargo.toml')):
        ui.info('Detected: Rust (cargo test)')
        cmd_run('cargo test', ctx)
        return

    if os.path.exists(os.path.join(cwd, 'go.mod')):
        ui.info('Detected: Go (go test)')
        cmd_run('go test ./...', ctx)
        return

    if os.path.exists(os.path.join(cwd, 'pom.xml')):
        ui.info('Detected: Java (mvn test)')
        cmd_run('mvn test', ctx)
        return

    if os.path.exists(os.path.join(cwd, 'build.gradle')):
        ui.info('Detected: Java (gradle test)')
        cmd_run('gradle test', ctx)
        return

    test_files = [f for f in dir_files if f.startswith('test') and f.endswith('.py')]
    if test_files:
        ui.info(f'Running: python -m pytest {" ".join(test_files)}')
        cmd_run(f'python -m pytest {" ".join(test_files)}', ctx)
        return

    ui.warn('No test framework detected.')
    ui.info('  Supported: pytest, npm test, cargo test, go test, mvn/gradle test')
    ui.info('  Or specify: test <command>')


def cmd_install(args, ctx):
    """Install packages. Auto-detects package manager."""
    cwd = _get_cwd()

    if not args:
        if os.path.exists(os.path.join(cwd, 'requirements.txt')):
            ui.info('Installing from requirements.txt...')
            cmd_run('pip install -r requirements.txt', ctx)
        elif os.path.exists(os.path.join(cwd, 'package.json')):
            ui.info('Installing from package.json...')
            cmd_run('npm install', ctx)
        elif os.path.exists(os.path.join(cwd, 'Cargo.toml')):
            ui.info('Building Rust dependencies...')
            cmd_run('cargo build', ctx)
        elif os.path.exists(os.path.join(cwd, 'go.mod')):
            ui.info('Installing Go dependencies...')
            cmd_run('go mod download', ctx)
        elif os.path.exists(os.path.join(cwd, 'Gemfile')):
            ui.info('Installing from Gemfile...')
            cmd_run('bundle install', ctx)
        elif os.path.exists(os.path.join(cwd, 'composer.json')):
            ui.info('Installing from composer.json...')
            cmd_run('composer install', ctx)
        else:
            ui.error('Usage: install <package1> [package2] ...')
            ui.info('  Or run in a directory with requirements.txt / package.json')
        return

    packages = args.strip()
    if os.path.exists(os.path.join(cwd, 'package.json')):
        ui.info(f'npm install {packages}')
        cmd_run(f'npm install {packages}', ctx)
    elif os.path.exists(os.path.join(cwd, 'Cargo.toml')):
        ui.info(f'cargo add {packages}')
        cmd_run(f'cargo add {packages}', ctx)
    elif os.path.exists(os.path.join(cwd, 'go.mod')):
        ui.info(f'go get {packages}')
        cmd_run(f'go get {packages}', ctx)
    else:
        ui.info(f'pip install {packages}')
        cmd_run(f'pip install {packages}', ctx)


def cmd_project(args, ctx):
    """Show project summary: language, deps, entry point, tests."""
    cwd = _get_cwd()
    import json as _json

    ui.header(f'Project: {os.path.basename(cwd)}')
    ui.separator()

    summary = _scan_project(cwd)

    if summary.get('language'):
        print(f'  {ui.BOLD}Language:{ui.RESET}     {summary["language"]}')
    if summary.get('git_branch'):
        print(f'  {ui.BOLD}Git branch:{ui.RESET}   {summary["git_branch"]}')
    if summary.get('git_status'):
        print(f'  {ui.BOLD}Git status:{ui.RESET}   {summary["git_status"]}')
    if summary.get('file_count'):
        print(f'  {ui.BOLD}Files:{ui.RESET}        {summary["file_count"]}')

    # Dependencies
    deps = []
    dep_file = None

    req_path = os.path.join(cwd, 'requirements.txt')
    if os.path.exists(req_path):
        dep_file = 'requirements.txt'
        try:
            with open(req_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        deps.append(line)
        except Exception:
            pass

    pyproj_path = os.path.join(cwd, 'pyproject.toml')
    if not deps and os.path.exists(pyproj_path):
        dep_file = 'pyproject.toml'
        try:
            with open(pyproj_path, 'r', encoding='utf-8') as f:
                in_deps = False
                for line in f:
                    if 'dependencies' in line and '=' in line:
                        in_deps = True
                        continue
                    if in_deps:
                        line = line.strip()
                        if line.startswith(']'):
                            in_deps = False
                        elif line.startswith('"') or line.startswith("'"):
                            deps.append(line.strip('",\' '))
        except Exception:
            pass

    pkg_path = os.path.join(cwd, 'package.json')
    if not deps and os.path.exists(pkg_path):
        dep_file = 'package.json'
        try:
            with open(pkg_path, 'r', encoding='utf-8') as f:
                pkg = _json.load(f)
            for key in ('dependencies', 'devDependencies'):
                if key in pkg:
                    for name, ver in pkg[key].items():
                        deps.append(f'{name}@{ver}')
        except Exception:
            pass

    cargo_path = os.path.join(cwd, 'Cargo.toml')
    if not deps and os.path.exists(cargo_path):
        dep_file = 'Cargo.toml'
        try:
            with open(cargo_path, 'r', encoding='utf-8') as f:
                in_deps = False
                for line in f:
                    if line.strip().startswith('[dependencies]'):
                        in_deps = True
                        continue
                    if in_deps:
                        if line.strip().startswith('['):
                            in_deps = False
                        elif '=' in line:
                            deps.append(line.strip())
        except Exception:
            pass

    if dep_file:
        print(f'  {ui.BOLD}Deps file:{ui.RESET}    {dep_file}')
    if deps:
        print(f'  {ui.BOLD}Dependencies:{ui.RESET} ({len(deps)})')
        for d in deps[:15]:
            print(f'    {ui.DIM}{d}{ui.RESET}')
        if len(deps) > 15:
            print(f'    {ui.DIM}... and {len(deps) - 15} more{ui.RESET}')

    entry_points = ['main.py', 'app.py', 'index.js', 'index.ts', 'main.go',
                    'main.rs', 'src/main.py', 'src/index.js', 'src/main.rs',
                    'src/main.go', 'src/App.java', 'manage.py', 'server.py']
    found_entry = [ep for ep in entry_points if os.path.exists(os.path.join(cwd, ep))]

    if os.path.exists(pkg_path):
        try:
            with open(pkg_path, 'r', encoding='utf-8') as f:
                pkg = _json.load(f)
            if 'main' in pkg:
                main_file = pkg['main']
                if main_file not in found_entry:
                    found_entry.insert(0, main_file)
        except Exception:
            pass

    if found_entry:
        print(f'  {ui.BOLD}Entry point:{ui.RESET}  {", ".join(found_entry)}')

    test_indicators = []
    try:
        dir_files = [f for f in os.listdir(cwd) if os.path.isfile(os.path.join(cwd, f))]
    except OSError:
        dir_files = []

    if any(f.startswith('test') and f.endswith('.py') for f in dir_files):
        test_indicators.append('pytest/unittest')
    if os.path.exists(os.path.join(cwd, 'tests')):
        test_indicators.append('tests/ directory')
    if os.path.exists(pkg_path):
        try:
            with open(pkg_path, 'r', encoding='utf-8') as f:
                pkg = _json.load(f)
            if pkg.get('scripts', {}).get('test'):
                test_indicators.append(f'npm test: {pkg["scripts"]["test"]}')
        except Exception:
            pass

    if test_indicators:
        print(f'  {ui.BOLD}Tests:{ui.RESET}        {", ".join(test_indicators)}')

    print()


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

def _parse_tool_calls(response):
    """Parse LLM response: separate text lines from tool call JSON lines.
    Returns (text_parts: list[str], tool_calls: list[dict])."""
    import json as _json
    lines = response.split('\n')
    text_parts = []
    tool_calls = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith('{"tool"'):
            try:
                call = _json.loads(stripped)
                if 'tool' in call:
                    tool_calls.append(call)
                    continue
            except (_json.JSONDecodeError, KeyError):
                pass
        text_parts.append(line)

    return text_parts, tool_calls


def _compact_args(args):
    """Format tool args for compact display."""
    parts = []
    for k, v in args.items():
        val = str(v)
        if len(val) > 40:
            val = val[:37] + '...'
        parts.append(f'{k}="{val}"')
    return ', '.join(parts)


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
    'h': cmd_help,          # alias
    'read': cmd_read,
    'r': cmd_read,          # alias
    'edit': cmd_edit,
    'e': cmd_edit,          # alias
    'create': cmd_create,
    'new': cmd_create,      # alias
    'run': cmd_run,
    'fix': cmd_fix,
    'test': cmd_test,
    't': cmd_test,          # alias
    'install': cmd_install,
    'i': cmd_install,       # alias
    'project': cmd_project,
    'proj': cmd_project,    # alias
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
        except FileNotFoundError as e:
            ui.error(f'File not found: {e}')
        except PermissionError as e:
            ui.error(f'Permission denied: {e}')
        except ConnectionError as e:
            ui.error(f'Connection failed: {e}')
            ui.info('  Check your internet connection or API endpoint.')
        except RuntimeError as e:
            ui.error(str(e))
        except Exception as e:
            # Show clean error, not a full traceback
            err_type = type(e).__name__
            ui.error(f'{err_type}: {e}')
            ui.dim(f'  (command: {cmd_name}, use "fix" to auto-fix)')
            # Store for "fix" command
            ctx['last_error'] = f'{err_type}: {e}'
            ctx['last_error_cmd'] = line
    else:
        # If not a known command, treat as a question to the LLM
        cmd_ask(line, ctx)

    return True
