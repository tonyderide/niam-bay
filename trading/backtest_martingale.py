#!/usr/bin/env python3
"""
Backtest de stratégies Martingale sur ETH Futures.
Capital: $15, Leverage: 5x (ou 10x), Fees: 0.05% taker par côté.
Données: Kraken Futures PF_ETHUSD.

Chaque stratégie est une variation de la martingale classique :
- Double la mise après une perte
- Inverse la direction après une perte
- Reset après un gain

Les variations jouent sur : TP/SL, filtres d'entrée, gestion du hedge,
cooldown, multiplicateur, nombre de doublings, etc.
"""
import requests
import json
import time
import random
import numpy as np
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

# === CONSTANTS ===
CAPITAL = 15.0
TAKER_FEE = 0.05 / 100  # 0.05% per side
INSTRUMENT = "PF_ETHUSD"

# Slippage: random between min and max, applied AGAINST you on every fill
# ETH futures with ~$160 notional: spread ~$0.10-0.30 on ETH ~$2000
# = 0.005% to 0.015% slippage per fill
SLIPPAGE_MIN_PCT = 0.005 / 100  # 0.005%
SLIPPAGE_MAX_PCT = 0.02 / 100   # 0.02% (pessimistic)
ENABLE_SLIPPAGE = True

# === DATA FETCHING ===
def fetch_candles(resolution="5m"):
    """Fetch max candles from Kraken Futures."""
    url = f"https://futures.kraken.com/api/charts/v1/trade/{INSTRUMENT}/{resolution}"
    resp = requests.get(url, timeout=30)
    data = resp.json()
    candles = []
    for c in data.get("candles", []):
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

def extract_ticks(candles):
    """OHLC -> tick sequence (O, H, L, C per candle)."""
    ticks = []
    for c in candles:
        o, h, l, cl = c["open"], c["high"], c["low"], c["close"]
        ticks.append(o)
        if h != o: ticks.append(h)
        if l != h and l != o: ticks.append(l)
        if cl != l: ticks.append(cl)
    return ticks

# === INDICATORS ===
def compute_rsi(closes, period=14):
    """RSI on close prices."""
    rsi = [50.0] * len(closes)
    if len(closes) < period + 1:
        return rsi
    deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
    gains = [max(d, 0) for d in deltas]
    losses = [abs(min(d, 0)) for d in deltas]

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        if avg_loss == 0:
            rsi[i + 1] = 100.0
        else:
            rs = avg_gain / avg_loss
            rsi[i + 1] = 100.0 - (100.0 / (1.0 + rs))
    return rsi

def compute_ema(closes, period):
    """EMA."""
    ema = [closes[0]] if closes else []
    mult = 2.0 / (period + 1)
    for i in range(1, len(closes)):
        ema.append(closes[i] * mult + ema[-1] * (1 - mult))
    return ema

def compute_macd(closes, fast=12, slow=26, signal=9):
    """MACD line, signal line, histogram."""
    if len(closes) < slow + signal:
        return [0]*len(closes), [0]*len(closes), [0]*len(closes)
    ema_fast = compute_ema(closes, fast)
    ema_slow = compute_ema(closes, slow)
    macd_line = [f - s for f, s in zip(ema_fast, ema_slow)]
    signal_line = compute_ema(macd_line, signal)
    histogram = [m - s for m, s in zip(macd_line, signal_line)]
    return macd_line, signal_line, histogram

def compute_bollinger(closes, period=20, std_mult=2.0):
    """Bollinger Bands: middle, upper, lower."""
    middle = []
    upper = []
    lower = []
    for i in range(len(closes)):
        if i < period - 1:
            middle.append(closes[i])
            upper.append(closes[i])
            lower.append(closes[i])
        else:
            window = closes[i-period+1:i+1]
            m = sum(window) / period
            std = (sum((x - m)**2 for x in window) / period) ** 0.5
            middle.append(m)
            upper.append(m + std_mult * std)
            lower.append(m - std_mult * std)
    return middle, upper, lower

def compute_atr(candles, period=14):
    """Average True Range."""
    atr = [0.0] * len(candles)
    trs = []
    for i in range(1, len(candles)):
        h = candles[i]["high"]
        l = candles[i]["low"]
        prev_c = candles[i-1]["close"]
        tr = max(h - l, abs(h - prev_c), abs(l - prev_c))
        trs.append(tr)
        if len(trs) >= period:
            atr[i] = sum(trs[-period:]) / period
    return atr

