#!/usr/bin/env bash
# martin-recap.sh — what happened on Martin since last check
# Consolidates VM critical-check.log + daily-brief.log + morning_brief_v2 + live state
# into a single timeline digest.
#
# Usage:
#   ./scripts/martin-recap.sh           # default 24h gap
#   ./scripts/martin-recap.sh 6         # explicit 6h gap

GAP_HOURS="${1:-24}"
SSH_KEY="${HOME}/.ssh/martin_vm.key"
VM_HOST="ubuntu@141.253.108.141"

GAP_ENTRIES=$(( GAP_HOURS * 12 ))   # critical-check is every 5min
SAMPLE_STEP=12                       # sample ~hourly

RAW=$(ssh -i "${SSH_KEY}" -o StrictHostKeyChecking=no "${VM_HOST}" "
echo '=== CRITICAL_LAST ==='
tail -${GAP_ENTRIES} /home/ubuntu/martin/scripts/critical-check.log | awk 'NR%${SAMPLE_STEP}==0 || \$0 !~ /OK\$/'
echo '=== DAILY_BRIEF_LAST ==='
tail -20 /home/ubuntu/martin/scripts/daily-brief.log
echo '=== MORNING_BRIEF_V2_NEWEST ==='
ls -t /home/ubuntu/docs/morning_brief_*.md 2>/dev/null | head -1 | xargs cat 2>/dev/null || echo '(no morning_brief_v2 today)'
echo '=== LIVE_SYSTEM ==='
curl -s http://localhost:8081/api/system/status
echo
echo '=== LIVE_BALANCE ==='
curl -s http://localhost:8081/api/bot/balance
echo
echo '=== LIVE_GRIDS ==='
curl -s http://localhost:8081/api/grid/active
echo
echo '=== LIVE_BTC ==='
curl -s 'http://localhost:8081/api/signal/ema_trend?instrument=PF_XBTUSD'
" 2>/dev/null)

# Pass RAW via env var to Python for clean parsing
export RAW
GAP_HOURS="${GAP_HOURS}" python3 <<'PYEOF'
import json, os, re
from datetime import datetime, timezone

gap_hours = int(os.environ.get('GAP_HOURS', '24'))
raw = os.environ.get('RAW', '')

def section(name):
    m = re.search(rf'=== {name} ===\n(.*?)(?=\n=== |\Z)', raw, re.DOTALL)
    return m.group(1).strip() if m else ''

def jget(blob, *keys):
    try:
        d = json.loads(blob)
        for k in keys:
            d = d[k]
        return d
    except Exception:
        return None

crit = section('CRITICAL_LAST')
brief = section('DAILY_BRIEF_LAST')
sys_blob = section('LIVE_SYSTEM')
bal_blob = section('LIVE_BALANCE')
grids_blob = section('LIVE_GRIDS')
btc_blob = section('LIVE_BTC')

# Trajectory: parse "YYYY-MM-DD HH:MM:SSZ PV=$135.12, DD=-0.15%"
traj = []
alerts = []
pv_re = re.compile(r'^(\S+ \S+) PV=\$([\d.]+), DD=(-?[\d.]+)%(.*)$')
for line in crit.splitlines():
    m = pv_re.match(line)
    if not m:
        continue
    ts, pv, dd, suffix = m.groups()
    is_ok = 'OK' in suffix or not suffix.strip()
    traj.append((ts, float(pv), float(dd)))
    if not is_ok:
        alerts.append(line)

if len(traj) > 6:
    step = max(1, len(traj) // 6)
    traj_sample = traj[::step][:6]
else:
    traj_sample = traj

delta_str = '(N/A)'
if len(traj) >= 2:
    delta = traj[-1][1] - traj[0][1]
    delta_pct = (delta / traj[0][1]) * 100 if traj[0][1] else 0
    delta_str = f"{delta:+.2f}$ ({delta_pct:+.2f}%)"

matin_ts, matin_msg = None, None
soir_ts, soir_msg = None, None
brief_lines = brief.splitlines()
for i, line in enumerate(brief_lines):
    if 'MATIN' in line and 'sending brief' in line:
        ts_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}Z)', line)
        matin_ts = ts_match.group(1) if ts_match else '?'
        matin_msg = brief_lines[i+1].strip() if i+1 < len(brief_lines) else ''
    elif 'SOIR' in line and 'sending brief' in line:
        ts_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}Z)', line)
        soir_ts = ts_match.group(1) if ts_match else '?'
        soir_msg = brief_lines[i+1].strip() if i+1 < len(brief_lines) else ''

pv_now = jget(bal_blob, 'accounts', 'flex', 'portfolioValue')
bal_now = jget(bal_blob, 'accounts', 'flex', 'balanceValue')
uptime = jget(sys_blob, 'uptime_human')
btc_price = jget(btc_blob, 'price')
btc_trend = jget(btc_blob, 'emaStatus')
btc_rsi = jget(btc_blob, 'rsi')
btc_sig = jget(btc_blob, 'signal')

try:
    grids_arr = json.loads(grids_blob)
    grid_count = len(grids_arr) if isinstance(grids_arr, list) else 0
except Exception:
    grid_count = 0

now_utc = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%MZ')

print(f"# Martin Recap — {now_utc}")
print(f"Gap analysé: {gap_hours}h | sources: critical-check, daily-brief, morning_brief_v2, /api live")
print()
print(f"## Trajectoire PV ({gap_hours}h)")
if traj_sample:
    for ts, pv, dd in traj_sample:
        print(f"- {ts} : ${pv:.2f} (DD {dd:+.2f}%)")
    print(f"Δ{gap_hours}h: {delta_str}")
else:
    print("(pas assez de données critical-check)")
print()
print("## Alertes pendant le gap")
if alerts:
    for a in alerts[:10]:
        print(f"- {a}")
else:
    print("(aucune — que des OK sur le critical-check 5min)")
print()
print("## Dernier brief Tony")
print(f"MATIN ☀️ {matin_ts or '(aucun)'} : {matin_msg or ''}")
print(f"SOIR  🌙 {soir_ts or '(aucun)'} : {soir_msg or ''}")
print()
print("## Maintenant")
pv_str = f"${pv_now:.2f}" if pv_now is not None else '?'
bal_str = f"${bal_now:.2f}" if bal_now is not None else '?'
btc_price_str = f"${btc_price:,.0f}" if btc_price else '?'
btc_rsi_str = f"{btc_rsi:.1f}" if btc_rsi else '?'
print(f"PV {pv_str} / déposé {bal_str} | grids actives {grid_count} | uptime {uptime or '?'}")
print(f"BTC {btc_price_str} — {btc_trend or '?'} RSI {btc_rsi_str} — signal {btc_sig or '?'}")
print()
print("## Lecture")
if grid_count == 0 and not alerts:
    print("- Bot idle, RegimeGate défensive (pas de grids ouvertes). 0 alerte sur le gap.")
    print("- Reco: rien à faire. Si décision live, lance martin-monitor.")
elif alerts:
    print(f"- {len(alerts)} alerte(s) détectée(s) pendant le gap. À investiguer.")
    print("- Reco: lance martin-monitor + lis les lignes non-OK ci-dessus.")
else:
    print(f"- Bot actif ({grid_count} grids), aucune alerte sur le gap.")
    print("- Reco: lance martin-monitor pour vérifier la santé par grid.")
PYEOF
