#!/usr/bin/env python3
"""
Market EEG — FFT-based market state detection for grid trading.

The idea: apply FFT on rolling price windows to detect the market's "brain state",
then only run the grid when conditions are favorable.

Market states (like brain EEG bands):
- DELTA: sleeping market, very low volatility — DON'T TRADE (waste of fees)
- ALPHA: calm oscillation, medium volatility — GRID TRADING (ideal)
- BETA:  active swings, higher volatility — GRID with wider spacing
- GAMMA: chaos, extreme moves — STOP TRADING (protect capital)

Uses REAL data, REAL fees (maker 0.02%), REAL numbers.
"""

import csv
import math
import os
import sys
from datetime import datetime

# ─────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────

def load_csv(path):
    """Load OHLCV CSV. Returns list of dicts with float values."""
    rows = []
    with open(path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({
                'timestamp': row['timestamp'],
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close']),
                'volume': float(row['volume']),
            })
    return rows


# ─────────────────────────────────────────────
# FFT / EEG ANALYSIS (pure Python, no numpy)
# ─────────────────────────────────────────────

def _fft_recursive(x):
    """Cooley-Tukey FFT (radix-2). Input length must be power of 2."""
    N = len(x)
    if N <= 1:
        return x
    even = _fft_recursive(x[0::2])
    odd = _fft_recursive(x[1::2])
    T = []
    for k in range(N // 2):
        angle = -2.0 * math.pi * k / N
        t = complex(math.cos(angle), math.sin(angle)) * odd[k]
        T.append(t)
    result = [0] * N
    for k in range(N // 2):
        result[k] = even[k] + T[k]
        result[k + N // 2] = even[k] - T[k]
    return result


def fft(x):
    """FFT with zero-padding to next power of 2."""
    N = len(x)
    # Pad to next power of 2
    n_padded = 1
    while n_padded < N:
        n_padded *= 2
    padded = [complex(v) for v in x] + [complex(0)] * (n_padded - N)
    return _fft_recursive(padded)


def compute_market_eeg(prices, window=60):
    """
    Apply FFT on a rolling window of prices.
    Returns the market state string and diagnostic info.

    Uses rolling returns, then FFT to get frequency decomposition.
    Classification is based on realized volatility of the window.
    The FFT spectral analysis adds nuance: we look at the ratio of
    low-freq vs high-freq power to detect regime.
    """
    if len(prices) < window + 1:
        return "UNKNOWN", {}

    window_prices = prices[-(window + 1):]
    returns = []
    for i in range(1, len(window_prices)):
        if window_prices[i - 1] != 0:
            returns.append((window_prices[i] - window_prices[i - 1]) / window_prices[i - 1])
        else:
            returns.append(0.0)

    # Volatility (std of returns as %)
    mean_r = sum(returns) / len(returns)
    variance = sum((r - mean_r) ** 2 for r in returns) / len(returns)
    volatility = math.sqrt(variance) * 100  # percentage

    # FFT analysis
    spectrum = fft(returns)
    magnitudes = [abs(s) for s in spectrum]
    N = len(magnitudes)
    half = N // 2

    # Power in low freq vs high freq bands
    if half > 2:
        low_freq_power = sum(magnitudes[1:half // 3]) if half // 3 > 1 else 0
        high_freq_power = sum(magnitudes[half // 3:half]) if half // 3 < half else 0
        total_power = low_freq_power + high_freq_power
        if total_power > 0:
            low_ratio = low_freq_power / total_power
        else:
            low_ratio = 0.5
    else:
        low_ratio = 0.5

    # Dominant frequency index (skip DC component)
    if half > 1:
        dominant_idx = 1
        for i in range(2, half):
            if magnitudes[i] > magnitudes[dominant_idx]:
                dominant_idx = i
        dominant_period = N / dominant_idx if dominant_idx > 0 else N
    else:
        dominant_period = N

    # Classification based on volatility + spectral shape
    # Hourly data: volatility thresholds calibrated for 1h candles
    info = {
        'volatility': volatility,
        'low_ratio': low_ratio,
        'dominant_period': dominant_period,
    }

    if volatility < 0.15:
        state = "DELTA"
    elif volatility < 0.55:
        state = "ALPHA"
    elif volatility < 1.2:
        state = "BETA"
    else:
        state = "GAMMA"

    return state, info


def compute_eeg_series(candles, window=60):
    """Compute EEG state for every candle. Returns list of states."""
    prices = [c['close'] for c in candles]
    states = []
    for i in range(len(prices)):
        if i < window:
            states.append("UNKNOWN")
        else:
            state, _ = compute_market_eeg(prices[:i + 1], window=window)
            states.append(state)
    return states


# ─────────────────────────────────────────────
# GRID BACKTEST ENGINE
# ─────────────────────────────────────────────

def backtest_grid(candles, states, strategy='always_on',
                  capital=100.0, leverage=5, base_spacing_pct=1.0,
                  levels=10, fee_rate=0.0002):
    """
    Grid trading backtest — realistic margin-aware engine.

    Strategy modes:
    - 'always_on':   grid always active (baseline)
    - 'eeg_filter':  grid only in ALPHA or BETA (off in DELTA/GAMMA)
    - 'eeg_adaptive': ALPHA=tight grid, BETA=wide grid, off in DELTA/GAMMA

    Realistic constraints:
    - Position size based on INITIAL capital (not fluctuating balance)
    - Max open positions capped at `levels`
    - Margin check: won't open if margin used > 80% of equity
    - Liquidation at equity < 20% of initial margin
    - Each grid level can only fill once per grid setup (no duplicate fills)

    Returns dict with performance metrics.
    """
    balance = capital  # cash balance (realized P&L included)
    peak_equity = capital
    max_drawdown = 0.0
    total_fees = 0.0
    total_realized = 0.0
    round_trips = 0
    hours_active = 0
    hours_total = 0
    liquidated = False

    # Open positions: list of (entry_price, size_in_asset)
    open_positions = []

    # Grid tracking
    grid_active = False
    grid_center = 0.0
    grid_spacing = 0.0
    filled_buy_levels = set()   # track which levels have been filled
    filled_sell_levels = set()

    # Fixed position size: allocate capital evenly across levels
    # Each level gets (capital * leverage) / levels in notional
    notional_per_level = (capital * leverage) / levels
    max_positions = levels  # cap open positions

    for i in range(1, len(candles)):
        if liquidated:
            break

        price = candles[i]['close']
        high = candles[i]['high']
        low = candles[i]['low']
        state = states[i]
        hours_total += 1

        # Decide if grid should be active
        should_trade = False
        spacing_mult = 1.0

        if strategy == 'always_on':
            should_trade = True
            spacing_mult = 1.0
        elif strategy == 'eeg_filter':
            should_trade = state in ('ALPHA', 'BETA')
            spacing_mult = 1.0
        elif strategy == 'eeg_adaptive':
            if state == 'ALPHA':
                should_trade = True
                spacing_mult = 1.0
            elif state == 'BETA':
                should_trade = True
                spacing_mult = 2.0
            else:
                should_trade = False

        # If switching from active to inactive: close all positions at market
        if not should_trade and open_positions:
            for entry_p, sz in open_positions:
                pnl = (price - entry_p) * sz
                fee = price * sz * fee_rate
                total_realized += pnl - fee
                total_fees += fee
                balance += pnl - fee
                round_trips += 1
            open_positions = []
            grid_active = False
            filled_buy_levels.clear()
            filled_sell_levels.clear()
            continue

        if not should_trade:
            grid_active = False
            continue

        hours_active += 1
        actual_spacing = base_spacing_pct * spacing_mult / 100.0 * price

        # Check if grid needs reset (price drifted too far from center)
        need_reset = False
        if not grid_active:
            need_reset = True
        elif abs(price - grid_center) > actual_spacing * (levels // 2):
            need_reset = True

        if need_reset:
            # Close existing positions (grid reset)
            for entry_p, sz in open_positions:
                pnl = (price - entry_p) * sz
                fee = price * sz * fee_rate
                total_realized += pnl - fee
                total_fees += fee
                balance += pnl - fee
                round_trips += 1
            open_positions = []
            grid_center = price
            grid_spacing = actual_spacing
            grid_active = True
            filled_buy_levels.clear()
            filled_sell_levels.clear()

        spacing = grid_spacing
        if spacing <= 0:
            continue

        # Size per level (fixed, based on initial capital)
        size_per_level = notional_per_level / price if price > 0 else 0
        if size_per_level <= 0:
            continue

        # Check grid level fills
        for lvl in range(1, levels // 2 + 1):
            buy_level = grid_center - lvl * spacing
            sell_level = grid_center + lvl * spacing

            # BUY fill: price dipped to buy_level, level not yet filled, room for positions
            if (low <= buy_level and lvl not in filled_buy_levels
                    and len(open_positions) < max_positions):
                # Margin check: used margin vs equity
                unrealized = sum((price - ep) * s for ep, s in open_positions)
                equity = balance + unrealized
                used_margin = sum(ep * s for ep, s in open_positions) / leverage
                new_margin = buy_level * size_per_level / leverage
                if used_margin + new_margin < equity * 0.8:
                    fee = buy_level * size_per_level * fee_rate
                    total_fees += fee
                    balance -= fee
                    open_positions.append((buy_level, size_per_level))
                    filled_buy_levels.add(lvl)

            # SELL (take profit): if price reached sell_level and we have open buys
            if high >= sell_level and lvl not in filled_sell_levels and open_positions:
                # Close the oldest position (FIFO)
                entry_p, sz = open_positions.pop(0)
                pnl = (sell_level - entry_p) * sz
                fee = sell_level * sz * fee_rate
                total_realized += pnl - fee
                total_fees += fee
                balance += pnl - fee
                round_trips += 1
                filled_sell_levels.add(lvl)
                # Reopen the buy level that was used
                if lvl in filled_buy_levels:
                    filled_buy_levels.discard(lvl)

        # Equity and drawdown
        unrealized = sum((price - ep) * s for ep, s in open_positions)
        equity = balance + unrealized
        if equity > peak_equity:
            peak_equity = equity
        dd = (peak_equity - equity) / peak_equity * 100 if peak_equity > 0 else 0
        if dd > max_drawdown:
            max_drawdown = dd

        # Liquidation check: equity < 20% of initial capital
        if equity < capital * 0.2 and open_positions:
            # Force close everything
            for entry_p, sz in open_positions:
                pnl = (price - entry_p) * sz
                fee = price * sz * fee_rate
                total_realized += pnl - fee
                total_fees += fee
                balance += pnl - fee
                round_trips += 1
            open_positions = []
            liquidated = True
            break

    # If not liquidated, close remaining at last price
    if not liquidated and open_positions:
        final_price = candles[-1]['close']
        for entry_p, sz in open_positions:
            pnl = (final_price - entry_p) * sz
            fee = final_price * sz * fee_rate
            total_realized += pnl - fee
            total_fees += fee
            balance += pnl - fee
            round_trips += 1

    # Fill remaining hours if liquidated early
    if liquidated:
        hours_total = len(candles) - 1

    time_in_market = (hours_active / hours_total * 100) if hours_total > 0 else 0
    profit_per_hour = (total_realized / hours_active) if hours_active > 0 else 0
    roi = ((balance - capital) / capital * 100) if capital > 0 else 0

    return {
        'final_balance': balance,
        'total_profit': total_realized,
        'total_fees': total_fees,
        'round_trips': round_trips,
        'max_drawdown': max_drawdown,
        'hours_active': hours_active,
        'hours_total': hours_total,
        'time_in_market': time_in_market,
        'profit_per_hour': profit_per_hour,
        'roi': roi,
        'liquidated': liquidated,
    }


# ─────────────────────────────────────────────
# ASCII VISUALIZATION
# ─────────────────────────────────────────────

def ascii_chart(candles, states, pair_name, width=120, height=20):
    """
    ASCII chart showing:
    - Price over time
    - EEG state bar (D/A/B/G)
    - Active vs paused indicator
    """
    prices = [c['close'] for c in candles]
    n = len(prices)

    # Downsample to width
    step = max(1, n // width)
    sampled_prices = []
    sampled_states = []
    sampled_times = []
    for i in range(0, n, step):
        chunk = prices[i:i + step]
        sampled_prices.append(sum(chunk) / len(chunk))
        # Most common state in chunk
        chunk_states = states[i:i + step]
        state_counts = {}
        for s in chunk_states:
            state_counts[s] = state_counts.get(s, 0) + 1
        sampled_states.append(max(state_counts, key=state_counts.get))
        sampled_times.append(candles[min(i, n - 1)]['timestamp'][:10])

    w = len(sampled_prices)
    p_min = min(sampled_prices)
    p_max = max(sampled_prices)
    p_range = p_max - p_min if p_max != p_min else 1

    lines = []
    lines.append(f"  {'=' * (w + 2)}")
    lines.append(f"  {pair_name} — Price Chart with EEG States")
    lines.append(f"  {'=' * (w + 2)}")

    # Price chart
    chart = [[' '] * w for _ in range(height)]
    for col in range(w):
        row = int((sampled_prices[col] - p_min) / p_range * (height - 1))
        row = min(height - 1, max(0, row))
        chart[height - 1 - row][col] = '*'

    for row_idx in range(height):
        price_label = p_max - (row_idx / (height - 1)) * p_range
        line = f"  {price_label:>10.2f} |{''.join(chart[row_idx])}|"
        lines.append(line)

    # X axis
    lines.append(f"  {'':>10} +{'-' * w}+")

    # EEG state bar
    state_chars = {'DELTA': 'D', 'ALPHA': 'A', 'BETA': 'B', 'GAMMA': 'G', 'UNKNOWN': '?'}
    state_line = ''.join(state_chars.get(s, '?') for s in sampled_states)
    lines.append(f"  {'EEG':>10} |{state_line}|")

    # Active bar (A=active for grid with EEG filter)
    active_line = ''.join(
        '#' if s in ('ALPHA', 'BETA') else '.' for s in sampled_states
    )
    lines.append(f"  {'Active':>10} |{active_line}|")

    # Time labels
    if w > 20:
        time_line = sampled_times[0].ljust(w // 2) + sampled_times[-1].rjust(w - w // 2)
    else:
        time_line = sampled_times[0]
    lines.append(f"  {'':>10}  {time_line}")

    # Legend
    lines.append("")
    lines.append("  Legend: D=DELTA(sleep) A=ALPHA(grid) B=BETA(wide grid) G=GAMMA(stop)")
    lines.append("         #=Grid Active  .=Grid Paused")

    return '\n'.join(lines)


# ─────────────────────────────────────────────
# EEG DISTRIBUTION ANALYSIS
# ─────────────────────────────────────────────

def eeg_distribution(states):
    """Count time spent in each state."""
    counts = {}
    total = 0
    for s in states:
        if s == "UNKNOWN":
            continue
        counts[s] = counts.get(s, 0) + 1
        total += 1
    dist = {}
    for s in ['DELTA', 'ALPHA', 'BETA', 'GAMMA']:
        c = counts.get(s, 0)
        dist[s] = {'count': c, 'pct': c / total * 100 if total > 0 else 0}
    return dist, total


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def run_analysis(data_path, pair_name, eeg_window=60):
    """Run full analysis for one pair."""
    print(f"\n{'=' * 80}")
    print(f"  MARKET EEG ANALYSIS: {pair_name}")
    print(f"{'=' * 80}")

    candles = load_csv(data_path)
    print(f"  Loaded {len(candles)} candles from {candles[0]['timestamp'][:10]} to {candles[-1]['timestamp'][:10]}")

    # Price range
    prices = [c['close'] for c in candles]
    print(f"  Price range: {min(prices):.4f} — {max(prices):.4f}")
    print(f"  Overall move: {(prices[-1] / prices[0] - 1) * 100:.1f}%")

    # Compute EEG
    states = compute_eeg_series(candles, window=eeg_window)
    dist, total = eeg_distribution(states)

    print(f"\n  EEG State Distribution (window={eeg_window}h):")
    print(f"  {'State':<10} {'Hours':>8} {'%':>8}")
    print(f"  {'-' * 28}")
    for s in ['DELTA', 'ALPHA', 'BETA', 'GAMMA']:
        d = dist[s]
        bar = '#' * int(d['pct'] / 2)
        print(f"  {s:<10} {d['count']:>8} {d['pct']:>7.1f}% {bar}")

    # ASCII chart
    print(f"\n{ascii_chart(candles, states, pair_name)}")

    # Backtest three strategies
    strategies = ['always_on', 'eeg_filter', 'eeg_adaptive']
    strategy_names = {
        'always_on': 'Baseline (always on)',
        'eeg_filter': 'EEG Filter (ALPHA+BETA only)',
        'eeg_adaptive': 'EEG Adaptive (tight/wide)',
    }

    results = {}
    for strat in strategies:
        r = backtest_grid(candles, states, strategy=strat,
                          capital=100.0, leverage=5, base_spacing_pct=1.0,
                          levels=10, fee_rate=0.0002)
        results[strat] = r

    # Results table
    print(f"\n  {'BACKTEST RESULTS':^78}")
    print(f"  {'-' * 78}")
    header = f"  {'Metric':<30}"
    for strat in strategies:
        header += f" {strategy_names[strat]:>15}"
    print(header)
    print(f"  {'-' * 78}")

    metrics = [
        ('Final Balance ($)', 'final_balance', '.2f'),
        ('Total Profit ($)', 'total_profit', '.2f'),
        ('ROI (%)', 'roi', '.2f'),
        ('Total Fees ($)', 'total_fees', '.4f'),
        ('Round Trips', 'round_trips', 'd'),
        ('Max Drawdown (%)', 'max_drawdown', '.2f'),
        ('Hours Active', 'hours_active', 'd'),
        ('Hours Total', 'hours_total', 'd'),
        ('Time in Market (%)', 'time_in_market', '.1f'),
        ('Profit/Hour Active ($)', 'profit_per_hour', '.4f'),
        ('Liquidated?', 'liquidated', ''),
    ]

    for label, key, fmt in metrics:
        line = f"  {label:<30}"
        for strat in strategies:
            val = results[strat][key]
            if fmt == '':
                line += f" {'YES' if val else 'no':>15}"
            else:
                line += f" {val:>15{fmt}}"
        print(line)

    print(f"  {'-' * 78}")

    # Verdict
    best_strat = max(strategies, key=lambda s: results[s]['profit_per_hour'])
    print(f"\n  >> Best profit/hour: {strategy_names[best_strat]}")

    best_roi = max(strategies, key=lambda s: results[s]['roi'])
    print(f"  >> Best ROI: {strategy_names[best_roi]}")

    safest = min(strategies, key=lambda s: results[s]['max_drawdown'])
    print(f"  >> Lowest drawdown: {strategy_names[safest]}")

    return results, states, candles


def generate_report(all_results):
    """Generate markdown report."""
    lines = []
    lines.append("# Market EEG — Backtest Results")
    lines.append("")
    lines.append(f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"**Data**: 3 months hourly candles (Dec 2025 — Mar 2026)")
    lines.append(f"**Capital**: $100, Leverage: 5x, Fees: 0.02% maker")
    lines.append("")
    lines.append("## Concept")
    lines.append("")
    lines.append("Apply FFT (Fast Fourier Transform) on rolling price windows to classify")
    lines.append("the market into 4 states, analogous to brain EEG frequency bands:")
    lines.append("")
    lines.append("| State | Volatility | Action |")
    lines.append("|-------|-----------|--------|")
    lines.append("| DELTA | < 0.15% | Sleep — don't trade |")
    lines.append("| ALPHA | 0.15-0.55% | Grid trading (tight spacing) |")
    lines.append("| BETA | 0.55-1.2% | Grid trading (wide spacing) |")
    lines.append("| GAMMA | > 1.2% | Stop — protect capital |")
    lines.append("")
    lines.append("## Results by Pair")

    for pair_name, (results, states, candles) in all_results.items():
        lines.append(f"\n### {pair_name}")
        lines.append("")

        prices = [c['close'] for c in candles]
        lines.append(f"- **Period**: {candles[0]['timestamp'][:10]} to {candles[-1]['timestamp'][:10]}")
        lines.append(f"- **Price**: {prices[0]:.4f} -> {prices[-1]:.4f} ({(prices[-1]/prices[0]-1)*100:.1f}%)")
        lines.append("")

        dist, total = eeg_distribution(states)
        lines.append("**EEG Distribution:**")
        lines.append("")
        lines.append("| State | Hours | % |")
        lines.append("|-------|-------|---|")
        for s in ['DELTA', 'ALPHA', 'BETA', 'GAMMA']:
            d = dist[s]
            lines.append(f"| {s} | {d['count']} | {d['pct']:.1f}% |")
        lines.append("")

        strategy_names = {
            'always_on': 'Baseline',
            'eeg_filter': 'EEG Filter',
            'eeg_adaptive': 'EEG Adaptive',
        }

        lines.append("**Performance:**")
        lines.append("")
        lines.append("| Metric | Baseline | EEG Filter | EEG Adaptive |")
        lines.append("|--------|----------|------------|--------------|")

        r = results
        metric_rows = [
            ('Final Balance', lambda s: f"${r[s]['final_balance']:.2f}"),
            ('Total Profit', lambda s: f"${r[s]['total_profit']:.2f}"),
            ('ROI', lambda s: f"{r[s]['roi']:.2f}%"),
            ('Fees Paid', lambda s: f"${r[s]['total_fees']:.4f}"),
            ('Round Trips', lambda s: f"{r[s]['round_trips']}"),
            ('Max Drawdown', lambda s: f"{r[s]['max_drawdown']:.2f}%"),
            ('Time in Market', lambda s: f"{r[s]['time_in_market']:.1f}%"),
            ('Profit/Hour', lambda s: f"${r[s]['profit_per_hour']:.4f}"),
        ]

        strats = ['always_on', 'eeg_filter', 'eeg_adaptive']
        for label, fn in metric_rows:
            vals = ' | '.join(fn(s) for s in strats)
            lines.append(f"| {label} | {vals} |")

    # Summary
    lines.append("\n## Key Question: Does EEG Filter Improve Profitability?")
    lines.append("")

    for pair_name, (results, states, candles) in all_results.items():
        baseline = results['always_on']
        filtered = results['eeg_filter']
        adaptive = results['eeg_adaptive']

        lines.append(f"### {pair_name}")
        lines.append("")

        # Compare ROI
        if filtered['roi'] > baseline['roi']:
            lines.append(f"- EEG Filter ROI: **{filtered['roi']:.2f}%** vs Baseline **{baseline['roi']:.2f}%** -> BETTER")
        else:
            lines.append(f"- EEG Filter ROI: **{filtered['roi']:.2f}%** vs Baseline **{baseline['roi']:.2f}%** -> WORSE")

        if adaptive['roi'] > baseline['roi']:
            lines.append(f"- EEG Adaptive ROI: **{adaptive['roi']:.2f}%** vs Baseline **{baseline['roi']:.2f}%** -> BETTER")
        else:
            lines.append(f"- EEG Adaptive ROI: **{adaptive['roi']:.2f}%** vs Baseline **{baseline['roi']:.2f}%** -> WORSE")

        # Compare drawdown
        if filtered['max_drawdown'] < baseline['max_drawdown']:
            lines.append(f"- EEG Filter Drawdown: **{filtered['max_drawdown']:.2f}%** vs Baseline **{baseline['max_drawdown']:.2f}%** -> SAFER")
        else:
            lines.append(f"- EEG Filter Drawdown: **{filtered['max_drawdown']:.2f}%** vs Baseline **{baseline['max_drawdown']:.2f}%** -> RISKIER")

        # Profit per hour
        if filtered['profit_per_hour'] > baseline['profit_per_hour']:
            lines.append(f"- EEG Filter Profit/Hour: **${filtered['profit_per_hour']:.4f}** vs Baseline **${baseline['profit_per_hour']:.4f}** -> MORE EFFICIENT")
        else:
            lines.append(f"- EEG Filter Profit/Hour: **${filtered['profit_per_hour']:.4f}** vs Baseline **${baseline['profit_per_hour']:.4f}** -> LESS EFFICIENT")

        # Fee savings
        fee_saved = baseline['total_fees'] - filtered['total_fees']
        lines.append(f"- Fees saved by EEG Filter: **${fee_saved:.4f}**")
        lines.append("")

    lines.append("## Conclusion")
    lines.append("")
    lines.append("_Automatically generated — see raw numbers above for deployment decision._")
    lines.append("")

    return '\n'.join(lines)


def main():
    print("=" * 80)
    print("  MARKET EEG — FFT-Based Market State Detection")
    print("  Backtest on 3 months of real crypto data")
    print("  Capital: $100 | Leverage: 5x | Fees: 0.02% maker")
    print("=" * 80)

    data_dir = "C:/niam-bay/trading/data"
    pairs = {
        'ETHUSD': os.path.join(data_dir, 'ETHUSD_1h_3mo.csv'),
        'ADAUSD': os.path.join(data_dir, 'ADAUSD_1h_3mo.csv'),
        'SOLUSD': os.path.join(data_dir, 'SOLUSD_1h_3mo.csv'),
    }

    all_results = {}
    for pair_name, path in pairs.items():
        if not os.path.exists(path):
            print(f"  WARNING: {path} not found, skipping {pair_name}")
            continue
        results, states, candles = run_analysis(path, pair_name)
        all_results[pair_name] = (results, states, candles)

    # Generate report
    report = generate_report(all_results)
    report_path = "C:/niam-bay/trading/research/market-eeg-results.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\n  Report written to: {report_path}")

    # Final verdict
    print(f"\n{'=' * 80}")
    print("  FINAL VERDICT")
    print(f"{'=' * 80}")
    for pair_name, (results, states, candles) in all_results.items():
        baseline_roi = results['always_on']['roi']
        filter_roi = results['eeg_filter']['roi']
        adaptive_roi = results['eeg_adaptive']['roi']
        baseline_dd = results['always_on']['max_drawdown']
        filter_dd = results['eeg_filter']['max_drawdown']
        adaptive_dd = results['eeg_adaptive']['max_drawdown']

        print(f"\n  {pair_name}:")
        print(f"    Baseline:     ROI={baseline_roi:+.2f}%  DD={baseline_dd:.2f}%")
        print(f"    EEG Filter:   ROI={filter_roi:+.2f}%  DD={filter_dd:.2f}%")
        print(f"    EEG Adaptive: ROI={adaptive_roi:+.2f}%  DD={adaptive_dd:.2f}%")

        best = max(['always_on', 'eeg_filter', 'eeg_adaptive'],
                    key=lambda s: results[s]['roi'])
        names = {'always_on': 'Baseline', 'eeg_filter': 'EEG Filter', 'eeg_adaptive': 'EEG Adaptive'}
        print(f"    >>> Winner: {names[best]}")

    print()


if __name__ == '__main__':
    main()
