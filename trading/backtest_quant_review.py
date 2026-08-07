"""
Backtest Quant Review — Config actuelle vs Config recommandée
=============================================================
Compare la config Compounder actuelle ($139, x5, 5 niveaux, 1.2%)
avec la config recommandée par les 6 quants/scalpers (x3, 6 niveaux, 2 paires).

Données : 3 mois horaires (1h) — SOL, DOT, LINK, ADA, ETH
Engine : backtest_grid_realistic.py (maker fills, recenter, maxloss)

Résultat : tableau comparatif complet.
"""

import csv, sys, json
from pathlib import Path
from collections import defaultdict

DATA_DIR = Path(__file__).parent / "data"

# ── Load candles ──

def load_csv(filepath):
    candles = []
    with open(filepath, "r") as f:
        for row in csv.DictReader(f):
            candles.append({
                "o": float(row["open"]),
                "h": float(row["high"]),
                "l": float(row["low"]),
                "c": float(row["close"]),
            })
    return candles

def load_json_90d(filepath):
    """Load 90-day 4h JSON data (Kraken format or raw list)."""
    with open(filepath) as f:
        d = json.load(f)
    if isinstance(d, list):
        return [{"o": float(c[1]), "h": float(c[2]), "l": float(c[3]), "c": float(c[4])} for c in d]
    key = [k for k in d['result'] if k != 'last'][0]
    candles = d['result'][key]
    return [{"o": float(c[1]), "h": float(c[2]), "l": float(c[3]), "c": float(c[4])} for c in candles]

# ── Grid Engine (from backtest_grid_realistic.py, simplified) ──

MAKER_FEE = 0.0002
TAKER_FEE = 0.0005

def run_grid(candles, spacing_pct, num_levels, leverage, capital,
             max_loss_pct=25.0, use_maxloss=True):
    spacing = spacing_pct / 100.0
    cash = capital
    total_fees = 0.0
    round_trips = 0
    num_recenters = 0
    peak_equity = capital
    max_drawdown = 0.0
    stopped_out = False
    total_recenter_cost = 0.0

    center = candles[0]["c"]

    def make_grid(center_price):
        buys = [center_price * (1 - i * spacing) for i in range(1, num_levels + 1)]
        sells = [center_price * (1 + i * spacing) for i in range(1, num_levels + 1)]
        return buys, sells

    buy_levels, sell_levels = make_grid(center)
    buy_armed = [True] * num_levels
    sell_armed = [False] * num_levels
    positions = {}
    notional_per_level = (capital * leverage) / num_levels

    equity_curve = []

    for candle in candles:
        h, l, c = candle["h"], candle["l"], candle["c"]

        # Buy fills (maker: strict cross)
        buys_filled = 0
        for i in range(num_levels):
            if not buy_armed[i]:
                continue
            bp = buy_levels[i]
            if l < bp and buys_filled < 1:
                qty = notional_per_level / bp
                fee = qty * bp * MAKER_FEE
                cash -= fee
                total_fees += fee
                positions[i] = (bp, qty)
                buy_armed[i] = False
                sell_armed[i] = True
                buys_filled += 1

        # Sell fills
        sells_filled = 0
        for i in range(num_levels):
            if not sell_armed[i]:
                continue
            sp = sell_levels[i]
            if h > sp and sells_filled < 1:
                if i not in positions:
                    continue
                bp, qty = positions[i]
                fee = qty * sp * MAKER_FEE
                pnl = qty * (sp - bp) - fee
                cash += pnl
                total_fees += fee
                del positions[i]
                sell_armed[i] = False
                buy_armed[i] = True
                round_trips += 1
                sells_filled += 1

        # Mark to market
        unrealized = sum(qty * (c - bp) for bp, qty in positions.values())
        equity = cash + unrealized
        equity_curve.append(equity)

        if equity > peak_equity:
            peak_equity = equity
        dd = (peak_equity - equity) / peak_equity * 100 if peak_equity > 0 else 0
        max_drawdown = max(max_drawdown, dd)

        # Max loss check
        if use_maxloss and equity <= capital * (1 - max_loss_pct / 100):
            for i, (bp, qty) in list(positions.items()):
                fee = qty * c * TAKER_FEE
                pnl = qty * (c - bp) - fee
                cash += pnl
                total_fees += fee
            positions.clear()
            stopped_out = True
            break

        # Recenter check
        upper_bound = center * (1 + (num_levels + 1) * spacing)
        lower_bound = center * (1 - (num_levels + 1) * spacing)

        if c > upper_bound or c < lower_bound:
            recenter_cost = 0
            for i, (bp, qty) in list(positions.items()):
                fee = qty * c * TAKER_FEE
                pnl = qty * (c - bp) - fee
                cash += pnl
                total_fees += fee
                recenter_cost += abs(pnl)
            positions.clear()
            total_recenter_cost += recenter_cost

            num_recenters += 1
            center = c
            buy_levels, sell_levels = make_grid(center)
            buy_armed = [True] * num_levels
            sell_armed = [False] * num_levels

            current_eq = cash
            if current_eq > 0:
                notional_per_level = (current_eq * leverage) / num_levels

    # Close remaining
    if not stopped_out:
        final_price = candles[-1]["c"]
        for i, (bp, qty) in list(positions.items()):
            fee = qty * final_price * TAKER_FEE
            pnl = qty * (final_price - bp) - fee
            cash += pnl
            total_fees += fee

    net_profit = cash - capital
    roi_pct = (net_profit / capital) * 100

    return {
        "net_profit": round(net_profit, 2),
        "roi_pct": round(roi_pct, 1),
        "round_trips": round_trips,
        "recenters": num_recenters,
        "recenter_cost": round(total_recenter_cost, 2),
        "max_dd_pct": round(max_drawdown, 1),
        "total_fees": round(total_fees, 2),
        "stopped": stopped_out,
        "profit_per_rt": round(net_profit / max(round_trips, 1), 4),
        "final_equity": round(cash, 2),
    }


