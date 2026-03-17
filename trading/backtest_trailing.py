#!/usr/bin/env python3
"""
Trailing Martingale Backtest
Idée de Tony : pas de TP fixe. On monte avec le prix, on trail le SL.
Si le prix monte de 5%, le SL monte aussi. On sort que quand ça retrace.
Martingale sur les pertes (le SL initial est touché).

On teste plein de variations :
- Trail distance (0.3% à 2%)
- SL initial (0.3% à 1.5%)
- Activation du trail (immédiat, après +0.3%, après +0.5%, etc.)
- Signaux d'entrée (MACD+Stoch, RSI+Stoch, etc.)
- Martingale mult (1.5x, 2x, 3x)
- Leverage (5x, 10x)

Capital $15, Fee 0.05%/side, Slippage Monte Carlo.
"""
import requests
import random
from datetime import datetime
from dataclasses import dataclass

CAPITAL = 15.0
TAKER_FEE = 0.05 / 100
SLIP_MIN = 0.005 / 100
SLIP_MAX = 0.02 / 100
INSTRUMENT = "PF_ETHUSD"
RUNS = 5

# === DATA & INDICATORS ===
def fetch_candles(resolution="5m"):
    url = f"https://futures.kraken.com/api/charts/v1/trade/{INSTRUMENT}/{resolution}"
    resp = requests.get(url, timeout=30)
    candles = []
    for c in resp.json().get("candles", []):
        candles.append({
            "ts": int(c["time"]) // 1000,
            "open": float(c["open"]),
            "high": float(c["high"]),
            "low": float(c["low"]),
            "close": float(c["close"]),
            "volume": float(c["volume"])
        })
    candles.sort(key=lambda x: x["ts"])
    return candles

def ema(data, period):
    out = [data[0]]
    m = 2.0 / (period + 1)
    for i in range(1, len(data)):
        out.append(data[i] * m + out[-1] * (1 - m))
    return out

def rsi(closes, period=14):
    out = [50.0] * len(closes)
    if len(closes) < period + 1: return out
    deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
    gains = [max(d, 0) for d in deltas]
    losses = [abs(min(d, 0)) for d in deltas]
    ag = sum(gains[:period]) / period
    al = sum(losses[:period]) / period
    for i in range(period, len(deltas)):
        ag = (ag * (period - 1) + gains[i]) / period
        al = (al * (period - 1) + losses[i]) / period
        out[i+1] = 100 - (100 / (1 + ag/al)) if al != 0 else 100
    return out

def macd(closes, fast=12, slow=26, sig=9):
    ef = ema(closes, fast)
    es = ema(closes, slow)
    line = [f - s for f, s in zip(ef, es)]
    signal = ema(line, sig)
    hist = [l - s for l, s in zip(line, signal)]
    return line, signal, hist

def stochastic(candles, period=14):
    k = [50.0] * len(candles)
    for i in range(period - 1, len(candles)):
        w = candles[i-period+1:i+1]
        h = max(c["high"] for c in w)
        l = min(c["low"] for c in w)
        k[i] = 100 * (candles[i]["close"] - l) / (h - l) if h != l else 50
    return k

def adx_indicator(candles, period=14):
    out = [0.0] * len(candles)
    if len(candles) < period * 2: return out
    plus_dm, minus_dm, tr_list = [], [], []
    for i in range(1, len(candles)):
        h, l = candles[i]["high"], candles[i]["low"]
        ph, pl, pc = candles[i-1]["high"], candles[i-1]["low"], candles[i-1]["close"]
        up, down = h - ph, pl - l
        plus_dm.append(up if up > down and up > 0 else 0)
        minus_dm.append(down if down > up and down > 0 else 0)
        tr_list.append(max(h - l, abs(h - pc), abs(l - pc)))
    if len(tr_list) < period: return out
    atr_s = sum(tr_list[:period])
    plus_s = sum(plus_dm[:period])
    minus_s = sum(minus_dm[:period])
    for i in range(period, len(tr_list)):
        atr_s = atr_s - atr_s/period + tr_list[i]
        plus_s = plus_s - plus_s/period + plus_dm[i]
        minus_s = minus_s - minus_s/period + minus_dm[i]
        if atr_s == 0: continue
        pdi = 100 * plus_s / atr_s
        mdi = 100 * minus_s / atr_s
        out[i+1] = 100 * abs(pdi - mdi) / (pdi + mdi) if (pdi + mdi) != 0 else 0
    return out

