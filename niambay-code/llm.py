"""
NiamBay Code — Multi-LLM client
Supports: SambaNova (DeepSeek), Mistral, Cerebras, Ollama
Uses only stdlib (urllib) — no pip install needed.
"""
import json
import time
import urllib.request
import urllib.error
import ssl
import sys
from config import PROVIDERS, get_api_key, get_current_provider

# Cooldown tracker: provider_name -> timestamp when cooldown expires
# After a 429, don't retry that provider for COOLDOWN_SECONDS
COOLDOWN_SECONDS = 60
_provider_cooldowns = {}

# Skip SSL verification for some providers that cause issues
_ctx = ssl.create_default_context()
_ctx.check_hostname = False
_ctx.verify_mode = ssl.CERT_NONE


def _call_openai_compat(url, api_key, model, messages, max_tokens=4096, stream=True):
    """Call an OpenAI-compatible API. Streams by default."""
    payload = {
        'model': model,
        'messages': messages,
        'max_tokens': max_tokens,
        'stream': stream,
    }

    headers = {
        'Content-Type': 'application/json',
    }
    if api_key:
        headers['Authorization'] = f'Bearer {api_key}'

    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers=headers, method='POST')

    try:
        resp = urllib.request.urlopen(req, context=_ctx, timeout=30)
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='replace')
        raise RuntimeError(f'LLM API error {e.code}: {body}')
    except urllib.error.URLError as e:
        raise RuntimeError(f'LLM connection error: {e.reason}')

    if not stream:
        body = json.loads(resp.read().decode('utf-8'))
        return body['choices'][0]['message']['content']

    # Stream SSE
    full_text = []
    for raw_line in resp:
        line = raw_line.decode('utf-8', errors='replace').strip()
        if not line:
            continue
        if line.startswith('data: '):
            data_str = line[6:]
            if data_str.strip() == '[DONE]':
                break
            try:
                chunk = json.loads(data_str)
                delta = chunk.get('choices', [{}])[0].get('delta', {})
                token = delta.get('content', '')
                if token:
                    sys.stdout.write(token)
                    sys.stdout.flush()
                    full_text.append(token)
            except json.JSONDecodeError:
                continue

    print()  # newline after streaming
    return ''.join(full_text)


def _is_on_cooldown(name):
    """Check if a provider is on cooldown after a 429."""
    expires = _provider_cooldowns.get(name, 0)
    if time.time() < expires:
        return True
    return False


def _set_cooldown(name):
    """Put a provider on cooldown for COOLDOWN_SECONDS."""
    _provider_cooldowns[name] = time.time() + COOLDOWN_SECONDS


def chat(messages, provider_name=None, stream=True):
    """
    Send messages to the current LLM provider with CASCADE fallback.
    If the current provider fails (rate limit, error), tries the next one.
    After a 429, the provider is put on cooldown for 60s.
    """
    if provider_name is None:
        provider_name = get_current_provider()

    # Build cascade order: current provider first, then others
    order = [provider_name] + [p for p in PROVIDERS if p != provider_name]

    last_error = None
    for name in order:
        provider = PROVIDERS.get(name)
        if not provider:
            continue

        api_key = get_api_key(name)
        if not api_key and name != 'ollama':
            continue

        # Skip providers on cooldown (rate-limited recently)
        if _is_on_cooldown(name):
            import ui
            remaining = int(_provider_cooldowns[name] - time.time())
            ui.dim(f'  [{name} on cooldown ({remaining}s left), skipping...]')
            continue

        try:
            return _call_openai_compat(
                url=provider['url'],
                api_key=api_key,
                model=provider['model'],
                messages=messages,
                max_tokens=provider.get('max_tokens', 4096),
                stream=stream,
            )
        except RuntimeError as e:
            last_error = e
            # If it's a 429 rate limit, put provider on cooldown
            if 'API error 429' in str(e):
                _set_cooldown(name)
                import ui
                ui.dim(f'  [{name} rate-limited (429), cooldown {COOLDOWN_SECONDS}s, trying next...]')
            else:
                import ui
                ui.dim(f'  [{name} failed, trying next...]')
            continue

    raise RuntimeError(f'All providers failed. Last error: {last_error}')


def quick_ask(prompt_text, system=None, provider_name=None):
    """Convenience: single prompt, returns text."""
    messages = []
    if system:
        messages.append({'role': 'system', 'content': system})
    messages.append({'role': 'user', 'content': prompt_text})
    return chat(messages, provider_name=provider_name)
