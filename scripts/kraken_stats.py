#!/usr/bin/env python3
"""Kraken Futures stats — fills, fees, realized PnL, funding, daily timeline.
Usage: python3 kraken_stats.py [SINCE_ISO]
Default SINCE: 2026-04-05T13:59:17Z (autobot launch)"""
import base64, hashlib, hmac, time, json, sys
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from collections import defaultdict
from datetime import datetime, timezone

env = {}
with open('/home/ubuntu/martin/.env') as f:
    for line in f:
        if '=' in line and not line.strip().startswith('#'):
            k, v = line.strip().split('=', 1)
            env[k] = v.strip('"').strip("'")

KEY, SEC = env['KRAKEN_API_KEY'], env['KRAKEN_API_SECRET']
HOST = 'https://futures.kraken.com'
UA = 'martin-stats/1.0'
SINCE_ISO = sys.argv[1] if len(sys.argv) > 1 else '2026-04-05T13:59:17Z'

_n = 0
def nonce():
    global _n
    v = max(time.time_ns(), _n + 1); _n = v; return str(v)

def sign(p, n, qs=''):
    m = (qs + n + p).encode(); h = hashlib.sha256(m).digest()
    return base64.b64encode(hmac.new(base64.b64decode(SEC), h, hashlib.sha512).digest()).decode()

def call(sig_path, url_path, params=None):
    qs = urlencode(params) if params else ''
    n = nonce()
    url = HOST + url_path + ('?' + qs if qs else '')
    r = Request(url, headers={'APIKey': KEY, 'Authent': sign(sig_path, n, qs), 'Nonce': n, 'User-Agent': UA})
    try:
        with urlopen(r, timeout=15) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return {'error': str(e)}

# === FILLS ===
print(f'[1/2] Fetching fills since {SINCE_ISO}...', file=sys.stderr)
fills_all = []
last_ft = None
for i in range(50):
    p = {'lastFillTime': last_ft} if last_ft else None
    r = call('/api/v3/fills', '/derivatives/api/v3/fills', p)
    if r.get('result') != 'success':
        print(f'  err: {r.get("error")}', file=sys.stderr); break
    fs = r.get('fills', [])
    if not fs: break
    seen = {f['fill_id'] for f in fills_all}
    new = [f for f in fs if f['fill_id'] not in seen]
    if not new: break
    fills_all.extend(new)
    oldest = min(f['fillTime'] for f in fs)
    if oldest <= SINCE_ISO: break
    last_ft = oldest
    time.sleep(0.4)
fills = [f for f in fills_all if f['fillTime'] >= SINCE_ISO]
print(f'  {len(fills)} fills', file=sys.stderr)

# === ACCOUNT LOG (paginate asc with from=id) ===
# Find starting id by binary search on dates
print(f'[2/2] Account log since {SINCE_ISO}...', file=sys.stderr)

# Binary search: find smallest id where date >= SINCE_ISO
def log_page(from_id, sort='asc'):
    return call('/api/history/v2/account-log', '/api/history/v2/account-log', {'from': from_id, 'count': 500, 'sort': sort})

# Get bounds first
r_first = log_page(1)
if not r_first.get('logs'):
    print(f'  err first: {r_first}', file=sys.stderr); sys.exit(1)
min_id = r_first['logs'][0]['id']
time.sleep(0.4)

r_last = call('/api/history/v2/account-log', '/api/history/v2/account-log', {'count': 1})
if not r_last.get('logs'):
    print(f'  err last: {r_last}', file=sys.stderr); sys.exit(1)
max_id = r_last['logs'][0]['id']
print(f'  id range: {min_id} .. {max_id}', file=sys.stderr)
time.sleep(0.4)

# Binary search for SINCE
lo, hi = min_id, max_id
target_id = max_id
while lo <= hi:
    mid = (lo + hi) // 2
    r = log_page(mid)
    if not r.get('logs'): break
    earliest = r['logs'][0]
    time.sleep(0.3)
    if earliest['date'] >= SINCE_ISO:
        target_id = earliest['id']
        hi = mid - 1
    else:
        lo = mid + 1

