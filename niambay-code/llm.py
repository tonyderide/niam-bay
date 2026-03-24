"""
NiamBay Code — Multi-LLM client
Supports: SambaNova (DeepSeek), Mistral, Cerebras, Ollama
Uses only stdlib (urllib) — no pip install needed.
"""
import json
import urllib.request
import urllib.error
import ssl
import sys
from config import PROVIDERS, get_api_key, get_current_provider

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
        resp = urllib.request.urlopen(req, context=_ctx, timeout=120)
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


def chat(messages, provider_name=None, stream=True):
    """
    Send messages to the current LLM provider.
    messages: list of {'role': 'user'|'assistant'|'system', 'content': '...'}
    Returns: assistant response text.
    """
    if provider_name is None:
        provider_name = get_current_provider()

    provider = PROVIDERS.get(provider_name)
    if not provider:
        raise RuntimeError(f'Unknown provider: {provider_name}')

    api_key = get_api_key(provider_name)

    # Ollama doesn't need a key
    if not api_key and provider_name != 'ollama':
        raise RuntimeError(
            f'No API key for {provider_name}. '
            f'Set {provider["env_key"]} env var or run: nb> set-key {provider_name} <key>'
        )

    return _call_openai_compat(
        url=provider['url'],
        api_key=api_key,
        model=provider['model'],
        messages=messages,
        max_tokens=provider.get('max_tokens', 4096),
        stream=stream,
    )


def quick_ask(prompt_text, system=None, provider_name=None):
    """Convenience: single prompt, returns text."""
    messages = []
    if system:
        messages.append({'role': 'system', 'content': system})
    messages.append({'role': 'user', 'content': prompt_text})
    return chat(messages, provider_name=provider_name)
