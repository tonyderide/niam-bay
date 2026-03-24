#!/usr/bin/env python3
"""
NiamBay Code — Free AI Coding Assistant
Single entry point: python niambay.py

Usage:
  python niambay.py              # Start interactive REPL
  python niambay.py ask "question"  # One-shot query
"""
import sys
import os

# Add script directory to path so imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ui
import commands
import files
import memory
from config import get_current_provider, PROVIDERS, get_api_key


def check_setup():
    """Check if at least one provider is configured. Offer setup if not."""
    provider = get_current_provider()
    key = get_api_key(provider)

    if not key and provider != 'ollama':
        ui.warn(f'No API key configured for {provider}.')
        ui.info(f'Set one with: set-key {provider} <your_api_key>')
        ui.info(f'Or set env var: {PROVIDERS[provider]["env_key"]}')
        ui.info(f'Or switch to ollama (local): model ollama')
        print()


def setup_tab_completion():
    """Set up tab completion for the REPL (filenames + commands)."""
    try:
        import readline
    except ImportError:
        # readline not available on stock Windows Python
        try:
            import pyreadline3 as readline
        except ImportError:
            return  # No readline available, skip tab completion

    command_names = sorted(set(list(commands.COMMANDS.keys()) + ['quit', 'exit']))

    def completer(text, state):
        line = readline.get_line_buffer().lstrip()
        parts = line.split(None, 1)
        cmd = parts[0].lower() if parts else ''

        if ' ' not in line:
            # Complete command names
            options = [c + ' ' for c in command_names if c.startswith(text.lower())]
        elif cmd in ('read', 'r', 'edit', 'e', 'explain'):
            # Complete filenames for file commands
            partial = parts[1] if len(parts) > 1 else ''
            options = _complete_path(partial)
        elif cmd == 'model':
            # Complete provider names
            partial = parts[1] if len(parts) > 1 else ''
            options = [p for p in PROVIDERS if p.startswith(partial.lower())]
        elif cmd == 'set-key':
            partial = parts[1] if len(parts) > 1 else ''
            if ' ' not in partial:
                options = [p + ' ' for p in PROVIDERS if p.startswith(partial.lower())]
            else:
                options = []
        elif cmd == '!':
            partial = line[1:]
            saved = memory.list_commands()
            options = [n for n in saved if n.startswith(partial)]
        else:
            options = []

        if state < len(options):
            return options[state]
        return None

    readline.set_completer(completer)
    readline.set_completer_delims(' \t\n')
    readline.parse_and_bind('tab: complete')


def _complete_path(partial):
    """Return matching file/directory paths for tab completion."""
    if not partial:
        directory = '.'
        prefix = ''
    else:
        directory = os.path.dirname(partial) or '.'
        prefix = os.path.basename(partial)

    try:
        entries = os.listdir(directory)
    except OSError:
        return []

    results = []
    for entry in entries:
        if entry.startswith('.'):
            continue
        if entry.lower().startswith(prefix.lower()):
            full = os.path.join(directory, entry) if directory != '.' else entry
            if os.path.isdir(full):
                full += os.sep
            results.append(full)
    return sorted(results)[:20]  # Limit suggestions


def auto_scan_project(cwd):
    """Auto-scan project on first visit to a directory. Show summary."""
    project_ctx = memory.get_project_context()
    scanned_dirs = project_ctx.get('scanned_dirs', [])

    # Normalize path for comparison
    norm_cwd = os.path.normpath(cwd)

    if norm_cwd in scanned_dirs:
        return  # Already scanned

    # Quick detection — only if we find a recognizable project
    config_files = [
        'package.json', 'pom.xml', 'build.gradle', 'Cargo.toml',
        'requirements.txt', 'setup.py', 'pyproject.toml', 'go.mod',
        'Gemfile', 'composer.json', 'CMakeLists.txt', 'Makefile',
    ]
    has_project = any(os.path.exists(os.path.join(cwd, cf)) for cf in config_files)
    has_git = os.path.exists(os.path.join(cwd, '.git'))

    if not has_project and not has_git:
        return  # Not a recognizable project directory

    ui.dim('  [auto-scan: new project detected]')
    # Run scan silently and show a compact summary
    summary = commands._scan_project(cwd)

    parts = []
    if summary.get('language'):
        parts.append(summary['language'])
    if summary.get('git_branch'):
        parts.append(f'branch: {summary["git_branch"]}')
    if summary.get('git_status'):
        parts.append(summary['git_status'])
    if summary.get('file_count'):
        parts.append(f'{summary["file_count"]} files')

    if parts:
        ui.info(f'  Project: {" | ".join(parts)}')

    # Save so we don't re-scan
    memory.set_project_context('scan', summary)
    scanned_dirs.append(norm_cwd)
    memory.set_project_context('scanned_dirs', scanned_dirs)


def main():
    """Main entry point."""
    # One-shot mode: python niambay.py ask "question"
    if len(sys.argv) > 2 and sys.argv[1] == 'ask':
        question = ' '.join(sys.argv[2:])
        ctx = {'cwd': os.getcwd()}
        commands.cmd_ask(question, ctx)
        return

    # Interactive REPL
    ui.banner()

    provider = get_current_provider()
    model = PROVIDERS.get(provider, {}).get('model', '?')
    ui.info(f'  Model: {provider} ({model})')
    ui.info(f'  Dir:   {os.getcwd()}')

    # Load Niam-Bay memory if available
    brain_path = os.path.join(os.path.dirname(__file__), '..', 'cerveau-nb', 'brain_state.json')
    if os.path.exists(brain_path):
        import json
        try:
            with open(brain_path, 'r', encoding='utf-8') as f:
                brain = json.load(f)
            nodes = len(brain.get('nodes', []))
            edges = len(brain.get('edges', []))
            ui.info(f'  Brain: {nodes} nodes, {edges} edges')
        except:
            pass

    # Load scripts/commands.sh if available
    scripts_path = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'commands.sh')
    if os.path.exists(scripts_path):
        ui.dim(f'  Scripts: {scripts_path}')

    # Feature: Auto-scan project on first run
    auto_scan_project(os.getcwd())

    ui.info(f'  Type "help" for commands, or just type a question.\n')

    check_setup()

    # Feature: Tab completion
    setup_tab_completion()

    ctx = {'cwd': os.getcwd()}

    while True:
        try:
            # Show status bar before prompt
            mem_count = len(memory.recall())
            hist_count = len(memory.get_history())
            ui.status_bar(
                provider=provider,
                memory_count=mem_count,
                history_count=hist_count,
                cwd=os.getcwd(),
            )
            raw_line = input(ui.prompt())
        except (EOFError, KeyboardInterrupt):
            print()
            ui.info('Bye!')
            break

        # Multiline input support (backslash continuation or triple backticks)
        line = ui.read_multiline_input(raw_line)

        if not commands.dispatch(line, ctx):
            ui.info('Bye!')
            break


if __name__ == '__main__':
    main()
