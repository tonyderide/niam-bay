#!/usr/bin/env python3
"""
Tests for NiamBay Code smart features.
Run: python test_features.py
"""
import os
import sys
import tempfile
import shutil

# Add script directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PASS = 0
FAIL = 0


def test(name, condition):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f'  PASS  {name}')
    else:
        FAIL += 1
        print(f'  FAIL  {name}')


def test_autocontext():
    """Test auto-context detection."""
    print('\n== Auto-context ==')
    import autocontext

    # Create a temp project
    tmpdir = tempfile.mkdtemp(prefix='nb_test_')
    try:
        # Create test files
        with open(os.path.join(tmpdir, 'main.py'), 'w') as f:
            f.write('def hello_world():\n    print("hello")\n')
        with open(os.path.join(tmpdir, 'utils.py'), 'w') as f:
            f.write('def calculate_total(items):\n    return sum(items)\n')

        # Test 1: Detect filename mention
        ctx = autocontext.detect_context('look at main.py', tmpdir)
        test('detects filename in user input', 'main.py' in ctx)

        # Test 2: Detect symbol (function name)
        ctx = autocontext.detect_context('what does calculate_total do?', tmpdir)
        test('detects function name symbol', 'calculate_total' in ctx)

        # Test 3: No context for generic question
        ctx = autocontext.detect_context('what is python?', tmpdir)
        test('no context for generic question', ctx == '')

        # Test 4: _detect_filenames finds existing files
        found = autocontext._detect_filenames('check main.py please', tmpdir)
        test('_detect_filenames finds main.py', len(found) == 1 and 'main.py' in found[0])

        # Test 5: _detect_symbols extracts snake_case
        symbols = autocontext._detect_symbols('fix the calculate_total function')
        test('_detect_symbols finds snake_case', 'calculate_total' in symbols)

        # Test 6: _wants_fix_or_diff triggers
        test('_wants_fix_or_diff: "fix the bug"', autocontext._wants_fix_or_diff('fix the bug'))
        test('_wants_fix_or_diff: "debug this"', autocontext._wants_fix_or_diff('debug this'))
        test('_wants_fix_or_diff: no trigger', not autocontext._wants_fix_or_diff('explain this code'))

        # Test 7: _is_text_file
        test('_is_text_file: .py', autocontext._is_text_file('test.py'))
        test('_is_text_file: .js', autocontext._is_text_file('app.js'))
        test('_is_text_file: .png (not text)', not autocontext._is_text_file('image.png'))

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_undo():
    """Test undo feature in files module."""
    print('\n== Undo ==')
    import files

    # Reset undo stack
    files._undo_stack.clear()

    tmpdir = tempfile.mkdtemp(prefix='nb_test_')
    try:
        test_file = os.path.join(tmpdir, 'test.txt')

        # Write initial content
        files.write_file(test_file, 'original content')
        test('write initial file', files.read_file(test_file) == 'original content')

        # Apply edit (saves undo)
        files.apply_edit(test_file, 'original content', 'modified content')
        test('apply_edit changes file', files.read_file(test_file) == 'modified content')
        test('undo stack has 1 entry', files.get_undo_count() == 1)

        # Undo
        filepath, success = files.undo_last_edit()
        test('undo succeeds', success)
        test('undo restores original', files.read_file(test_file) == 'original content')
        test('undo stack empty after undo', files.get_undo_count() == 0)

        # Undo when nothing to undo
        filepath, success = files.undo_last_edit()
        test('undo fails when empty', not success)

        # Multiple edits, multiple undos
        files.apply_edit(test_file, 'original content', 'v2')
        files.apply_edit(test_file, 'v2', 'v3')
        files.apply_edit(test_file, 'v3', 'v4')
        test('3 edits in stack', files.get_undo_count() == 3)

        files.undo_last_edit()
        test('undo to v3', files.read_file(test_file) == 'v3')
        files.undo_last_edit()
        test('undo to v2', files.read_file(test_file) == 'v2')
        files.undo_last_edit()
        test('undo to original', files.read_file(test_file) == 'original content')

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
        files._undo_stack.clear()


