#!/usr/bin/env python3
"""
Backtest Martin Grid ADAPTATIF sur BTC/USD
Le grid switch automatiquement entre SHORT, NEUTRAL, LONG selon le regime de marche.

Regime detection basee sur :
- EMA 20/50 cross (direction)
- RSI 14 (momentum)
- Changement 24h (tendance recente)

Inspiré de docs/pensees/2026-03-29-adaptive-algorithm.md
"""

import csv
import json
import math
from collections import defaultdict
from datetime import datetime, timedelta

# === 1. LOAD DATA ===

def load_csv_candles(filepath):
    candles = []
    with open(filepath) as f:
        reader = csv.DictReader(f)
        for row in reader:
            candles.append({
                "time": datetime.strptime(row["timestamp"], "%Y-%m-%d %H:%M:%S"),
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": float(row["volume"]),
            })
    return candles


# === 2. INDICATORS ===

def calc_ema(prices, period):
    """Calculate EMA for a list of prices. Returns list of same length (NaN-padded)."""
    if len(prices) < period:
        return [None] * len(prices)

    ema = [None] * (period - 1)
    # SMA as seed
    sma = sum(prices[:period]) / period
    ema.append(sma)

    multiplier = 2 / (period + 1)
    for i in range(period, len(prices)):
        val = prices[i] * multiplier + ema[-1] * (1 - multiplier)
        ema.append(val)

    return ema


def calc_rsi(prices, period=14):
    """Calculate RSI. Returns list of same length (None-padded)."""
    if len(prices) < period + 1:
        return [None] * len(prices)

    rsi = [None] * period

    # Initial average gain/loss
    gains = []
    losses = []
    for i in range(1, period + 1):
        change = prices[i] - prices[i-1]
        gains.append(max(change, 0))
        losses.append(max(-change, 0))

    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period

    if avg_loss == 0:
        rsi.append(100.0)
    else:
        rs = avg_gain / avg_loss
        rsi.append(100 - (100 / (1 + rs)))

    for i in range(period + 1, len(prices)):
        change = prices[i] - prices[i-1]
        gain = max(change, 0)
        loss = max(-change, 0)

        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period

        if avg_loss == 0:
            rsi.append(100.0)
        else:
            rs = avg_gain / avg_loss
            rsi.append(100 - (100 / (1 + rs)))

    return rsi


def calc_volatility(prices, window=96):
    """Calculate rolling volatility (std of returns) over window candles.
    For 15min candles, 96 = 24 hours."""
    vol = [None] * window
    for i in range(window, len(prices)):
        returns = []
        for j in range(i - window + 1, i + 1):
            if prices[j-1] > 0:
                returns.append((prices[j] - prices[j-1]) / prices[j-1])
        if returns:
            mean_r = sum(returns) / len(returns)
            variance = sum((r - mean_r) ** 2 for r in returns) / len(returns)
            # Annualize: sqrt(periods_per_day) * std
            # 15min candles: 96 per day
            vol.append(math.sqrt(variance) * math.sqrt(96) * 100)  # in %
        else:
            vol.append(None)
    return vol


# === 3. REGIME DETECTION ===