# Walk forward from target_id
print(f'  starting at id {target_id}', file=sys.stderr)
logs_all = []
cur = target_id
for i in range(50):
    r = log_page(cur)
    if not r.get('logs'): break
    new = r['logs']
    seen = {l['id'] for l in logs_all}
    new = [l for l in new if l['id'] not in seen]
    if not new: break
    logs_all.extend(new)
    last_id = max(l['id'] for l in new)
    print(f'  page {i}: +{len(new)} (now through {new[-1]["date"]})', file=sys.stderr)
    if last_id >= max_id: break
    cur = last_id + 1
    time.sleep(0.4)

print(f'  {len(logs_all)} entries', file=sys.stderr); print('', file=sys.stderr)

# === AGGREGATE ===
fee_p = defaultdict(float); pnl_p = defaultdict(float); fund_p = defaultdict(float)
daily = defaultdict(lambda: {'fees':0,'pnl':0,'funding':0,'fills':0})

for e in logs_all:
    if e.get('date', '') < SINCE_ISO: continue
    info = (e.get('info') or '').lower()
    d = e['date'][:10]
    pair = (e.get('contract') or '').upper()
    fee = e.get('fee'); pnl = e.get('realized_pnl'); rfund = e.get('realized_funding')
    if 'futures trade' in info:
        if fee is not None: fee_p[pair] += float(fee); daily[d]['fees'] += float(fee)
        if pnl is not None: pnl_p[pair] += float(pnl); daily[d]['pnl'] += float(pnl)
        if rfund is not None: fund_p[pair] += float(rfund); daily[d]['funding'] += float(rfund)

for f in fills:
    daily[f['fillTime'][:10]]['fills'] += 1

pairs = sorted(set(list(pnl_p) + list(fee_p) + list(fund_p)) - {''})
print('=' * 74)
print(f'KRAKEN STATS — since {SINCE_ISO} → {datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}')
print('=' * 74)
print(f'{"Pair":<14}{"Fills":>7}{"RealPnL":>11}{"Fees":>9}{"Funding":>10}{"Net":>11}')
print('-' * 74)
gP=gF=gFd=gFi=0
for p in pairs:
    fc = sum(1 for x in fills if x['symbol'].upper()==p)
    n = pnl_p[p] - fee_p[p] + fund_p[p]
    gP+=pnl_p[p]; gF+=fee_p[p]; gFd+=fund_p[p]; gFi+=fc
    print(f'{p:<14}{fc:>7}{pnl_p[p]:>+11.4f}{fee_p[p]:>9.4f}{fund_p[p]:>+10.4f}{n:>+11.4f}')
print('-' * 74)
print(f'{"TOTAL":<14}{gFi:>7}{gP:>+11.4f}{gF:>9.4f}{gFd:>+10.4f}{gP-gF+gFd:>+11.4f}')
print()
print(f'NET PROFIT: ${gP-gF+gFd:+.4f}  =  PnL ${gP:+.2f}  −  Fees ${gF:.2f}  +  Funding ${gFd:+.2f}')
print()
print('=' * 74)
print('DAILY TIMELINE')
print('=' * 74)
print(f'{"Date":<12}{"Fills":>7}{"RealPnL":>11}{"Fees":>9}{"Funding":>10}{"Net":>11}{"Cumul":>11}')
print('-' * 74)
cum = 0
for d in sorted(daily):
    x = daily[d]
    nd = x['pnl'] - x['fees'] + x['funding']
    cum += nd
    print(f'{d:<12}{x["fills"]:>7}{x["pnl"]:>+11.4f}{x["fees"]:>9.4f}{x["funding"]:>+10.4f}{nd:>+11.4f}{cum:>+11.4f}')
