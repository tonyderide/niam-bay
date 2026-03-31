#!/usr/bin/env python3
"""
check_signal.py — Verifie le signal EMA_TREND pour Martin Grid (multi-paires)

Usage:
    python scripts/check_signal.py              # BTC/USD par defaut
    python scripts/check_signal.py --pair ETH   # ETH/USD
    python scripts/check_signal.py --all        # Toutes les paires

Signaux verifies:
    EMA_TREND:     EMA50 > EMA200 AND RSI(14) > 50      (win rate 78.1%)
    EMA_CONFIRMED: EMA_TREND pour 3 candles consecutives + RSI > 50 pour 2 consecutives
    Circuit breaker: avertissement si RSI < 35
"""

import sys
import urllib.request
import json
import time

PAIRS = {
    "BTC": ("XXBTZUSD", "BTC/USD"),
    "ETH": ("XETHZUSD", "ETH/USD"),
    "SOL": ("SOLUSD", "SOL/USD"),
    "DOT": ("DOTUSD", "DOT/USD"),
}

INTERVAL = 60  # 1h candles
N_CANDLES = 250  # need 200+ for EMA200


def http_get(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "niam-bay-signal/2.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"Erreur reseau: {e}", file=sys.stderr)
        return None


def calc_ema(closes, period):
    if len(closes) < period:
        return [None] * len(closes)
    result = [None] * (period - 1)
    sma = sum(closes[:period]) / period
    result.append(sma)
    k = 2.0 / (period + 1)
    for i in range(period, len(closes)):
        result.append(closes[i] * k + result[-1] * (1 - k))
    return result


def calc_rsi(closes, period=14):
    if len(closes) < period + 1:
        return [None] * len(closes)
    result = [None] * period
    gains, losses = [], []
    for i in range(1, period + 1):
        d = closes[i] - closes[i - 1]
        gains.append(max(d, 0))
        losses.append(max(-d, 0))
    avg_g = sum(gains) / period
    avg_l = sum(losses) / period

    def rsi_val(ag, al):
        if al == 0:
            return 100.0
        return 100 - (100 / (1 + ag / al))

    result.append(rsi_val(avg_g, avg_l))
    for i in range(period + 1, len(closes)):
        d = closes[i] - closes[i - 1]
        avg_g = (avg_g * (period - 1) + max(d, 0)) / period
        avg_l = (avg_l * (period - 1) + max(-d, 0)) / period
        result.append(rsi_val(avg_g, avg_l))
    return result


def calc_stochastic(highs, lows, closes, k_period=14):
    n = len(closes)
    k_list = [None] * n
    for i in range(k_period - 1, n):
        lo = min(lows[i - k_period + 1: i + 1])
        hi = max(highs[i - k_period + 1: i + 1])
        if hi == lo:
            k_list[i] = 50.0
        else:
            k_list[i] = (closes[i] - lo) / (hi - lo) * 100
    return k_list


def check_pair(kraken_pair, pair_label):
    """Check signals for a single pair. Returns dict with results."""
    since = int(time.time()) - N_CANDLES * 3600 - 3600
    url = f"https://api.kraken.com/0/public/OHLC?pair={kraken_pair}&interval={INTERVAL}&since={since}"
    data = http_get(url)

    if not data:
        return None

    errors = data.get("error", [])
    if errors:
        print(f"  Erreur Kraken ({pair_label}): {errors}", file=sys.stderr)
        return None

    result = data.get("result", {})
    ohlc_key = [k for k in result.keys() if k != "last"]
    if not ohlc_key:
        return None

    ohlc = result[ohlc_key[0]]
    if not ohlc:
        return None

    closes = [float(c[4]) for c in ohlc]
    highs = [float(c[2]) for c in ohlc]
    lows = [float(c[3]) for c in ohlc]

    if len(closes) < 205:
        return {"error": f"Donnees insuffisantes ({len(closes)} candles)"}

    current_price = closes[-1]

    # Compute indicators
    ema50_series = calc_ema(closes, 50)
    ema200_series = calc_ema(closes, 200)
    rsi_series = calc_rsi(closes, 14)
    stoch_series = calc_stochastic(highs, lows, closes, 14)

    ema50_val = ema50_series[-1]
    ema200_val = ema200_series[-1]
    rsi_val = rsi_series[-1] if rsi_series[-1] is not None else 50.0
    stoch_val = stoch_series[-1] if stoch_series[-1] is not None else 50.0

    # EMA_TREND
    cond_ema = ema50_val is not None and ema200_val is not None and ema50_val > ema200_val
    cond_rsi = rsi_val > 50
    ema_trend = cond_ema and cond_rsi

    # EMA_CONFIRMED: 3 consecutive EMA cross + 2 consecutive RSI > 50
    ema_confirmed = False
    if len(ema50_series) >= 3 and len(rsi_series) >= 2:
        ema_cross_3 = all(
            ema50_series[-(i+1)] is not None and ema200_series[-(i+1)] is not None
            and ema50_series[-(i+1)] > ema200_series[-(i+1)]
            for i in range(3)
        )
        rsi_above_2 = all(
            rsi_series[-(i+1)] is not None and rsi_series[-(i+1)] > 50
            for i in range(2)
        )
        ema_confirmed = ema_cross_3 and rsi_above_2

    # Circuit breaker
    circuit_breaker_rsi = rsi_val < 35
    circuit_breaker_stoch = circuit_breaker_rsi and stoch_val < 20

    return {
        "pair": pair_label,
        "price": current_price,
        "ema50": ema50_val,
        "ema200": ema200_val,
        "rsi": rsi_val,
        "stoch_k": stoch_val,
        "ema_cross": cond_ema,
        "rsi_above_50": cond_rsi,
        "ema_trend": ema_trend,
        "ema_confirmed": ema_confirmed,
        "circuit_breaker_rsi": circuit_breaker_rsi,
        "circuit_breaker_stoch": circuit_breaker_stoch,
    }


def print_single(r):
    """Print detailed signal for a single pair."""
    if r is None:
        print("  Erreur: impossible de recuperer les donnees.")
        return
    if "error" in r:
        print(f"  {r['error']}")
        return

    ok = "ok"
    no = "!!"

    print()
    print(f"  {r['pair']} actuel:  ${r['price']:,.2f}")
    print(f"  EMA 50       :  ${r['ema50']:,.2f}  [{ok if r['ema_cross'] else no}]")
    print(f"  EMA 200      :  ${r['ema200']:,.2f}")
    print(f"  RSI(14)      :  {r['rsi']:.1f}  [{ok if r['rsi_above_50'] else no}]")
    print(f"  Stoch %K     :  {r['stoch_k']:.1f}")
    print()

    # EMA_TREND
    if r["ema_trend"]:
        print("  [EMA_TREND]     OUVRIR GRID  (EMA50>EMA200 + RSI>50)")
    else:
        reason = "EMA50<EMA200" if not r["ema_cross"] else f"RSI {r['rsi']:.1f}<50"
        print(f"  [EMA_TREND]     ATTENDRE  ({reason})")

    # EMA_CONFIRMED
    if r["ema_confirmed"]:
        print("  [EMA_CONFIRMED] OUVRIR GRID  (3 candles EMA cross + 2 candles RSI>50)")
    else:
        print("  [EMA_CONFIRMED] ATTENDRE")

    # Circuit breakers
    if r["circuit_breaker_rsi"]:
        print(f"  [CIRCUIT BREAKER] RSI = {r['rsi']:.1f} < 35 — NE PAS OUVRIR")
    if r["circuit_breaker_stoch"]:
        print(f"  [CIRCUIT BREAKER] RSI {r['rsi']:.1f} + Stoch {r['stoch_k']:.1f} — DANGER EXTREME")

    print()
    # Final verdict
    if r["circuit_breaker_rsi"]:
        print("  " + "=" * 40)
        print("  VERDICT: NE PAS OUVRIR (circuit breaker)")
        print("  " + "=" * 40)
    elif r["ema_trend"]:
        print("  " + "=" * 40)
        print("  VERDICT: OUVRIR GRID MARTIN")
        confirmed = " (CONFIRME)" if r["ema_confirmed"] else " (non confirme)"
        print(f"  EMA_TREND actif{confirmed}")
        print("  " + "=" * 40)
    else:
        print("  " + "=" * 40)
        print("  VERDICT: ATTENDRE")
        print("  " + "=" * 40)


def print_table(results):
    """Print signal table for all pairs."""
    print()
    print(f"  {'Paire':<10} {'Prix':>12} {'EMA50':>10} {'EMA200':>10} {'RSI':>6} {'Stoch':>6} {'EMA_TREND':>10} {'CONFIRMED':>10} {'CB':>6}")
    print("  " + "-" * 86)

    for r in results:
        if r is None or "error" in r:
            pair = r.get("pair", "?") if r else "?"
            print(f"  {pair:<10} {'ERREUR':>12}")
            continue

        ema_str = "OUVRIR" if r["ema_trend"] else "ATTENDRE"
        conf_str = "OUVRIR" if r["ema_confirmed"] else "ATTENDRE"
        cb_str = ""
        if r["circuit_breaker_stoch"]:
            cb_str = "DANGER"
        elif r["circuit_breaker_rsi"]:
            cb_str = "WARN"
        else:
            cb_str = "-"

        print(
            f"  {r['pair']:<10} "
            f"${r['price']:>10,.2f} "
            f"${r['ema50']:>8,.0f} "
            f"${r['ema200']:>8,.0f} "
            f"{r['rsi']:>5.1f} "
            f"{r['stoch_k']:>5.1f} "
            f"{ema_str:>10} "
            f"{conf_str:>10} "
            f"{cb_str:>6}"
        )

    print()


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Check Martin Grid signal (EMA_TREND)")
    parser.add_argument("--pair", type=str, default="BTC",
                        help="Pair to check: BTC, ETH, SOL, DOT (default: BTC)")
    parser.add_argument("--all", action="store_true",
                        help="Check all pairs")
    args = parser.parse_args()

    print("Chargement signaux Martin Grid...", flush=True)

    if args.all:
        # Check all pairs
        results = []
        for short_name, (kraken_pair, label) in PAIRS.items():
            print(f"  {label}...", end="", flush=True)
            r = check_pair(kraken_pair, label)
            if r:
                r["pair"] = label
            results.append(r)
            print(" ok" if r and "error" not in r else " erreur")
            time.sleep(1)  # Rate limit

        print_table(results)

        # Summary
        open_pairs = [r["pair"] for r in results if r and "error" not in r and r["ema_trend"]]
        if open_pairs:
            print(f"  Signal OUVRIR actif sur: {', '.join(open_pairs)}")
        else:
            print("  Aucune paire avec signal OUVRIR.")

        cb_pairs = [r["pair"] for r in results if r and "error" not in r and r["circuit_breaker_rsi"]]
        if cb_pairs:
            print(f"  Circuit breaker RSI<35 sur: {', '.join(cb_pairs)}")

    else:
        # Single pair
        short = args.pair.upper()
        if short not in PAIRS:
            print(f"Paire inconnue: {short}. Disponibles: {', '.join(PAIRS.keys())}")
            sys.exit(1)

        kraken_pair, label = PAIRS[short]
        r = check_pair(kraken_pair, label)
        print_single(r)


if __name__ == "__main__":
    main()