class RegimeDetector:
    """
    Detect market regime based on indicators.

    Modes:
    - CASH: volatility too high (>5%) or no clear signal
    - SHORT: bearish (price < EMA50, RSI < 40, 24h change < -2%)
    - LONG: bullish (price > EMA20, RSI > 50, EMA20 > EMA50, 24h change > +1%)
    - NEUTRAL: range (low volatility, RSI 40-60, price between EMAs)

    Anti-whipsaw: hysteresis + cooldown + confirmation counter
    """

    # Hysteresis thresholds
    ENTER_BEAR_RSI = 40
    EXIT_BEAR_RSI = 45
    ENTER_BULL_RSI = 55
    EXIT_BULL_RSI = 48
    ENTER_RANGE_VOL_MAX = 3.0
    EXIT_RANGE_VOL = 4.0
    CASH_VOL_ENTER = 6.0
    CASH_VOL_EXIT = 4.5

    # Cooldown: minimum candles in one mode before switching
    # 15min candles: 8 = 2 hours
    MIN_MODE_CANDLES = 8

    # Confirmation: need N consecutive signals
    CONFIRMATIONS_REQUIRED = 3

    def __init__(self):
        self.current_mode = "NEUTRAL"
        self.mode_since_candle = 0
        self.candidate_mode = None
        self.candidate_count = 0
        self.switch_log = []

    def detect_raw(self, price, ema20, ema50, rsi, vol_24h, change_24h):
        """Raw regime detection without anti-whipsaw."""

        # CASH: extreme volatility
        if vol_24h is not None and vol_24h > self.CASH_VOL_ENTER:
            return "CASH"

        # BEAR: price below EMA50, RSI bearish, negative momentum
        if (ema50 is not None and price < ema50
            and rsi is not None and rsi < self.ENTER_BEAR_RSI
            and change_24h is not None and change_24h < -1.5):
            if change_24h is not None and change_24h < -5.0:
                return "CASH"  # crash = stay out
            return "SHORT"

        # BULL: price above EMA20, RSI bullish, golden cross, positive momentum
        if (ema20 is not None and ema50 is not None
            and price > ema20 and ema20 > ema50
            and rsi is not None and rsi > self.ENTER_BULL_RSI
            and change_24h is not None and change_24h > 0.5):
            return "LONG"

        # RANGE: low volatility, neutral RSI, price between EMAs
        if (vol_24h is not None and vol_24h < self.ENTER_RANGE_VOL_MAX
            and rsi is not None and 40 <= rsi <= 60
            and ema20 is not None and ema50 is not None):
            ema_low = min(ema20, ema50) * 0.995
            ema_high = max(ema20, ema50) * 1.005
            if ema_low <= price <= ema_high and change_24h is not None and abs(change_24h) < 2.0:
                return "NEUTRAL"

        # Default: keep current mode, or NEUTRAL if no signal
        return None  # no strong signal

    def should_exit_current(self, price, ema20, ema50, rsi, vol_24h, change_24h):
        """Check if we should exit current mode (relaxed thresholds = hysteresis)."""
        mode = self.current_mode

        if mode == "CASH":
            return vol_24h is not None and vol_24h < self.CASH_VOL_EXIT

        if mode == "SHORT":
            return (rsi is not None and rsi > self.EXIT_BEAR_RSI) or (change_24h is not None and change_24h > -0.5)

        if mode == "LONG":
            return (rsi is not None and rsi < self.EXIT_BULL_RSI) or (change_24h is not None and change_24h < 0.0)

        if mode == "NEUTRAL":
            return (vol_24h is not None and vol_24h > self.EXIT_RANGE_VOL) or (change_24h is not None and abs(change_24h) > 3.0)

        return False

    def update(self, candle_idx, price, ema20, ema50, rsi, vol_24h, change_24h):
        """Full update with anti-whipsaw. Returns current mode."""

        raw_signal = self.detect_raw(price, ema20, ema50, rsi, vol_24h, change_24h)

        # If no clear signal, keep current mode
        if raw_signal is None:
            self.candidate_mode = None
            self.candidate_count = 0
            return self.current_mode

        # If signal matches current mode, reset candidate
        if raw_signal == self.current_mode:
            self.candidate_mode = None
            self.candidate_count = 0
            return self.current_mode

        # Exception: CASH is immediate (survival)
        if raw_signal == "CASH" and self.current_mode != "CASH":
            old = self.current_mode
            self.current_mode = "CASH"
            self.mode_since_candle = candle_idx
            self.candidate_mode = None
            self.candidate_count = 0
            self.switch_log.append((candle_idx, old, "CASH", "EMERGENCY"))
            return self.current_mode

        # Check exit conditions (hysteresis)
        should_exit = self.should_exit_current(price, ema20, ema50, rsi, vol_24h, change_24h)
        if not should_exit:
            return self.current_mode

        # Cooldown check
        candles_in_mode = candle_idx - self.mode_since_candle
        if candles_in_mode < self.MIN_MODE_CANDLES:
            return self.current_mode

        # Confirmation check
        if raw_signal == self.candidate_mode:
            self.candidate_count += 1
        else:
            self.candidate_mode = raw_signal
            self.candidate_count = 1

        if self.candidate_count >= self.CONFIRMATIONS_REQUIRED:
            old = self.current_mode
            self.current_mode = raw_signal
            self.mode_since_candle = candle_idx
            self.candidate_mode = None
            self.candidate_count = 0
            self.switch_log.append((candle_idx, old, raw_signal, "CONFIRMED"))
            return self.current_mode

        return self.current_mode


