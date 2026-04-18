# ─── Kraken Realized Stats (V2 — in-memory cached) ───
import base64, hashlib, hmac
from urllib.parse import urlencode
from collections import defaultdict
from datetime import datetime, timezone, timedelta

_KRAKEN_ENV = None
_LOG_CACHE = {
    'entries': [],
    'max_id': 0,
    'last_refresh': 0,
    'bootstrap_done': False,
}
_LOG_LOCK = asyncio.Lock()
_LOG_REFRESH_SEC = 300
_LOG_BOOTSTRAP_DAYS = 35

def _load_kraken_env():
    global _KRAKEN_ENV
    if _KRAKEN_ENV is None:
        _KRAKEN_ENV = {}
        try:
            with open('/home/ubuntu/martin/.env') as f:
                for line in f:
                    if '=' in line and not line.strip().startswith('#'):
                        k, v = line.strip().split('=', 1)
                        _KRAKEN_ENV[k] = v.strip('"').strip("'")
        except Exception as e:
            log.error(f'Failed to load kraken env: {e}')
    return _KRAKEN_ENV

def _kraken_nonce():
    if not hasattr(_kraken_nonce, '_last'):
        _kraken_nonce._last = 0
    v = max(time.time_ns() * 5, _kraken_nonce._last + 1)
    _kraken_nonce._last = v
    return str(v)

def _kraken_sign(path, n, qs, secret):
    msg = (qs + n + path).encode()
    h = hashlib.sha256(msg).digest()
    return base64.b64encode(hmac.new(base64.b64decode(secret), h, hashlib.sha512).digest()).decode()

async def _kraken_call(sig_path, url_path, params=None):
    env = _load_kraken_env()
    key, sec = env['KRAKEN_API_KEY'], env['KRAKEN_API_SECRET']
    qs = urlencode(params) if params else ''
    n = _kraken_nonce()
    url = 'https://futures.kraken.com' + url_path + ('?' + qs if qs else '')
    headers = {'APIKey': key, 'Authent': _kraken_sign(sig_path, n, qs, sec), 'Nonce': n, 'User-Agent': 'niam-bay-gateway/1.0'}
    try:
        r = await http_client.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            return 200, r.json()
        return r.status_code, None
    except Exception as e:
        return 0, None

async def _bootstrap_log_cache():
    since_iso = (datetime.now(timezone.utc) - timedelta(days=_LOG_BOOTSTRAP_DAYS)).isoformat().replace('+00:00', 'Z')
    code, r = await _kraken_call('/api/history/v2/account-log', '/api/history/v2/account-log', {'count': 1})
    if code != 200 or not r or not r.get('logs'):
        log.error(f'bootstrap: cannot get last id, code={code}')
        return False
    max_id = r['logs'][0]['id']
    await asyncio.sleep(0.5)
    code, r = await _kraken_call('/api/history/v2/account-log', '/api/history/v2/account-log', {'from': 1, 'count': 500, 'sort': 'asc'})
    if code != 200 or not r or not r.get('logs'):
        log.error(f'bootstrap: cannot get first id, code={code}')
        return False
    min_id = r['logs'][0]['id']
    lo, hi = min_id, max_id
    target = max_id
    for _ in range(20):
        if lo > hi: break
        mid = (lo + hi) // 2
        await asyncio.sleep(0.5)
        code, r = await _kraken_call('/api/history/v2/account-log', '/api/history/v2/account-log', {'from': mid, 'count': 500, 'sort': 'asc'})
        if code != 200 or not r or not r.get('logs'):
            await asyncio.sleep(2)
            continue
        earliest = r['logs'][0]
        if earliest['date'] >= since_iso:
            target = earliest['id']
            hi = mid - 1
        else:
            lo = mid + 1
    all_logs = []
    cur = target
    for _ in range(40):
        await asyncio.sleep(0.5)
        code, r = await _kraken_call('/api/history/v2/account-log', '/api/history/v2/account-log', {'from': cur, 'count': 500, 'sort': 'asc'})
        if code == 429:
            await asyncio.sleep(15)
            continue
        if code != 200 or not r or not r.get('logs'):
            break
        new = r['logs']
        seen = {l['id'] for l in all_logs}
        new = [l for l in new if l['id'] not in seen]
        if not new: break
        all_logs.extend(new)
        last_id = max(l['id'] for l in new)
        if last_id >= max_id: break
        cur = last_id + 1
    _LOG_CACHE['entries'] = sorted(all_logs, key=lambda l: l['id'])
    _LOG_CACHE['max_id'] = max((l['id'] for l in all_logs), default=0)
    _LOG_CACHE['last_refresh'] = time.time()
    _LOG_CACHE['bootstrap_done'] = True
    log.info(f'Log cache bootstrapped: {len(all_logs)} entries, max_id={_LOG_CACHE["max_id"]}')
    return True

