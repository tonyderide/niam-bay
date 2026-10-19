import json, time, urllib.request, random
M = 60; ts = lambda d: int(time.mktime(time.strptime(d, "%Y-%m-%d")))
def candles(sym):
    out = {}; t = ts("2026-01-01"); end = ts("2026-10-17")
    while t < end:
        try: d = json.load(urllib.request.urlopen(f"https://futures.kraken.com/api/charts/v1/trade/{sym}/1m?from={t}&to={min(end, t+1800*M)}", timeout=60))["candles"]
        except Exception: time.sleep(3); continue
        for c in d: out[c["time"]//1000] = (float(c["open"]), float(c["high"]), float(c["low"]), float(c["close"]), float(c["volume"]))
        t += 1800*M; time.sleep(0.15)
    b = {}
    for t, v in out.items():
        k = t // 180 * 180; o = b.get(k)
        b[k] = v if o is None else (o[0], max(o[1], v[1]), min(o[2], v[2]), v[3], o[4] + v[4])
    T = sorted(b); return T, [b[t] for t in T]
def run(T, C, exe, fee, rnd=None, nflip=None):
    n = len(C); e = C[0][3]; pv = vv = 0; day = None; sig = [0]*n
    for i in range(n):
        o, h, l, c, v = C[i]; d = T[i] // 86400
        if d != day: pv = vv = 0; day = d
        pv += (h+l+c)/3*v; vv += v; vw = pv/vv if vv else c
        e = c if i == 0 else e + (c-e)*2/10
        sig[i] = 1 if e > vw else -1
    flips = [i for i in range(1, n) if sig[i] != sig[i-1]]
    if rnd is not None: flips = sorted(rnd.sample(range(1, n-1), min(nflip, n-2)))
    eq = 1.0; peak = 1.0; dd = 0; pos = 0; entry = None; trades = []
    for i in flips:
        j = i if exe == "A" else i + 1
        if j >= n: break
        px = C[j][3] if exe == "A" else C[j][0]
        if pos != 0: r = pos*(px/entry-1) - fee; trades.append(r); eq *= 1+r; peak = max(peak, eq); dd = min(dd, eq/peak-1)
        pos = (sig[i] if rnd is None else (-pos if pos else 1)); entry = px; eq *= 1 - fee
    return eq-1, dd, trades, len(flips)
SYM = {"BTC": "PF_XBTUSD", "ETH": "PF_ETHUSD", "SOL": "PF_SOLUSD"}
D = {k: candles(s) for k, s in SYM.items()}
cut = ts("2026-07-01")
for per, f in (("JANVIER-JUIN", lambda t: t < cut), ("JUILLET-OCTOBRE (jamais vue)", lambda t: t >= cut)):
    print(f"\n== {per} ==")
    for k, (T, C) in D.items():
        idx = [i for i, t in enumerate(T) if f(t)]; T2 = [T[i] for i in idx]; C2 = [C[i] for i in idx]
        for exe, fee, lab in (("A", 0.0005, "clôture, taker"), ("B", 0.0005, "bougie suivante, taker"), ("B", 0.0002, "bougie suivante, maker")):
            r, dd, tr, nf = run(T2, C2, exe, fee)
            line = f"{k} {lab:24} trades {len(tr):5} | gagnants {sum(x>0 for x in tr)/max(1,len(tr)):4.0%} | net moyen {sum(tr)/max(1,len(tr))*100:+.3f} % | total {r*100:+8.1f} % | pire creux {dd*100:5.0f} %"
            if exe == "B" and fee == 0.0005:
                rnd = random.Random(0); R = sorted(run(T2, C2, "B", fee, rnd, nf)[0] for _ in range(200)); line += f" | hasard p95 {R[190]*100:+.1f} %"
            print(line, flush=True)
