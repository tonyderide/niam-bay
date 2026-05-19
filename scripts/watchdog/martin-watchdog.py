#!/usr/bin/env python3
"""
Martin Watchdog — runs on the Oracle VM via cron every 15 min.
Fetches local Martin state + Kraken OHLC 48h, applies expert-validated triggers,
sends Telegram alert when thresholds cross. 0 LLM tokens.

State file: /home/ubuntu/martin-watchdog.state.json (last alert sent, to avoid spam)
Log file:   /home/ubuntu/martin-watchdog.log (append, rotated manually)

Triggers (first match wins):
  1. Martin API unreachable                 → ABORT-ALERT
  2. BTC close < EMA200                      → WARN-REGIME
  3. Any grid uPnL / capital <= -10%         → ABORT this grid
  4. Any grid lower_bound within 0.5% of 48h low → WARN-CASCADE (near break)
  5. Total uPnL <= -5% AND 0 RT in 8h       → WARN-BLEED
  6. Total portfolio drop >= 3% in 24h      → ABORT-DD

Alerts are de-duplicated per (trigger_name, pair) with a 2h cooldown.
"""
import json
import os
import sys
import time
import urllib.request
import statistics
from datetime import datetime, timezone, timedelta

PORT = 8081
BASE = f"http://localhost:{PORT}"
STATE_FILE = "/home/ubuntu/martin-watchdog.state.json"
LOG_FILE = "/home/ubuntu/martin-watchdog.log"
TELEGRAM_TOKEN = "7913168011:AAG76RsddMBpUnveiEdK2HSk4PQLS7Ab454"
TELEGRAM_CHAT = 6574420846
COOLDOWN_SEC = 2 * 60 * 60  # 2h between duplicate alerts

PAIRS = ['PF_LINKUSD', 'PF_DOTUSD', 'PF_SOLUSD', 'PF_ADAUSD']


def log(msg: str):
    ts = datetime.now(timezone.utc).isoformat()
    line = f"{ts} {msg}\n"
    with open(LOG_FILE, 'a') as f:
        f.write(line)


def fetch_json(url: str, timeout: int = 10):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        return {'__error__': str(e)}


def telegram(msg: str) -> bool:
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = json.dumps({"chat_id": TELEGRAM_CHAT, "text": msg}).encode()
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read()).get('ok', False)
    except Exception as e:
        log(f"telegram_err: {e}")
        return False


def load_state():
    if not os.path.exists(STATE_FILE):
        return {}
    try:
        return json.load(open(STATE_FILE))
    except Exception:
        return {}


def save_state(s):
    tmp = STATE_FILE + '.tmp'
    json.dump(s, open(tmp, 'w'))
    os.replace(tmp, STATE_FILE)


def should_alert(state: dict, key: str) -> bool:
    last = state.get(key, 0)
    return (time.time() - last) > COOLDOWN_SEC


def mark_alert(state: dict, key: str):
    state[key] = time.time()


def fetch_48h_low(pair: str):
    d = fetch_json(f"https://futures.kraken.com/api/charts/v1/trade/{pair}/1h")
    if '__error__' in d:
        return None
    candles = d.get('candles', [])[-48:]
    if not candles:
        return None
    return min(float(c['low']) for c in candles)


def fetch_24h_portfolio_change(state: dict, current_pv: float) -> float:
    now = time.time()
    hist = state.get('pv_history', [])
    hist = [(t, v) for t, v in hist if now - t < 30 * 3600]
    hist.append([now, current_pv])
    state['pv_history'] = hist
    cutoff = now - 24 * 3600
    old = [v for t, v in hist if t <= cutoff]
    if not old:
        return 0.0
    baseline = old[-1]
    return (current_pv - baseline) / baseline * 100 if baseline else 0.0