# === SIGNALS ===
def sig_macd_stoch(ctx, i):
    hist = ctx["macd_hist"]
    k = ctx["stoch_k"]
    if i < 1: return None
    if hist[i] > 0 and hist[i-1] <= 0 and k[i] < 40: return "LONG"
    if hist[i] < 0 and hist[i-1] >= 0 and k[i] > 60: return "SHORT"
    return None

def sig_macd_stoch_adx(ctx, i):
    hist = ctx["macd_hist"]
    k = ctx["stoch_k"]
    a = ctx["adx"]
    if i < 1: return None
    if a[i] < 20: return None
    if hist[i] > 0 and hist[i-1] <= 0 and k[i] < 40: return "LONG"
    if hist[i] < 0 and hist[i-1] >= 0 and k[i] > 60: return "SHORT"
    return None

def sig_rsi_stoch(ctx, i):
    r = ctx["rsi"]
    k = ctx["stoch_k"]
    if r[i] < 30 and k[i] < 30: return "LONG"
    if r[i] > 70 and k[i] > 70: return "SHORT"
    return None

def sig_ema_macd(ctx, i):
    """EMA trend + MACD cross."""
    ef = ctx["ema_fast"]
    es = ctx["ema_slow"]
    hist = ctx["macd_hist"]
    if i < 1: return None
    if ef[i] > es[i] and hist[i] > 0 and hist[i-1] <= 0: return "LONG"
    if ef[i] < es[i] and hist[i] < 0 and hist[i-1] >= 0: return "SHORT"
    return None

def sig_stoch_cross(ctx, i):
    k = ctx["stoch_k"]
    d = ctx["stoch_d"]
    if i < 1: return None
    if k[i] > d[i] and k[i-1] <= d[i-1] and k[i] < 30: return "LONG"
    if k[i] < d[i] and k[i-1] >= d[i-1] and k[i] > 70: return "SHORT"
    return None

def sig_any_trend(ctx, i):
    """Enter with EMA trend, no cross needed. Looser filter = more trades."""
    ef = ctx["ema_fast"]
    es = ctx["ema_slow"]
    hist = ctx["macd_hist"]
    if ef[i] > es[i] and hist[i] > 0: return "LONG"
    if ef[i] < es[i] and hist[i] < 0: return "SHORT"
    return None

SIGNALS = [
    ("MACD+Stoch", sig_macd_stoch),
    ("MACD+Stoch+ADX", sig_macd_stoch_adx),
    ("RSI+Stoch", sig_rsi_stoch),
    ("EMA+MACD", sig_ema_macd),
    ("Stoch Cross", sig_stoch_cross),
    ("Trend (EMA+MACD)", sig_any_trend),
]

# === SIMULATION ===
@dataclass
class Result:
    name: str
    trades: int = 0
    wins: int = 0
    pnl: float = 0.0
    max_drawdown: float = 0.0
    peak: float = 0.0
    fees: float = 0.0
    blown: int = 0
    max_profit_trade: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0


