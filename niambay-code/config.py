"""
NiamBay Code — Configuration & API keys
"""
import os
import json
import platform

# Paths
if platform.system() == 'Windows':
    HOME = os.environ.get('USERPROFILE', os.path.expanduser('~'))
else:
    HOME = os.path.expanduser('~')

CONFIG_DIR = os.path.join(HOME, '.niambay-code')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'config.json')
MEMORY_FILE = os.path.join(CONFIG_DIR, 'memory.json')
HISTORY_FILE = os.path.join(CONFIG_DIR, 'history')

# Default providers
PROVIDERS = {
    'deepseek': {
        'url': 'https://api.sambanova.ai/v1/chat/completions',
        'model': 'DeepSeek-V3-0324',
        'env_key': 'SAMBANOVA_API_KEY',
        'max_tokens': 4096,
    },
    'mistral': {
        'url': 'https://api.mistral.ai/v1/chat/completions',
        'model': 'mistral-small-latest',
        'env_key': 'MISTRAL_API_KEY',
        'max_tokens': 4096,
    },
    'cerebras': {
        'url': 'https://api.cerebras.ai/v1/chat/completions',
        'model': 'llama-4-scout-17b-16e-instruct',
        'env_key': 'CEREBRAS_API_KEY',
        'max_tokens': 4096,
    },
    'ollama': {
        'url': 'http://localhost:11434/v1/chat/completions',
        'model': 'niambay2',
        'env_key': '',
        'max_tokens': 4096,
    },
}

DEFAULT_PROVIDER = 'mistral'


def ensure_config_dir():
    """Create config directory if it doesn't exist."""
    os.makedirs(CONFIG_DIR, exist_ok=True)


def load_config():
    """Load config from file, return dict."""
    ensure_config_dir()
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {}


def save_config(cfg):
    """Save config dict to file."""
    ensure_config_dir()
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, indent=2)


def get_api_key(provider_name):
    """Get API key: env var first, then config file."""
    provider = PROVIDERS.get(provider_name, {})
    env_key = provider.get('env_key', '')

    # 1. Environment variable
    if env_key:
        val = os.environ.get(env_key, '')
        if val:
            return val

    # 2. Config file
    cfg = load_config()
    keys = cfg.get('api_keys', {})
    return keys.get(provider_name, '')


def set_api_key(provider_name, key):
    """Save an API key to config file."""
    cfg = load_config()
    if 'api_keys' not in cfg:
        cfg['api_keys'] = {}
    cfg['api_keys'][provider_name] = key
    save_config(cfg)


def get_current_provider():
    """Get current provider name from config."""
    cfg = load_config()
    return cfg.get('provider', DEFAULT_PROVIDER)


def set_current_provider(name):
    """Set current provider in config."""
    cfg = load_config()
    cfg['provider'] = name
    save_config(cfg)