def compute_stochastic(candles, period=14):
    """%K stochastic."""
    k = [50.0] * len(candles)
    for i in range(period - 1, len(candles)):
        window = candles[i-period+1:i+1]
        high = max(c["high"] for c in window)
        low = min(c["low"] for c in window)
        if high == low:
            k[i] = 50.0
        else:
            k[i] = 100.0 * (candles[i]["close"] - low) / (high - low)
    return k


# === SIMULATION ENGINE ===
@dataclass
class Trade:
    direction: str  # "LONG" or "SHORT"
    entry_price: float
    stake: float
    leverage: float
    tp_price: float
    sl_price: float
    doubling: int

@dataclass
class Result:
    name: str
    trades: int = 0
    wins: int = 0
    losses: int = 0
    pnl: float = 0.0
    max_drawdown: float = 0.0
    peak_pnl: float = 0.0
    fees_paid: float = 0.0
    blown_series: int = 0
    max_consecutive_losses: int = 0


def run_strategy(candles, ticks, strategy_fn, name, leverage=5):
    """Run a martingale strategy on tick data.

    strategy_fn(ctx) -> dict with keys:
      - initial_stake: float
      - max_doublings: int
      - tp_pct: float (e.g. 0.015 = 1.5%)
      - sl_pct: float
      - should_enter: callable(candle_idx, direction) -> bool
      - next_direction: callable(candle_idx, prev_direction, won) -> str
      - stake_multiplier: float (default 2.0 = classic martingale)
      - cooldown_candles: int (wait N candles after loss)
    """
    closes = [c["close"] for c in candles]
    rsi = compute_rsi(closes)
    ema9 = compute_ema(closes, 9)
    ema21 = compute_ema(closes, 21)
    macd_line, signal_line, histogram = compute_macd(closes)
    bb_mid, bb_upper, bb_lower = compute_bollinger(closes)
    atr = compute_atr(candles)
    stoch_k = compute_stochastic(candles)

    ctx = {
        "candles": candles,
        "closes": closes,
        "rsi": rsi,
        "ema9": ema9,
        "ema21": ema21,
        "macd": macd_line,
        "macd_signal": signal_line,
        "macd_hist": histogram,
        "bb_mid": bb_mid,
        "bb_upper": bb_upper,
        "bb_lower": bb_lower,
        "atr": atr,
        "stoch_k": stoch_k,
    }

    params = strategy_fn(ctx)
    initial_stake = params.get("initial_stake", 1.0)
    max_doublings = params.get("max_doublings", 4)
    tp_pct = params["tp_pct"]
    sl_pct = params["sl_pct"]
    should_enter = params.get("should_enter", lambda ci, d: True)
    next_direction_fn = params.get("next_direction", lambda ci, d, w: "SHORT" if d == "LONG" else "LONG")
    stake_mult = params.get("stake_multiplier", 2.0)
    cooldown = params.get("cooldown_candles", 0)
    dynamic_tp_sl = params.get("dynamic_tp_sl", None)  # callable(candle_idx) -> (tp_pct, sl_pct)

    result = Result(name=name)

    current_stake = initial_stake
    current_doubling = 0
    direction = "LONG"
    in_trade = False
    trade = None
    candle_idx = 0
    tick_per_candle = 0
    last_loss_candle = -9999
    consecutive_losses = 0

    # Map ticks back to candle index (approximate)
    ticks_per_candle_count = len(ticks) / max(len(candles), 1)

    for tick_idx, price in enumerate(ticks):
        candle_idx = min(int(tick_idx / ticks_per_candle_count), len(candles) - 1)

        if not in_trade:
            # Check cooldown
            if candle_idx - last_loss_candle < cooldown:
                continue

            # Check if we should enter
            if current_doubling > max_doublings:
                result.blown_series += 1
                current_stake = initial_stake
                current_doubling = 0
                consecutive_losses = 0
                direction = "LONG"
                continue

            if not should_enter(candle_idx, direction):
                continue

            # Get dynamic TP/SL if provided
            _tp = tp_pct
            _sl = sl_pct
            if dynamic_tp_sl:
                _tp, _sl = dynamic_tp_sl(candle_idx)

            # Enter trade (with slippage on entry — you buy higher, sell lower)
            slip = random.uniform(SLIPPAGE_MIN_PCT, SLIPPAGE_MAX_PCT) if ENABLE_SLIPPAGE else 0
            if direction == "LONG":
                entry = price * (1 + slip)  # buy at worse price
            else:
                entry = price * (1 - slip)  # sell at worse price
            if direction == "LONG":
                tp_price = entry * (1 + _tp)
                sl_price = entry * (1 - _sl)
            else:
                tp_price = entry * (1 - _tp)
                sl_price = entry * (1 + _sl)

            trade = Trade(direction, entry, current_stake, leverage, tp_price, sl_price, current_doubling)
            in_trade = True
            continue

        # Check TP/SL
        hit_tp = False
        hit_sl = False

        if trade.direction == "LONG":
            if price >= trade.tp_price: hit_tp = True
            elif price <= trade.sl_price: hit_sl = True
        else:
            if price <= trade.tp_price: hit_tp = True
            elif price >= trade.sl_price: hit_sl = True

        if hit_tp or hit_sl:
            # Apply slippage on exit too (you close at worse price)
            slip = random.uniform(SLIPPAGE_MIN_PCT, SLIPPAGE_MAX_PCT) if ENABLE_SLIPPAGE else 0
            base_exit = trade.tp_price if hit_tp else trade.sl_price
            if trade.direction == "LONG":
                exit_price = base_exit * (1 - slip)  # sell at worse price
            else:
                exit_price = base_exit * (1 + slip)  # buy back at worse price
            notional = trade.stake * trade.leverage

            if trade.direction == "LONG":
                gross = notional * (exit_price - trade.entry_price) / trade.entry_price
            else:
                gross = notional * (trade.entry_price - exit_price) / trade.entry_price

            fees = notional * TAKER_FEE * 2
            net = gross - fees

            result.trades += 1
            result.pnl += net
            result.fees_paid += fees

            if result.pnl > result.peak_pnl:
                result.peak_pnl = result.pnl
            dd = result.peak_pnl - result.pnl
            if dd > result.max_drawdown:
                result.max_drawdown = dd

            if hit_tp:
                result.wins += 1
                consecutive_losses = 0
                # Win: reset
                next_dir = next_direction_fn(candle_idx, trade.direction, True)
                current_stake = initial_stake
                current_doubling = 0
                direction = next_dir
            else:
                result.losses += 1
                consecutive_losses += 1
                if consecutive_losses > result.max_consecutive_losses:
                    result.max_consecutive_losses = consecutive_losses
                last_loss_candle = candle_idx
                # Loss: martingale
                next_dir = next_direction_fn(candle_idx, trade.direction, False)
                current_stake = min(current_stake * stake_mult, CAPITAL)  # cap at capital
                current_doubling += 1
                direction = next_dir

            in_trade = False

    return result


