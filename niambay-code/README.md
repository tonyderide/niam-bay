# NiamBay Code ញ៉ាំបាយ

Free AI coding assistant in the terminal. Like Claude Code, but powered by free LLMs.

## Quick Start

```bash
python niambay.py
```

No pip install needed — pure Python stdlib.

## Setup

Set an API key for at least one provider:

```bash
# Option 1: Environment variable
export SAMBANOVA_API_KEY=your_key_here

# Option 2: Inside NiamBay Code
nb> set-key deepseek your_key_here

# Option 3: Use local Ollama (no key needed)
nb> model ollama
```

### Free API Keys
- **SambaNova** (DeepSeek V3): https://cloud.sambanova.ai/ — free tier
- **Mistral**: https://console.mistral.ai/ — free tier
- **Cerebras**: https://cloud.cerebras.ai/ — free tier
- **Ollama**: https://ollama.ai/ — local, no key needed

## Commands

| Command | Description |
|---------|-------------|
| `read <file>` | Show file contents with line numbers |
| `edit <file>` | LLM suggests edits, show diff, you approve |
| `run <command>` | Execute shell command |
| `search <pattern>` | Search in project files |
| `git <command>` | Git shortcut |
| `ask <question>` | Ask the LLM anything |
| `explain [file]` | Explain project or file |
| `remember <text>` | Save note to memory |
| `recall` | Show saved notes |
| `commands` | Show saved commands |
| `save-cmd <name> <cmd>` | Save reusable command |
| `!<name>` | Run saved command |
| `model [name]` | Show/switch LLM provider |
| `set-key <provider> <key>` | Set API key |
| `files` | List project files |
| `help` | Show all commands |
| `quit` | Exit |

Anything that isn't a command gets sent to the LLM as a question.

## One-shot mode

```bash
python niambay.py ask "explain what a decorator is in Python"
```

## Memory

Stored in `~/.niambay-code/`:
- `config.json` — provider settings, API keys
- `memory.json` — notes, saved commands, conversation history

## Requirements

- Python 3.7+
- No pip dependencies (uses urllib)
- Windows 10+ or Linux
