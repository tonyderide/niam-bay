"""
NiamBay Code — Tool definitions and execution
The LLM can call these tools to interact with the machine directly.
"""
import os
import re
import subprocess

import ui
import files as files_module


TOOLS = [
    {
        "name": "run_command",
        "description": "Execute a shell command on the machine",
        "parameters": {"command": "the command to run"}
    },
    {
        "name": "read_file",
        "description": "Read a file and return its contents",
        "parameters": {"path": "file path to read"}
    },
    {
        "name": "edit_file",
        "description": "Replace content in a file",
        "parameters": {"path": "file path", "old_text": "text to find", "new_text": "replacement text"}
    },
    {
        "name": "search_code",
        "description": "Search for a pattern in project files",
        "parameters": {"pattern": "regex or text to search"}
    },
    {
        "name": "list_files",
        "description": "List files in the current directory",
        "parameters": {"path": "directory path (default: current)"}
    },
    {
        "name": "git",
        "description": "Run a git command",
        "parameters": {"args": "git arguments (status, diff, log, etc.)"}
    },
]

# Commands that require user confirmation before execution
DANGEROUS_PATTERNS = re.compile(
    r'(?:^|\s)(rm\s|rmdir\b|del\s|format\s|mkfs\b|dd\s|shutdown\b|reboot\b|'
    r'taskkill\b|kill\s|>\s*/dev/|rd\s|Remove-Item\b|Clear-Content\b)',
    re.IGNORECASE,
)


def _needs_confirmation(tool_name, args):
    """Check if a tool call needs user confirmation before executing."""
    if tool_name == 'run_command':
        cmd = args.get('command', '')
        if DANGEROUS_PATTERNS.search(cmd):
            return True, f'Dangerous command: {cmd}'
    elif tool_name == 'edit_file':
        path = args.get('path', '?')
        old = args.get('old_text', '')
        new = args.get('new_text', '')
        return True, f'Edit {path}: "{old[:60]}" -> "{new[:60]}"'
    return False, ''


def execute_tool(name, args, ctx):
    """Execute a tool and return the result as string."""
    cwd = ctx.get('cwd', os.getcwd())

    if name == 'run_command':
        command = args.get('command', '')
        if not command:
            return 'Error: no command provided'
        # Safety check for dangerous commands
        needs, reason = _needs_confirmation(name, args)
        if needs:
            if not ui.ask_confirm(f'{reason} — execute?'):
                return '[User cancelled execution]'
        ui.dim(f'  $ {command}')
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True,
                timeout=60, cwd=cwd,
            )
            output = (result.stdout or '') + (result.stderr or '')
            if result.returncode != 0:
                output += f'\n[exit code: {result.returncode}]'
            return output.strip() or '(no output)'
        except subprocess.TimeoutExpired:
            return '[Error: command timed out (60s)]'
        except Exception as e:
            return f'[Error: {e}]'

    elif name == 'read_file':
        path = args.get('path', '')
        if not path:
            return 'Error: no path provided'
        full = path if os.path.isabs(path) else os.path.join(cwd, path)
        try:
            content = files_module.read_file(full)
            # Truncate very large files
            lines = content.split('\n')
            if len(lines) > 500:
                content = '\n'.join(lines[:500]) + '\n... (truncated at 500 lines)'
            return content
        except FileNotFoundError:
            return f'Error: file not found: {path}'
        except Exception as e:
            return f'Error reading file: {e}'

    elif name == 'edit_file':
        path = args.get('path', '')
        old_text = args.get('old_text', '')
        new_text = args.get('new_text', '')
        if not path:
            return 'Error: no path provided'
        full = path if os.path.isabs(path) else os.path.join(cwd, path)
        try:
            content = files_module.read_file(full)
        except FileNotFoundError:
            return f'Error: file not found: {path}'

        if old_text not in content:
            return f'Error: old_text not found in {path}'

        new_content = content.replace(old_text, new_text, 1)

        # Show diff and ask confirmation
        has_changes = ui.show_diff(path, content, new_content)
        if not has_changes:
            return 'No changes detected.'

        needs, reason = _needs_confirmation(name, args)
        if needs:
            if not ui.ask_confirm('Apply this edit?'):
                return '[User cancelled edit]'

        files_module.apply_edit(full, content, new_content)
        return f'Edit applied to {path}'

    elif name == 'search_code':
        pattern = args.get('pattern', '')
        if not pattern:
            return 'Error: no pattern provided'
        results = files_module.search_files(pattern, cwd)
        if not results:
            return 'No matches found.'
        lines = []
        for fpath, lineno, line_text in results[:30]:
            lines.append(f'{fpath}:{lineno}: {line_text}')
        output = '\n'.join(lines)
        if len(results) > 30:
            output += f'\n... ({len(results)} total matches)'
        return output

    elif name == 'list_files':
        path = args.get('path', '') or cwd
        full = path if os.path.isabs(path) else os.path.join(cwd, path)
        try:
            project_files = files_module.list_project_files(full, max_files=100)
            return '\n'.join(project_files) if project_files else '(no files found)'
        except Exception as e:
            return f'Error: {e}'

    elif name == 'git':
        git_args = args.get('args', 'status')
        ui.dim(f'  $ git {git_args}')
        try:
            result = subprocess.run(
                f'git {git_args}', shell=True, capture_output=True, text=True,
                timeout=30, cwd=cwd,
            )
            output = (result.stdout or '') + (result.stderr or '')
            return output.strip() or '(no output)'
        except subprocess.TimeoutExpired:
            return '[Error: git command timed out (30s)]'
        except Exception as e:
            return f'[Error: {e}]'

    return f'Unknown tool: {name}'
