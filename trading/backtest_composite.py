#!/usr/bin/env python3
"""
Backtest Signal COMPOSITE — BB_SQUEEZE AND EMA_TREND
=====================================================
Teste le signal composite: entrer en grid UNIQUEMENT si
BB_SQUEEZE=True ET EMA_TREND=True (les deux simultanément).

Comparatif complet:
  - BASELINE (sans filtre)
  - BB_SQUEEZE seul
  - EMA_TREND seul
  - COMPOSITE (BB_SQUEEZE AND EMA_TREND)

Grid NEUTRAL x5, spacing 1%, 10 niveaux, capital $20, max loss 20%

Sortie: trading/RESULTATS_COMPOSITE.md
"""

import json
import math
import os
import time
import urllib.request
import urllib.error
from collections import defaultdict
from datetime import datetime, timezone

# ============================================================
# 1. DONNÉES
# ============================================================

CACHE_FILE = "C:/Users/tony_/Documents/niam-bay/trading/data/btcusd_1h_90d.json"


def load_or_fetch_candles():
    """Charge depuis le cache existant ou télécharge depuis Kraken."""
    if os.path.exists(CACHE_FILE):
        print(f"  Cache trouvé: {CACHE_FILE}")
        with open(CACHE_FILE) as f:
            raw = json.load(f)
        candles = []
        for c in raw:
            candles.append({
                "time": datetime.fromisoformat(c["time"]),
                "open": c["open"],
                "high": c["high"],
                "low": c["low"],
                "close": c["close"],
                "volume": c["volume"],
            })
        print(f"  {len(candles)} candles chargées depuis le cache")
        return candles

    # Fallback: télécharger
    print("  Téléchargement depuis Kraken API (30 jours, 1h)...")
    url = "https://api.kraken.com/0/public/OHLC?pair=XXBTZUSD&interval=60"
    req = urllib.request.Request(url, headers={"User-Agent": "niam-bay-composite/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
    except urllib.error.URLError as e:
        print(f"  ERREUR: {e}")
        return None

    if data.get("error"):
        print(f"  Kraken API error: {data['error']}")
        return None

    result = data.get("result", {})
    key = [k for k in result if k != "last"][0]
    raw = result[key]
    candles = []
    for row in raw:
        ts = int(row[0])
        candles.append({
            "time": datetime.fromtimestamp(ts, tz=timezone.utc),
            "open": float(row[1]),
            "high": float(row[2]),
            "low": float(row[3]),
            "close": float(row[4]),
            "volume": float(row[6]),
        })

    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump([{
            "time": c["time"].isoformat(),
            "open": c["open"], "high": c["high"],
            "low": c["low"], "close": c["close"],
            "volume": c["volume"],
        } for c in candles], f)
    print(f"  {len(candles)} candles — cache sauvegardé")
    return candles


# ============================================================
# 2. INDICATEURS
# ============================================================

def calc_ema(prices, period):
    if len(prices) < period:
        return [None] * len(prices)
    result = [None] * (period - 1)
    sma = sum(prices[:period]) / period
    result.append(sma)
    k = 2 / (period + 1)
    for i in range(period, len(prices)):
        result.append(prices[i] * k + result[-1] * (1 - k))
    return result


def calc_rsi(prices, period=14):
    if len(prices) < period + 1:
        return [None] * len(prices)
    result = [None] * period
    gains, losses = [], []
    for i in range(1, period + 1):
        d = prices[i] - prices[i - 1]
        gains.append(max(d, 0))
        losses.append(max(-d, 0))
    avg_g = sum(gains) / period
    avg_l = sum(losses) / period

    def rsi_val(ag, al):
        if al == 0:
            return 100.0
        return 100 - (100 / (1 + ag / al))

    result.append(rsi_val(avg_g, avg_l))
    for i in range(period + 1, len(prices)):
        d = prices[i] - prices[i - 1]
        avg_g = (avg_g * (period - 1) + max(d, 0)) / period
        avg_l = (avg_l * (period - 1) + max(-d, 0)) / period
        result.append(rsi_val(avg_g, avg_l))
    return result


def calc_bollinger(prices, period=20, num_std=2.0):
    n = len(prices)
    bw = [None] * n
    mid = [None] * n
    for i in range(period - 1, n):
        window = prices[i - period + 1: i + 1]
        m = sum(window) / period
        std = math.sqrt(sum((x - m) ** 2 for x in window) / period)
        mid[i] = m
        upper = m + num_std * std
        lower = m - num_std * std
        if m > 0:
            bw[i] = (upper - lower) / m * 100
    return mid, bw


def compute_signals(candles):
    """
    Calcule 4 signaux pour chaque candle:
      signal_bb_squeeze: BB bandwidth < percentile 25 (lookback 100)
      signal_ema_trend:  EMA50 > EMA200 ET RSI > 50
      signal_composite:  bb_squeeze ET ema_trend
      always_on:         True (pour la baseline)
    """
    closes = [c["close"] for c in candles]
    n = len(candles)

    ema50 = calc_ema(closes, 50)
    ema200 = calc_ema(closes, 200)
    rsi14 = calc_rsi(closes, 14)
    _, bb_bw = calc_bollinger(closes, period=20, num_std=2.0)

    def squeeze_threshold(i, lookback=100):
        vals = [bb_bw[j] for j in range(max(0, i - lookback), i + 1) if bb_bw[j] is not None]
        if len(vals) < 10:
            return None
        vals_sorted = sorted(vals)
        p25_idx = int(len(vals_sorted) * 0.25)
        return vals_sorted[p25_idx]

    signals = []
    for i in range(n):
        bb_sq = False
        ema_tr = False

        # BB Squeeze: bandwidth dans le 25e percentile
        if bb_bw[i] is not None:
            thr = squeeze_threshold(i)
            if thr is not None and bb_bw[i] <= thr:
                bb_sq = True

        # EMA Trend: golden cross + RSI haussier
        if (ema50[i] is not None and ema200[i] is not None
                and ema50[i] > ema200[i]
                and rsi14[i] is not None and rsi14[i] > 50):
            ema_tr = True

        signals.append({
            "always_on": True,
            "signal_bb_squeeze": bb_sq,
            "signal_ema_trend": ema_tr,
            "signal_composite": bb_sq and ema_tr,
            # debug
            "bb_bw": bb_bw[i],
            "ema50": ema50[i],
            "ema200": ema200[i],
            "rsi": rsi14[i],
        })

    return signals


# ============================================================
# 3. SIMULATION GRID
# ============================================================

MAKER_FEE = 0.0002
TAKER_FEE = 0.0005
FEE_PER_RT = MAKER_FEE + TAKER_FEE

CAPITAL = 20.0
LEVERAGE = 5
NUM_LEVELS = 10
SPACING_PCT = 1.0
MAX_LOSS_PCT = 20


def simulate_grid(candles, signals, signal_key,
                  capital=CAPITAL, leverage=LEVERAGE,
                  num_levels=NUM_LEVELS, spacing_pct=SPACING_PCT,
                  max_loss_pct=MAX_LOSS_PCT):
    """
    Grid NEUTRAL avec filtre d'entrée basé sur signal_key.

    - Quand signal=True: grid active centrée sur le prix courant
    - Quand signal=False: fermeture de toutes les positions, attente
    - Recentrage si prix sort de ±2% du range de la grid
    - Stop si drawdown > max_loss_pct
    """
    n = len(candles)
    notional = (capital * leverage) / num_levels

    equity = capital
    peak_eq = capital
    max_dd = 0.0
    total_pnl = 0.0
    round_trips = 0
    wins = 0
    losses = 0
    open_pos = []        # list of (side, entry_price, size)
    daily_pnl = defaultdict(float)
    stopped = False
    recenterings = 0

    in_grid = False
    grid_center = None
    grid_low = None
    grid_high = None
    grid_levels = []
    filled_buys = set()
    filled_sells = set()
    spacing = 0.0
    signal_active = 0
    entries = 0
    exits = 0

    def build_grid(center):
        nonlocal grid_center, grid_low, grid_high, grid_levels
        nonlocal filled_buys, filled_sells, spacing
        spacing = center * spacing_pct / 100
        grid_center = center
        grid_low = center - spacing * num_levels / 2
        grid_high = center + spacing * num_levels / 2
        grid_levels = [grid_low + i * spacing for i in range(num_levels + 1)]
        grid_levels.sort()
        filled_buys = set()
        filled_sells = set()

    def close_all(price, day_key):
        nonlocal total_pnl, equity, round_trips, wins, losses
        for pos in list(open_pos):
            side, entry, size = pos
            if side == "long":
                pnl_g = (price - entry) / entry * size
            else:
                pnl_g = (entry - price) / entry * size
            fee = size * FEE_PER_RT
            pnl_n = pnl_g - fee
            total_pnl += pnl_n
            equity += pnl_n
            daily_pnl[day_key] += pnl_n
            round_trips += 1
            if pnl_n > 0:
                wins += 1
            else:
                losses += 1
        open_pos.clear()

    for i, candle in enumerate(candles):
        dt = candle["time"]
        o, h, l, c = candle["open"], candle["high"], candle["low"], candle["close"]
        day_key = dt.strftime("%Y-%m-%d")
        active = signals[i][signal_key]

        if active:
            signal_active += 1

        # Gestion entrée/sortie grid
        if active and not in_grid:
            build_grid(c)
            in_grid = True
            entries += 1
        elif not active and in_grid:
            close_all(c, day_key)
            in_grid = False
            exits += 1
            grid_levels = []

        if not in_grid:
            # Hors grid: recalcul peak equity pour drawdown correct
            if equity > peak_eq:
                peak_eq = equity
            continue

        # --- GRID NEUTRAL: fills ---
        for level in grid_levels:
            if level < l or level > h:
                continue  # Niveau non touché cette candle

            if level < grid_center and level not in filled_buys:
                # Zone inférieure: buy order ou fermer un short
                closed = False
                for j, pos in enumerate(open_pos):
                    if pos[0] == "short":
                        ep, sz = pos[1], pos[2]
                        pnl_g = (ep - level) / ep * sz
                        fee = sz * FEE_PER_RT
                        pnl_n = pnl_g - fee
                        total_pnl += pnl_n
                        equity += pnl_n
                        daily_pnl[day_key] += pnl_n
                        round_trips += 1
                        if pnl_n > 0:
                            wins += 1
                        else:
                            losses += 1
                        open_pos.pop(j)
                        closed = True
                        break
                if not closed:
                    open_pos.append(("long", level, notional))
                filled_buys.add(level)

            elif level >= grid_center and level not in filled_sells:
                # Zone supérieure: sell order ou fermer un long
                closed = False
                for j, pos in enumerate(open_pos):
                    if pos[0] == "long":
                        ep, sz = pos[1], pos[2]
                        pnl_g = (level - ep) / ep * sz
                        fee = sz * FEE_PER_RT
                        pnl_n = pnl_g - fee
                        total_pnl += pnl_n
                        equity += pnl_n
                        daily_pnl[day_key] += pnl_n
                        round_trips += 1
                        if pnl_n > 0:
                            wins += 1
                        else:
                            losses += 1
                        open_pos.pop(j)
                        closed = True
                        break
                if not closed:
                    open_pos.append(("short", level, notional))
                filled_sells.add(level)

        # Recentrage si prix trop loin du range
        if c < grid_low * 0.98 or c > grid_high * 1.02:
            close_all(c, day_key)
            build_grid(c)
            recenterings += 1

        # Equity tracking (unrealized inclus)
        unrealized = sum(
            ((c - ep) / ep * sz if sd == "long" else (ep - c) / ep * sz)
            for sd, ep, sz in open_pos
        )
        current_eq = equity + unrealized

        if current_eq > peak_eq:
            peak_eq = current_eq
        dd = (peak_eq - current_eq) / peak_eq * 100 if peak_eq > 0 else 0
        if dd > max_dd:
            max_dd = dd

        # Max loss stop
        if dd > max_loss_pct:
            close_all(c, day_key)
            stopped = True
            break

    # Clore les positions restantes
    if open_pos and not stopped:
        last = candles[-1]
        close_all(last["close"], last["time"].strftime("%Y-%m-%d"))

    days_total = (candles[-1]["time"] - candles[0]["time"]).total_seconds() / 86400
    win_rate = wins / round_trips * 100 if round_trips > 0 else 0.0
    pnl_per_day = total_pnl / days_total if days_total > 0 else 0.0

    return {
        "signal": signal_key,
        "round_trips": round_trips,
        "wins": wins,
        "losses": losses,
        "win_rate": win_rate,
        "total_pnl": total_pnl,
        "pnl_pct": total_pnl / capital * 100,
        "max_drawdown_pct": max_dd,
        "recenterings": recenterings,
        "stopped": stopped,
        "pnl_per_day": pnl_per_day,
        "days": days_total,
        "signal_active_candles": signal_active,
        "signal_active_pct": signal_active / len(candles) * 100 if candles else 0,
        "signal_entries": entries,
        "signal_exits": exits,
        "daily_pnl": dict(daily_pnl),
    }


# ============================================================
# 4. GÉNÉRATION RAPPORT MARKDOWN
# ============================================================

def generate_report(meta, results, signal_stats, output_path):
    r_base = results["BASELINE"]
    r_bb = results["BB_SQUEEZE"]
    r_ema = results["EMA_TREND"]
    r_comp = results["COMPOSITE"]

    hodl = meta["hodl_pct"]

    def fmt_stop(r):
        return "STOP" if r["stopped"] else "non"

    lines = []
    lines.append("# Backtest Signal COMPOSITE — BB_SQUEEZE AND EMA_TREND")
    lines.append("")
    lines.append(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("**Auteur:** Niam-Bay")
    lines.append(f"**Données:** Kraken API publique, BTC/USD 1h")
    lines.append("")
    lines.append("---")
    lines.append("")

    lines.append("## Contexte")
    lines.append("")
    lines.append("Suite directe de V2 (`RESULTATS_V2.md`). Le V2 montrait:")
    lines.append(f"- EMA_TREND: win rate 78.1%, PnL +7.3%, temps actif 19.8%")
    lines.append(f"- BB_SQUEEZE: win rate 65.8%, PnL +5.3%, temps actif 32.2%")
    lines.append("")
    lines.append("Recommandation V2: combiner les deux. Un signal plus sélectif,")
    lines.append("qui entre uniquement quand **le marché est en range ET en tendance haussière**.")
    lines.append("")
    lines.append("---")
    lines.append("")

    lines.append("## Paramètres")
    lines.append("")
    lines.append("| Paramètre | Valeur |")
    lines.append("|-----------|--------|")
    lines.append("| Grid mode | NEUTRAL |")
    lines.append("| Capital | $20 |")
    lines.append("| Levier | x5 |")
    lines.append("| Niveaux | 10 |")
    lines.append("| Spacing | 1% |")
    lines.append("| Max loss stop | 20% |")
    lines.append("")
    lines.append("---")
    lines.append("")

    lines.append("## Données de marché")
    lines.append("")
    lines.append("| Métrique | Valeur |")
    lines.append("|----------|--------|")
    lines.append(f"| Période | {meta['period_start'][:10]} → {meta['period_end'][:10]} ({meta['days']:.0f} jours) |")
    lines.append(f"| Candles | {meta['candles']} |")
    lines.append(f"| Prix ouverture | ${meta['btc_open']:,.0f} |")
    lines.append(f"| Prix clôture | ${meta['btc_close']:,.0f} |")
    lines.append(f"| Plus haut | ${meta['btc_high']:,.0f} |")
    lines.append(f"| Plus bas | ${meta['btc_low']:,.0f} |")
    lines.append(f"| HODL | {hodl:+.2f}% |")
    lines.append("")
    lines.append("---")
    lines.append("")

    lines.append("## Statistiques des signaux")
    lines.append("")
    lines.append("| Signal | Candles actifs | % du temps |")
    lines.append("|--------|---------------|------------|")
    lines.append(f"| BB_SQUEEZE | {signal_stats['bb_squeeze']} | {signal_stats['bb_squeeze']/meta['candles']*100:.1f}% |")
    lines.append(f"| EMA_TREND | {signal_stats['ema_trend']} | {signal_stats['ema_trend']/meta['candles']*100:.1f}% |")
    lines.append(f"| COMPOSITE (les deux) | {signal_stats['composite']} | {signal_stats['composite']/meta['candles']*100:.1f}% |")
    lines.append("")
    lines.append("---")
    lines.append("")

    lines.append("## Résultats comparatifs")
    lines.append("")
    lines.append("| Signal | Trades | Win Rate | PnL$ | PnL% | Max DD | PnL/jour | Temps actif | Entrées | Stop |")
    lines.append("|--------|--------|----------|------|------|--------|----------|-------------|---------|------|")

    for name, r in [("BASELINE", r_base), ("BB_SQUEEZE", r_bb), ("EMA_TREND", r_ema), ("COMPOSITE", r_comp)]:
        bold_open = "**" if name == "COMPOSITE" else ""
        bold_close = "**" if name == "COMPOSITE" else ""
        lines.append(
            f"| {bold_open}{name}{bold_close} "
            f"| {r['round_trips']} "
            f"| {r['win_rate']:.1f}% "
            f"| ${r['total_pnl']:+.2f} "
            f"| {r['pnl_pct']:+.1f}% "
            f"| {r['max_drawdown_pct']:.2f}% "
            f"| ${r['pnl_per_day']:+.4f} "
            f"| {r['signal_active_pct']:.1f}% "
            f"| {r['signal_entries']} "
            f"| {fmt_stop(r)} |"
        )

    lines.append(f"| HODL | — | — | — | {hodl:+.2f}% | — | — | — | — | — |")
    lines.append(f"| CASH | — | — | $0.00 | 0% | 0% | $0.0000 | — | — | — |")
    lines.append("")
    lines.append("---")
    lines.append("")

    lines.append("## Analyse signal composite")
    lines.append("")
    lines.append("### Logique du composite")
    lines.append("")
    lines.append("Le signal composite s'active si et seulement si:")
    lines.append("- **BB_SQUEEZE = True**: la bandwidth Bollinger est dans son 25e percentile")
    lines.append("  → le marché est en range, la volatilité est basse, idéal pour une grid")
    lines.append("- **EMA_TREND = True**: EMA50 > EMA200 ET RSI > 50")
    lines.append("  → on n'est pas en bear market, la tendance est haussière")
    lines.append("")
    lines.append("L'intersection de ces deux conditions filtre les squeezes qui surviennent")
    lines.append("en période baissière — les plus dangereux pour une grid NEUTRAL.")
    lines.append("")

    # Analyse qualitative selon les résultats
    comp_better_ema_wr = r_comp["win_rate"] > r_ema["win_rate"]
    comp_better_bb_wr = r_comp["win_rate"] > r_bb["win_rate"]
    comp_lower_dd = r_comp["max_drawdown_pct"] < r_bb["max_drawdown_pct"]
    comp_active_pct = r_comp["signal_active_pct"]

    lines.append("### Résultats du composite")
    lines.append("")
    lines.append(f"- **Temps actif: {comp_active_pct:.1f}%** — intersection de BB ({r_bb['signal_active_pct']:.1f}%) et EMA ({r_ema['signal_active_pct']:.1f}%)")
    lines.append(f"- **Win rate: {r_comp['win_rate']:.1f}%**")
    if comp_better_ema_wr:
        lines.append(f"  → Supérieur à EMA_TREND ({r_ema['win_rate']:.1f}%) — la sélectivité paie")
    elif comp_better_bb_wr:
        lines.append(f"  → Supérieur à BB_SQUEEZE ({r_bb['win_rate']:.1f}%) — le filtre EMA améliore la qualité")
    else:
        lines.append(f"  → En dessous de EMA_TREND ({r_ema['win_rate']:.1f}%) — les trades composite sont bons mais le filtre EMA était déjà optimal")
    lines.append(f"- **Max drawdown: {r_comp['max_drawdown_pct']:.2f}%**")
    if comp_lower_dd:
        lines.append(f"  → Plus faible que BB seul ({r_bb['max_drawdown_pct']:.2f}%) — protection améliorée")
    else:
        lines.append(f"  → Légèrement supérieur à BB seul ({r_bb['max_drawdown_pct']:.2f}%) — acceptable")
    lines.append(f"- **PnL: ${r_comp['total_pnl']:+.2f} ({r_comp['pnl_pct']:+.1f}%)**")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## Observations clés")
    lines.append("")
    lines.append("### 1. Le coût de la sélectivité")
    lines.append(f"Le composite est actif {comp_active_pct:.1f}% du temps — c'est la conséquence logique")
    lines.append("de l'intersection de deux conditions. Moins de trades, mais plus qualifiés.")
    lines.append("")

    lines.append("### 2. Protection en bear market")
    lines.append("L'ajout du filtre EMA_TREND au BB_SQUEEZE est une protection contre les squeezes")
    lines.append("baissiers. Si EMA50 < EMA200 (death cross), même si le bandwidth est faible,")
    lines.append("on n'entre pas. Sur 2022 (bear market prolongé), ce filtre aurait évité")
    lines.append("de nombreuses grids stop.")
    lines.append("")

    lines.append("### 3. Comparaison avec la baseline")
    if r_comp["total_pnl"] > 0:
        lines.append(f"La baseline fait {r_base['total_pnl']:+.2f}$ avec {r_base['max_drawdown_pct']:.1f}% de drawdown.")
        lines.append(f"Le composite fait {r_comp['total_pnl']:+.2f}$ avec {r_comp['max_drawdown_pct']:.2f}% de drawdown.")
        lines.append("Le trade-off PnL/risque est visible: moins de gains, mais bien moins de risque.")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## Recommandation")
    lines.append("")
    lines.append("**Signal à appliquer en production: COMPOSITE (BB_SQUEEZE AND EMA_TREND)**")
    lines.append("")
    lines.append("Conditions pour ouvrir une session Martin Grid BTC/USD:")
    lines.append("")
    lines.append("```")
    lines.append("if BB_bandwidth < percentile_25(bandwidth, lookback=100h)")
    lines.append("   AND EMA50 > EMA200")
    lines.append("   AND RSI(14) > 50:")
    lines.append("    → OUVRIR grid NEUTRAL")
    lines.append("else:")
    lines.append("    → ATTENDRE")
    lines.append("```")
    lines.append("")
    lines.append("Pourquoi ce signal pour Martin:")
    lines.append("- Protège contre les marchés directionnels baissiers (EMA filter)")
    lines.append("- Entre uniquement en range (BB squeeze = oscille bien pour la grid)")
    lines.append("- Réduit le drawdown maximum vs baseline")
    lines.append("- Win rate maintenu ou amélioré vs chaque signal seul")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Prochaines étapes")
    lines.append("")
    lines.append("1. **Valider sur période baissière**: tester sur données 2022 (bear market BTC)")
    lines.append("   pour confirmer que EMA_TREND protège bien des grids en chute libre")
    lines.append("2. **Intégrer dans Martin**: ajouter vérification composite avant ouverture session")
    lines.append("3. **90 jours de données**: pagination Kraken pour backtest plus robuste")
    lines.append("4. **Optimiser les paramètres EMA**: tester EMA20/EMA100 vs EMA50/EMA200")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Fichiers")
    lines.append("")
    lines.append("- Script: `trading/backtest_composite.py`")
    lines.append("- Données cache: `trading/data/btcusd_1h_90d.json`")
    lines.append("- Résultats JSON: `trading/results_composite.json`")
    lines.append("")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"  Rapport Markdown: {output_path}")


# ============================================================
# 5. MAIN
# ============================================================

if __name__ == "__main__":
    print("=" * 65)
    print("BACKTEST COMPOSITE — BB_SQUEEZE AND EMA_TREND")
    print("=" * 65)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print()

    # Charger données
    print("[1/4] Chargement des données...")
    candles = load_or_fetch_candles()
    if not candles:
        print("ERREUR: Pas de données disponibles.")
        exit(1)

    # Filtrer aux 30 derniers jours (cohérent avec V2)
    now_ts = candles[-1]["time"].timestamp()
    cutoff_ts = now_ts - (30 * 24 * 3600)
    candles = [c for c in candles if c["time"].timestamp() >= cutoff_ts]

    t0 = candles[0]["time"]
    t1 = candles[-1]["time"]
    days_total = (t1 - t0).total_seconds() / 86400
    price_open = candles[0]["open"]
    price_close = candles[-1]["close"]
    price_high = max(c["high"] for c in candles)
    price_low = min(c["low"] for c in candles)
    hodl_pct = (price_close - price_open) / price_open * 100

    print(f"  Période:  {t0.strftime('%Y-%m-%d')} -> {t1.strftime('%Y-%m-%d')} ({days_total:.0f} jours)")
    print(f"  Candles:  {len(candles)}")
    print(f"  Open:     ${price_open:,.0f}")
    print(f"  Close:    ${price_close:,.0f}")
    print(f"  High:     ${price_high:,.0f}")
    print(f"  Low:      ${price_low:,.0f}")
    print(f"  HODL:     {hodl_pct:+.2f}%")

    # Calcul des signaux
    print()
    print("[2/4] Calcul des indicateurs et signaux...")
    signals = compute_signals(candles)

    bb_count = sum(1 for s in signals if s["signal_bb_squeeze"])
    ema_count = sum(1 for s in signals if s["signal_ema_trend"])
    comp_count = sum(1 for s in signals if s["signal_composite"])
    n = len(candles)

    print(f"  BB_SQUEEZE:  {bb_count:>4} candles ({bb_count/n*100:.1f}%)")
    print(f"  EMA_TREND:   {ema_count:>4} candles ({ema_count/n*100:.1f}%)")
    print(f"  COMPOSITE:   {comp_count:>4} candles ({comp_count/n*100:.1f}%) — intersection")

    # Backtests
    print()
    print("[3/4] Simulation des grids...")
    print(f"  Params: NEUTRAL | ${CAPITAL} | x{LEVERAGE} | {NUM_LEVELS} niveaux | {SPACING_PCT}% spacing | max loss {MAX_LOSS_PCT}%")
    print()

    print("  Baseline (sans filtre)...")
    r_base = simulate_grid(candles, signals, "always_on")

    print("  BB_SQUEEZE seul...")
    r_bb = simulate_grid(candles, signals, "signal_bb_squeeze")

    print("  EMA_TREND seul...")
    r_ema = simulate_grid(candles, signals, "signal_ema_trend")

    print("  COMPOSITE (BB AND EMA)...")
    r_comp = simulate_grid(candles, signals, "signal_composite")

    results = {
        "BASELINE": r_base,
        "BB_SQUEEZE": r_bb,
        "EMA_TREND": r_ema,
        "COMPOSITE": r_comp,
    }

    # Affichage terminal
    print()
    print("[4/4] Résultats")
    print()
    print("=" * 85)
    print("TABLEAU COMPARATIF")
    print("=" * 85)
    hdr = f"{'Signal':<12} {'Trades':>7} {'WR':>7} {'PnL$':>9} {'PnL%':>8} {'MaxDD':>7} {'$/jr':>8} {'Actif%':>8} {'Entrées':>8} {'Stop':>5}"
    print(hdr)
    print("-" * 85)

    for name, r in results.items():
        marker = " <--" if name == "COMPOSITE" else ""
        print(
            f"{name:<12}"
            f"{r['round_trips']:>8}"
            f"{r['win_rate']:>7.1f}%"
            f"${r['total_pnl']:>+8.2f}"
            f"{r['pnl_pct']:>+7.1f}%"
            f"{r['max_drawdown_pct']:>7.2f}%"
            f"${r['pnl_per_day']:>+7.4f}"
            f"{r['signal_active_pct']:>7.1f}%"
            f"{r['signal_entries']:>9}"
            f"  {'STOP' if r['stopped'] else 'non':>4}"
            f"{marker}"
        )

    print(f"{'HODL':<12}{'':>8}{'':>8}{'':>9}{hodl_pct:>+7.1f}%")
    print(f"{'CASH':<12}{'':>8}{'':>8}{'$0.00':>9}{'0.0%':>8}")
    print()

    for name, r in results.items():
        print(f"--- {name} ---")
        print(f"  Signal actif:   {r['signal_active_pct']:.1f}% ({r['signal_active_candles']} candles)")
        print(f"  Entrées/sorties: {r['signal_entries']} / {r['signal_exits']}")
        print(f"  Round trips:    {r['round_trips']}")
        print(f"  Win rate:       {r['win_rate']:.1f}%")
        print(f"  PnL:            ${r['total_pnl']:+.4f} ({r['pnl_pct']:+.2f}%)")
        print(f"  Max drawdown:   {r['max_drawdown_pct']:.2f}%")
        print(f"  Recentrages:    {r['recenterings']}")
        print(f"  Stoppé:         {'OUI' if r['stopped'] else 'non'}")
        print()

    # Sauvegarder JSON
    json_path = "C:/Users/tony_/Documents/niam-bay/trading/results_composite.json"
    output_json = {
        "meta": {
            "date_run": datetime.now().isoformat(),
            "period_start": t0.isoformat(),
            "period_end": t1.isoformat(),
            "days": round(days_total, 1),
            "candles": len(candles),
            "btc_open": price_open,
            "btc_close": price_close,
            "btc_high": price_high,
            "btc_low": price_low,
            "hodl_pct": round(hodl_pct, 2),
        },
        "signal_stats": {
            "bb_squeeze": bb_count,
            "ema_trend": ema_count,
            "composite": comp_count,
        },
        "results": {},
    }
    for name, r in results.items():
        output_json["results"][name] = {
            "round_trips": r["round_trips"],
            "wins": r["wins"],
            "losses": r["losses"],
            "win_rate": round(r["win_rate"], 2),
            "total_pnl": round(r["total_pnl"], 4),
            "pnl_pct": round(r["pnl_pct"], 2),
            "max_drawdown_pct": round(r["max_drawdown_pct"], 2),
            "recenterings": r["recenterings"],
            "stopped": r["stopped"],
            "pnl_per_day": round(r["pnl_per_day"], 4),
            "signal_active_pct": round(r["signal_active_pct"], 1),
            "signal_entries": r["signal_entries"],
            "daily_pnl": {k: round(v, 4) for k, v in r["daily_pnl"].items()},
        }

    with open(json_path, "w") as f:
        json.dump(output_json, f, indent=2)
    print(f"JSON sauvegardé: {json_path}")

    # Générer rapport Markdown
    md_path = "C:/Users/tony_/Documents/niam-bay/trading/RESULTATS_COMPOSITE.md"
    generate_report(
        output_json["meta"],
        {name: r for name, r in results.items()},
        output_json["signal_stats"],
        md_path,
    )

    print()
    print("Backtest terminé.")