def simulate_trailing(candles, ctx, params, seed=0):
    random.seed(seed)

    sig_fn = params["signal"]
    trail_pct = params["trail_pct"]        # trailing stop distance (e.g. 0.01 = 1%)
    sl_initial = params["sl_initial"]      # initial SL before trail activates
    trail_activate = params["trail_activate"]  # activate trail after this much profit (0 = immediate)
    trail_tight = params.get("trail_tight", None)  # tighter trail once in profit (e.g. 0.005 = 0.5%)
    leverage = params["leverage"]
    initial_stake = params["stake"]
    mult = params["mult"]
    max_d = params["max_doublings"]
    cooldown = params.get("cooldown", 0)

    r = Result(name=params["name"])
    current_stake = initial_stake
    current_doubling = 0
    in_trade = False
    direction = None
    entry_price = 0.0
    sl_price = 0.0
    best_price = 0.0  # best price since entry (for trailing)
    trailing_active = False
    last_loss_i = -9999
    win_pnls = []
    loss_pnls = []

    for i in range(50, len(candles)):
        c = candles[i]

        if not in_trade:
            if i - last_loss_i < cooldown:
                continue
            if current_doubling > max_d:
                r.blown += 1
                current_stake = initial_stake
                current_doubling = 0
                continue

            sig = sig_fn(ctx, i)
            if sig is None:
                continue

            direction = sig
            slip = random.uniform(SLIP_MIN, SLIP_MAX)
            if direction == "LONG":
                entry_price = c["close"] * (1 + slip)
                sl_price = entry_price * (1 - sl_initial)
                best_price = entry_price
            else:
                entry_price = c["close"] * (1 - slip)
                sl_price = entry_price * (1 + sl_initial)
                best_price = entry_price
            trailing_active = False
            in_trade = True
            continue

        # Update best price and trailing stop
        if direction == "LONG":
            # Use high of candle for best price tracking
            candle_best = c["high"]
            if candle_best > best_price:
                best_price = candle_best

            # Check if trail should activate
            profit_pct = (best_price - entry_price) / entry_price
            if profit_pct >= trail_activate:
                trailing_active = True

            # Update trailing SL
            if trailing_active:
                # Use tighter trail once in profit
                in_profit = best_price > entry_price
                active_trail = trail_tight if (trail_tight and in_profit) else trail_pct
                new_sl = best_price * (1 - active_trail)
                if new_sl > sl_price:
                    sl_price = new_sl

            # Check SL hit
            if c["low"] <= sl_price:
                # Exit
                slip = random.uniform(SLIP_MIN, SLIP_MAX)
                exit_price = sl_price * (1 - slip)
                notional = current_stake * leverage
                gross = notional * (exit_price - entry_price) / entry_price
                fee = notional * TAKER_FEE * 2
                net = gross - fee

                r.trades += 1
                r.pnl += net
                r.fees += fee
                if r.pnl > r.peak: r.peak = r.pnl
                dd = r.peak - r.pnl
                if dd > r.max_drawdown: r.max_drawdown = dd

                if net > r.max_profit_trade:
                    r.max_profit_trade = net

                if net > 0:
                    r.wins += 1
                    win_pnls.append(net)
                    current_stake = initial_stake
                    current_doubling = 0
                else:
                    loss_pnls.append(net)
                    last_loss_i = i
                    current_stake = min(current_stake * mult, CAPITAL)
                    current_doubling += 1
                    # Invert direction on loss
                    direction = "SHORT" if direction == "LONG" else "LONG"

                in_trade = False

        else:  # SHORT
            candle_best = c["low"]
            if candle_best < best_price:
                best_price = candle_best

            profit_pct = (entry_price - best_price) / entry_price
            if profit_pct >= trail_activate:
                trailing_active = True

            if trailing_active:
                in_profit = best_price < entry_price
                active_trail = trail_tight if (trail_tight and in_profit) else trail_pct
                new_sl = best_price * (1 + active_trail)
                if new_sl < sl_price:
                    sl_price = new_sl

            if c["high"] >= sl_price:
                slip = random.uniform(SLIP_MIN, SLIP_MAX)
                exit_price = sl_price * (1 + slip)
                notional = current_stake * leverage
                gross = notional * (entry_price - exit_price) / entry_price
                fee = notional * TAKER_FEE * 2
                net = gross - fee

                r.trades += 1
                r.pnl += net
                r.fees += fee
                if r.pnl > r.peak: r.peak = r.pnl
                dd = r.peak - r.pnl
                if dd > r.max_drawdown: r.max_drawdown = dd

                if net > r.max_profit_trade:
                    r.max_profit_trade = net

                if net > 0:
                    r.wins += 1
                    win_pnls.append(net)
                    current_stake = initial_stake
                    current_doubling = 0
                else:
                    loss_pnls.append(net)
                    last_loss_i = i
                    current_stake = min(current_stake * mult, CAPITAL)
                    current_doubling += 1
                    direction = "LONG" if direction == "SHORT" else "SHORT"

                in_trade = False

    r.avg_win = sum(win_pnls) / len(win_pnls) if win_pnls else 0
    r.avg_loss = sum(loss_pnls) / len(loss_pnls) if loss_pnls else 0
    return r