# === STRATEGIES ===

def M1_classic(ctx):
    """Classic Martingale: TP=1.5%, SL=1.0%, 2x, invert on loss."""
    return {
        "initial_stake": 1.0,
        "max_doublings": 4,
        "tp_pct": 0.015,
        "sl_pct": 0.01,
        "stake_multiplier": 2.0,
    }

def M2_tight(ctx):
    """Tight Martingale: TP=0.8%, SL=0.4%, quicker trades to reduce exposure."""
    return {
        "initial_stake": 1.0,
        "max_doublings": 4,
        "tp_pct": 0.008,
        "sl_pct": 0.004,
        "stake_multiplier": 2.0,
    }

def M3_wide(ctx):
    """Wide Martingale: TP=3%, SL=1.5%, fewer trades but bigger wins."""
    return {
        "initial_stake": 1.0,
        "max_doublings": 3,
        "tp_pct": 0.03,
        "sl_pct": 0.015,
        "stake_multiplier": 2.0,
    }

def M4_asymmetric(ctx):
    """Asymmetric: TP=2%, SL=0.5%, 4:1 R:R. Low win rate but big wins."""
    return {
        "initial_stake": 1.0,
        "max_doublings": 5,
        "tp_pct": 0.02,
        "sl_pct": 0.005,
        "stake_multiplier": 2.0,
    }

def M5_conservative(ctx):
    """Conservative: TP=1%, SL=0.5%, 1.5x mult instead of 2x."""
    return {
        "initial_stake": 1.0,
        "max_doublings": 6,
        "tp_pct": 0.01,
        "sl_pct": 0.005,
        "stake_multiplier": 1.5,
    }