# === 4. ADAPTIVE GRID SIMULATION ===

MAKER_FEE = 0.0002
TAKER_FEE = 0.0005
FEE_PER_RT = MAKER_FEE + TAKER_FEE

def simulate_adaptive_grid(candles, capital, leverage, num_levels, base_spacing_pct,
                            max_loss_pct=15, mode_override=None):
    """
    Simulate Martin Grid with adaptive mode switching.

    If mode_override is set ("SHORT"/"NEUTRAL"/"LONG"), use fixed mode (for comparison).
    Otherwise, use RegimeDetector to switch dynamically.
    """
    if not candles or num_levels < 2:
        return None

    # Precompute indicators
    closes = [c["close"] for c in candles]
    ema20 = calc_ema(closes, 20)
    ema50 = calc_ema(closes, 50)
    rsi14 = calc_rsi(closes, 14)
    vol24 = calc_volatility(closes, 96)  # 96 x 15min = 24h

    # 24h change: look back 96 candles
    change_24h_list = [None] * 96
    for i in range(96, len(closes)):
        change_24h_list.append((closes[i] - closes[i-96]) / closes[i-96] * 100)

    # State
    detector = RegimeDetector()
    if mode_override:
        detector.current_mode = mode_override

    equity = capital
    peak_equity = capital
    max_drawdown_pct = 0.0
    total_pnl = 0.0
    round_trips = 0
    wins = 0
    losses = 0
    open_positions = []
    daily_pnl = defaultdict(float)
    equity_curve = []
    recenterings = 0
    mode_switches = 0
    stopped = False

    current_grid_mode = mode_override or "NEUTRAL"
    grid_center = None
    grid_low = None
    grid_high = None
    grid_levels = []
    filled_buys = set()
    filled_sells = set()
    spacing = 0.0

    mode_time = defaultdict(int)  # candles spent in each mode
    mode_pnl = defaultdict(float)

    def build_grid(center, spac_pct):
        nonlocal grid_center, grid_low, grid_high, grid_levels, filled_buys, filled_sells, spacing
        spacing = center * spac_pct / 100
        grid_center = center
        grid_low = center - spacing * num_levels / 2
        grid_high = center + spacing * num_levels / 2
        grid_levels = []
        for i in range(num_levels + 1):
            grid_levels.append(grid_low + i * spacing)
        grid_levels.sort()
        filled_buys = set()
        filled_sells = set()

    def close_all_positions(price, day_key, reason=""):
        nonlocal total_pnl, equity, round_trips, wins, losses, recenterings
        for pos in open_positions:
            side, entry_price, size_usd = pos
            if side == "long":
                pnl_gross = (price - entry_price) / entry_price * size_usd
            else:
                pnl_gross = (entry_price - price) / entry_price * size_usd
            fee = size_usd * FEE_PER_RT
            pnl_net = pnl_gross - fee
            total_pnl += pnl_net
            equity += pnl_net
            daily_pnl[day_key] += pnl_net
            mode_pnl[current_grid_mode] += pnl_net
            round_trips += 1
            if pnl_net > 0: wins += 1
            else: losses += 1
        open_positions.clear()
        if reason == "recenter":
            recenterings += 1

    notional_per_level = (capital * leverage) / num_levels

    # Initialize grid at first close
    initial_price = candles[0]["close"]

    # Mode-specific spacing multiplier
    def get_spacing_for_mode(mode):
        if mode == "SHORT":
            return base_spacing_pct * 1.2  # slightly wider for short
        elif mode == "LONG":
            return base_spacing_pct * 0.9  # tighter for long to capture uptrend
        else:
            return base_spacing_pct

    build_grid(initial_price, get_spacing_for_mode(current_grid_mode))

    for ci, candle in enumerate(candles):
        dt = candle["time"]
        o, h, l, c = candle["open"], candle["high"], candle["low"], candle["close"]
        day_key = dt.strftime("%Y-%m-%d")

        # --- REGIME DETECTION ---
        if mode_override is None:
            new_mode = detector.update(
                ci, c,
                ema20[ci], ema50[ci], rsi14[ci],
                vol24[ci] if ci < len(vol24) else None,
                change_24h_list[ci] if ci < len(change_24h_list) else 0
            )

            if new_mode != current_grid_mode:
                # Mode switch! Close positions and rebuild grid
                close_all_positions(c, day_key, reason="mode_switch")
                current_grid_mode = new_mode
                mode_switches += 1

                if new_mode == "CASH":
                    # No grid in CASH mode
                    grid_levels = []
                else:
                    build_grid(c, get_spacing_for_mode(new_mode))

        mode_time[current_grid_mode] += 1

        # Skip grid logic in CASH mode
        if current_grid_mode == "CASH" or not grid_levels:
            # Track equity
            unrealized = sum(
                ((c - ep) / ep * sz if sd == "long" else (ep - c) / ep * sz)
                for sd, ep, sz in open_positions
            )
            current_equity = equity + unrealized
            equity_curve.append((dt.isoformat(), current_equity, c, current_grid_mode))
            continue

        # --- GRID LOGIC ---
        mode = current_grid_mode

        for level in grid_levels:
            if level < l or level > h:
                continue

            if mode == "SHORT":
                if level >= grid_center and level not in filled_sells:
                    open_positions.append(("short", level, notional_per_level))
                    filled_sells.add(level)
                elif level < grid_center and level not in filled_buys:
                    closed = False
                    for j, pos in enumerate(open_positions):
                        if pos[0] == "short":
                            ep, sz = pos[1], pos[2]
                            pnl_gross = (ep - level) / ep * sz
                            fee = sz * FEE_PER_RT
                            pnl_net = pnl_gross - fee
                            total_pnl += pnl_net
                            equity += pnl_net
                            daily_pnl[day_key] += pnl_net
                            mode_pnl[mode] += pnl_net
                            round_trips += 1
                            if pnl_net > 0: wins += 1
                            else: losses += 1
                            open_positions.pop(j)
                            filled_buys.add(level)
                            closed = True
                            break
                    if not closed:
                        filled_buys.add(level)

            elif mode == "LONG":
                if level <= grid_center and level not in filled_buys:
                    open_positions.append(("long", level, notional_per_level))
                    filled_buys.add(level)
                elif level > grid_center and level not in filled_sells:
                    closed = False
                    for j, pos in enumerate(open_positions):
                        if pos[0] == "long":
                            ep, sz = pos[1], pos[2]
                            pnl_gross = (level - ep) / ep * sz
                            fee = sz * FEE_PER_RT
                            pnl_net = pnl_gross - fee
                            total_pnl += pnl_net
                            equity += pnl_net
                            daily_pnl[day_key] += pnl_net
                            mode_pnl[mode] += pnl_net
                            round_trips += 1
                            if pnl_net > 0: wins += 1
                            else: losses += 1
                            open_positions.pop(j)
                            filled_sells.add(level)
                            closed = True
                            break
                    if not closed:
                        filled_sells.add(level)

            elif mode == "NEUTRAL":
                if level < grid_center and level not in filled_buys:
                    closed_short = False
                    for j, pos in enumerate(open_positions):
                        if pos[0] == "short":
                            ep, sz = pos[1], pos[2]
                            pnl_gross = (ep - level) / ep * sz
                            fee = sz * FEE_PER_RT
                            pnl_net = pnl_gross - fee
                            total_pnl += pnl_net
                            equity += pnl_net
                            daily_pnl[day_key] += pnl_net
                            mode_pnl[mode] += pnl_net
                            round_trips += 1
                            if pnl_net > 0: wins += 1
                            else: losses += 1
                            open_positions.pop(j)
                            closed_short = True
                            break
                    if not closed_short:
                        open_positions.append(("long", level, notional_per_level))
                    filled_buys.add(level)

                elif level >= grid_center and level not in filled_sells:
                    closed_long = False
                    for j, pos in enumerate(open_positions):
                        if pos[0] == "long":
                            ep, sz = pos[1], pos[2]
                            pnl_gross = (level - ep) / ep * sz
                            fee = sz * FEE_PER_RT
                            pnl_net = pnl_gross - fee
                            total_pnl += pnl_net
                            equity += pnl_net
                            daily_pnl[day_key] += pnl_net
                            mode_pnl[mode] += pnl_net
                            round_trips += 1
                            if pnl_net > 0: wins += 1
                            else: losses += 1
                            open_positions.pop(j)
                            closed_long = True
                            break
                    if not closed_long:
                        open_positions.append(("short", level, notional_per_level))
                    filled_sells.add(level)

        # --- RECENTER ---
        if grid_low and grid_high and (c < grid_low * 0.98 or c > grid_high * 1.02):
            close_all_positions(c, day_key, reason="recenter")
            build_grid(c, get_spacing_for_mode(current_grid_mode))

        # --- EQUITY TRACKING ---
        unrealized = sum(
            ((c - ep) / ep * sz if sd == "long" else (ep - c) / ep * sz)
            for sd, ep, sz in open_positions
        )
        current_equity = equity + unrealized
        equity_curve.append((dt.isoformat(), current_equity, c, current_grid_mode))

        if current_equity > peak_equity:
            peak_equity = current_equity
        dd_pct = (peak_equity - current_equity) / peak_equity * 100 if peak_equity > 0 else 0
        if dd_pct > max_drawdown_pct:
            max_drawdown_pct = dd_pct

        # --- MAX LOSS STOP ---
        if max_loss_pct and dd_pct > max_loss_pct:
            close_all_positions(c, day_key, reason="maxloss")
            stopped = True
            break

    # Close remaining
    if open_positions and not stopped:
        last_price = candles[-1]["close"]
        day_key = candles[-1]["time"].strftime("%Y-%m-%d")
        close_all_positions(last_price, day_key, reason="end")

    win_rate = wins / round_trips * 100 if round_trips > 0 else 0
    days = (candles[-1]["time"] - candles[0]["time"]).total_seconds() / 86400
    pnl_per_day = total_pnl / days if days > 0 else 0
    hodl_pct = (candles[-1]["close"] - candles[0]["close"]) / candles[0]["close"] * 100

    return {
        "mode": mode_override or "ADAPTIVE",
        "round_trips": round_trips,
        "wins": wins,
        "losses": losses,
        "win_rate": win_rate,
        "total_pnl": total_pnl,
        "pnl_pct": total_pnl / capital * 100,
        "max_drawdown_pct": max_drawdown_pct,
        "recenterings": recenterings,
        "mode_switches": mode_switches,
        "stopped": stopped,
        "pnl_per_day": pnl_per_day,
        "days": days,
        "hodl_pct": hodl_pct,
        "mode_time": dict(mode_time),
        "mode_pnl": {k: round(v, 4) for k, v in mode_pnl.items()},
        "daily_pnl": dict(daily_pnl),
        "switch_log": detector.switch_log if not mode_override else [],
        "equity_curve": equity_curve,
    }


