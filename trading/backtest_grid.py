import json
import datetime
from collections import defaultdict

# === LOAD DATA ===
def load_candles(filename):
    with open(filename) as f:
        d = json.load(f)
    key = [k for k in d['result'] if k != 'last'][0]
    candles = d['result'][key]
    return [(int(c[0]), float(c[1]), float(c[2]), float(c[3]), float(c[4]), float(c[6])) for c in candles]

pairs_data = {}
for pair, fname in [('ETH', 'ethusd_4h.json'), ('SOL', 'solusd_4h.json'), ('DOT', 'dotusd_4h.json')]:
    pairs_data[pair] = load_candles(f'C:/niam-bay/trading/{fname}')

pairs_1h = {}
for pair, fname in [('ETH', 'eth_ohlc.json'), ('SOL', 'sol_ohlc.json'), ('DOT', 'dot_ohlc.json')]:
    pairs_1h[pair] = load_candles(f'C:/niam-bay/trading/{fname}')

MAKER_FEE = 0.0002
TAKER_FEE = 0.0005

def simulate_grid(candles, capital, leverage, spacing_pct, num_levels, stop_loss_change24h=None):
    if not candles:
        return None

    initial_price = candles[0][4]
    position_size = (capital * leverage) / num_levels

    results = {
        'round_trips': 0, 'wins': 0, 'losses': 0,
        'total_profit': 0.0, 'max_drawdown': 0.0,
        'fills': 0, 'stopped_count': 0,
        'daily_profits': defaultdict(float),
        'hourly_profits': defaultdict(float),
    }

    equity = capital
    peak_equity = capital
    spacing = spacing_pct / 100.0
    grid_center = initial_price

    def make_grid(center):
        levels = []
        for i in range(1, num_levels // 2 + 1):
            levels.append(('buy', center * (1 - i * spacing), False))
            levels.append(('sell', center * (1 + i * spacing), False))
        return levels

    grid = make_grid(grid_center)
    open_buys = []
    open_sells = []
    price_history = []

    for candle in candles:
        ts, o, h, l, c, vol = candle
        dt = datetime.datetime.fromtimestamp(ts)
        day_key = dt.strftime('%Y-%m-%d')
        hour_key = dt.hour
        price_history.append(c)

        # Stop-loss check
        if stop_loss_change24h is not None:
            lookback = 6  # 6 x 4h = 24h
            if len(price_history) > lookback:
                change_24h = abs(c - price_history[-lookback-1]) / price_history[-lookback-1] * 100
                if change_24h > stop_loss_change24h:
                    for bp in open_buys:
                        pnl = (c - bp) * (position_size / bp)
                        fee = position_size * (MAKER_FEE + TAKER_FEE)
                        net = pnl - fee
                        results['total_profit'] += net
                        results['round_trips'] += 1
                        results['daily_profits'][day_key] += net
                        if net > 0: results['wins'] += 1
                        else: results['losses'] += 1
                    for sp in open_sells:
                        pnl = (sp - c) * (position_size / sp)
                        fee = position_size * (MAKER_FEE + TAKER_FEE)
                        net = pnl - fee
                        results['total_profit'] += net
                        results['round_trips'] += 1
                        results['daily_profits'][day_key] += net
                        if net > 0: results['wins'] += 1
                        else: results['losses'] += 1
                    open_buys = []
                    open_sells = []
                    results['stopped_count'] += 1
                    grid_center = c
                    grid = make_grid(grid_center)
                    equity = capital + results['total_profit']
                    if equity > peak_equity: peak_equity = equity
                    dd = (peak_equity - equity) / peak_equity * 100 if peak_equity > 0 else 0
                    if dd > results['max_drawdown']: results['max_drawdown'] = dd
                    continue

        new_grid = []
        for gtype, gprice, gfilled in grid:
            if gfilled:
                new_grid.append((gtype, gprice, gfilled))
                continue

            if gtype == 'buy' and l <= gprice:
                open_buys.append(gprice)
                results['fills'] += 1
                new_grid.append((gtype, gprice, True))
                if open_sells:
                    sell_price = open_sells.pop(0)
                    pnl = (sell_price - gprice) * (position_size / gprice)
                    fee = position_size * (MAKER_FEE + TAKER_FEE)
                    net = pnl - fee
                    results['total_profit'] += net
                    results['round_trips'] += 1
                    results['daily_profits'][day_key] += net
                    results['hourly_profits'][hour_key] += net
                    if net > 0: results['wins'] += 1
                    else: results['losses'] += 1
                    open_buys.pop()
            elif gtype == 'sell' and h >= gprice:
                open_sells.append(gprice)
                results['fills'] += 1
                new_grid.append((gtype, gprice, True))
                if open_buys:
                    buy_price = open_buys.pop(0)
                    pnl = (gprice - buy_price) * (position_size / buy_price)
                    fee = position_size * (MAKER_FEE + TAKER_FEE)
                    net = pnl - fee
                    results['total_profit'] += net
                    results['round_trips'] += 1
                    results['daily_profits'][day_key] += net
                    results['hourly_profits'][hour_key] += net
                    if net > 0: results['wins'] += 1
                    else: results['losses'] += 1
                    open_sells.pop()
            else:
                new_grid.append((gtype, gprice, gfilled))

        grid = new_grid

        unrealized = 0
        for bp in open_buys:
            unrealized += (c - bp) * (position_size / bp)
        for sp in open_sells:
            unrealized += (sp - c) * (position_size / sp)

        current_equity = capital + results['total_profit'] + unrealized
        if current_equity > peak_equity: peak_equity = current_equity
        dd = (peak_equity - current_equity) / peak_equity * 100 if peak_equity > 0 else 0
        if dd > results['max_drawdown']: results['max_drawdown'] = dd

        all_filled = all(gf for _, _, gf in grid)
        price_drift = abs(c - grid_center) / grid_center
        if all_filled or price_drift > spacing * (num_levels // 2 + 2):
            grid_center = c
            grid = make_grid(grid_center)

    num_days = (candles[-1][0] - candles[0][0]) / 86400
    results['num_days'] = num_days
    results['profit_per_day'] = results['total_profit'] / num_days if num_days > 0 else 0
    results['win_rate'] = results['wins'] / results['round_trips'] * 100 if results['round_trips'] > 0 else 0

    last_price = candles[-1][4]
    results['open_buys'] = len(open_buys)
    results['open_sells'] = len(open_sells)
    unrealized_final = 0
    for bp in open_buys:
        unrealized_final += (last_price - bp) * (position_size / bp)
    for sp in open_sells:
        unrealized_final += (sp - last_price) * (position_size / sp)
    results['unrealized_pnl'] = unrealized_final
    results['total_with_unrealized'] = results['total_profit'] + unrealized_final

    return results

# === RUN ALL STRATEGIES ===
strategies = [
    {'name': 'Grid x5, spacing 1%, 10 niveaux', 'leverage': 5, 'spacing': 1.0, 'levels': 10, 'stop': None},
    {'name': 'Grid x5, spacing 1.5%, 10 niveaux', 'leverage': 5, 'spacing': 1.5, 'levels': 10, 'stop': None},
    {'name': 'Grid x5, spacing 2%, 10 niveaux', 'leverage': 5, 'spacing': 2.0, 'levels': 10, 'stop': None},
    {'name': 'Grid x10, spacing 1%, 10 niveaux', 'leverage': 10, 'spacing': 1.0, 'levels': 10, 'stop': None},
    {'name': 'Grid x5, spacing 1%, stop 3%', 'leverage': 5, 'spacing': 1.0, 'levels': 10, 'stop': 3.0},
]

capital = 100
all_results = {}

for pair, candles in pairs_data.items():
    all_results[pair] = {}
    first_price = candles[0][4]
    last_price = candles[-1][4]
    price_change = (last_price - first_price) / first_price * 100
    all_results[pair]['price_change'] = price_change
    all_results[pair]['first_price'] = first_price
    all_results[pair]['last_price'] = last_price

    for strat in strategies:
        r = simulate_grid(candles, capital, strat['leverage'], strat['spacing'], strat['levels'], strat['stop'])
        all_results[pair][strat['name']] = r

# === CYCLE ANALYSIS ===
cycle_analysis = {}
for pair, candles in pairs_1h.items():
    hourly_vol = defaultdict(list)
    dow_vol = defaultdict(list)
    hourly_range = defaultdict(list)

    for i in range(1, len(candles)):
        ts, o, h, l, c, vol = candles[i]
        dt = datetime.datetime.fromtimestamp(ts)
        prev_c = candles[i-1][4]
        ret = abs(c - prev_c) / prev_c * 100
        range_pct = (h - l) / l * 100
        hourly_vol[dt.hour].append(ret)
        dow_vol[dt.weekday()].append(ret)
        hourly_range[dt.hour].append(range_pct)

    avg_hourly_vol = {h: sum(v)/len(v) for h, v in hourly_vol.items()}
    avg_dow_vol = {d: sum(v)/len(v) for d, v in dow_vol.items()}
    avg_hourly_range = {h: sum(v)/len(v) for h, v in hourly_range.items()}

    cycle_analysis[pair] = {
        'hourly_volatility': avg_hourly_vol,
        'dow_volatility': avg_dow_vol,
        'hourly_range': avg_hourly_range,
    }

# === VOLATILITY ANALYSIS on 4h data ===
vol_4h_analysis = {}
for pair, candles in pairs_data.items():
    weekly_returns = defaultdict(list)
    for i in range(1, len(candles)):
        ts, o, h, l, c, vol = candles[i]
        dt = datetime.datetime.fromtimestamp(ts)
        week_key = dt.strftime('%Y-W%W')
        prev_c = candles[i-1][4]
        ret = (c - prev_c) / prev_c * 100
        weekly_returns[week_key].append(ret)

    weekly_vol = {w: (sum(r)/len(r), max(r)-min(r), len(r)) for w, r in weekly_returns.items()}
    vol_4h_analysis[pair] = weekly_vol

# === OUTPUT ===
output = []
output.append("=" * 80)
output.append("BACKTEST GRID TRADING - 3 MOIS (27 Dec 2025 - 27 Mar 2026)")
output.append("Capital: 100 USD par strategie | Donnees: Kraken OHLC 4h (541 candles)")
output.append("Fees: maker 0.02% + taker 0.05% = 0.07% par RT")
output.append("=" * 80)

for pair in ['ETH', 'SOL', 'DOT']:
    pr = all_results[pair]
    output.append(f"\n{'='*60}")
    output.append(f"  {pair}/USD")
    output.append(f"  Prix: {pr['first_price']:.2f} -> {pr['last_price']:.2f} ({pr['price_change']:+.1f}%)")
    output.append(f"{'='*60}")

    for strat in strategies:
        r = pr[strat['name']]
        output.append(f"\n  --- {strat['name']} ---")
        output.append(f"  Round trips: {r['round_trips']}")
        output.append(f"  Fills: {r['fills']}")
        output.append(f"  Win rate: {r['win_rate']:.1f}%")
        output.append(f"  Profit realise: ${r['total_profit']:.2f}")
        output.append(f"  Unrealized PnL: ${r['unrealized_pnl']:.2f}")
        output.append(f"  Total (realise + unrealized): ${r['total_with_unrealized']:.2f}")
        output.append(f"  Max drawdown: {r['max_drawdown']:.1f}%")
        output.append(f"  Profit/jour: ${r['profit_per_day']:.4f}")
        output.append(f"  Jours: {r['num_days']:.1f}")
        if r.get('stopped_count', 0) > 0:
            output.append(f"  Stop-loss declenche: {r['stopped_count']}x")
        output.append(f"  Positions ouvertes: {r['open_buys']} buys, {r['open_sells']} sells")

output.append(f"\n{'='*80}")
output.append("ANALYSE DES CYCLES (donnees 1h, 30 derniers jours)")
output.append("=" * 80)

days_names = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim']
for pair in ['ETH', 'SOL', 'DOT']:
    ca = cycle_analysis[pair]
    output.append(f"\n--- {pair} ---")
    sorted_hours = sorted(ca['hourly_volatility'].items(), key=lambda x: x[1], reverse=True)
    output.append(f"  Top 5 heures les plus volatiles:")
    for h, v in sorted_hours[:5]:
        output.append(f"    {h:02d}h: {v:.4f}% avg move, range={ca['hourly_range'][h]:.4f}%")
    output.append(f"  Bottom 3 heures (calmes):")
    for h, v in sorted_hours[-3:]:
        output.append(f"    {h:02d}h: {v:.4f}% avg move, range={ca['hourly_range'][h]:.4f}%")
    output.append(f"  Volatilite par jour de semaine:")
    for d in range(7):
        if d in ca['dow_volatility']:
            output.append(f"    {days_names[d]}: {ca['dow_volatility'][d]:.4f}%")

# Best strategy summary
output.append(f"\n{'='*80}")
output.append("CLASSEMENT - MEILLEURE STRATEGIE PAR PAIRE")
output.append("=" * 80)
for pair in ['ETH', 'SOL', 'DOT']:
    best_name = None
    best_profit = -999999
    for strat in strategies:
        r = all_results[pair][strat['name']]
        if r['total_with_unrealized'] > best_profit:
            best_profit = r['total_with_unrealized']
            best_name = strat['name']
    output.append(f"  {pair}: {best_name} -> ${best_profit:.2f}")

result_text = "\n".join(output)
print(result_text)

# Save raw data for the markdown report
import pickle
with open('C:/niam-bay/trading/backtest_results.pkl', 'wb') as f:
    pickle.dump({
        'all_results': {p: {k: v for k, v in pr.items() if not isinstance(v, defaultdict) and k not in [s['name'] for s in strategies]} | {s['name']: {kk: (dict(vv) if isinstance(vv, defaultdict) else vv) for kk, vv in all_results[p][s['name']].items()} for s in strategies} for p, pr in all_results.items()},
        'cycle_analysis': {p: {k: dict(v) for k, v in ca.items()} for p, ca in cycle_analysis.items()},
        'vol_4h': {p: dict(v) for p, v in vol_4h_analysis.items()},
    }, f)
print("\nResults saved.")