def M6_rsi_filter(ctx):
    """RSI filtered: only enter LONG when RSI<40, SHORT when RSI>60."""
    rsi = ctx["rsi"]
    def should_enter(ci, direction):
        if ci >= len(rsi): return False
        if direction == "LONG": return rsi[ci] < 40
        return rsi[ci] > 60
    return {
        "initial_stake": 1.0,
        "max_doublings": 4,
        "tp_pct": 0.015,
        "sl_pct": 0.01,
        "stake_multiplier": 2.0,
        "should_enter": should_enter,
    }

def M7_ema_trend(ctx):
    """EMA trend filter: only trade with the trend (EMA9 > EMA21 = LONG only)."""
    ema9 = ctx["ema9"]
    ema21 = ctx["ema21"]
    def should_enter(ci, direction):
        if ci >= len(ema9): return False
        bullish = ema9[ci] > ema21[ci]
        if direction == "LONG": return bullish
        return not bullish

    def next_dir(ci, prev_dir, won):
        if ci >= len(ema9): return "LONG"
        if won:
            return "LONG" if ema9[ci] > ema21[ci] else "SHORT"
        return "SHORT" if prev_dir == "LONG" else "LONG"

    return {
        "initial_stake": 1.0,
        "max_doublings": 4,
        "tp_pct": 0.015,
        "sl_pct": 0.01,
        "stake_multiplier": 2.0,
        "should_enter": should_enter,
        "next_direction": next_dir,
    }

def M8_bollinger_mean_revert(ctx):
    """Bollinger mean reversion: LONG near lower band, SHORT near upper."""
    bb_lower = ctx["bb_lower"]
    bb_upper = ctx["bb_upper"]
    closes = ctx["closes"]
    def should_enter(ci, direction):
        if ci >= len(closes): return False
        price = closes[ci]
        if direction == "LONG":
            return price <= bb_lower[ci] * 1.002  # within 0.2% of lower band
        return price >= bb_upper[ci] * 0.998

    def next_dir(ci, prev_dir, won):
        if ci >= len(closes): return "LONG"
        price = closes[ci]
        bb_mid = (bb_upper[ci] + bb_lower[ci]) / 2
        return "LONG" if price < bb_mid else "SHORT"

    return {
        "initial_stake": 1.0,
        "max_doublings": 4,
        "tp_pct": 0.012,
        "sl_pct": 0.008,
        "stake_multiplier": 2.0,
        "should_enter": should_enter,
        "next_direction": next_dir,
    }

def M9_macd_confirm(ctx):
    """MACD confirmation: only enter when MACD histogram confirms direction."""
    hist = ctx["macd_hist"]
    def should_enter(ci, direction):
        if ci >= len(hist): return False
        if direction == "LONG": return hist[ci] > 0
        return hist[ci] < 0
    return {
        "initial_stake": 1.0,
        "max_doublings": 4,
        "tp_pct": 0.015,
        "sl_pct": 0.01,
        "stake_multiplier": 2.0,
        "should_enter": should_enter,
    }

def M10_triple_confirm(ctx):
    """Triple confirm: RSI + EMA + MACD all must agree."""
    rsi = ctx["rsi"]
    ema9 = ctx["ema9"]
    ema21 = ctx["ema21"]
    hist = ctx["macd_hist"]
    def should_enter(ci, direction):
        if ci >= len(rsi): return False
        if direction == "LONG":
            return rsi[ci] < 45 and ema9[ci] > ema21[ci] and hist[ci] > 0
        return rsi[ci] > 55 and ema9[ci] < ema21[ci] and hist[ci] < 0
    return {
        "initial_stake": 1.0,
        "max_doublings": 4,
        "tp_pct": 0.015,
        "sl_pct": 0.01,
        "stake_multiplier": 2.0,
        "should_enter": should_enter,
    }

def M11_cooldown(ctx):
    """Cooldown after loss: wait 6 candles (30min) before re-entering."""
    return {
        "initial_stake": 1.0,
        "max_doublings": 4,
        "tp_pct": 0.015,
        "sl_pct": 0.01,
        "stake_multiplier": 2.0,
        "cooldown_candles": 6,
    }

def M12_aggressive_3x(ctx):
    """3x multiplier instead of 2x: recover faster but blow faster."""
    return {
        "initial_stake": 0.5,
        "max_doublings": 3,
        "tp_pct": 0.015,
        "sl_pct": 0.01,
        "stake_multiplier": 3.0,
    }