# ── Run all configs ──

PAIRS_1H = {
    "SOL": DATA_DIR / "SOLUSD_1h_3mo.csv",
    "DOT": DATA_DIR / "DOTUSD_1h_3mo.csv",
    "LINK": DATA_DIR / "LINKUSD_15m.csv",  # 15m if no 1h
    "ADA": DATA_DIR / "ADAUSD_1h_3mo.csv",
    "ETH": DATA_DIR / "ETHUSD_1h_3mo.csv",
}

# Also use 90d JSON (4h candles) for pairs that have it
PAIRS_90D = {
    "SOL": DATA_DIR / "SOLUSD_90d.json",
    "DOT": DATA_DIR / "DOTUSD_90d.json",
    "LINK": DATA_DIR / "LINKUSD_90d.json",
    "ATOM": DATA_DIR / "ATOMUSD_90d.json",
    "AVAX": DATA_DIR / "AVAXUSD_90d.json",
}

TOTAL_CAPITAL = 139.0

# Config 1: ACTUELLE — Compounder (SOL + LINK + ADA, x5, 1.2%, 5 niveaux)
CONFIG_ACTUELLE = {
    "name": "COMPOUNDER ACTUEL",
    "pairs": ["SOL", "LINK", "ADA"],
    "leverage": 5,
    "spacing": 1.2,
    "levels": 5,
    "capital_per_pair": TOTAL_CAPITAL / 3,  # ~$46.33
}

# Config 2: RECOMMANDÉE QUANTS — SOL x3 + LINK x5, 6 niveaux, réserve
CONFIG_RECOMMANDEE = {
    "name": "RECOMMANDÉ QUANTS",
    "pairs": ["SOL", "LINK"],
    "leverage_map": {"SOL": 3, "LINK": 5},
    "spacing_map": {"SOL": 1.2, "LINK": 0.8},
    "levels": 6,
    "capital_per_pair": 55.0,  # $29 en réserve
}

# Config 3: CONSERVATIVE — x3, 2%, 8 niveaux, 2 paires
CONFIG_CONSERVATIVE = {
    "name": "CONSERVATIVE x3",
    "pairs": ["SOL", "DOT"],
    "leverage": 3,
    "spacing": 2.0,
    "levels": 8,
    "capital_per_pair": 60.0,
}

# Config 4: AGGRESSIVE — x5, 0.8%, 10 niveaux, 1 paire (DOT seul)
CONFIG_AGGRESSIVE = {
    "name": "AGGRESSIVE DOT",
    "pairs": ["DOT"],
    "leverage": 5,
    "spacing": 0.8,
    "levels": 10,
    "capital_per_pair": 120.0,  # $19 réserve
}

# Config 5: SWEEP — test systematique sur DOT (meilleur backtest historique)
SWEEP_CONFIGS = []
for sp in [0.5, 0.8, 1.0, 1.2, 1.5, 2.0]:
    for lv in [3, 5]:
        for nl in [4, 6, 8]:
            SWEEP_CONFIGS.append({
                "spacing": sp,
                "leverage": lv,
                "levels": nl,
            })


