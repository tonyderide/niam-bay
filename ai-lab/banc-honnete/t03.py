import json, time, urllib.request, random, calendar
ts = lambda d: calendar.timegm(time.strptime(d, "%Y-%m-%d")); FEE = 0.0005
def get(sym, res, a, b):
    step = {"1h": 3600, "4h": 14400}[res]; out = {}; t = a - 100*step
    while t < b:
        for _ in range(8):
            try: d = json.load(urllib.request.urlopen(f"https://futures.kraken.com/api/charts/v1/trade/{sym}/{res}?from={t}&to={min(b, t+1800*step)}", timeout=60))["candles"]; break
            except Exception: time.sleep(3)
        for c in d: out[c["time"]//1000] = tuple(float(c[x]) for x in ("open","high","low","close"))
        t += 1800*step; time.sleep(0.2)
    T = sorted(out); return T, [out[x] for x in T]
def supertrend(C):
    n = len(C); tr = [C[0][1]-C[0][2]] + [max(C[i][1]-C[i][2], abs(C[i][1]-C[i-1][3]), abs(C[i][2]-C[i-1][3])) for i in range(1, n)]
    atr = [tr[0]]; [atr.append(atr[-1] + (tr[i]-atr[-1])/10) for i in range(1, n)]
    d = [1]*n; up = [0]*n; dn = [0]*n
    for i in range(n):
        hl2 = (C[i][1]+C[i][2])/2; u = hl2 - 3*atr[i]; l = hl2 + 3*atr[i]
        if i: 
            u = max(u, up[i-1]) if C[i-1][3] > up[i-1] else u
            l = min(l, dn[i-1]) if C[i-1][3] < dn[i-1] else l
            d[i] = 1 if (d[i-1] == -1 and C[i][3] > dn[i-1]) else -1 if (d[i-1] == 1 and C[i][3] < up[i-1]) else d[i-1]
        up[i], dn[i] = u, l
    return d
def equity(C, flips, dirs):  # flips: indices d'entrée (open), dirs: sens
    eq = 1.0
    for k, i in enumerate(flips):
        j = flips[k+1] if k+1 < len(flips) else len(C)-1
        px_out = C[j][0] if k+1 < len(flips) else C[j][3]
        eq *= (1 + dirs[k]*(px_out/C[i][0]-1) - 2*FEE)
    return eq-1
SYM = {"BTC": "PF_XBTUSD", "ETH": "PF_ETHUSD", "SOL": "PF_SOLUSD"}
ok = True
for res in ("1h", "4h"):
    for per, a, b in (("2024-2025", ts("2024-01-01"), ts("2026-01-01")), ("2026", ts("2026-01-01"), ts("2026-10-17"))):
        S = []; R = [0]*500; pos = 0
        for k, s in SYM.items():
            T, C = get(s, res, a, b); d = supertrend(C); lo = next(i for i, t in enumerate(T) if t >= a)
            fl = [i+1 for i in range(lo, len(C)-1) if d[i] != d[i-1]]; dirs = [d[i-1] for i in fl]
            r = equity(C, fl, dirs); S.append(r); pos += r > 0; bh = C[-1][3]/C[lo][0]-1
            for j in range(500):
                rnd = random.Random(j); f2 = sorted(rnd.sample(range(lo+1, len(C)-1), len(fl))); s0 = rnd.choice((1,-1))
                R[j] += equity(C, f2, [s0*(-1)**m for m in range(len(f2))])
            print(f"{res} {per:9} {k}: trades {len(fl):4} | total {r*100:+7.1f} % | [garder {bh*100:+.0f} %]", flush=True)
        R.sort(); tot = sum(S)
        good = all(x > 0 for x in S) if False else (tot > 0 and tot > R[475] and (per != "2024-2025" or pos >= 2))
        ok &= good; print(f"   somme {tot*100:+.1f} % | hasard p95 {R[475]*100:+.1f} % | {'OK' if good else 'NON'}")
print("VERDICT :", "GAGNE" if ok else "PERD")