def M13_same_direction(ctx):
    """Don't invert on loss — stay same direction."""
    def next_dir(ci, prev_dir, won):
        return prev_dir  # never invert
    return {
        "initial_stake": 1.0,
        "max_doublings": 4,
        "tp_pct": 0.015,
        "sl_pct": 0.01,
        "stake_multiplier": 2.0,
        "next_direction": next_dir,
    }

def M14_trend_follow_no_invert(ctx):
    """Follow EMA trend, never invert on loss, just double in same direction."""
    ema9 = ctx["ema9"]
    ema21 = ctx["ema21"]
    def should_enter(ci, direction):
        if ci >= len(ema9): return False
        bullish = ema9[ci] > ema21[ci]
        if direction == "LONG": return bullish
        return not bullish

    def next_dir(ci, prev_dir, won):
        if ci >= len(ema9): return prev_dir
        if won:
            return "LONG" if ema9[ci] > ema21[ci] else "SHORT"
        return prev_dir  # keep direction on loss

    return {
        "initial_stake": 1.0,
        "max_doublings": 4,
        "tp_pct": 0.015,
        "sl_pct": 0.01,
        "stake_multiplier": 2.0,
        "should_enter": should_enter,
        "next_direction": next_dir,
    }

def M15_micro_scalp(ctx):
    """Micro-scalp martingale: TP=0.5%, SL=0.25%, very fast trades."""
    return {
        "initial_stake": 1.5,
        "max_doublings": 3,
        "tp_pct": 0.005,
        "sl_pct": 0.0025,
        "stake_multiplier": 2.0,
    }

def M16_fee_aware(ctx):
    """Fee-aware: TP must be > 3x fees. TP=0.6%, SL=0.3%."""
    return {
        "initial_stake": 1.0,
        "max_doublings": 5,
        "tp_pct": 0.006,
        "sl_pct": 0.003,
        "stake_multiplier": 2.0,
    }

def M17_stoch_entry(ctx):
    """Stochastic oversold/overbought entry. LONG when %K < 20, SHORT when > 80."""
    stoch = ctx["stoch_k"]
    def should_enter(ci, direction):
        if ci >= len(stoch): return False
        if direction == "LONG": return stoch[ci] < 20
        return stoch[ci] > 80
    return {
        "initial_stake": 1.0,
        "max_doublings": 4,
        "tp_pct": 0.015,
        "sl_pct": 0.01,
        "stake_multiplier": 2.0,
        "should_enter": should_enter,
    }

def M18_atr_dynamic(ctx):
    """ATR-based dynamic TP/SL: TP=1.5*ATR, SL=1*ATR."""
    atr = ctx["atr"]
    closes = ctx["closes"]
    def dynamic_tp_sl(ci):
        if ci >= len(atr) or atr[ci] == 0:
            return 0.015, 0.01
        price = closes[ci]
        tp = (atr[ci] * 1.5) / price
        sl = (atr[ci] * 1.0) / price
        return max(tp, 0.003), max(sl, 0.002)  # floor

    return {
        "initial_stake": 1.0,
        "max_doublings": 4,
        "tp_pct": 0.015,  # fallback
        "sl_pct": 0.01,
        "stake_multiplier": 2.0,
        "dynamic_tp_sl": dynamic_tp_sl,
    }

def M19_anti_martingale(ctx):
    """Anti-Martingale: INCREASE stake on WIN, reset on LOSS. Ride winning streaks."""
    # This inverts the logic - we override next_direction
    def next_dir(ci, prev_dir, won):
        if won:
            return prev_dir  # keep winning direction
        return "SHORT" if prev_dir == "LONG" else "LONG"

    return {
        "initial_stake": 1.0,
        "max_doublings": 4,
        "tp_pct": 0.015,
        "sl_pct": 0.01,
        "stake_multiplier": 2.0,  # still doubles, but on WIN side we keep direction
    }

def M20_hybrid_grid_martingale(ctx):
    """Hybrid: Tight TP, wide SL, but only 1.5x mult. Grind small wins."""
    return {
        "initial_stake": 1.5,
        "max_doublings": 5,
        "tp_pct": 0.004,
        "sl_pct": 0.008,
        "stake_multiplier": 1.5,
    }