def test_project_scan():
    """Test project scan feature."""
    print('\n== Project Scan ==')
    import commands

    tmpdir = tempfile.mkdtemp(prefix='nb_test_')
    try:
        # Create a Python project
        with open(os.path.join(tmpdir, 'requirements.txt'), 'w') as f:
            f.write('flask\nrequests\n')
        with open(os.path.join(tmpdir, 'README.md'), 'w') as f:
            f.write('# Test Project\n')
        with open(os.path.join(tmpdir, 'main.py'), 'w') as f:
            f.write('print("hello")\n')

        summary = commands._scan_project(tmpdir)
        test('detects Python language', summary.get('language') == 'Python')
        test('detects requirements.txt', summary.get('config_file') == 'requirements.txt')
        test('finds key files', 'README.md' in summary.get('key_files', []))
        test('counts files', summary.get('file_count', 0) >= 3)

        # Test Node.js project
        tmpdir2 = tempfile.mkdtemp(prefix='nb_test_')
        with open(os.path.join(tmpdir2, 'package.json'), 'w') as f:
            f.write('{"name": "test"}')
        summary2 = commands._scan_project(tmpdir2)
        test('detects JavaScript/Node.js', summary2.get('language') == 'JavaScript/Node.js')
        shutil.rmtree(tmpdir2, ignore_errors=True)

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_clipboard():
    """Test clipboard copy function (may not work in all environments)."""
    print('\n== Clipboard ==')
    import commands

    # Test _copy_to_clipboard exists and is callable
    test('_copy_to_clipboard is callable', callable(commands._copy_to_clipboard))

    # Test _extract_code_block
    text_with_code = "Here's the fix:\n```python\nprint('hello')\n```\nDone."
    code = commands._extract_code_block(text_with_code)
    test('extracts code block', code == "print('hello')")

    text_without_code = "Just a plain explanation."
    code2 = commands._extract_code_block(text_without_code)
    test('returns None without code block', code2 is None)


def test_conversation_history():
    """Test conversation history in context."""
    print('\n== Conversation History ==')
    import memory
    import commands

    # The _build_messages function should include history
    # Test that it includes system prompt + history + user message
    ctx = {'cwd': os.getcwd()}
    messages = commands._build_messages('test question', ctx)

    test('messages has system prompt', messages[0]['role'] == 'system')
    test('messages has user prompt', messages[-1]['role'] == 'user')
    test('user prompt is correct', messages[-1]['content'] == 'test question')

    # Test history format
    history = memory.get_history_for_llm()
    test('history returns list', isinstance(history, list))


def test_command_registry():
    """Test that all new commands are registered."""
    print('\n== Command Registry ==')
    import commands

    test('undo command registered', 'undo' in commands.COMMANDS)
    test('copy command registered', 'copy' in commands.COMMANDS)
    test('scan command registered', 'scan' in commands.COMMANDS)
    test('all original commands intact', all(
        c in commands.COMMANDS for c in [
            'help', 'read', 'edit', 'run', 'search', 'git', 'ask',
            'explain', 'remember', 'recall', 'commands', 'save-cmd',
            'model', 'set-key', 'files'
        ]
    ))


def test_imports():
    """Test that all modules import correctly."""
    print('\n== Imports ==')
    try:
        import autocontext
        test('autocontext imports', True)
    except ImportError as e:
        test(f'autocontext imports: {e}', False)

    try:
        import files
        test('files imports (with undo)', hasattr(files, 'undo_last_edit'))
    except ImportError as e:
        test(f'files imports: {e}', False)

    try:
        import commands
        test('commands imports (with new features)', True)
    except ImportError as e:
        test(f'commands imports: {e}', False)

    try:
        import niambay
        test('niambay imports (with tab completion)', hasattr(niambay, 'setup_tab_completion'))
    except ImportError as e:
        test(f'niambay imports: {e}', False)

    try:
        import ui
        test('ui imports', True)
    except ImportError as e:
        test(f'ui imports: {e}', False)

    try:
        import memory
        test('memory imports', True)
    except ImportError as e:
        test(f'memory imports: {e}', False)

    try:
        import llm
        test('llm imports', True)
    except ImportError as e:
        test(f'llm imports: {e}', False)

    try:
        import config
        test('config imports', True)
    except ImportError as e:
        test(f'config imports: {e}', False)


if __name__ == '__main__':
    print('NiamBay Code — Feature Tests')
    print('=' * 40)

    test_imports()
    test_autocontext()
    test_undo()
    test_project_scan()
    test_clipboard()
    test_conversation_history()
    test_command_registry()

    print(f'\n{"=" * 40}')
    print(f'Results: {PASS} passed, {FAIL} failed')
    if FAIL > 0:
        sys.exit(1)
    else:
        print('All tests passed!')
        sys.exit(0)