def main():
    state = load_state()
    alerts = []

    active = fetch_json(f"{BASE}/api/grid/active")
    if '__error__' in active:
        key = 'api_down'
        if should_alert(state, key):
            alerts.append(("ABORT-ALERT", f"Martin API unreachable: {active['__error__']}"))
            mark_alert(state, key)
        save_state(state)
        for lvl, msg in alerts:
            telegram(f"[{lvl}] {msg}")
            log(f"ALERT {lvl}: {msg}")
        return

    balance = fetch_json(f"{BASE}/api/bot/balance")
    signal = fetch_json(f"{BASE}/api/signal/ema_trend?instrument=PF_XBTUSD")

    flex = (balance.get('accounts') or {}).get('flex', {}) if '__error__' not in balance else {}
    pv = flex.get('portfolioValue') or 0.0

    dd24 = fetch_24h_portfolio_change(state, pv)
    if dd24 <= -3.0 and should_alert(state, 'dd_24h'):
        alerts.append(("ABORT-DD", f"Portfolio {pv:.2f}$ | 24h {dd24:+.2f}%"))
        mark_alert(state, 'dd_24h')

    if '__error__' not in signal:
        price = signal.get('price') or 0
        ema200 = signal.get('ema200') or 0
        if price and ema200 and price < ema200 and should_alert(state, 'btc_ema200'):
            delta = (price - ema200) / ema200 * 100
            alerts.append(("WARN-REGIME", f"BTC ${price:.0f} sous EMA200 ${ema200:.0f} ({delta:+.2f}%)"))
            mark_alert(state, 'btc_ema200')

    total_upnl = 0.0
    total_rt_8h = 0
    for p in active or []:
        g = fetch_json(f"{BASE}/api/grid/status/{p}")
        if '__error__' in g or not g:
            continue
        upnl = g.get('krakenUnrealizedPnl') or 0.0
        cap = g.get('capital') or 1
        pct = upnl / cap * 100
        total_upnl += upnl

        if pct <= -10 and should_alert(state, f'grid_loss_{p}'):
            alerts.append(("ABORT-GRID", f"{p}: uPnL {upnl:+.2f}$ ({pct:.1f}% du cap ${cap})"))
            mark_alert(state, f'grid_loss_{p}')

        lower = g.get('lowerBound') or 0
        low48 = fetch_48h_low(p)
        if lower and low48 and low48 > 0:
            proximity = (low48 - lower) / lower * 100
            if 0 < proximity < 0.5 and should_alert(state, f'cascade_{p}'):
                alerts.append(("WARN-CASCADE", f"{p}: 48h low ${low48:.4f} à {proximity:.2f}% du lower ${lower}"))
                mark_alert(state, f'cascade_{p}')

        started = g.get('startedAt')
        rt = g.get('completedRoundTrips') or 0
        if started:
            try:
                t0 = datetime.fromisoformat(started.replace('Z', '+00:00'))
                hours = (datetime.now(timezone.utc) - t0).total_seconds() / 3600
                if hours < 8:
                    total_rt_8h += rt
            except Exception:
                pass

    total_cap = sum((g.get('capital') or 0) for p in (active or []) for g in [fetch_json(f"{BASE}/api/grid/status/{p}")] if g and '__error__' not in g)
    if total_cap > 0:
        total_upnl_pct = total_upnl / total_cap * 100
        if total_upnl_pct <= -5 and total_rt_8h == 0 and should_alert(state, 'bleed'):
            alerts.append(("WARN-BLEED", f"Total uPnL {total_upnl:+.2f}$ ({total_upnl_pct:.1f}%) | 0 RT en 8h sur {len(active)} grids"))
            mark_alert(state, 'bleed')

    save_state(state)

    for lvl, msg in alerts:
        header = f"[{lvl}] {msg}"
        telegram(header)
        log(f"ALERT {lvl}: {msg}")

    if not alerts:
        log(f"ok pv={pv:.2f} upnl={total_upnl:+.2f} 24h={dd24:+.2f}%")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        log(f"CRASH: {e}")
        sys.exit(1)