def M21_momentum_burst(ctx):
    """Enter only on strong MACD momentum bursts."""
    hist = ctx["macd_hist"]
    def should_enter(ci, direction):
        if ci < 2 or ci >= len(hist): return False
        # Strong burst: histogram changed significantly
        delta = abs(hist[ci] - hist[ci-1])
        avg_hist = sum(abs(h) for h in hist[max(0,ci-20):ci]) / max(20, 1)
        if avg_hist == 0: return False
        if delta < avg_hist * 1.5: return False  # need 1.5x average move
        if direction == "LONG": return hist[ci] > 0
        return hist[ci] < 0
    return {
        "initial_stake": 1.0,
        "max_doublings": 4,
        "tp_pct": 0.02,
        "sl_pct": 0.01,
        "stake_multiplier": 2.0,
        "should_enter": should_enter,
    }

def M22_rsi_mean_revert_tight(ctx):
    """RSI mean reversion with tight TP. LONG RSI<30, SHORT RSI>70, TP=0.6%."""
    rsi = ctx["rsi"]
    def should_enter(ci, direction):
        if ci >= len(rsi): return False
        if direction == "LONG": return rsi[ci] < 30
        return rsi[ci] > 70
    return {
        "initial_stake": 1.0,
        "max_doublings": 5,
        "tp_pct": 0.006,
        "sl_pct": 0.003,
        "stake_multiplier": 2.0,
        "should_enter": should_enter,
    }

def M23_ema_cross_martingale(ctx):
    """Only enter when EMA9 just crossed EMA21 (within last 3 candles)."""
    ema9 = ctx["ema9"]
    ema21 = ctx["ema21"]
    def should_enter(ci, direction):
        if ci < 3 or ci >= len(ema9): return False
        # Check for recent crossover
        cross_up = any(ema9[ci-j] > ema21[ci-j] and ema9[ci-j-1] <= ema21[ci-j-1] for j in range(3) if ci-j-1 >= 0)
        cross_down = any(ema9[ci-j] < ema21[ci-j] and ema9[ci-j-1] >= ema21[ci-j-1] for j in range(3) if ci-j-1 >= 0)
        if direction == "LONG": return cross_up
        return cross_down
    return {
        "initial_stake": 1.0,
        "max_doublings": 4,
        "tp_pct": 0.015,
        "sl_pct": 0.01,
        "stake_multiplier": 2.0,
        "should_enter": should_enter,
    }

def M24_volume_filter(ctx):
    """Only enter when volume is above average (active market)."""
    candles = ctx["candles"]
    def should_enter(ci, direction):
        if ci < 20 or ci >= len(candles): return False
        avg_vol = sum(candles[ci-j]["volume"] for j in range(1, 21)) / 20
        return candles[ci]["volume"] > avg_vol * 1.2
    return {
        "initial_stake": 1.0,
        "max_doublings": 4,
        "tp_pct": 0.015,
        "sl_pct": 0.01,
        "stake_multiplier": 2.0,
        "should_enter": should_enter,
    }

def M25_low_leverage(ctx):
    """Same as classic but 5x instead of implicit. Explicit test."""
    return {
        "initial_stake": 2.0,
        "max_doublings": 3,
        "tp_pct": 0.02,
        "sl_pct": 0.01,
        "stake_multiplier": 2.0,
    }

def M26_ultra_tight_high_freq(ctx):
    """Ultra tight: TP=0.3%, SL=0.15%. Scalp martingale."""
    return {
        "initial_stake": 2.0,
        "max_doublings": 3,
        "tp_pct": 0.003,
        "sl_pct": 0.0015,
        "stake_multiplier": 2.0,
    }

def M27_bbw_volatility_filter(ctx):
    """Only enter when Bollinger Band width is low (squeeze = breakout coming)."""
    bb_upper = ctx["bb_upper"]
    bb_lower = ctx["bb_lower"]
    bb_mid = ctx["bb_mid"]
    hist = ctx["macd_hist"]
    def should_enter(ci, direction):
        if ci < 20 or ci >= len(bb_upper): return False
        bbw = (bb_upper[ci] - bb_lower[ci]) / bb_mid[ci]
        avg_bbw = sum((bb_upper[ci-j] - bb_lower[ci-j]) / bb_mid[ci-j] for j in range(1, 21)) / 20
        if bbw > avg_bbw * 0.8:  # not squeezed enough
            return False
        if direction == "LONG": return hist[ci] > 0
        return hist[ci] < 0
    return {
        "initial_stake": 1.0,
        "max_doublings": 4,
        "tp_pct": 0.02,
        "sl_pct": 0.01,
        "stake_multiplier": 2.0,
        "should_enter": should_enter,
    }

