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
    ui.info(f'  Type "help" for commands, or just type a question.\n')

    check_setup()

    ctx = {'cwd': os.getcwd()}

    while True:
        try:
            line = input(ui.prompt())
        except (EOFError, KeyboardInterrupt):
            print()
            ui.info('Bye!')
            break

        if not commands.dispatch(line, ctx):
            ui.info('Bye!')
            break


if __name__ == '__main__':
    main()