def print_header(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


def run_config(config, candles_map):
    """Run a named config across its pairs."""
    results = {}
    total_profit = 0
    total_rts = 0
    worst_dd = 0

    for pair in config["pairs"]:
        if pair not in candles_map:
            continue
        candles = candles_map[pair]

        leverage = config.get("leverage_map", {}).get(pair, config.get("leverage", 5))
        spacing = config.get("spacing_map", {}).get(pair, config.get("spacing", 1.2))
        cap = config.get("capital_per_pair", TOTAL_CAPITAL / len(config["pairs"]))
        levels = config.get("levels", 6)

        r = run_grid(candles, spacing, levels, leverage, cap)
        results[pair] = r
        total_profit += r["net_profit"]
        total_rts += r["round_trips"]
        worst_dd = max(worst_dd, r["max_dd_pct"])

    return results, total_profit, total_rts, worst_dd


def print_results(config_name, results, total_profit, total_rts, worst_dd):
    print(f"\n  📊 {config_name}")
    print(f"  {'─'*60}")
    print(f"  {'Pair':<6} {'Profit':>8} {'ROI%':>7} {'RTs':>5} {'Recnt':>5} {'MaxDD%':>7} {'Fees':>7} {'Stop':>5}")
    print(f"  {'─'*60}")
    for pair, r in results.items():
        stop = "YES" if r["stopped"] else "no"
        print(f"  {pair:<6} ${r['net_profit']:>7} {r['roi_pct']:>6.1f}% {r['round_trips']:>5} {r['recenters']:>5} {r['max_dd_pct']:>6.1f}% ${r['total_fees']:>5} {stop:>5}")
    print(f"  {'─'*60}")
    roi_total = (total_profit / TOTAL_CAPITAL) * 100
    print(f"  TOTAL   ${total_profit:>7.2f}  {roi_total:>5.1f}%  {total_rts:>4} RT   MaxDD: {worst_dd:.1f}%")


if __name__ == "__main__":
    # Load all data
    print("\n  Loading data...")
    candles_1h = {}
    for pair, path in PAIRS_1H.items():
        if path.exists():
            candles_1h[pair] = load_csv(path)
            print(f"    {pair}: {len(candles_1h[pair])} candles (1h/15m)")

    candles_4h = {}
    for pair, path in PAIRS_90D.items():
        if path.exists():
            candles_4h[pair] = load_json_90d(path)
            print(f"    {pair}: {len(candles_4h[pair])} candles (4h/90d)")

    # Merge: prefer 1h, fallback to 4h
    all_candles = {**candles_4h, **candles_1h}

    # ═══════════════════════════════════════════════
    # TEST 1: Compare 4 configs sur données 1h (3 mois)
    # ═══════════════════════════════════════════════

    print_header("BACKTEST COMPARATIF — 4 CONFIGS × $139 × 3 MOIS")

    for config in [CONFIG_ACTUELLE, CONFIG_RECOMMANDEE, CONFIG_CONSERVATIVE, CONFIG_AGGRESSIVE]:
        results, tp, tr, wd = run_config(config, all_candles)
        print_results(config["name"], results, tp, tr, wd)

    # ═══════════════════════════════════════════════
    # TEST 2: Sweep DOT — meilleur combo spacing/levier/niveaux
    # ═══════════════════════════════════════════════

    print_header("SWEEP DOT — 36 COMBINAISONS (spacing × levier × niveaux)")
    print(f"\n  Capital: $100 par test | Données: {len(all_candles.get('DOT', []))} candles")
    print(f"  {'Spacing':>7} {'Lever':>5} {'Levels':>6} {'Profit':>8} {'ROI%':>7} {'RTs':>5} {'Recnt':>5} {'MaxDD%':>7} {'Stop':>5}")
    print(f"  {'─'*65}")

    best_roi = -999
    best_config = None
    sweep_results = []

    dot_candles = all_candles.get("DOT", [])
    if dot_candles:
        for sc in SWEEP_CONFIGS:
            r = run_grid(dot_candles, sc["spacing"], sc["levels"], sc["leverage"], 100.0)
            stop = "YES" if r["stopped"] else "no"
            sweep_results.append((sc, r))
            if r["roi_pct"] > best_roi:
                best_roi = r["roi_pct"]
                best_config = sc
            print(f"  {sc['spacing']:>6.1f}% {sc['leverage']:>4}x {sc['levels']:>5} ${r['net_profit']:>7} {r['roi_pct']:>6.1f}% {r['round_trips']:>5} {r['recenters']:>5} {r['max_dd_pct']:>6.1f}% {stop:>5}")

    if best_config:
        print(f"\n  🏆 BEST: spacing={best_config['spacing']}%, x{best_config['leverage']}, {best_config['levels']} levels → ROI {best_roi:.1f}%")

    # ═══════════════════════════════════════════════
    # TEST 3: Sweep SOL — mêmes combos
    # ═══════════════════════════════════════════════

    print_header("SWEEP SOL — 36 COMBINAISONS")
    print(f"\n  Capital: $100 par test | Données: {len(all_candles.get('SOL', []))} candles")
    print(f"  {'Spacing':>7} {'Lever':>5} {'Levels':>6} {'Profit':>8} {'ROI%':>7} {'RTs':>5} {'Recnt':>5} {'MaxDD%':>7} {'Stop':>5}")
    print(f"  {'─'*65}")

    best_roi_sol = -999
    best_config_sol = None

    sol_candles = all_candles.get("SOL", [])
    if sol_candles:
        for sc in SWEEP_CONFIGS:
            r = run_grid(sol_candles, sc["spacing"], sc["levels"], sc["leverage"], 100.0)
            stop = "YES" if r["stopped"] else "no"
            if r["roi_pct"] > best_roi_sol:
                best_roi_sol = r["roi_pct"]
                best_config_sol = sc
            print(f"  {sc['spacing']:>6.1f}% {sc['leverage']:>4}x {sc['levels']:>5} ${r['net_profit']:>7} {r['roi_pct']:>6.1f}% {r['round_trips']:>5} {r['recenters']:>5} {r['max_dd_pct']:>6.1f}% {stop:>5}")

    if best_config_sol:
        print(f"\n  🏆 BEST: spacing={best_config_sol['spacing']}%, x{best_config_sol['leverage']}, {best_config_sol['levels']} levels → ROI {best_roi_sol:.1f}%")

    # ═══════════════════════════════════════════════
    # TEST 4: Sweep LINK
    # ═══════════════════════════════════════════════

    print_header("SWEEP LINK — 36 COMBINAISONS")
    print(f"\n  Capital: $100 par test | Données: {len(all_candles.get('LINK', []))} candles")
    print(f"  {'Spacing':>7} {'Lever':>5} {'Levels':>6} {'Profit':>8} {'ROI%':>7} {'RTs':>5} {'Recnt':>5} {'MaxDD%':>7} {'Stop':>5}")
    print(f"  {'─'*65}")

    best_roi_link = -999
    best_config_link = None

    link_candles = all_candles.get("LINK", [])
    if link_candles:
        for sc in SWEEP_CONFIGS:
            r = run_grid(link_candles, sc["spacing"], sc["levels"], sc["leverage"], 100.0)
            stop = "YES" if r["stopped"] else "no"
            if r["roi_pct"] > best_roi_link:
                best_roi_link = r["roi_pct"]
                best_config_link = sc
            print(f"  {sc['spacing']:>6.1f}% {sc['leverage']:>4}x {sc['levels']:>5} ${r['net_profit']:>7} {r['roi_pct']:>6.1f}% {r['round_trips']:>5} {r['recenters']:>5} {r['max_dd_pct']:>6.1f}% {stop:>5}")

    if best_config_link:
        print(f"\n  🏆 BEST: spacing={best_config_link['spacing']}%, x{best_config_link['leverage']}, {best_config_link['levels']} levels → ROI {best_roi_link:.1f}%")

    # ═══════════════════════════════════════════════
    # RÉSUMÉ FINAL
    # ═══════════════════════════════════════════════

    print_header("RÉSUMÉ FINAL — RECOMMANDATION")
    print(f"""
  Capital total : ${TOTAL_CAPITAL}
  Période       : 3 mois de données historiques
  Engine        : Maker fills, recenter avec taker fees, maxloss 25%

  Meilleure config par paire :
    DOT  : spacing={best_config['spacing'] if best_config else '?'}%, x{best_config['leverage'] if best_config else '?'}, {best_config['levels'] if best_config else '?'} levels → ROI {best_roi:.1f}%
    SOL  : spacing={best_config_sol['spacing'] if best_config_sol else '?'}%, x{best_config_sol['leverage'] if best_config_sol else '?'}, {best_config_sol['levels'] if best_config_sol else '?'} levels → ROI {best_roi_sol:.1f}%
    LINK : spacing={best_config_link['spacing'] if best_config_link else '?'}%, x{best_config_link['leverage'] if best_config_link else '?'}, {best_config_link['levels'] if best_config_link else '?'} levels → ROI {best_roi_link:.1f}%
""")