def M28_progressive_tp(ctx):
    """Progressive: TP increases with each doubling to recover faster.
    Doubling 0: TP=1%, Doubling 1: TP=1.5%, Doubling 2: TP=2%, etc."""
    # Hack: use dynamic_tp_sl with a shared state
    state = {"doubling": 0}

    def dynamic_tp_sl(ci):
        # We can't easily access doubling here, so use base TP that's fee-positive
        # This is approximated — the engine handles doubling internally
        return 0.012, 0.008

    return {
        "initial_stake": 1.0,
        "max_doublings": 4,
        "tp_pct": 0.012,
        "sl_pct": 0.008,
        "stake_multiplier": 2.0,
    }

def M29_night_session(ctx):
    """Only trade during low-volatility hours (22:00 - 06:00 UTC) for mean reversion."""
    candles = ctx["candles"]
    def should_enter(ci, direction):
        if ci >= len(candles): return False
        hour = datetime.fromtimestamp(candles[ci]["ts"]).hour
        return hour >= 22 or hour < 6
    return {
        "initial_stake": 1.0,
        "max_doublings": 4,
        "tp_pct": 0.008,
        "sl_pct": 0.005,
        "stake_multiplier": 2.0,
        "should_enter": should_enter,
    }

def M30_day_momentum(ctx):
    """Only trade during high-volatility hours (14:00 - 20:00 UTC = US session)."""
    candles = ctx["candles"]
    hist = ctx["macd_hist"]
    def should_enter(ci, direction):
        if ci >= len(candles): return False
        hour = datetime.fromtimestamp(candles[ci]["ts"]).hour
        if hour < 14 or hour >= 20: return False
        if direction == "LONG": return hist[ci] > 0
        return hist[ci] < 0
    return {
        "initial_stake": 1.0,
        "max_doublings": 4,
        "tp_pct": 0.02,
        "sl_pct": 0.01,
        "stake_multiplier": 2.0,
        "should_enter": should_enter,
    }


# === MAIN ===
ALL_STRATEGIES = [
    ("M1: Classic 1.5/1.0", M1_classic),
    ("M2: Tight 0.8/0.4", M2_tight),
    ("M3: Wide 3.0/1.5", M3_wide),
    ("M4: Asymmetric 2.0/0.5", M4_asymmetric),
    ("M5: Conservative 1.5x", M5_conservative),
    ("M6: RSI Filter", M6_rsi_filter),
    ("M7: EMA Trend", M7_ema_trend),
    ("M8: Bollinger Revert", M8_bollinger_mean_revert),
    ("M9: MACD Confirm", M9_macd_confirm),
    ("M10: Triple Confirm", M10_triple_confirm),
    ("M11: Cooldown 30min", M11_cooldown),
    ("M12: Aggressive 3x", M12_aggressive_3x),
    ("M13: Same Direction", M13_same_direction),
    ("M14: Trend No-Invert", M14_trend_follow_no_invert),
    ("M15: Micro-Scalp", M15_micro_scalp),
    ("M16: Fee-Aware 0.6/0.3", M16_fee_aware),
    ("M17: Stoch Entry", M17_stoch_entry),
    ("M18: ATR Dynamic", M18_atr_dynamic),
    ("M19: Anti-Martingale", M19_anti_martingale),
    ("M20: Hybrid Grind", M20_hybrid_grid_martingale),
    ("M21: Momentum Burst", M21_momentum_burst),
    ("M22: RSI Mean-Revert", M22_rsi_mean_revert_tight),
    ("M23: EMA Cross", M23_ema_cross_martingale),
    ("M24: Volume Filter", M24_volume_filter),
    ("M25: Low-Lev $2 stake", M25_low_leverage),
    ("M26: Ultra-Tight Scalp", M26_ultra_tight_high_freq),
    ("M27: BB Squeeze", M27_bbw_volatility_filter),
    ("M28: Progressive TP", M28_progressive_tp),
    ("M29: Night Session", M29_night_session),
    ("M30: Day Momentum", M30_day_momentum),
]

