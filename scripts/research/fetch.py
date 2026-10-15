#!/usr/bin/env python3
"""Télécharge des klines Binance (spot) en cache CSV. Usage: fetch.py OUTDIR INTERVAL DAYS SYM..."""
import csv, json, os, sys, time, urllib.request
out, itv, days, syms = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4:]
step = {"1h": 3600_000, "4h": 14400_000, "1d": 86400_000}[itv]
for s in syms:
    path = f"{out}/{s}_{itv}.csv"
    if os.path.exists(path):
        continue
    end = int(time.time() * 1000); start = end - days * 86400_000; rows = []
    while start < end:
        u = f"https://api.binance.com/api/v3/klines?symbol={s}&interval={itv}&limit=1000&startTime={start}"
        r = json.load(urllib.request.urlopen(u, timeout=30))
        if not r: break
        rows += r; start = r[-1][0] + step
    with open(path, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["t", "o", "h", "l", "c", "v"])
        for k in rows: w.writerow([k[0], k[1], k[2], k[3], k[4], k[5]])
    print(s, len(rows))
