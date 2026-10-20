import json, time, urllib.request, random, calendar
ts = lambda d: calendar.timegm(time.strptime(d, "%Y-%m-%d")); FEE = 0.001
def h1(sym, a, b):
    out = {}; t = a - 400*3600
    while t < b:
        for _ in range(8):
            try: d = json.load(urllib.request.urlopen(f"https://futures.kraken.com/api/charts/v1/trade/{sym}/1h?from={t}&to={min(b, t+1800*3600)}", timeout=60))["candles"]; break
            except Exception: time.sleep(3)
        for c in d: out[c["time"]//1000] = tuple(float(c[x]) for x in ("open","high","low","close"))
        t += 1800*3600; time.sleep(0.2)
    T = sorted(out); return T, [out[x] for x in T]
def ema(xs, n):
    e = xs[0]; o = []
    for x in xs: e += (x-e)*2/(n+1); o.append(e)
    return o
def walk(C, i, s, dist, n):  # suit le trade depuis l'open i ; renvoie rendement net
    ent = C[i][0]; sl = ent*(1-s*dist); tp = ent*(1+s*1.5*dist)
    for j in range(i, n):
        o, h, l, c = C[j]
        if (s > 0 and l <= sl) or (s < 0 and h >= sl): return -dist - FEE, j
        if (s > 0 and h >= tp) or (s < 0 and l <= tp): return 1.5*dist - FEE, j
    return s*(C[n-1][3]/ent-1) - FEE, n-1
def run(T, C, a):
    cl = [c[3] for c in C]; e200 = ema(cl, 200); m = [x-y for x, y in zip(ema(cl, 12), ema(cl, 26))]; sg = ema(m, 9)
    n = len(C); i = 1; tr = []
    while i < n-1:
        if T[i] >= a and i > 300:
            up = m[i-1] <= sg[i-1] and m[i] > sg[i] and m[i] < 0 and sg[i] < 0 and cl[i] > e200[i]
            dn = m[i-1] >= sg[i-1] and m[i] < sg[i] and m[i] > 0 and sg[i] > 0 and cl[i] < e200[i]
            if up or dn:
                s = 1 if up else -1; dist = max(.003, abs(C[i+1][0]-e200[i])/C[i+1][0])
                r, j = walk(C, i+1, s, dist, n); tr.append((r, dist)); i = j+1; continue
        i += 1
    return tr
def null(C, T, a, tr, rnd):
    lo = next(k for k, t in enumerate(T) if t >= a); tot = 0
    for _, dist in tr:
        i = rnd.randrange(lo, len(C)-2); tot += walk(C, i, rnd.choice((1,-1)), dist, len(C))[0]
    return tot
SYM = {"BTC": "PF_XBTUSD", "ETH": "PF_ETHUSD", "SOL": "PF_SOLUSD"}
ok = True
for per, a, b in (("2024-2025", ts("2024-01-01"), ts("2026-01-01")), ("2026 jan-oct", ts("2026-01-01"), ts("2026-10-17"))):
    print(f"== {per} =="); S = 0; pos = 0; N = 0; R = [0]*500
    for k, s in SYM.items():
        T, C = h1(s, a, b); tr = run(T, C, a); net = sum(r for r, _ in tr); S += net; pos += net > 0; N += len(tr)
        for j in range(500): R[j] += null(C, T, a, tr, random.Random(j))
        print(f"  {k}: trades {len(tr):4} | gagnants {sum(r>0 for r,_ in tr)/max(1,len(tr)):.0%} | net {net*100:+.1f} %", flush=True)
    R.sort(); print(f"  SOMME {S*100:+.1f} % | hasard médiane {R[250]*100:+.1f} % p95 {R[475]*100:+.1f} %")
    ok &= S > 0 and S > R[475] and N >= 30 and (per != "2024-2025" or pos >= 2)
print("VERDICT :", "GAGNE" if ok else "PERD")