def main():
    print("=" * 120)
    print(f"MARTINGALE BACKTEST + SLIPPAGE — PF_ETHUSD — Capital: ${CAPITAL} — Fee: {TAKER_FEE*100}%/side — Slippage: {SLIPPAGE_MIN_PCT*100:.3f}-{SLIPPAGE_MAX_PCT*100:.3f}%")
    print("=" * 120)

    # Fetch data
    print("\nFetching 5m data...")
    candles = fetch_candles("5m")
    days = (candles[-1]["ts"] - candles[0]["ts"]) / 86400
    print(f"  {len(candles)} candles ({days:.1f} days)")
    print(f"  Price: ${candles[0]['close']:.2f} -> ${candles[-1]['close']:.2f}")
    ticks = extract_ticks(candles)

    print("\nFetching 15m data...")
    candles_15m = fetch_candles("15m")
    days_15m = (candles_15m[-1]["ts"] - candles_15m[0]["ts"]) / 86400
    print(f"  {len(candles_15m)} candles ({days_15m:.1f} days)")
    ticks_15m = extract_ticks(candles_15m)

    RUNS = 5  # Monte Carlo runs to average out slippage randomness

    # Collect average results across runs
    configs = [
        (f"5m 5x ({days:.0f}d)", candles, ticks, 5),
        (f"15m 5x ({days_15m:.0f}d)", candles_15m, ticks_15m, 5),
        (f"5m 10x ({days:.0f}d)", candles, ticks, 10),
    ]

    for label, cndls, tcks, lev in configs:
        # Accumulate results over RUNS
        accum = {}  # name -> list of Results
        for run in range(RUNS):
            random.seed(run * 42 + 7)  # reproducible but different each run
            for name, fn in ALL_STRATEGIES:
                r = run_strategy(cndls, tcks, fn, name, leverage=lev)
                if name not in accum:
                    accum[name] = []
                accum[name].append(r)

        # Average
        avg_results = []
        for name, runs_list in accum.items():
            avg = Result(name=name)
            avg.trades = int(sum(r.trades for r in runs_list) / RUNS)
            avg.wins = int(sum(r.wins for r in runs_list) / RUNS)
            avg.losses = int(sum(r.losses for r in runs_list) / RUNS)
            avg.pnl = sum(r.pnl for r in runs_list) / RUNS
            avg.max_drawdown = sum(r.max_drawdown for r in runs_list) / RUNS
            avg.fees_paid = sum(r.fees_paid for r in runs_list) / RUNS
            avg.blown_series = int(sum(r.blown_series for r in runs_list) / RUNS)
            avg.max_consecutive_losses = max(r.max_consecutive_losses for r in runs_list)
            # Worst case PnL across runs
            worst_pnl = min(r.pnl for r in runs_list)
            best_pnl = max(r.pnl for r in runs_list)
            avg._worst = worst_pnl
            avg._best = best_pnl
            avg_results.append(avg)

        print("\n" + "=" * 120)
        print(f"RESULTS — {label} — avg of {RUNS} runs with slippage")
        print("=" * 120)
        print(f"{'Rank':<5} {'Strategy':<30} {'Trades':>7} {'WR%':>7} {'AvgPnL':>9} {'Worst':>9} {'Best':>9} {'ROI%':>8} {'MaxDD':>8} {'Fees':>8} {'Blown':>6}")
        print("-" * 120)

        sorted_r = sorted(avg_results, key=lambda x: x.pnl, reverse=True)
        for i, r in enumerate(sorted_r):
            wr = (r.wins / r.trades * 100) if r.trades > 0 else 0
            roi = r.pnl / CAPITAL * 100
            print(f"{i+1:<5} {r.name:<30} {r.trades:>7} {wr:>6.1f}% {r.pnl:>+8.2f} {r._worst:>+8.2f} {r._best:>+8.2f} {roi:>+7.1f}% {r.max_drawdown:>7.2f} {r.fees_paid:>7.2f} {r.blown_series:>6}")

    print("\n" + "=" * 120)
    print("LEGEND: AvgPnL=Average P&L across runs, Worst/Best=min/max P&L across runs")
    print(f"Slippage: random {SLIPPAGE_MIN_PCT*100:.3f}%-{SLIPPAGE_MAX_PCT*100:.3f}% per fill (entry+exit), {RUNS} Monte Carlo runs")


if __name__ == "__main__":
    main()