# === 5. MAIN ===

if __name__ == "__main__":
    DATA_PATH = "/sessions/loving-exciting-meitner/mnt/niam-bay/trading/data/XXBTZUSD_15m.csv"

    print("Loading BTC/USD 15m OHLC data...")
    candles = load_csv_candles(DATA_PATH)
    print(f"  Loaded {len(candles)} candles")

    t0 = candles[0]["time"]
    t1 = candles[-1]["time"]
    days = (t1 - t0).total_seconds() / 86400
    hodl_pct = (candles[-1]["close"] - candles[0]["close"]) / candles[0]["close"] * 100

    print(f"  Period: {t0} -> {t1} ({days:.1f} days)")
    print(f"  Open: ${candles[0]['open']:,.2f} | Close: ${candles[-1]['close']:,.2f}")
    print(f"  High: ${max(c['high'] for c in candles):,.2f} | Low: ${min(c['low'] for c in candles):,.2f}")
    print(f"  HODL: {hodl_pct:+.2f}%")

    # Params
    CAPITAL = 15.0
    LEVERAGE = 5
    NUM_LEVELS = 10
    BASE_SPACING_PCT = 0.50  # same as session 84

    # Precompute indicators for display
    closes = [c["close"] for c in candles]
    ema20 = calc_ema(closes, 20)
    ema50 = calc_ema(closes, 50)
    rsi14 = calc_rsi(closes, 14)
    vol24 = calc_volatility(closes, 96)

    print(f"\n  Indicators at end:")
    print(f"    EMA20: ${ema20[-1]:,.0f}" if ema20[-1] else "    EMA20: N/A")
    print(f"    EMA50: ${ema50[-1]:,.0f}" if ema50[-1] else "    EMA50: N/A")
    print(f"    RSI14: {rsi14[-1]:.1f}" if rsi14[-1] else "    RSI14: N/A")
    print(f"    Vol24h: {vol24[-1]:.2f}%" if vol24[-1] else "    Vol24h: N/A")

    # === RUN ALL MODES ===

    strategies = ["ADAPTIVE", "SHORT", "NEUTRAL", "LONG"]
    results = {}

    for strat in strategies:
        override = None if strat == "ADAPTIVE" else strat

        # With max loss
        r = simulate_adaptive_grid(
            candles, CAPITAL, LEVERAGE, NUM_LEVELS, BASE_SPACING_PCT,
            max_loss_pct=15, mode_override=override
        )
        results[f"{strat}_maxloss"] = r

        # Without max loss
        r2 = simulate_adaptive_grid(
            candles, CAPITAL, LEVERAGE, NUM_LEVELS, BASE_SPACING_PCT,
            max_loss_pct=None, mode_override=override
        )
        results[f"{strat}_nolimit"] = r2

    # === DISPLAY ===

    print(f"\n{'='*75}")
    print(f"COMPARISON: ADAPTIVE vs FIXED MODES (Max Loss 15%)")
    print(f"{'='*75}")
    print(f"{'Strategy':<12} {'RTs':>5} {'WR':>6} {'PnL':>10} {'PnL%':>8} {'MaxDD':>7} {'$/day':>8} {'Rcntr':>6} {'MdSwitch':>8} {'Stop':>5}")
    print("-" * 82)

    for strat in strategies:
        r = results[f"{strat}_maxloss"]
        ms = r.get('mode_switches', 0)
        print(f"{strat:<12} {r['round_trips']:>5} {r['win_rate']:>5.1f}% ${r['total_pnl']:>+8.2f} {r['pnl_pct']:>+7.1f}% {r['max_drawdown_pct']:>6.1f}% ${r['pnl_per_day']:>+6.3f} {r['recenterings']:>6} {ms:>8} {'YES' if r['stopped'] else 'no':>5}")

    print(f"{'HODL':<12} {'':>5} {'':>6} {'':>10} {hodl_pct:>+7.1f}%")
    print(f"{'CASH':<12} {'':>5} {'':>6} {'$0.00':>10} {'+0.0%':>8} {'0.0%':>7}")

    print(f"\n{'='*75}")
    print(f"COMPARISON: ADAPTIVE vs FIXED MODES (No Max Loss)")
    print(f"{'='*75}")
    print(f"{'Strategy':<12} {'RTs':>5} {'WR':>6} {'PnL':>10} {'PnL%':>8} {'MaxDD':>7} {'$/day':>8} {'Rcntr':>6} {'MdSwitch':>8}")
    print("-" * 77)

    for strat in strategies:
        r = results[f"{strat}_nolimit"]
        ms = r.get('mode_switches', 0)
        print(f"{strat:<12} {r['round_trips']:>5} {r['win_rate']:>5.1f}% ${r['total_pnl']:>+8.2f} {r['pnl_pct']:>+7.1f}% {r['max_drawdown_pct']:>6.1f}% ${r['pnl_per_day']:>+6.3f} {r['recenterings']:>6} {ms:>8}")

    # === ADAPTIVE DETAILS ===

    r_adaptive = results["ADAPTIVE_nolimit"]

    print(f"\n{'='*75}")
    print(f"ADAPTIVE MODE DETAILS (No Max Loss)")
    print(f"{'='*75}")

    print(f"\nMode time distribution (candles):")
    total_candles = sum(r_adaptive['mode_time'].values())
    for mode, count in sorted(r_adaptive['mode_time'].items()):
        pct = count / total_candles * 100
        print(f"  {mode:<10}: {count:>5} candles ({pct:>5.1f}%)")

    print(f"\nPnL by mode:")
    for mode, pnl in sorted(r_adaptive['mode_pnl'].items()):
        print(f"  {mode:<10}: ${pnl:>+.4f}")

    print(f"\nMode switches: {r_adaptive['mode_switches']}")
    print(f"Switch log:")
    for candle_idx, old, new, reason in r_adaptive['switch_log']:
        dt = candles[candle_idx]["time"] if candle_idx < len(candles) else "?"
        print(f"  [{dt}] {old} -> {new} ({reason})")

    print(f"\nDaily PnL:")
    for day in sorted(r_adaptive['daily_pnl'].keys()):
        print(f"  {day}: ${r_adaptive['daily_pnl'][day]:+.4f}")

    # === SPACING SENSITIVITY FOR ADAPTIVE ===

    print(f"\n{'='*75}")
    print(f"SPACING SENSITIVITY (Adaptive mode, no max loss)")
    print(f"{'='*75}")

    for sp_pct in [0.3, 0.5, 0.7, 1.0, 1.5]:
        r = simulate_adaptive_grid(
            candles, CAPITAL, LEVERAGE, NUM_LEVELS, sp_pct,
            max_loss_pct=None, mode_override=None
        )
        print(f"  Spacing {sp_pct}%: RT={r['round_trips']:>3} WR={r['win_rate']:>5.1f}% PnL=${r['total_pnl']:>+.2f} ({r['pnl_pct']:>+.1f}%) DD={r['max_drawdown_pct']:.1f}% Switches={r['mode_switches']}")

    # === SAVE ===

    output = {
        "data": {
            "candles": len(candles),
            "period": f"{t0} -> {t1}",
            "days": round(days, 1),
            "hodl_pct": round(hodl_pct, 2),
            "btc_open": candles[0]["open"],
            "btc_close": candles[-1]["close"],
        },
        "params": {
            "capital": CAPITAL, "leverage": LEVERAGE,
            "num_levels": NUM_LEVELS, "base_spacing_pct": BASE_SPACING_PCT,
        },
    }

    for key, r in results.items():
        output[key] = {
            "round_trips": r["round_trips"], "wins": r["wins"], "losses": r["losses"],
            "win_rate": round(r["win_rate"], 1),
            "total_pnl": round(r["total_pnl"], 4),
            "pnl_pct": round(r["pnl_pct"], 2),
            "max_drawdown_pct": round(r["max_drawdown_pct"], 2),
            "recenterings": r["recenterings"],
            "mode_switches": r.get("mode_switches", 0),
            "stopped": r["stopped"],
            "pnl_per_day": round(r["pnl_per_day"], 4),
            "mode_time": r.get("mode_time", {}),
            "mode_pnl": r.get("mode_pnl", {}),
        }

    with open("/sessions/loving-exciting-meitner/backtest_adaptive_btc.json", "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n\nResults saved to backtest_adaptive_btc.json")