# === CONFIGS ===
# (name, trail_pct, sl_initial, trail_activate, stake, mult, max_d, leverage, cooldown, trail_tight)
TRAIL_CONFIGS = [
    # Tight trails
    ("T0.3% act0 SL0.5%",    0.003, 0.005, 0.0,   1.0, 2.0, 4, 5, 0, None),
    ("T0.5% act0 SL0.5%",    0.005, 0.005, 0.0,   1.0, 2.0, 4, 5, 0, None),
    ("T0.7% act0 SL0.5%",    0.007, 0.005, 0.0,   1.0, 2.0, 4, 5, 0, None),
    ("T1.0% act0 SL0.5%",    0.010, 0.005, 0.0,   1.0, 2.0, 4, 5, 0, None),
    ("T1.0% act0 SL1.0%",    0.010, 0.010, 0.0,   1.0, 2.0, 4, 5, 0, None),
    ("T1.5% act0 SL0.5%",    0.015, 0.005, 0.0,   1.0, 2.0, 4, 5, 0, None),
    ("T2.0% act0 SL0.5%",    0.020, 0.005, 0.0,   1.0, 2.0, 4, 5, 0, None),

    # Delayed activation
    ("T0.5% act0.3 SL0.5%",  0.005, 0.005, 0.003, 1.0, 2.0, 4, 5, 0, None),
    ("T0.5% act0.5 SL0.5%",  0.005, 0.005, 0.005, 1.0, 2.0, 4, 5, 0, None),
    ("T0.7% act0.5 SL0.5%",  0.007, 0.005, 0.005, 1.0, 2.0, 4, 5, 0, None),
    ("T1.0% act0.5 SL0.5%",  0.010, 0.005, 0.005, 1.0, 2.0, 4, 5, 0, None),
    ("T1.0% act1.0 SL0.5%",  0.010, 0.005, 0.010, 1.0, 2.0, 4, 5, 0, None),
    ("T0.5% act0.3 SL1.0%",  0.005, 0.010, 0.003, 1.0, 2.0, 4, 5, 0, None),
    ("T1.0% act0.5 SL1.0%",  0.010, 0.010, 0.005, 1.0, 2.0, 4, 5, 0, None),

    # 10x leverage
    ("T0.5% act0 SL0.5% x10",   0.005, 0.005, 0.0,   1.0, 2.0, 4, 10, 0, None),
    ("T0.7% act0 SL0.5% x10",   0.007, 0.005, 0.0,   1.0, 2.0, 4, 10, 0, None),
    ("T1.0% act0 SL0.5% x10",   0.010, 0.005, 0.0,   1.0, 2.0, 4, 10, 0, None),
    ("T0.5% act0.3 SL0.5 x10",  0.005, 0.005, 0.003, 1.0, 2.0, 4, 10, 0, None),
    ("T0.7% act0.5 SL0.5 x10",  0.007, 0.005, 0.005, 1.0, 2.0, 4, 10, 0, None),
    ("T1.0% act0.5 SL0.5 x10",  0.010, 0.005, 0.005, 1.0, 2.0, 4, 10, 0, None),
    ("T1.0% act1.0 SL0.5 x10",  0.010, 0.005, 0.010, 1.0, 2.0, 4, 10, 0, None),

    # 3x martingale
    ("T0.5% act0 SL0.5% 3x",    0.005, 0.005, 0.0,   1.0, 3.0, 3, 5, 0, None),
    ("T0.7% act0 SL0.5% 3x",    0.007, 0.005, 0.0,   1.0, 3.0, 3, 5, 0, None),
    ("T1.0% act0.5 SL0.5 3x",   0.010, 0.005, 0.005, 1.0, 3.0, 3, 5, 0, None),
    ("T0.7% act0.5 SL0.5 3x10", 0.007, 0.005, 0.005, 1.0, 3.0, 3, 10, 0, None),
    ("T1.0% act0.5 SL0.5 3x10", 0.010, 0.005, 0.005, 1.0, 3.0, 3, 10, 0, None),

    # $2 stake
    ("T0.7% act0 SL0.5% $2",    0.007, 0.005, 0.0,   2.0, 2.0, 3, 5, 0, None),
    ("T1.0% act0.5 SL0.5 $2",   0.010, 0.005, 0.005, 2.0, 2.0, 3, 5, 0, None),
    ("T0.7% act0 SL0.5 $2x10",  0.007, 0.005, 0.0,   2.0, 2.0, 3, 10, 0, None),
    ("T1.0% act0.5 SL0.5 $2x10",0.010, 0.005, 0.005, 2.0, 2.0, 3, 10, 0, None),

    # With cooldown
    ("T0.7% act0 SL0.5% cool3", 0.007, 0.005, 0.0,   1.0, 2.0, 4, 5, 3, None),
    ("T1.0% act0.5 SL0.5 cool3",0.010, 0.005, 0.005, 1.0, 2.0, 4, 5, 3, None),

    # Wide SL for breathing room
    ("T0.5% act0 SL1.5%",    0.005, 0.015, 0.0,   1.0, 2.0, 4, 5, 0, None),
    ("T1.0% act0 SL1.5%",    0.010, 0.015, 0.0,   1.0, 2.0, 4, 5, 0, None),
    ("T1.0% act0.5 SL1.5%",  0.010, 0.015, 0.005, 1.0, 2.0, 4, 5, 0, None),
    ("T1.0% act0.5 SL1.5x10",0.010, 0.015, 0.005, 1.0, 2.0, 4, 10, 0, None),

    # === TONY'S IDEA: trail 1% initial, tighten to 0.5% once in profit ===
    ("T1%→0.5% act0 SL1%",      0.010, 0.010, 0.0,   1.0, 2.0, 4, 5, 0, 0.005),
    ("T1%→0.5% act0 SL1% x10",  0.010, 0.010, 0.0,   1.0, 2.0, 4, 10, 0, 0.005),
    ("T1%→0.5% act0.3 SL1%",    0.010, 0.010, 0.003, 1.0, 2.0, 4, 5, 0, 0.005),
    ("T1%→0.5% act0.3 SL1 x10", 0.010, 0.010, 0.003, 1.0, 2.0, 4, 10, 0, 0.005),
    ("T1%→0.5% act0.5 SL1%",    0.010, 0.010, 0.005, 1.0, 2.0, 4, 5, 0, 0.005),
    ("T1%→0.5% act0.5 SL1 x10", 0.010, 0.010, 0.005, 1.0, 2.0, 4, 10, 0, 0.005),
    ("T1%→0.5% act0 SL0.5%",    0.010, 0.005, 0.0,   1.0, 2.0, 4, 5, 0, 0.005),
    ("T1%→0.5% act0 SL0.5 x10", 0.010, 0.005, 0.0,   1.0, 2.0, 4, 10, 0, 0.005),
    ("T1%→0.3% act0 SL1%",      0.010, 0.010, 0.0,   1.0, 2.0, 4, 5, 0, 0.003),
    ("T1%→0.3% act0 SL1% x10",  0.010, 0.010, 0.0,   1.0, 2.0, 4, 10, 0, 0.003),
    # With 3x mult
    ("T1%→0.5% act0 SL1% 3x",   0.010, 0.010, 0.0,   1.0, 3.0, 3, 5, 0, 0.005),
    ("T1%→0.5% act0 SL1% 3x10", 0.010, 0.010, 0.0,   1.0, 3.0, 3, 10, 0, 0.005),
    # $2 stake
    ("T1%→0.5% act0 SL1% $2",   0.010, 0.010, 0.0,   2.0, 2.0, 3, 5, 0, 0.005),
    ("T1%→0.5% act0 SL1% $2x10",0.010, 0.010, 0.0,   2.0, 2.0, 3, 10, 0, 0.005),
    # Wider initial SL
    ("T1%→0.5% act0 SL1.5%",    0.010, 0.015, 0.0,   1.0, 2.0, 4, 5, 0, 0.005),
    ("T1%→0.5% act0 SL1.5 x10", 0.010, 0.015, 0.0,   1.0, 2.0, 4, 10, 0, 0.005),
]


