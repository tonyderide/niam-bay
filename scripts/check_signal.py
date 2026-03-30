#!/usr/bin/env python3
"""
check_signal.py — Vérifie si le signal EMA_TREND est actif pour Martin Grid BTC/USD

Usage:
    python scripts/check_signal.py

Sortie:
    OUVRIR GRID  ou  ATTENDRE
    avec les valeurs EMA50, EMA200, RSI actuelles.

Signal EMA_TREND (meilleur signal backtesté, win rate 78.1%):
    EMA50 > EMA200  AND  RSI(14) > 50
"""

import sys
import urllib.request
import json
import time

PAIR = "XXBTZUSD"
INTERVAL = 60  # minutes (1h candles)
N_CANDLES = 250  # besoin d'au moins 200 pour EMA200


def http_get(url: str):
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"Erreur réseau: {e}", file=sys.stderr)
        sys.exit(1)


def ema(closes: list, period: int) -> float:
    """Calcule l'EMA sur les closes, retourne la valeur finale."""
    k = 2.0 / (period + 1)
    val = closes[0]
    for c in closes[1:]:
        val = c * k + val * (1 - k)
    return val


def rsi(closes: list, period: int = 14) -> float:
    """Calcule le RSI sur les dernières closes."""
    if len(closes) < period + 1:
        return 50.0
    gains, losses = [], []
    for i in range(1, period + 1):
        delta = closes[-period - 1 + i] - closes[-period - 1 + i - 1]
        if delta >= 0:
            gains.append(delta)
            losses.append(0.0)
        else:
            gains.append(0.0)
            losses.append(-delta)
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1 + rs))


def main():
    print("Chargement données BTC/USD 1h (Kraken)...", flush=True)
    since = int(time.time()) - N_CANDLES * 3600 - 3600
    url = f"https://api.kraken.com/0/public/OHLC?pair={PAIR}&interval={INTERVAL}&since={since}"
    data = http_get(url)

    errors = data.get("error", [])
    if errors:
        print(f"Erreur Kraken: {errors}", file=sys.stderr)
        sys.exit(1)

    result = data.get("result", {})
    ohlc = result.get(PAIR, result.get("XXBTZUSD", []))
    if not ohlc:
        print("Aucune donnée OHLC reçue.", file=sys.stderr)
        sys.exit(1)

    # ohlc: [time, open, high, low, close, vwap, volume, count]
    closes = [float(c[4]) for c in ohlc]

    if len(closes) < 205:
        print(f"Données insuffisantes ({len(closes)} candles). Besoin de 205+.", file=sys.stderr)
        sys.exit(1)

    current_price = closes[-1]
    ema50_val = ema(closes[-50:], 50)
    ema200_val = ema(closes[-200:], 200)
    rsi_val = rsi(closes, 14)

    cond_ema = ema50_val > ema200_val
    cond_rsi = rsi_val > 50

    print()
    print(f"BTC/USD actuel :  ${current_price:,.0f}")
    print(f"EMA 50         :  ${ema50_val:,.0f}  {'✓' if cond_ema else '✗'}")
    print(f"EMA 200        :  ${ema200_val:,.0f}  {'✓' if not cond_ema else '✓'}")
    print(f"RSI(14)        :  {rsi_val:.1f}  {'✓' if cond_rsi else '✗'}")
    print()

    if cond_ema and cond_rsi:
        print("━" * 40)
        print("  SIGNAL: OUVRIR GRID MARTIN")
        print("  (EMA_TREND actif — win rate historique 78.1%)")
        print("━" * 40)
    elif not cond_ema:
        print("━" * 40)
        print("  SIGNAL: ATTENDRE")
        print(f"  (EMA50 < EMA200 — bear market potentiel)")
        print("━" * 40)
    else:
        print("━" * 40)
        print("  SIGNAL: ATTENDRE")
        print(f"  (RSI {rsi_val:.1f} < 50 — momentum faible)")
        print("━" * 40)


if __name__ == "__main__":
    main()