async def _refresh_log_cache():
    code, r = await _kraken_call('/api/history/v2/account-log', '/api/history/v2/account-log', {'from': _LOG_CACHE['max_id'] + 1, 'count': 500, 'sort': 'asc'})
    _LOG_CACHE['last_refresh'] = time.time()
    if code == 200 and r and r.get('logs'):
        new = r['logs']
        seen = {l['id'] for l in _LOG_CACHE['entries']}
        new = [l for l in new if l['id'] not in seen]
        if new:
            _LOG_CACHE['entries'].extend(new)
            _LOG_CACHE['entries'].sort(key=lambda l: l['id'])
            _LOG_CACHE['max_id'] = max((l['id'] for l in _LOG_CACHE['entries']), default=0)
            log.info(f'Log cache refreshed: +{len(new)} entries')

async def _ensure_log_cache():
    async with _LOG_LOCK:
        if not _LOG_CACHE['bootstrap_done']:
            await _bootstrap_log_cache()
            return
        if time.time() - _LOG_CACHE['last_refresh'] > _LOG_REFRESH_SEC:
            await _refresh_log_cache()

def _aggregate_logs(entries, since_iso):
    fee_p = defaultdict(float)
    pnl_p = defaultdict(float)
    fund_p = defaultdict(float)
    daily = defaultdict(lambda: {'fees': 0, 'pnl': 0, 'funding': 0, 'trades': 0})
    for e in entries:
        if e.get('date', '') < since_iso:
            continue
        info = (e.get('info') or '').lower()
        d = e['date'][:10]
        pair = (e.get('contract') or '').upper()
        fee = e.get('fee')
        pnl = e.get('realized_pnl')
        rfund = e.get('realized_funding')
        if 'futures trade' in info:
            if fee is not None:
                fee_p[pair] += float(fee)
                daily[d]['fees'] += float(fee)
            if pnl is not None:
                pnl_p[pair] += float(pnl)
                daily[d]['pnl'] += float(pnl)
                daily[d]['trades'] += 1
            if rfund is not None:
                fund_p[pair] += float(rfund)
                daily[d]['funding'] += float(rfund)
    total_pnl = sum(pnl_p.values())
    total_fee = sum(fee_p.values())
    total_fund = sum(fund_p.values())
    return {
        'since': since_iso,
        'computed_at': datetime.now(timezone.utc).isoformat(),
        'cache_entries': len(entries),
        'total': {
            'realized_pnl': round(total_pnl, 4),
            'fees': round(total_fee, 4),
            'funding': round(total_fund, 4),
            'net': round(total_pnl - total_fee + total_fund, 4),
        },
        'by_pair': {
            p: {
                'realized_pnl': round(pnl_p[p], 4),
                'fees': round(fee_p[p], 4),
                'funding': round(fund_p[p], 4),
                'net': round(pnl_p[p] - fee_p[p] + fund_p[p], 4),
            } for p in sorted(set(list(pnl_p) + list(fee_p) + list(fund_p)) - {''})
        },
        'daily': {d: {**daily[d], 'net': round(daily[d]['pnl'] - daily[d]['fees'] + daily[d]['funding'], 4)} for d in sorted(daily)},
    }

@app.get('/api/stats/realized')
async def stats_realized(since: str = None):
    await _ensure_log_cache()
    if not since:
        since = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat().replace('+00:00', 'Z')
    return _aggregate_logs(_LOG_CACHE['entries'], since)