def main():
    print("Fetching data...")
    candles_5m = fetch_candles("5m")
    candles_15m = fetch_candles("15m")
    d5 = (candles_5m[-1]["ts"] - candles_5m[0]["ts"]) / 86400
    d15 = (candles_15m[-1]["ts"] - candles_15m[0]["ts"]) / 86400
    print(f"5m: {len(candles_5m)} candles ({d5:.1f}d) | 15m: {len(candles_15m)} candles ({d15:.1f}d)")

    total = len(SIGNALS) * len(TRAIL_CONFIGS)
    print(f"\n{total} combos × 2 timeframes × {RUNS} MC runs = {total * 2 * RUNS} simulations")

    candles_1h = fetch_candles("1h")
    d1h = (candles_1h[-1]["ts"] - candles_1h[0]["ts"]) / 86400
    print(f"1h: {len(candles_1h)} candles ({d1h:.1f}d)")

    for label, candles, days in [("1h", candles_1h, d1h), ("15m", candles_15m, d15), ("5m", candles_5m, d5)]:
        # Compute indicators once
        closes = [c["close"] for c in candles]
        _rsi = rsi(closes)
        _macd_l, _macd_s, _macd_h = macd(closes)
        _stoch_k = stochastic(candles)
        _stoch_d = ema(_stoch_k, 3)
        _ema_f = ema(closes, 9)
        _ema_s = ema(closes, 21)
        _adx = adx_indicator(candles)

        ctx = {
            "rsi": _rsi, "macd_hist": _macd_h, "macd_line": _macd_l, "macd_signal": _macd_s,
            "stoch_k": _stoch_k, "stoch_d": _stoch_d,
            "ema_fast": _ema_f, "ema_slow": _ema_s,
            "adx": _adx, "candles": candles, "closes": closes,
        }

        all_results = []

        for sig_name, sig_fn in SIGNALS:
            for cfg_name, trail, sl_init, act, stake, mult, maxd, lev, cool, tight in TRAIL_CONFIGS:
                params = {
                    "name": f"{sig_name} | {cfg_name}",
                    "signal": sig_fn,
                    "trail_pct": trail, "sl_initial": sl_init, "trail_activate": act,
                    "trail_tight": tight,
                    "stake": stake, "mult": mult, "max_doublings": maxd,
                    "leverage": lev, "cooldown": cool,
                }

                run_results = []
                for run in range(RUNS):
                    r = simulate_trailing(candles, ctx, params, seed=run*42+7)
                    run_results.append(r)

                avg_pnl = sum(r.pnl for r in run_results) / RUNS
                worst = min(r.pnl for r in run_results)
                best = max(r.pnl for r in run_results)
                avg_trades = sum(r.trades for r in run_results) / RUNS
                avg_wins = sum(r.wins for r in run_results) / RUNS
                avg_dd = sum(r.max_drawdown for r in run_results) / RUNS
                avg_fees = sum(r.fees for r in run_results) / RUNS
                avg_blown = sum(r.blown for r in run_results) / RUNS
                max_profit = max(r.max_profit_trade for r in run_results)
                avg_avg_win = sum(r.avg_win for r in run_results) / RUNS
                avg_avg_loss = sum(r.avg_loss for r in run_results) / RUNS

                if avg_trades >= 3:
                    all_results.append({
                        "name": f"{sig_name} | {cfg_name}",
                        "signal": sig_name,
                        "config": cfg_name,
                        "trades": avg_trades,
                        "wr": avg_wins / avg_trades * 100 if avg_trades else 0,
                        "pnl": avg_pnl, "worst": worst, "best": best,
                        "roi": avg_pnl / CAPITAL * 100,
                        "dd": avg_dd, "fees": avg_fees, "blown": avg_blown,
                        "max_win": max_profit,
                        "avg_win": avg_avg_win,
                        "avg_loss": avg_avg_loss,
                    })

        all_results.sort(key=lambda x: x["pnl"], reverse=True)

        print(f"\n{'='*160}")
        print(f"TOP 40 TRAILING MARTINGALE — {label} ({days:.0f}d) — {RUNS} MC runs")
        print(f"{'='*160}")
        print(f"{'#':<4} {'Signal':<18} {'Config':<26} {'Tr':>5} {'WR%':>6} {'AvgPnL':>8} {'Worst':>8} {'Best':>8} {'ROI%':>7} {'MaxDD':>7} {'Fees':>6} {'Blwn':>5} {'MaxWin':>7} {'AvgW':>7} {'AvgL':>7}")
        print("-" * 160)

        for i, r in enumerate(all_results[:40]):
            print(f"{i+1:<4} {r['signal']:<18} {r['config']:<26} {r['trades']:>5.0f} {r['wr']:>5.1f}% {r['pnl']:>+7.2f} {r['worst']:>+7.2f} {r['best']:>+7.2f} {r['roi']:>+6.1f}% {r['dd']:>6.2f} {r['fees']:>5.2f} {r['blown']:>4.0f} {r['max_win']:>+6.2f} {r['avg_win']:>+6.3f} {r['avg_loss']:>+6.3f}")

        # Robust
        robust = sorted([r for r in all_results if r["worst"] > 0], key=lambda x: x["worst"], reverse=True)
        if robust:
            print(f"\n{'='*160}")
            print(f"TOP 20 ROBUST (worst > 0) — {label}")
            print(f"{'='*160}")
            print(f"{'#':<4} {'Signal':<18} {'Config':<26} {'Tr':>5} {'WR%':>6} {'AvgPnL':>8} {'Worst':>8} {'Best':>8} {'ROI%':>7} {'MaxDD':>7} {'MaxWin':>7} {'AvgW':>7}")
            print("-" * 160)
            for i, r in enumerate(robust[:20]):
                print(f"{i+1:<4} {r['signal']:<18} {r['config']:<26} {r['trades']:>5.0f} {r['wr']:>5.1f}% {r['pnl']:>+7.2f} {r['worst']:>+7.2f} {r['best']:>+7.2f} {r['roi']:>+6.1f}% {r['dd']:>6.2f} {r['max_win']:>+6.2f} {r['avg_win']:>+6.3f}")

        # Best per signal
        print(f"\n  BEST PER SIGNAL — {label}:")
        seen = set()
        for r in all_results:
            if r["signal"] not in seen:
                seen.add(r["signal"])
                print(f"    {r['signal']:<18} → {r['config']:<26} PnL={r['pnl']:>+7.2f} ROI={r['roi']:>+6.1f}% WR={r['wr']:.1f}% MaxWin={r['max_win']:>+6.2f}")

    print("\nDone.")

if __name__ == "__main__":
    main()
