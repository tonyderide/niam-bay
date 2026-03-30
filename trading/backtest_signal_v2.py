#!/usr/bin/env python3
"""
Backtest Signal V2 — Filtres d'entrée pour grids Martin BTC/USD
=================================================================
Teste 3 signaux d'entrée combinés sur 90 jours de données 1h Kraken:

  Signal 1: RSI(14) < 35 + Stochastic < 20  (zone de survente = entrée long)
  Signal 2: EMA(50) > EMA(200) + RSI > 50   (tendance haussière confirmée)
  Signal 3: Bollinger Bands squeeze          (faible volatilité = bon pour grid)

Pour chaque signal: grid NEUTRAL x5, spacing 1%, 10 niveaux, capital $20

Métriques: win rate, PnL, max drawdown, nombre de trades
"""

import json
import math
import time
import urllib.request
import urllib.error
from collections import defaultdict
from datetime import datetime, timezone

# ============================================================
# 1. TÉLÉCHARGEMENT DONNÉES KRAKEN (API publique)
# ============================================================

KRAKEN_OHLC_URL = "https://api.kraken.com/0/public/OHLC"
CACHE_FILE = "C:/Users/tony_/Documents/niam-bay/trading/data/btcusd_1h_90d.json"


def fetch_kraken_ohlc(pair="XXBTZUSD", interval=60, since=None):
    """
    Télécharge les candles OHLC depuis l'API publique Kraken.
    interval=60 = 1 heure (en minutes)
    Retourne une liste de dicts {time, open, high, low, close, volume}
    """
    url = f"{KRAKEN_OHLC_URL}?pair={pair}&interval={interval}"
    if since:
        url += f"&since={since}"

    print(f"  Fetching: {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "niam-bay-backtest/2.0"})

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
    except urllib.error.URLError as e:
        print(f"  ERROR fetching: {e}")
        return None

    if data.get("error"):
        print(f"  Kraken API error: {data['error']}")
        return None

    result = data.get("result", {})
    ohlc_key = [k for k in result.keys() if k != "last"]
    if not ohlc_key:
        print("  ERROR: no OHLC data in response")
        return None

    raw = result[ohlc_key[0]]
    candles = []
    for row in raw:
        # row: [time, open, high, low, close, vwap, volume, count]
        ts = int(row[0])
        candles.append({
            "time": datetime.fromtimestamp(ts, tz=timezone.utc),
            "open": float(row[1]),
            "high": float(row[2]),
            "low": float(row[3]),
            "close": float(row[4]),
            "volume": float(row[6]),
        })

    return candles


def load_or_fetch_candles(days=90):
    """
    Charge depuis le cache ou télécharge les données.
    Kraken retourne max 720 candles par appel (1h = 720h = 30 jours).
    On fait plusieurs appels pour couvrir 90 jours.
    """
    import os

    # Try cache first
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

    print("  Téléchargement depuis Kraken API (90 jours, 1h)...")

    # Kraken retourne max 720 candles par appel.
    # 90 jours * 24h = 2160 candles — on fait 3 appels.
    now_ts = int(time.time())
    # Start: 90 jours avant maintenant
    start_ts = now_ts - (days * 24 * 3600)

    all_candles = []
    since = start_ts

    for attempt in range(5):  # max 5 appels
        batch = fetch_kraken_ohlc("XXBTZUSD", interval=60, since=since)
        if not batch:
            break

        # Filtrer les candles avant notre since (Kraken inclut parfois les anciennes)
        batch = [c for c in batch if c["time"].timestamp() >= since]

        if not batch:
            break

        all_candles.extend(batch)
        last_ts = int(batch[-1]["time"].timestamp())

        print(f"    Batch {attempt+1}: {len(batch)} candles, dernière: {batch[-1]['time']}")

        # Si on a assez
        if last_ts >= now_ts - 3600:
            break

        since = last_ts + 1
        time.sleep(1)  # Respect rate limit Kraken

    # Dédupliquer et trier
    seen = set()
    unique = []
    for c in all_candles:
        ts = c["time"].timestamp()
        if ts not in seen:
            seen.add(ts)
            unique.append(c)
    unique.sort(key=lambda x: x["time"])

    print(f"  Total: {len(unique)} candles uniques")

    # Sauvegarder le cache
    import os
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    to_save = [{
        "time": c["time"].isoformat(),
        "open": c["open"], "high": c["high"],
        "low": c["low"], "close": c["close"],
        "volume": c["volume"],
    } for c in unique]
    with open(CACHE_FILE, "w") as f:
        json.dump(to_save, f)
    print(f"  Cache sauvegardé: {CACHE_FILE}")

    return unique


# ============================================================
# 2. INDICATEURS TECHNIQUES
# ============================================================

def calc_ema(prices, period):
    """EMA — retourne liste de même longueur (None pour les premiers)."""
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
    """RSI Wilder — retourne liste (None pour les premiers)."""
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


def calc_stochastic(highs, lows, closes, k_period=14, d_period=3):
    """
    Stochastic %K et %D.
    %K = (close - lowest_low) / (highest_high - lowest_low) * 100
    %D = SMA(%K, d_period)
    Retourne (k_list, d_list).
    """
    n = len(closes)
    k_list = [None] * n

    for i in range(k_period - 1, n):
        lo = min(lows[i - k_period + 1: i + 1])
        hi = max(highs[i - k_period + 1: i + 1])
        if hi == lo:
            k_list[i] = 50.0
        else:
            k_list[i] = (closes[i] - lo) / (hi - lo) * 100

    # %D = SMA de %K sur d_period
    d_list = [None] * n
    for i in range(k_period - 1 + d_period - 1, n):
        vals = [k_list[j] for j in range(i - d_period + 1, i + 1) if k_list[j] is not None]
        if len(vals) == d_period:
            d_list[i] = sum(vals) / d_period

    return k_list, d_list


def calc_bollinger(prices, period=20, num_std=2.0):
    """
    Bollinger Bands.
    Retourne (mid, upper, lower, bandwidth) — toutes listes.
    bandwidth = (upper - lower) / mid * 100 (en %)
    Squeeze = bandwidth faible (< seuil).
    """
    n = len(prices)
    mid = [None] * n
    upper = [None] * n
    lower = [None] * n
    bandwidth = [None] * n

    for i in range(period - 1, n):
        window = prices[i - period + 1: i + 1]
        m = sum(window) / period
        std = math.sqrt(sum((x - m) ** 2 for x in window) / period)
        mid[i] = m
        upper[i] = m + num_std * std
        lower[i] = m - num_std * std
        if m > 0:
            bandwidth[i] = (upper[i] - lower[i]) / m * 100

    return mid, upper, lower, bandwidth


# ============================================================
# 3. SIGNAUX D'ENTRÉE
# ============================================================

def compute_signals(candles):
    """
    Calcule les indicateurs et détermine le signal pour chaque candle.

    Signal 1: RSI_STOCH_OVERSOLD
        RSI(14) < 35 ET Stochastic %K < 20
        Zone de survente — potentiel rebond — idéal pour ouvrir une grid NEUTRAL

    Signal 2: EMA_TREND_BULL
        EMA(50) > EMA(200) ET RSI(14) > 50
        Tendance haussière confirmée — grid NEUTRAL dans un bull market

    Signal 3: BB_SQUEEZE
        Bollinger bandwidth < percentile 25 des 100 derniers jours
        Faible volatilité = range = parfait pour grid
    """
    closes = [c["close"] for c in candles]
    highs = [c["high"] for c in candles]
    lows = [c["low"] for c in candles]
    n = len(candles)

    ema50 = calc_ema(closes, 50)
    ema200 = calc_ema(closes, 200)
    rsi14 = calc_rsi(closes, 14)
    stoch_k, stoch_d = calc_stochastic(highs, lows, closes, k_period=14, d_period=3)
    bb_mid, bb_upper, bb_lower, bb_bw = calc_bollinger(closes, period=20, num_std=2.0)

    # Percentile dynamique pour le squeeze: on regarde les 100 dernières valeurs valides
    def bb_squeeze_threshold(i, lookback=100):
        """25e percentile du bandwidth sur les lookback dernières valeurs."""
        vals = [bb_bw[j] for j in range(max(0, i - lookback), i + 1) if bb_bw[j] is not None]
        if len(vals) < 10:
            return None
        vals_sorted = sorted(vals)
        p25_idx = int(len(vals_sorted) * 0.25)
        return vals_sorted[p25_idx]

    signals = []
    for i in range(n):
        s = {
            "signal1_rsi_stoch": False,
            "signal2_ema_trend": False,
            "signal3_bb_squeeze": False,
            "rsi": rsi14[i],
            "stoch_k": stoch_k[i],
            "ema50": ema50[i],
            "ema200": ema200[i],
            "bb_bw": bb_bw[i],
        }

        # Signal 1: RSI survente + Stoch survente
        if (rsi14[i] is not None and rsi14[i] < 35
                and stoch_k[i] is not None and stoch_k[i] < 20):
            s["signal1_rsi_stoch"] = True

        # Signal 2: Golden cross (EMA50 > EMA200) + momentum haussier
        if (ema50[i] is not None and ema200[i] is not None
                and ema50[i] > ema200[i]
                and rsi14[i] is not None and rsi14[i] > 50):
            s["signal2_ema_trend"] = True

        # Signal 3: Bollinger squeeze
        if bb_bw[i] is not None:
            threshold = bb_squeeze_threshold(i)
            if threshold is not None and bb_bw[i] <= threshold:
                s["signal3_bb_squeeze"] = True

        signals.append(s)

    return signals


# ============================================================
# 4. SIMULATION GRID MARTIN
# ============================================================

MAKER_FEE = 0.0002
TAKER_FEE = 0.0005
FEE_PER_RT = MAKER_FEE + TAKER_FEE

CAPITAL = 20.0      # $20
LEVERAGE = 5        # x5
NUM_LEVELS = 10     # 10 niveaux
SPACING_PCT = 1.0   # 1% entre chaque niveau
MODE = "NEUTRAL"


def simulate_grid_with_signal(candles, signals, signal_key,
                               capital=CAPITAL, leverage=LEVERAGE,
                               num_levels=NUM_LEVELS, spacing_pct=SPACING_PCT,
                               mode=MODE, max_loss_pct=20):
    """
    Simule une grid Martin NEUTRAL avec filtre d'entrée basé sur signal_key.

    Logique:
    - Si signal actif: on est "en grid" (positions peuvent s'ouvrir)
    - Si signal inactif: on ferme la grid et on attend
    - Le grid se centre sur le prix au moment où le signal s'active
    - Recenter si prix sort de ±2% du range

    Retourne dict avec métriques.
    """
    n = len(candles)
    notional_per_level = (capital * leverage) / num_levels

    equity = capital
    peak_equity = capital
    max_dd_pct = 0.0
    total_pnl = 0.0
    round_trips = 0
    wins = 0
    losses = 0
    open_positions = []
    daily_pnl = defaultdict(float)
    equity_curve = []
    stopped = False
    recenterings = 0

    # Grid state
    in_grid = False
    grid_center = None
    grid_low = None
    grid_high = None
    grid_levels = []
    filled_buys = set()
    filled_sells = set()
    spacing = 0.0

    # Stats signal
    signal_active_candles = 0
    signal_entries = 0       # Nombre de fois qu'on entre en grid
    signal_exits = 0         # Nombre de fois qu'on sort de grid

    def build_grid(center):
        nonlocal grid_center, grid_low, grid_high, grid_levels, filled_buys, filled_sells, spacing
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
        for pos in open_positions:
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
        open_positions.clear()

    for i, candle in enumerate(candles):
        dt = candle["time"]
        o, h, l, c = candle["open"], candle["high"], candle["low"], candle["close"]
        day_key = dt.strftime("%Y-%m-%d")
        sig = signals[i]
        active = sig[signal_key]

        if active:
            signal_active_candles += 1

        # --- Entrée / Sortie de grid selon signal ---
        if active and not in_grid:
            # Signal vient de s'activer: on ouvre la grid
            build_grid(c)
            in_grid = True
            signal_entries += 1

        elif not active and in_grid:
            # Signal éteint: on ferme tout et on attend
            close_all(c, day_key)
            in_grid = False
            signal_exits += 1
            grid_levels = []

        if not in_grid:
            # Hors grid: on track l'equity sans position
            current_equity = equity
            equity_curve.append((dt.isoformat(), current_equity, c, "WAIT"))
            if current_equity > peak_equity:
                peak_equity = current_equity
            continue

        # --- GRID LOGIC (NEUTRAL mode) ---
        for level in grid_levels:
            if level < l or level > h:
                continue

            if level < grid_center and level not in filled_buys:
                # Zone achat
                closed_short = False
                for j, pos in enumerate(open_positions):
                    if pos[0] == "short":
                        ep, sz = pos[1], pos[2]
                        pnl_g = (ep - level) / ep * sz
                        fee = sz * FEE_PER_RT
                        pnl_n = pnl_g - fee
                        total_pnl += pnl_n
                        equity += pnl_n
                        daily_pnl[day_key] += pnl_n
                        round_trips += 1
                        if pnl_n > 0: wins += 1
                        else: losses += 1
                        open_positions.pop(j)
                        closed_short = True
                        break
                if not closed_short:
                    open_positions.append(("long", level, notional_per_level))
                filled_buys.add(level)

            elif level >= grid_center and level not in filled_sells:
                # Zone vente
                closed_long = False
                for j, pos in enumerate(open_positions):
                    if pos[0] == "long":
                        ep, sz = pos[1], pos[2]
                        pnl_g = (level - ep) / ep * sz
                        fee = sz * FEE_PER_RT
                        pnl_n = pnl_g - fee
                        total_pnl += pnl_n
                        equity += pnl_n
                        daily_pnl[day_key] += pnl_n
                        round_trips += 1
                        if pnl_n > 0: wins += 1
                        else: losses += 1
                        open_positions.pop(j)
                        closed_long = True
                        break
                if not closed_long:
                    open_positions.append(("short", level, notional_per_level))
                filled_sells.add(level)

        # --- RECENTER si prix sort du range ---
        if c < grid_low * 0.98 or c > grid_high * 1.02:
            close_all(c, day_key)
            build_grid(c)
            recenterings += 1

        # --- EQUITY TRACKING ---
        unrealized = sum(
            ((c - ep) / ep * sz if sd == "long" else (ep - c) / ep * sz)
            for sd, ep, sz in open_positions
        )
        current_equity = equity + unrealized
        equity_curve.append((dt.isoformat(), current_equity, c, "GRID"))

        if current_equity > peak_equity:
            peak_equity = current_equity
        dd_pct = (peak_equity - current_equity) / peak_equity * 100 if peak_equity > 0 else 0
        if dd_pct > max_dd_pct:
            max_dd_pct = dd_pct

        # --- MAX LOSS STOP ---
        if max_loss_pct and dd_pct > max_loss_pct:
            close_all(c, day_key)
            stopped = True
            break

    # Fermer positions restantes
    if open_positions and not stopped:
        last = candles[-1]
        close_all(last["close"], last["time"].strftime("%Y-%m-%d"))

    days = (candles[-1]["time"] - candles[0]["time"]).total_seconds() / 86400
    win_rate = wins / round_trips * 100 if round_trips > 0 else 0
    pnl_per_day = total_pnl / days if days > 0 else 0
    hodl_pct = (candles[-1]["close"] - candles[0]["close"]) / candles[0]["close"] * 100

    return {
        "signal": signal_key,
        "capital": capital,
        "leverage": leverage,
        "num_levels": num_levels,
        "spacing_pct": spacing_pct,
        "mode": mode,
        "round_trips": round_trips,
        "wins": wins,
        "losses": losses,
        "win_rate": win_rate,
        "total_pnl": total_pnl,
        "pnl_pct": total_pnl / capital * 100,
        "max_drawdown_pct": max_dd_pct,
        "recenterings": recenterings,
        "stopped": stopped,
        "pnl_per_day": pnl_per_day,
        "days": days,
        "hodl_pct": hodl_pct,
        "signal_active_candles": signal_active_candles,
        "signal_entries": signal_entries,
        "signal_exits": signal_exits,
        "signal_active_pct": signal_active_candles / len(candles) * 100 if candles else 0,
        "daily_pnl": dict(daily_pnl),
        "equity_curve": equity_curve[:100],  # sample pour éviter fichier trop gros
    }


def simulate_baseline_no_signal(candles, capital=CAPITAL, leverage=LEVERAGE,
                                  num_levels=NUM_LEVELS, spacing_pct=SPACING_PCT,
                                  mode=MODE, max_loss_pct=20):
    """
    Baseline: grid toujours active (sans filtre de signal).
    Pour comparer avec les signaux filtrés.
    """
    # On crée un signal toujours True
    fake_signals = [{"always_on": True} for _ in candles]
    return simulate_grid_with_signal(
        candles, fake_signals, "always_on",
        capital, leverage, num_levels, spacing_pct, mode, max_loss_pct
    )


# ============================================================
# 5. MAIN
# ============================================================

if __name__ == "__main__":
    print("=" * 65)
    print("BACKTEST SIGNAL V2 — Filtres d'entrée Martin Grid BTC/USD")
    print("=" * 65)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print()

    # --- Charger les données ---
    print("[1/4] Chargement des données (90 jours, 1h)...")
    candles = load_or_fetch_candles(days=90)

    if not candles:
        print("ERREUR: Pas de données disponibles.")
        exit(1)

    # Filtrer aux 90 derniers jours
    now_ts = candles[-1]["time"].timestamp()
    cutoff_ts = now_ts - (90 * 24 * 3600)
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

    # --- Calculer les signaux ---
    print()
    print("[2/4] Calcul des indicateurs et signaux...")
    signals = compute_signals(candles)

    # Statistiques des signaux
    s1_count = sum(1 for s in signals if s["signal1_rsi_stoch"])
    s2_count = sum(1 for s in signals if s["signal2_ema_trend"])
    s3_count = sum(1 for s in signals if s["signal3_bb_squeeze"])

    print(f"  Signal 1 (RSI<35 + Stoch<20):    {s1_count:>4} candles actifs ({s1_count/len(candles)*100:.1f}%)")
    print(f"  Signal 2 (EMA50>EMA200 + RSI>50): {s2_count:>4} candles actifs ({s2_count/len(candles)*100:.1f}%)")
    print(f"  Signal 3 (BB Squeeze):            {s3_count:>4} candles actifs ({s3_count/len(candles)*100:.1f}%)")

    # --- Backtests ---
    print()
    print("[3/4] Simulation des grids...")

    # Paramètres
    print(f"  Grid: NEUTRAL | Capital: ${CAPITAL} | Levier: x{LEVERAGE} | Levels: {NUM_LEVELS} | Spacing: {SPACING_PCT}%")
    print()

    # Baseline (sans filtre)
    print("  Baseline (sans filtre)...")
    r_baseline = simulate_baseline_no_signal(candles)

    # Signal 1
    print("  Signal 1: RSI<35 + Stoch<20...")
    r_s1 = simulate_grid_with_signal(candles, signals, "signal1_rsi_stoch")

    # Signal 2
    print("  Signal 2: EMA50>EMA200 + RSI>50...")
    r_s2 = simulate_grid_with_signal(candles, signals, "signal2_ema_trend")

    # Signal 3
    print("  Signal 3: BB Squeeze...")
    r_s3 = simulate_grid_with_signal(candles, signals, "signal3_bb_squeeze")

    results = {
        "BASELINE": r_baseline,
        "RSI+STOCH": r_s1,
        "EMA_TREND": r_s2,
        "BB_SQUEEZE": r_s3,
    }

    # --- Affichage résultats ---
    print()
    print("[4/4] Résultats")
    print()
    print("=" * 80)
    print("TABLEAU COMPARATIF")
    print("=" * 80)
    header = f"{'Signal':<12} {'RTs':>5} {'WR':>6} {'PnL$':>8} {'PnL%':>7} {'MaxDD':>7} {'$/jr':>7} {'Actif%':>7} {'Entrées':>8} {'Stop':>5}"
    print(header)
    print("-" * 80)

    for name, r in results.items():
        print(
            f"{name:<12} "
            f"{r['round_trips']:>5} "
            f"{r['win_rate']:>5.1f}% "
            f"${r['total_pnl']:>+6.2f} "
            f"{r['pnl_pct']:>+6.1f}% "
            f"{r['max_drawdown_pct']:>6.1f}% "
            f"${r['pnl_per_day']:>+5.3f} "
            f"{r['signal_active_pct']:>6.1f}% "
            f"{r['signal_entries']:>8} "
            f"{'OUI' if r['stopped'] else 'non':>5}"
        )

    print(f"{'HODL':>12}{'':>5}{'':>7}{'':>9}{hodl_pct:>+6.1f}%")
    print(f"{'CASH (0%)':>12}{'':>5}{'':>7}{'$0.00':>9}{'+0.0%':>8}")

    # Détails par signal
    for name, r in results.items():
        if name == "BASELINE":
            continue
        print()
        print(f"--- {name} ---")
        print(f"  Signal actif:     {r['signal_active_pct']:.1f}% du temps ({r['signal_active_candles']} candles)")
        print(f"  Entrées en grid:  {r['signal_entries']}")
        print(f"  Sorties de grid:  {r['signal_exits']}")
        print(f"  Round trips:      {r['round_trips']}")
        print(f"  Win rate:         {r['win_rate']:.1f}%")
        print(f"  PnL total:        ${r['total_pnl']:+.4f} ({r['pnl_pct']:+.1f}%)")
        print(f"  PnL/jour:         ${r['pnl_per_day']:+.4f}")
        print(f"  Max drawdown:     {r['max_drawdown_pct']:.2f}%")
        print(f"  Recentrages:      {r['recenterings']}")
        print(f"  Stoppé:           {'OUI' if r['stopped'] else 'non'}")

    # Détail PnL quotidien du meilleur signal
    best_name = max(
        [(n, r) for n, r in results.items()],
        key=lambda x: x[1]["total_pnl"]
    )[0]
    best_r = results[best_name]

    print()
    print(f"=== PnL Quotidien du meilleur signal ({best_name}) ===")
    for day in sorted(best_r["daily_pnl"].keys())[-30:]:  # 30 derniers jours
        bar = "#" * max(0, int(best_r["daily_pnl"][day] * 20))
        neg = "" if best_r["daily_pnl"][day] >= 0 else "-"
        print(f"  {day}: ${best_r['daily_pnl'][day]:>+7.4f} {bar}")

    # --- Sauvegarde JSON ---
    output = {
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
        "params": {
            "capital": CAPITAL,
            "leverage": LEVERAGE,
            "num_levels": NUM_LEVELS,
            "spacing_pct": SPACING_PCT,
            "mode": MODE,
            "max_loss_pct": 20,
        },
        "signal_stats": {
            "signal1_rsi_stoch": s1_count,
            "signal2_ema_trend": s2_count,
            "signal3_bb_squeeze": s3_count,
        },
        "results": {},
    }

    for name, r in results.items():
        output["results"][name] = {
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

    json_path = "C:/Users/tony_/Documents/niam-bay/trading/results_signal_v2.json"
    with open(json_path, "w") as f:
        json.dump(output, f, indent=2)

    print()
    print(f"Résultats JSON: {json_path}")
    print()
    print("Backtest terminé.")
