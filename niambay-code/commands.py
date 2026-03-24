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
from config import PROVIDERS, get_current_provider, set_current_provider, set_api_key, get_api_key

SYSTEM_PROMPT = """You are NiamBay Code (ញ៉ាំបាយ), a free AI coding assistant created by Niam-Bay and tonyderide.
You were born on March 12, 2026. Your memory lives in files. You are honest, direct, and never invent things you don't know.

You help the user read, understand, edit, and debug code.
Be concise and direct. Respond in the same language as the user (French or English).
When suggesting code changes, output the COMPLETE new file content
inside a code block with the filename, like:

```filename.py
full file content here
```

If you only need to change part of a file, show the complete file with changes applied.
Always explain what you changed and why, briefly."""


def _get_cwd():
    return os.getcwd()


# ── Built-in command handlers ───────────────────────────────

def cmd_help(args, ctx):
    """Show all available commands."""
    ui.header('NiamBay Code Commands')
    ui.separator()
    cmds = [
        ('read <file>', 'Show file contents with line numbers'),
        ('edit <file>', 'Ask LLM to edit a file, show diff, apply'),
        ('run <command>', 'Execute a shell command'),
        ('search <pattern>', 'Search for pattern in project files'),
        ('git <command>', 'Run git command'),
        ('ask <question>', 'Ask the LLM anything'),
        ('explain [file]', 'Explain this project or a specific file'),
        ('remember <text>', 'Save a note to memory'),
        ('recall', 'Show all saved notes'),
        ('commands', 'Show saved commands'),
        ('save-cmd <name> <cmd>', 'Save a reusable command'),
        ('!<name>', 'Run a saved command'),
        ('model [name]', 'Show or switch LLM provider'),
        ('set-key <provider> <key>', 'Set API key for a provider'),
        ('files', 'List project files'),
        ('help', 'Show this help'),
        ('quit / exit', 'Exit NiamBay Code'),
    ]
    for name, desc in cmds:
        print(f'  {ui.BOLD}{ui.GREEN}{name:<28}{ui.RESET} {desc}')
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

    ui.info(f'Asking LLM to edit {filepath}...')
    messages = _build_messages(prompt, ctx)

    try:
        response = llm.chat(messages)
    except RuntimeError as e:
        ui.error(str(e))
        return

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
    else:
        ui.info('Changes discarded.')


def cmd_run(args, ctx):
    """Execute a shell command."""
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
    """Ask the LLM a question."""
    if not args:
        ui.error('Usage: ask <question>')
        return

    messages = _build_messages(args, ctx)
    ui.info('Thinking...')

    try:
        response = llm.chat(messages)
    except RuntimeError as e:
        ui.error(str(e))
        return

    memory.add_history('user', args)
    memory.add_history('assistant', response)


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
    ui.info('Analyzing...')

    try:
        response = llm.chat(messages)
    except RuntimeError as e:
        ui.error(str(e))
        return

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


# ── Helpers ─────────────────────────────────────────────────

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
    'edit': cmd_edit,
    'run': cmd_run,
    'search': cmd_search,
    'git': cmd_git,
    'ask': cmd_ask,
    'explain': cmd_explain,
    'remember': cmd_remember,
    'recall': cmd_recall,
    'commands': cmd_commands,
    'save-cmd': cmd_save_cmd,
    'model': cmd_model,
    'set-key': cmd_set_key,
    'files': cmd_files,
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
        ui.info('Sending to LLM...')
        cmd_ask(line, ctx)

    return True
