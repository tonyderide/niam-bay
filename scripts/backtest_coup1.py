#!/usr/bin/env python3
"""Backtest du coup n°1 du mode audace (mandat capital NB, 2026-10-15).

Setup : short DOT quand BTC ET DOT sont en DOWNTREND (EMA50 < EMA200, 1h),
que le prix remonte toucher l'EMA50 de DOT et que le RSI14 de DOT est > 45.
Entrée à l'EMA50, SL +SL_PCT, TP -TP_PCT. Si SL et TP sont touchés dans la même bougie : on compte le SL (hypothèse pessimiste).
Une position à la fois. Les frais taker (aller + retour) sont appliqués sur le notionnel, à LEV x.
Données : klines 1h Binance (DOTUSDT, BTCUSDT), ~DAYS jours.
"""
import json, sys, time, urllib.request

DAYS = int(sys.argv[1]) if len(sys.argv) > 1 else 90
SL_PCT, TP_PCT, LEV, FEE = 0.023, 0.045, 20, 0.0005


def klines(sym, days):
    end = int(time.time() * 1000)
    start = end - days * 86400_000 - 250 * 3600_000  # + warmup EMA200
    out = []
    while start < end:
        url = f"https://api.binance.com/api/v3/klines?symbol={sym}&interval=1h&limit=1000&startTime={start}"
        rows = json.load(urllib.request.urlopen(url, timeout=20))
        if not rows:
            break
        out += rows
        start = rows[-1][0] + 3600_000
    return {r[0]: (float(r[2]), float(r[3]), float(r[4])) for r in out}  # t -> (high, low, close)


def ema(vals, n):
    k, e, res = 2 / (n + 1), None, []
    for v in vals:
        e = v if e is None else v * k + e * (1 - k)
        res.append(e)
    return res


def rsi(closes, n=14):
    res, ag, al = [None] * len(closes), 0.0, 0.0
    for i in range(1, len(closes)):
        d = closes[i] - closes[i - 1]
        g, l = max(d, 0), max(-d, 0)
        if i <= n:
            ag += g / n; al += l / n
        else:
            ag = (ag * (n - 1) + g) / n; al = (al * (n - 1) + l) / n
        if i >= n:
            res[i] = 100 if al == 0 else 100 - 100 / (1 + ag / al)
    return res


dot, btc = klines("DOTUSDT", DAYS), klines("BTCUSDT", DAYS)
ts = sorted(set(dot) & set(btc))
dc = [dot[t][2] for t in ts]; bc = [btc[t][2] for t in ts]
d50, d200, b50, b200, r = ema(dc, 50), ema(dc, 200), ema(bc, 50), ema(bc, 200), rsi(dc)

trades, pos = [], None
for i in range(201, len(ts)):
    hi, lo, _ = dot[ts[i]]
    if pos:
        entry, sl, tp = pos
        if hi >= sl:
            trades.append(-SL_PCT); pos = None
        elif lo <= tp:
            trades.append(TP_PCT); pos = None
        continue
    # signal évalué sur la bougie précédente (pas de look-ahead), entrée si le prix touche l'EMA50 précédente
    j = i - 1
    if b50[j] < b200[j] and d50[j] < d200[j] and r[j] and r[j] > 45 and dc[j] < d50[j] and hi >= d50[j]:
        e = d50[j]
        pos = (e, e * (1 + SL_PCT), e * (1 - TP_PCT))

n = len(trades); w = sum(1 for t in trades if t > 0)
cap = 1.0; ruin = False
for t in trades:
    cap *= max(0.0, 1 + LEV * t - 2 * FEE * LEV)
    if cap <= 0.05:
        ruin = True
be = SL_PCT / (SL_PCT + TP_PCT)
print(f"jours={DAYS} bougies={len(ts)} trades={n} gagnants={w} winrate={w / n if n else 0:.1%} breakeven≈{be:.1%} (hors frais)")
print(f"séquence={''.join('W' if t > 0 else 'L' for t in trades)}")
print(f"capital x{cap:.3f} en enchaînant tout à {LEV}x (all-in) | ruine={'oui' if ruin else 'non'}")
